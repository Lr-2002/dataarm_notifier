"""Telemetry Producer - Main class for sending telemetry data to Rerun viewer."""

import asyncio
import logging
import time
from typing import Optional

import cv2
import numpy as np
import rerun as rr

from .config import TelemetryConfig
from .data_types import (
    DashboardState,
    EventLog,
    TelemetryDataPoint,
    TelemetryThresholds,
)
from .enums import StatusLevel
from .simulation import SimulationData
from .can_metrics_server import CANMetricsServer
from .arm_telemetry_server import ArmTelemetryServer

logger = logging.getLogger(__name__)


class TelemetryProducer:
    """Producer class for sending robot telemetry data to Rerun viewer.

    This class handles:
    - Position tracking (Target vs Actual)
    - Dynamics monitoring (velocity, torque, acceleration)
    - Camera feed streaming
    - System health alerts and event logging
    - CAN metrics server for receiving data from can_monitor
    """

    def __init__(
        self,
        app_name: str = "Robot_Telemetry",
        config_path: Optional[str] = None,
        connect: Optional[str] = None,
    ):
        """Initialize the telemetry producer.

        Args:
            app_name: Name shown in Rerun viewer
            config_path: Path to YAML config file
            connect: TCP address to connect to existing viewer (e.g., "127.0.0.1:9876")
        """
        self.app_name = app_name
        self.config = TelemetryConfig.load(config_path)
        self.thresholds: TelemetryThresholds = self.config.thresholds

        self._start_time: float = time.time()
        self._last_status: StatusLevel = StatusLevel.INFO
        self._event_logged: set = set()  # Track logged events to avoid duplicates

        # CAN metrics server (optional)
        self._can_server: Optional[CANMetricsServer] = None
        self._can_server_task: Optional[asyncio.Task] = None
        self._arm_server: Optional[ArmTelemetryServer] = None
        self._arm_server_task: Optional[asyncio.Task] = None

        # Initialize Rerun
        if connect:
            rr.init(app_name, spawn=False)
            rr.connect(connect)
            logger.info(f"Connected to Rerun viewer at {connect}")
        else:
            rr.init(app_name, spawn=True)
            logger.info(f"Started Rerun viewer: {app_name}")

        logger.info(f"TelemetryProducer initialized with frequency: {self.config.frequency}Hz")

    def _get_elapsed(self) -> float:
        """Get elapsed time since initialization."""
        return time.time() - self._start_time

    # =========================================================================
    # User Story 1: Motion Tracking
    # =========================================================================

    def log_position(
        self, target: float, actual: float, timestamp: Optional[float] = None
    ) -> tuple[float, StatusLevel, str]:
        """Log target and actual position for tracking visualization.

        Args:
            target: Commanded position (radians)
            actual: Measured position (radians)
            timestamp: Optional timestamp, auto-generated if None

        Returns:
            Tuple of (elapsed_time, status, message)
        """
        elapsed = timestamp if timestamp is not None else self._get_elapsed()

        # Log to Rerun with shared path prefix for auto-grouping
        rr.log("drive/pos/target", rr.Scalars(target))
        rr.log("drive/pos/actual", rr.Scalars(actual))

        # Check thresholds and get status
        status, message = self.check_thresholds(target, actual, 0.0)

        return elapsed, status, message

    def check_thresholds(
        self, target: float, actual: float, torque: float
    ) -> tuple[StatusLevel, str]:
        """Check data against thresholds and return status.

        Args:
            target: Target position
            actual: Actual position
            torque: Motor torque

        Returns:
            Tuple of (StatusLevel, message)
        """
        tracking_error = abs(target - actual)

        # Determine status based on thresholds
        if self.thresholds.check_torque_error(torque):
            return StatusLevel.ERROR, f"Torque Critical: {torque:.2f}Nm"
        elif self.thresholds.check_tracking(tracking_error):
            return StatusLevel.ERROR, f"Tracking Deviation High: {tracking_error:.3f}rad"
        elif self.thresholds.check_torque_warning(torque):
            return StatusLevel.WARNING, f"High Torque Load: {torque:.2f}Nm"
        else:
            return StatusLevel.INFO, "System Nominal"

    # =========================================================================
    # User Story 2: Dynamics Monitoring
    # =========================================================================

    def log_velocity(
        self, raw: float, filtered: float, timestamp: Optional[float] = None
    ) -> None:
        """Log raw and filtered velocity for noise comparison.

        Args:
            raw: Raw velocity measurement (rad/s)
            filtered: Filtered velocity (rad/s)
            timestamp: Optional timestamp
        """
        elapsed = timestamp if timestamp is not None else self._get_elapsed()

        # Log both velocities with shared path prefix for overlay
        rr.log("drive/vel/raw", rr.Scalars(raw))
        rr.log("drive/vel/filtered", rr.Scalars(filtered))

    def log_dynamics(
        self, torque: float, acceleration: float, timestamp: Optional[float] = None
    ) -> None:
        """Log torque and filtered acceleration.

        Args:
            torque: Motor torque (Nm)
            acceleration: Filtered acceleration (rad/s^2)
            timestamp: Optional timestamp
        """
        elapsed = timestamp if timestamp is not None else self._get_elapsed()

        # Log dynamics signals
        rr.log("drive/torque", rr.Scalars(torque))
        rr.log("drive/acc_filtered", rr.Scalars(acceleration))

    # =========================================================================
    # User Story 3: Camera Feed
    # =========================================================================

    def log_camera(self, frame: Optional[np.ndarray]) -> None:
        """Log camera frame to visualization.

        Args:
            frame: RGB image array (H, W, 3) or None for placeholder
        """
        if frame is None:
            # Create placeholder when camera unavailable
            placeholder = np.zeros((240, 320, 3), dtype=np.uint8)
            cv2.putText(
                placeholder,
                "Camera Unavailable",
                (50, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (128, 128, 128),
                2,
            )
            rr.log("sensors/camera_main", rr.Image(placeholder))
            return

        # Ensure RGB format (Rerun expects RGB)
        if len(frame.shape) == 2:
            # Grayscale to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        elif frame.shape[2] == 3:
            # BGR to RGB (OpenCV uses BGR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame

        rr.log("sensors/camera_main", rr.Image(frame_rgb))

    # =========================================================================
    # User Story 4: System Health Alerts
    # =========================================================================

    def update_status(self, level: StatusLevel, message: str) -> None:
        """Update dashboard status display.

        Args:
            level: Status level (INFO/WARNING/ERROR)
            message: Status message
        """
        elapsed = self._get_elapsed()
        self._last_status = level

        # Create markdown dashboard
        icon = level.to_emoji()
        md_text = f"""# System Status: {level.value}
### {icon} {message}
* **Time:** {elapsed:.2f}s
* **Mode:** Auto-Tracking
"""
        rr.log("notify/dashboard", rr.TextDocument(md_text, media_type="text/markdown"))

    def log_event(self, level: StatusLevel, message: str) -> None:
        """Log event to event log (only for WARNING/ERROR).

        Args:
            level: Event severity
            message: Event description
        """
        # Only log WARNING and ERROR events
        if level == StatusLevel.INFO:
            return

        # Create unique event key to avoid duplicate logs
        event_key = f"{level.value}:{message}"

        if event_key in self._event_logged:
            return  # Already logged this event

        elapsed = self._get_elapsed()
        event_text = f"[{elapsed:.2f}] {level.value}: {message}"

        rr.log("notify/log", rr.TextLog(event_text))
        self._event_logged.add(event_key)

        logger.info(f"Event logged: {event_text}")

    def shutdown(self) -> None:
        """Graceful shutdown of producer."""
        elapsed = self._get_elapsed()
        rr.log("notify/dashboard", rr.TextDocument(f"# 🛑 SYSTEM STOPPED\n\nRuntime: {elapsed:.2f}s"))
        logger.info(f"TelemetryProducer shutdown. Total runtime: {elapsed:.2f}s")

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def log_telemetry_data(self, data: TelemetryDataPoint) -> None:
        """Log complete telemetry data point.

        Args:
            data: TelemetryDataPoint with all values
        """
        # Log positions
        self.log_position(data.target_position, data.actual_position, data.timestamp)

        # Log velocities
        self.log_velocity(data.raw_velocity, data.filtered_velocity, data.timestamp)

        # Log dynamics
        self.log_dynamics(data.torque, data.filtered_acceleration, data.timestamp)

        # Check thresholds and update status
        status, message = self.check_thresholds(
            data.target_position, data.actual_position, data.torque
        )

        if status != self._last_status:
            self.update_status(status, message)

        if status in (StatusLevel.WARNING, StatusLevel.ERROR):
            self.log_event(status, message)

    def log_simulation_data(self, data: "SimulationData") -> None:
        """Log simulation data to Rerun.

        Args:
            data: SimulationData from SimulationEngine
        """
        # Log positions
        rr.log("drive/pos/target", rr.Scalars(data.target_position))
        rr.log("drive/pos/actual", rr.Scalars(data.actual_position))

        # Log velocities
        rr.log("drive/vel/raw", rr.Scalars(data.raw_velocity))
        rr.log("drive/vel/filtered", rr.Scalars(data.filtered_velocity))

        # Log dynamics
        rr.log("drive/torque", rr.Scalars(data.torque))
        rr.log("drive/acc_filtered", rr.Scalars(data.filtered_acceleration))

        # Update status
        if data.status != self._last_status:
            self.update_status(data.status, data.status_message)

        if data.status in (StatusLevel.WARNING, StatusLevel.ERROR):
            self.log_event(data.status, data.status_message)

    # =========================================================================
    # CAN Metrics Server Methods (T020)
    # =========================================================================

    def start_can_server(
        self, port: int = 9877, host: str = "127.0.0.1", *, activate_blueprint: bool = True
    ) -> None:
        """Start the CAN metrics TCP server.

        Args:
            port: TCP port to listen on (default: 9877)
            host: Host address to bind (default: 127.0.0.1)
            activate_blueprint: If True, makes the CAN layout active/default in Rerun.
        """
        if self._can_server is not None:
            logger.warning("CAN metrics server already running")
            return

        self._can_server = CANMetricsServer(
            port=port,
            host=host,
            app_name=self.app_name,
            init_rerun=False,
            activate_blueprint=activate_blueprint,
        )
        self._can_server_task = asyncio.create_task(self._can_server.start())
        logger.info(f"CAN metrics server starting on {host}:{port}")

    def stop_can_server(self) -> None:
        """Stop the CAN metrics TCP server."""
        if self._can_server is None:
            return

        asyncio.create_task(self._can_server.stop())
        self._can_server = None
        self._can_server_task = None
        logger.info("CAN metrics server stopped")

    @property
    def can_server(self) -> Optional[CANMetricsServer]:
        """Get the CAN metrics server instance."""
        return self._can_server

    # =========================================================================
    # Arm Telemetry Server Methods
    # =========================================================================

    def start_arm_server(self, port: int = 9878, host: str = "127.0.0.1") -> None:
        """Start the arm telemetry TCP server.

        Args:
            port: TCP port to listen on (default: 9878)
            host: Host address to bind (default: 127.0.0.1)
        """
        if self._arm_server is not None:
            logger.warning("Arm telemetry server already running")
            return

        self._arm_server = ArmTelemetryServer(port=port, host=host, timeline="time_s")
        self._arm_server_task = asyncio.create_task(self._arm_server.start())
        logger.info(f"Arm telemetry server starting on {host}:{port}")

    def stop_arm_server(self) -> None:
        """Stop the arm telemetry TCP server."""
        if self._arm_server is None:
            return

        asyncio.create_task(self._arm_server.stop())
        self._arm_server = None
        self._arm_server_task = None
        logger.info("Arm telemetry server stopped")

    @property
    def arm_server(self) -> Optional[ArmTelemetryServer]:
        return self._arm_server

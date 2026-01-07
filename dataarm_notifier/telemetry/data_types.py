"""Telemetry Data Types - Dataclasses for telemetry data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .enums import ProfileType, StatusLevel


@dataclass
class TelemetryDataPoint:
    """Single telemetry sample at a point in time."""

    timestamp: float
    target_position: float
    actual_position: float
    raw_velocity: float = 0.0
    filtered_velocity: float = 0.0
    filtered_acceleration: float = 0.0
    torque: float = 0.0
    status: StatusLevel = StatusLevel.INFO
    status_message: str = "System Nominal"

    @property
    def tracking_error(self) -> float:
        """Calculate tracking error (absolute difference)."""
        return abs(self.target_position - self.actual_position)


@dataclass
class DashboardState:
    """Current system status displayed on dashboard."""

    status: StatusLevel = StatusLevel.INFO
    message: str = "System Nominal"
    timestamp: float = 0.0
    elapsed_time: float = 0.0
    mode: str = "Auto-Tracking"


@dataclass
class SimulationProfile:
    """Configuration for built-in simulation profile."""

    name: str
    profile_type: ProfileType
    amplitude: float = 1.0
    frequency: float = 0.5
    phase: float = 0.0
    noise: float = 0.0
    lag: float = 0.0
    step_time: float = 0.0
    threshold: float = 1.8
    slope: float = 1.0
    trigger_delay: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "SimulationProfile":
        """Create SimulationProfile from dictionary."""
        return cls(
            name=data.get("name", "default"),
            profile_type=ProfileType.from_value(data.get("type", "sine")),
            amplitude=data.get("amplitude", 1.0),
            frequency=data.get("frequency", 0.5),
            phase=data.get("phase", 0.0),
            noise=data.get("noise", 0.0),
            lag=data.get("lag", 0.0),
            step_time=data.get("step_time", 0.0),
            threshold=data.get("threshold", 1.8),
            slope=data.get("slope", 1.0),
            trigger_delay=data.get("trigger_delay", 0.0),
        )


@dataclass
class EventLog:
    """Timestamped event entry for event log."""

    timestamp: float
    level: StatusLevel
    message: str

    @classmethod
    def from_data(cls, timestamp: float, level: StatusLevel, message: str) -> "EventLog":
        """Create EventLog from telemetry data."""
        return cls(timestamp=timestamp, level=level, message=message)


@dataclass
class TelemetryThresholds:
    """Threshold configuration for alert detection."""

    tracking_deviation: float = 0.3
    torque_warning: float = 1.8
    torque_error: float = 2.5
    velocity_max: float = 5.0

    @classmethod
    def from_dict(cls, data: dict) -> "TelemetryThresholds":
        """Create TelemetryThresholds from dictionary."""
        return cls(
            tracking_deviation=data.get("tracking_deviation", 0.3),
            torque_warning=data.get("torque_warning", 1.8),
            torque_error=data.get("torque_error", 2.5),
            velocity_max=data.get("velocity_max", 5.0),
        )

    def check_tracking(self, error: float) -> bool:
        """Check if tracking deviation exceeds threshold."""
        return error > self.tracking_deviation

    def check_torque_warning(self, torque: float) -> bool:
        """Check if torque exceeds warning threshold."""
        return torque > self.torque_warning

    def check_torque_error(self, torque: float) -> bool:
        """Check if torque exceeds error threshold."""
        return torque > self.torque_error

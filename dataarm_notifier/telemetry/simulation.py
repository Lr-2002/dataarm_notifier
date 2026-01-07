"""Simulation Engine - Built-in simulation profiles for testing without real robot."""

import logging
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .config import TelemetryConfig
from .data_types import SimulationProfile, TelemetryThresholds
from .enums import ProfileType, StatusLevel

logger = logging.getLogger(__name__)


@dataclass
class SimulationData:
    """Data returned from simulation engine."""

    timestamp: float
    target_position: float
    actual_position: float
    raw_velocity: float
    filtered_velocity: float
    filtered_acceleration: float
    torque: float
    status: StatusLevel
    status_message: str


class SimulationEngine:
    """Engine for generating simulated robot telemetry data.

    Supports multiple profile types:
    - SINE: Continuous oscillatory motion
    - STEP: Instant position change
    - RAMP: Linear position change
    - TORQUE_THRESHOLD: Triggers warning at threshold
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize simulation engine.

        Args:
            config_path: Path to YAML config file with profiles
        """
        self.config = TelemetryConfig.load(config_path)
        self.thresholds: TelemetryThresholds = self.config.thresholds

        self._start_time: float = time.time()
        self._current_profile: Optional[SimulationProfile] = None
        self._profile_start: float = 0.0
        self._elapsed: float = 0.0

        # Set default profile
        default_profile = self.config.simulation.get("default_profile", "")
        if default_profile:
            self.set_profile(default_profile)
        elif self.config.list_profiles():
            self.set_profile(self.config.list_profiles()[0])

        logger.info(f"SimulationEngine initialized with {len(self.config.list_profiles())} profiles")

    def list_profiles(self) -> list[str]:
        """List available profile names."""
        return self.config.list_profiles()

    def set_profile(self, profile_name: str) -> bool:
        """Activate a simulation profile by name.

        Args:
            profile_name: Name of profile from config

        Returns:
            True if profile found and activated, False otherwise
        """
        profile = self.config.get_profile(profile_name)
        if profile is None:
            logger.warning(f"Profile '{profile_name}' not found")
            return False

        self._current_profile = profile
        self._profile_start = self._get_elapsed()
        logger.info(f"Activated profile: {profile_name} ({profile.profile_type.value})")
        return True

    def _get_elapsed(self) -> float:
        """Get elapsed time since initialization."""
        return time.time() - self._start_time

    def step(self, dt: float) -> SimulationData:
        """Advance simulation by one time step.

        Args:
            dt: Time step in seconds

        Returns:
            SimulationData with simulated telemetry values
        """
        self._elapsed = self._get_elapsed()

        if self._current_profile is None:
            # Return default if no profile set
            return self._create_default_data()

        profile = self._current_profile
        profile_time = self._elapsed - self._profile_start

        # Generate signals based on profile type
        if profile.profile_type == ProfileType.SINE:
            target, actual, raw_vel, filt_vel, accel, torque = self._sine_profile(
                profile, profile_time
            )
        elif profile.profile_type == ProfileType.STEP:
            target, actual, raw_vel, filt_vel, accel, torque = self._step_profile(
                profile, profile_time
            )
        elif profile.profile_type == ProfileType.RAMP:
            target, actual, raw_vel, filt_vel, accel, torque = self._ramp_profile(
                profile, profile_time
            )
        elif profile.profile_type == ProfileType.TORQUE_THRESHOLD:
            target, actual, raw_vel, filt_vel, accel, torque = self._torque_threshold_profile(
                profile, profile_time
            )
        else:
            target, actual, raw_vel, filt_vel, accel, torque = self._sine_profile(
                profile, profile_time
            )

        # Determine status
        tracking_error = abs(target - actual)
        status, message = self._determine_status(tracking_error, torque)

        return SimulationData(
            timestamp=self._elapsed,
            target_position=target,
            actual_position=actual,
            raw_velocity=raw_vel,
            filtered_velocity=filt_vel,
            filtered_acceleration=accel,
            torque=torque,
            status=status,
            status_message=message,
        )

    def _create_default_data(self) -> SimulationData:
        """Create default simulation data when no profile is active."""
        t = self._elapsed
        target = np.sin(t * 0.5)
        actual = target  # No lag for default
        raw_vel = np.cos(t * 0.5) + np.random.normal(0, 0.1)
        filt_vel = np.cos(t * 0.5)
        accel = -np.sin(t * 0.5)
        torque = 0.5

        return SimulationData(
            timestamp=t,
            target_position=target,
            actual_position=actual,
            raw_velocity=raw_vel,
            filtered_velocity=filt_vel,
            filtered_acceleration=accel,
            torque=torque,
            status=StatusLevel.INFO,
            status_message="System Nominal",
        )

    def _sine_profile(
        self, profile: SimulationProfile, t: float
    ) -> tuple[float, float, float, float, float, float]:
        """Generate sine wave profile.

        Args:
            profile: Simulation profile configuration
            t: Time in seconds

        Returns:
            Tuple of (target, actual, raw_vel, filt_vel, accel, torque)
        """
        target = profile.amplitude * np.sin(2 * np.pi * profile.frequency * t + profile.phase)

        # Actual position with lag
        lag_time = profile.lag if profile.lag > 0 else 0.1
        actual = profile.amplitude * np.sin(
            2 * np.pi * profile.frequency * (t - lag_time) + profile.phase
        )

        # Add noise
        noise = np.random.normal(0, profile.noise) if profile.noise > 0 else 0

        # Derivatives
        filt_vel = 2 * np.pi * profile.frequency * profile.amplitude * np.cos(
            2 * np.pi * profile.frequency * t + profile.phase
        )
        raw_vel = filt_vel + noise
        accel = -(
            2 * np.pi * profile.frequency
        ) ** 2 * profile.amplitude * np.sin(2 * np.pi * profile.frequency * t + profile.phase)

        # Torque (simple model)
        torque = abs(filt_vel * 0.1) + abs(accel * 0.05)

        return target, actual, raw_vel, filt_vel, accel, torque

    def _step_profile(
        self, profile: SimulationProfile, t: float
    ) -> tuple[float, float, float, float, float, float]:
        """Generate step response profile.

        Args:
            profile: Simulation profile configuration
            t: Time in seconds

        Returns:
            Tuple of (target, actual, raw_vel, filt_vel, accel, torque)
        """
        step_time = profile.step_time if profile.step_time > 0 else 2.0

        # Target steps at step_time
        target = profile.amplitude if t >= step_time else 0.0

        # Actual follows with lag (first-order system simulation)
        lag_time = 0.1
        if t >= step_time + lag_time:
            actual = profile.amplitude
        elif t >= step_time:
            actual = profile.amplitude * (t - step_time) / lag_time
        else:
            actual = 0.0

        # Noise
        noise = np.random.normal(0, profile.noise) if profile.noise > 0 else 0

        # Derivatives
        filt_vel = (actual - (profile.amplitude if t >= step_time + lag_time * 2 else 0)) / 0.02
        raw_vel = filt_vel + noise
        accel = 0.0  # Simplified

        # Torque
        torque = abs(filt_vel * 0.1)

        return target, actual, raw_vel, filt_vel, accel, torque

    def _ramp_profile(
        self, profile: SimulationProfile, t: float
    ) -> tuple[float, float, float, float, float, float]:
        """Generate ramp profile.

        Args:
            profile: Simulation profile configuration
            t: Time in seconds

        Returns:
            Tuple of (target, actual, raw_vel, filt_vel, accel, torque)
        """
        slope = profile.slope if profile.slope > 0 else 0.5

        # Target ramps linearly
        target = slope * t

        # Actual follows with lag
        lag_time = 0.1
        actual = max(0, slope * (t - lag_time))

        # Noise
        noise = np.random.normal(0, profile.noise) if profile.noise > 0 else 0

        # Derivatives
        filt_vel = slope
        raw_vel = filt_vel + noise
        accel = 0.0

        # Torque
        torque = 0.5 + abs(filt_vel * 0.05)

        return target, actual, raw_vel, filt_vel, accel, torque

    def _torque_threshold_profile(
        self, profile: SimulationProfile, t: float
    ) -> tuple[float, float, float, float, float, float]:
        """Generate profile that triggers torque warning at threshold.

        Args:
            profile: Simulation profile configuration
            t: Time in seconds

        Returns:
            Tuple of (target, actual, raw_vel, filt_vel, accel, torque)
        """
        threshold = profile.threshold
        trigger_delay = profile.trigger_delay

        # Simple sine motion
        target = np.sin(t * 0.5)
        actual = target

        # Torque increases over time
        torque_progress = min(1.0, max(0, (t - trigger_delay) / 5.0))
        torque = threshold * torque_progress * 1.5  # Go above threshold

        # Noise
        noise = np.random.normal(0, profile.noise) if profile.noise > 0 else 0

        # Derivatives
        filt_vel = 0.5 * np.cos(t * 0.5)
        raw_vel = filt_vel + noise
        accel = -0.25 * np.sin(t * 0.5)

        return target, actual, raw_vel, filt_vel, accel, torque

    def _determine_status(
        self, tracking_error: float, torque: float
    ) -> tuple[StatusLevel, str]:
        """Determine system status based on thresholds.

        Args:
            tracking_error: Tracking deviation
            torque: Current torque

        Returns:
            Tuple of (StatusLevel, message)
        """
        if self.thresholds.check_torque_error(torque):
            return StatusLevel.ERROR, f"Torque Critical: {torque:.2f}Nm"
        elif self.thresholds.check_tracking(tracking_error):
            return StatusLevel.ERROR, f"Tracking Deviation High: {tracking_error:.3f}rad"
        elif self.thresholds.check_torque_warning(torque):
            return StatusLevel.WARNING, f"High Torque Load: {torque:.2f}Nm"
        else:
            return StatusLevel.INFO, "System Nominal"

    def shutdown(self) -> None:
        """Stop simulation and cleanup."""
        logger.info(f"SimulationEngine shutdown. Total runtime: {self._elapsed:.2f}s")

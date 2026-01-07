"""Unit tests for telemetry dataclasses."""

import pytest
from dataclasses import dataclass

from dataarm_notifier.telemetry.data_types import (
    TelemetryDataPoint,
    DashboardState,
    SimulationProfile,
    EventLog,
    TelemetryThresholds,
)
from dataarm_notifier.telemetry.enums import ProfileType, StatusLevel


class TestTelemetryDataPoint:
    """Tests for TelemetryDataPoint dataclass."""

    def test_telemetry_data_point_creation(self):
        """Test creating a TelemetryDataPoint."""
        data = TelemetryDataPoint(
            timestamp=1.0,
            target_position=1.0,
            actual_position=0.9,
            raw_velocity=0.5,
            filtered_velocity=0.45,
            filtered_acceleration=0.1,
            torque=0.5,
            status=StatusLevel.INFO,
            status_message="Test",
        )
        assert data.timestamp == 1.0
        assert data.target_position == 1.0
        assert data.actual_position == 0.9

    def test_telemetry_data_point_defaults(self):
        """Test default values."""
        data = TelemetryDataPoint(timestamp=0.0, target_position=0.0, actual_position=0.0)
        assert data.raw_velocity == 0.0
        assert data.filtered_velocity == 0.0
        assert data.status == StatusLevel.INFO
        assert data.status_message == "System Nominal"

    def test_tracking_error_property(self):
        """Test tracking error calculation."""
        data = TelemetryDataPoint(
            timestamp=0.0,
            target_position=1.0,
            actual_position=0.8,
        )
        assert abs(data.tracking_error - 0.2) < 0.001

    def test_tracking_error_zero(self):
        """Test tracking error when positions match."""
        data = TelemetryDataPoint(
            timestamp=0.0,
            target_position=1.0,
            actual_position=1.0,
        )
        assert data.tracking_error == 0.0


class TestDashboardState:
    """Tests for DashboardState dataclass."""

    def test_dashboard_state_creation(self):
        """Test creating a DashboardState."""
        state = DashboardState(
            status=StatusLevel.INFO,
            message="Test Message",
            timestamp=1.0,
            elapsed_time=5.0,
            mode="Manual",
        )
        assert state.status == StatusLevel.INFO
        assert state.message == "Test Message"
        assert state.elapsed_time == 5.0

    def test_dashboard_state_defaults(self):
        """Test default values."""
        state = DashboardState()
        assert state.status == StatusLevel.INFO
        assert state.message == "System Nominal"
        assert state.elapsed_time == 0.0


class TestSimulationProfile:
    """Tests for SimulationProfile dataclass."""

    def test_simulation_profile_creation(self):
        """Test creating a SimulationProfile."""
        profile = SimulationProfile(
            name="test_profile",
            profile_type=ProfileType.SINE,
            amplitude=2.0,
            frequency=1.0,
            phase=0.5,
            noise=0.1,
            lag=0.02,
        )
        assert profile.name == "test_profile"
        assert profile.profile_type == ProfileType.SINE
        assert profile.amplitude == 2.0

    def test_simulation_profile_defaults(self):
        """Test default values."""
        profile = SimulationProfile(name="default", profile_type=ProfileType.SINE)
        assert profile.amplitude == 1.0
        assert profile.frequency == 0.5
        assert profile.noise == 0.0

    def test_simulation_profile_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "name": "custom",
            "type": "step",
            "amplitude": 1.5,
            "frequency": 0.8,
        }
        profile = SimulationProfile.from_dict(data)
        assert profile.name == "custom"
        assert profile.profile_type == ProfileType.STEP
        assert profile.amplitude == 1.5


class TestEventLog:
    """Tests for EventLog dataclass."""

    def test_event_log_creation(self):
        """Test creating an EventLog."""
        event = EventLog(
            timestamp=1.0,
            level=StatusLevel.WARNING,
            message="High torque detected",
        )
        assert event.timestamp == 1.0
        assert event.level == StatusLevel.WARNING
        assert event.message == "High torque detected"

    def test_event_log_from_data(self):
        """Test creating from data."""
        event = EventLog.from_data(
            timestamp=2.0,
            level=StatusLevel.ERROR,
            message="Tracking failed",
        )
        assert event.timestamp == 2.0
        assert event.level == StatusLevel.ERROR


class TestTelemetryThresholds:
    """Tests for TelemetryThresholds dataclass."""

    def test_telemetry_thresholds_creation(self):
        """Test creating TelemetryThresholds."""
        thresholds = TelemetryThresholds(
            tracking_deviation=0.5,
            torque_warning=2.0,
            torque_error=3.0,
            velocity_max=10.0,
        )
        assert thresholds.tracking_deviation == 0.5
        assert thresholds.torque_warning == 2.0

    def test_telemetry_thresholds_defaults(self):
        """Test default values."""
        thresholds = TelemetryThresholds()
        assert thresholds.tracking_deviation == 0.3
        assert thresholds.torque_warning == 1.8
        assert thresholds.torque_error == 2.5

    def test_telemetry_thresholds_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "tracking_deviation": 0.4,
            "torque_warning": 1.5,
            "torque_error": 2.0,
            "velocity_max": 8.0,
        }
        thresholds = TelemetryThresholds.from_dict(data)
        assert thresholds.tracking_deviation == 0.4
        assert thresholds.torque_warning == 1.5

    def test_check_tracking(self):
        """Test tracking deviation check."""
        thresholds = TelemetryThresholds(tracking_deviation=0.3)
        assert thresholds.check_tracking(0.5) is True
        assert thresholds.check_tracking(0.2) is False
        assert thresholds.check_tracking(0.3) is False  # Equal is not exceeding

    def test_check_torque_warning(self):
        """Test torque warning check."""
        thresholds = TelemetryThresholds(torque_warning=1.8)
        assert thresholds.check_torque_warning(2.0) is True
        assert thresholds.check_torque_warning(1.5) is False
        assert thresholds.check_torque_warning(1.8) is False

    def test_check_torque_error(self):
        """Test torque error check."""
        thresholds = TelemetryThresholds(torque_error=2.5)
        assert thresholds.check_torque_error(3.0) is True
        assert thresholds.check_torque_error(2.0) is False
        assert thresholds.check_torque_error(2.5) is False

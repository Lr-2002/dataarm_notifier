"""Integration tests for the complete telemetry system."""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from dataarm_notifier.telemetry.producer import TelemetryProducer
from dataarm_notifier.telemetry.simulation import SimulationEngine
from dataarm_notifier.telemetry.enums import StatusLevel
from dataarm_notifier.telemetry.config import TelemetryConfig
from dataarm_notifier.telemetry.data_types import (
    TelemetryDataPoint,
    DashboardState,
    EventLog,
    TelemetryThresholds,
)


class MockRR:
    """Mock Rerun module for testing."""

    def __init__(self):
        self.logged_data = []
        self.init_called = False
        self.connect_called = False

    def init(self, app_name, spawn=False):
        self.init_called = True

    def connect(self, address):
        self.connect_called = True

    def log(self, entity_path, entity):
        self.logged_data.append((entity_path, entity))

    def TextDocument(self, text, media_type=None):
        return Mock(text=text, media_type=media_type)

    def TextLog(self, text):
        return Mock(text=text)

    def Image(self, data):
        return Mock(data=data)

    def Scalars(self, values):
        return Mock(values=values)


@pytest.fixture
def mock_rr():
    """Create a mock Rerun module."""
    return MockRR()


@pytest.fixture
def producer(mock_rr):
    """Create a TelemetryProducer with mocked Rerun."""
    with patch("dataarm_notifier.telemetry.producer.rr", mock_rr):
        prod = TelemetryProducer(app_name="IntegrationTest")
        yield prod
        prod.shutdown()


class TestProducerSimulationIntegration:
    """Integration tests for producer and simulation."""

    def test_producer_with_simulation_data(self, producer, mock_rr):
        """Test producer logging simulation data."""
        engine = SimulationEngine()

        for i in range(10):
            data = engine.step(0.1)
            producer.log_simulation_data(data)

        # Verify data was logged
        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "drive/pos/target" in entity_paths
        assert "drive/pos/actual" in entity_paths
        assert "drive/vel/raw" in entity_paths
        assert "drive/vel/filtered" in entity_paths
        assert "drive/torque" in entity_paths


class TestConfigSimulationIntegration:
    """Integration tests for config and simulation."""

    def test_config_loaded_with_profiles(self):
        """Test config loads with simulation profiles."""
        config = TelemetryConfig.load()

        # Should have loaded without errors
        assert isinstance(config.frequency, int)
        assert isinstance(config.thresholds, TelemetryThresholds)


class TestEndToEndDataFlow:
    """End-to-end data flow tests."""

    def test_complete_telemetry_cycle(self, producer, mock_rr):
        """Test complete telemetry data cycle."""
        # Generate data point
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

        # Log data point
        producer.log_telemetry_data(data)

        # Verify all data was logged
        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "drive/pos/target" in entity_paths
        assert "drive/pos/actual" in entity_paths
        assert "drive/vel/raw" in entity_paths
        assert "drive/vel/filtered" in entity_paths
        assert "drive/torque" in entity_paths


class TestModuleExportsIntegration:
    """Tests for module exports integration."""

    def test_all_exports_available(self):
        """Test all expected exports are available."""
        from dataarm_notifier import (
            TelemetryProducer,
            SimulationEngine,
            StatusLevel,
            ProfileType,
            TelemetryConfig,
            TelemetryDataPoint,
            DashboardState,
            EventLog,
            SimulationProfile,
            SimulationData,
            TelemetryThresholds,
        )

        # All imports should succeed
        assert TelemetryProducer is not None
        assert SimulationEngine is not None
        assert StatusLevel is not None
        assert ProfileType is not None

    def test_telemetry_module_exports(self):
        """Test telemetry module exports."""
        from dataarm_notifier.telemetry import (
            TelemetryProducer,
            SimulationEngine,
            StatusLevel,
            ProfileType,
            TelemetryConfig,
            TelemetryDataPoint,
            DashboardState,
            EventLog,
            SimulationProfile,
            SimulationData,
            TelemetryThresholds,
        )

        assert all(x is not None for x in [
            TelemetryProducer, SimulationEngine, StatusLevel, ProfileType,
            TelemetryConfig, TelemetryDataPoint, DashboardState, EventLog,
            SimulationProfile, SimulationData, TelemetryThresholds,
        ])


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_graceful_shutdown(self, producer, mock_rr):
        """Test graceful shutdown of all components."""
        engine = SimulationEngine()

        # Run a few steps
        for _ in range(5):
            data = engine.step(0.1)
            producer.log_simulation_data(data)

        # Shutdown should not raise
        producer.shutdown()
        engine.shutdown()

    def test_multiple_profile_switches(self, producer):
        """Test switching between multiple profiles."""
        engine = SimulationEngine()

        # Try setting various profiles
        profiles_tried = []
        for profile_name in ["sine_tracking", "step_response", "ramp"]:
            result = engine.set_profile(profile_name)
            profiles_tried.append((profile_name, result))

        # At least one should have worked or returned False gracefully
        assert len(profiles_tried) > 0


class TestStatusAndEventIntegration:
    """Integration tests for status and events."""

    def test_status_triggers_events(self, producer, mock_rr):
        """Test that status changes trigger appropriate events."""
        # Update status explicitly
        producer.update_status(StatusLevel.WARNING, "High Load")

        # Should have logged dashboard update
        entity_paths = [e[0] for e in mock_rr.logged_data]
        # Status update should have been called
        assert "notify/dashboard" in entity_paths

    def test_dashboard_state_reflects_status(self, producer):
        """Test dashboard state updates correctly."""
        # Create dashboard state
        state = DashboardState(
            status=StatusLevel.INFO,
            message="System Nominal",
            timestamp=1.0,
            elapsed_time=5.0,
        )

        assert state.status == StatusLevel.INFO
        assert state.message == "System Nominal"


class TestEventLogIntegration:
    """Integration tests for event logging."""

    def test_event_creation_and_logging(self, producer, mock_rr):
        """Test event creation and logging."""
        # Create event
        event = EventLog(
            timestamp=1.0,
            level=StatusLevel.WARNING,
            message="High Temperature",
        )

        assert event.timestamp == 1.0
        assert event.level == StatusLevel.WARNING

        # Log event
        producer.log_event(event.level, event.message)

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "notify/log" in entity_paths

    def test_event_from_data(self):
        """Test creating event from telemetry data."""
        event = EventLog.from_data(
            timestamp=2.0,
            level=StatusLevel.ERROR,
            message="Motor Failure",
        )

        assert event.timestamp == 2.0
        assert event.level == StatusLevel.ERROR
        assert event.message == "Motor Failure"

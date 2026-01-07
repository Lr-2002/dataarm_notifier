"""Unit tests for TelemetryProducer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from dataarm_notifier.telemetry.producer import TelemetryProducer
from dataarm_notifier.telemetry.enums import StatusLevel


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
        prod = TelemetryProducer(app_name="Test")
        yield prod
        prod.shutdown()


class TestTelemetryProducerLogPosition:
    """Tests for TelemetryProducer.log_position method."""

    def test_log_position_basic(self, producer, mock_rr):
        """Test logging basic position data."""
        elapsed, status, message = producer.log_position(1.0, 0.9)

        assert elapsed >= 0
        assert status == StatusLevel.INFO
        assert "System Nominal" in message

        # Check that Rerun log was called
        assert len(mock_rr.logged_data) >= 2
        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "drive/pos/target" in entity_paths
        assert "drive/pos/actual" in entity_paths

    def test_log_position_with_timestamp(self, producer, mock_rr):
        """Test logging with custom timestamp."""
        elapsed, status, message = producer.log_position(1.0, 0.9, timestamp=100.0)
        assert elapsed == 100.0

    def test_log_position_tracking_error(self, producer):
        """Test tracking error detection."""
        # Normal case
        elapsed, status, message = producer.log_position(1.0, 1.0)
        assert status == StatusLevel.INFO

        # Large deviation (should trigger ERROR)
        elapsed, status, message = producer.log_position(1.0, 0.5)
        assert status == StatusLevel.ERROR
        assert "Tracking Deviation" in message


class TestTelemetryProducerCheckThresholds:
    """Tests for TelemetryProducer.check_thresholds method."""

    def test_check_thresholds_normal(self, producer):
        """Test normal operating conditions."""
        status, message = producer.check_thresholds(1.0, 0.9, 0.5)
        assert status == StatusLevel.INFO

    def test_check_thresholds_high_torque_warning(self, producer):
        """Test high torque warning threshold."""
        status, message = producer.check_thresholds(1.0, 0.9, 2.0)
        assert status == StatusLevel.WARNING
        assert "High Torque" in message

    def test_check_thresholds_high_torque_error(self, producer):
        """Test high torque error threshold."""
        status, message = producer.check_thresholds(1.0, 0.9, 3.0)
        assert status == StatusLevel.ERROR
        assert "Torque Critical" in message

    def test_check_thresholds_tracking_error(self, producer):
        """Test tracking deviation error."""
        status, message = producer.check_thresholds(1.0, 0.5, 0.5)
        assert status == StatusLevel.ERROR
        assert "Tracking Deviation" in message


class TestTelemetryProducerLogVelocity:
    """Tests for TelemetryProducer.log_velocity method."""

    def test_log_velocity_basic(self, producer, mock_rr):
        """Test logging velocity data."""
        producer.log_velocity(1.0, 0.9)

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "drive/vel/raw" in entity_paths
        assert "drive/vel/filtered" in entity_paths


class TestTelemetryProducerLogDynamics:
    """Tests for TelemetryProducer.log_dynamics method."""

    def test_log_dynamics_basic(self, producer, mock_rr):
        """Test logging dynamics data."""
        producer.log_dynamics(1.0, 0.5)

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "drive/torque" in entity_paths
        assert "drive/acc_filtered" in entity_paths


class TestTelemetryProducerUpdateStatus:
    """Tests for TelemetryProducer.update_status method."""

    def test_update_status_info(self, producer, mock_rr):
        """Test updating status to INFO."""
        producer.update_status(StatusLevel.INFO, "System Nominal")

        # Check TextDocument was logged
        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "notify/dashboard" in entity_paths

    def test_update_status_warning(self, producer, mock_rr):
        """Test updating status to WARNING."""
        producer.update_status(StatusLevel.WARNING, "High Load")

        # Verify status changed
        assert producer._last_status == StatusLevel.WARNING


class TestTelemetryProducerLogEvent:
    """Tests for TelemetryProducer.log_event method."""

    def test_log_event_warning(self, producer, mock_rr):
        """Test logging a warning event."""
        producer.log_event(StatusLevel.WARNING, "High temperature")

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "notify/log" in entity_paths

    def test_log_event_error(self, producer, mock_rr):
        """Test logging an error event."""
        producer.log_event(StatusLevel.ERROR, "Motor failure")

        # Check duplicate events are not logged
        producer.log_event(StatusLevel.ERROR, "Motor failure")
        event_count = sum(1 for e in mock_rr.logged_data if e[0] == "notify/log")
        assert event_count == 1  # Only one event should be logged

    def test_log_event_info_skipped(self, producer, mock_rr):
        """Test that INFO events are not logged."""
        producer.log_event(StatusLevel.INFO, "Normal operation")

        # INFO events should not be logged
        entity_paths = [e[0] for e in mock_rr.logged_data]
        # Count only notify/log entries for events (not dashboard)
        event_count = sum(1 for e in mock_rr.logged_data if e[0] == "notify/log")
        assert event_count == 0


class TestTelemetryProducerLogCamera:
    """Tests for TelemetryProducer.log_camera method."""

    def test_log_camera_none(self, producer, mock_rr):
        """Test logging placeholder when camera is unavailable."""
        producer.log_camera(None)

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "sensors/camera_main" in entity_paths

    def test_log_camera_rgb_image(self, producer, mock_rr):
        """Test logging RGB image."""
        # Create a small test image
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        producer.log_camera(frame)

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "sensors/camera_main" in entity_paths

    def test_log_camera_grayscale(self, producer, mock_rr):
        """Test logging grayscale image."""
        # Create a small grayscale test image
        frame = np.zeros((240, 320), dtype=np.uint8)
        producer.log_camera(frame)

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "sensors/camera_main" in entity_paths


class TestTelemetryProducerShutdown:
    """Tests for TelemetryProducer.shutdown method."""

    def test_shutdown(self, producer, mock_rr):
        """Test graceful shutdown."""
        producer.shutdown()

        entity_paths = [e[0] for e in mock_rr.logged_data]
        assert "notify/dashboard" in entity_paths

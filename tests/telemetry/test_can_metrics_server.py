"""Tests for CAN Metrics Server."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch


class TestCANMetricsServer:
    """Test cases for CANMetricsServer."""

    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        from dataarm_notifier.telemetry.can_metrics_server import CANMetricsServer
        return CANMetricsServer(port=9877)

    def test_initialization(self, server):
        """Test server initialization with default values."""
        assert server._port == 9877
        assert server._host == "127.0.0.1"
        assert server._running is False
        assert server._can_id_to_name == {}

    def test_can_id_to_name_property(self, server):
        """Test can_id_to_name property returns copy."""
        server._can_id_to_name = {1: "shoulder_joint"}
        copy = server.can_id_to_name
        copy[2] = "other_joint"
        assert 2 not in server.can_id_to_name

    def test_is_running_property(self, server):
        """Test is_running property."""
        assert server.is_running is False
        server._running = True
        assert server.is_running is True

    @pytest.mark.asyncio
    async def test_handle_metrics_stub(self, server):
        """Test _handle_metrics method (stub)."""
        data = {"bus_load_percent": 25.5}
        # Should not raise exception
        server._handle_metrics(data)

    @pytest.mark.asyncio
    async def test_handle_event_stub(self, server):
        """Test _handle_event method (stub)."""
        data = {"event_type": "timeout", "can_id": 17}
        # Should not raise exception
        server._handle_event(data)

    @pytest.mark.asyncio
    async def test_handle_mapping_stub(self, server):
        """Test _handle_mapping method (stub)."""
        data = {"joint_names": {1: "shoulder_joint"}}
        # Should not raise exception
        server._handle_mapping(data)

    @pytest.mark.asyncio
    async def test_process_message_metrics(self, server):
        """Test processing metrics message."""
        server._handle_metrics = Mock()
        message = {"type": "metrics", "data": {"bus_load_percent": 25.5}}
        server._process_message(message)
        server._handle_metrics.assert_called_once_with({"bus_load_percent": 25.5})

    @pytest.mark.asyncio
    async def test_process_message_event(self, server):
        """Test processing event message."""
        server._handle_event = Mock()
        message = {"type": "event", "data": {"event_type": "timeout"}}
        server._process_message(message)
        server._handle_event.assert_called_once_with({"event_type": "timeout"})

    @pytest.mark.asyncio
    async def test_process_message_mapping(self, server):
        """Test processing mapping message."""
        server._handle_mapping = Mock()
        message = {"type": "mapping", "data": {"joint_names": {1: "test"}}}
        server._process_message(message)
        server._handle_mapping.assert_called_once_with({"joint_names": {1: "test"}})

    @pytest.mark.asyncio
    async def test_process_message_ping(self, server):
        """Test processing ping message."""
        message = {"type": "ping", "data": {}}
        # Should not raise exception
        server._process_message(message)

    @pytest.mark.asyncio
    async def test_process_message_unknown(self, server):
        """Test processing unknown message type."""
        message = {"type": "unknown_type", "data": {}}
        # Should not raise exception, just log warning
        server._process_message(message)


class TestCANMetricsServerIntegration:
    """Integration tests for CANMetricsServer."""

    @pytest.fixture
    async def server_client_pair(self):
        """Create a connected server-client pair."""
        from dataarm_notifier.telemetry.can_metrics_server import CANMetricsServer

        server = CANMetricsServer(port=9878)
        server_task = asyncio.create_task(server.start())

        # Wait for server to start
        await asyncio.sleep(0.1)

        # Create client
        from dataarm.control.hardware.can_monitor.client_adapter import CANMetricsClient
        client = CANMetricsClient(host="127.0.0.1", port=9878)
        connected = await client.connect()

        assert connected, "Failed to connect client to server"

        yield server, client

        # Cleanup
        await client.stop()
        await server.stop()
        server_task.cancel()

    @pytest.mark.asyncio
    async def test_send_metrics(self, server_client_pair):
        """Test sending metrics from client to server."""
        server, client = server_client_pair

        # Mock _handle_metrics to capture call
        captured_data = []
        original_handle = server._handle_metrics
        def capture_metrics(data):
            captured_data.append(data)
        server._handle_metrics = capture_metrics

        # Send metrics
        metrics = {"bus_load_percent": 25.5, "total_frames": 100}
        await client.send_metrics(metrics)

        # Wait for processing
        await asyncio.sleep(0.1)

        assert len(captured_data) == 1
        assert captured_data[0]["bus_load_percent"] == 25.5

    @pytest.mark.asyncio
    async def test_send_event(self, server_client_pair):
        """Test sending event from client to server."""
        server, client = server_client_pair

        # Mock _handle_event to capture call
        captured_data = []
        def capture_event(data):
            captured_data.append(data)
        server._handle_event = capture_event

        # Send event
        event = {"event_type": "timeout", "can_id": 17}
        await client.send_event(event)

        # Wait for processing
        await asyncio.sleep(0.1)

        assert len(captured_data) == 1
        assert captured_data[0]["event_type"] == "timeout"

    @pytest.mark.asyncio
    async def test_send_mapping(self, server_client_pair):
        """Test sending mapping from client to server."""
        server, client = server_client_pair

        # Mock _handle_mapping to capture call
        captured_data = []
        def capture_mapping(data):
            captured_data.append(data)
        server._handle_mapping = capture_mapping

        # Send mapping
        mapping = {"joint_names": {1: "shoulder_joint", 17: "shoulder_response"}}
        await client.send_mapping(mapping)

        # Wait for processing
        await asyncio.sleep(0.1)

        assert len(captured_data) == 1
        assert captured_data[0]["joint_names"][1] == "shoulder_joint"

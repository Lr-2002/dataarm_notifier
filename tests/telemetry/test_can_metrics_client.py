"""Tests for CAN Metrics Client."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio


@pytest.fixture
def client():
    """Create a test client instance."""
    from control.hardware.can_monitor.client_adapter import CANMetricsClient
    return CANMetricsClient(host="127.0.0.1", port=9877)


class TestCANMetricsClient:
    """Test cases for CANMetricsClient."""

    def test_initialization(self, client):
        """Test client initialization with default values."""
        assert client._host == "127.0.0.1"
        assert client._port == 9877
        assert client._running is False
        assert client._connected is False

    def test_is_connected_property(self, client):
        """Test is_connected property."""
        assert client.is_connected is False
        client._connected = True
        assert client.is_connected is True

    def test_reconnect_interval(self, client):
        """Test reconnect interval is 5 seconds."""
        assert client.RECONNECT_INTERVAL == 5.0


class TestCANMetricsClientConnection:
    """Test cases for CANMetricsClient connection handling."""

    @pytest.fixture
    def mock_stream(self):
        """Create mock stream reader and writer."""
        reader = AsyncMock()
        # StreamWriter.write() is synchronous in asyncio, but drain()/wait_closed() are async.
        writer = Mock()
        writer.write = Mock()
        writer.drain = AsyncMock()
        writer.close = Mock()
        writer.wait_closed = AsyncMock()
        return reader, writer

    @pytest.mark.anyio
    async def test_connect_success(self, client, mock_stream):
        """Test successful connection."""
        reader, writer = mock_stream

        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = (reader, writer)

            result = await client.connect()

            assert result is True
            assert client._connected is True
            mock_conn.assert_called_once_with("127.0.0.1", 9877)

    @pytest.mark.anyio
    async def test_connect_refused(self, client):
        """Test connection refused."""
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.side_effect = ConnectionRefusedError()

            result = await client.connect()

            assert result is False
            assert client._connected is False

    @pytest.mark.anyio
    async def test_send_message_not_connected(self, client):
        """Test sending message when not connected."""
        result = await client.send_metrics({"test": "data"})
        assert result is False

    @pytest.mark.anyio
    async def test_send_metrics_format(self, client, mock_stream):
        """Test metrics message format."""
        reader, writer = mock_stream

        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = (reader, writer)
            await client.connect()

            metrics = {
                "bus_load_percent": 25.5,
                "total_frames": 100,
                "active_ids": 6
            }
            await client.send_metrics(metrics)

            # Check the message was written
            assert writer.write.called
            sent_data = writer.write.call_args[0][0].decode()

            # Verify JSON structure
            import json
            message = json.loads(sent_data)
            assert message["type"] == "metrics"
            assert "timestamp_ns" in message
            assert message["data"]["bus_load_percent"] == 25.5

    @pytest.mark.anyio
    async def test_send_event_format(self, client, mock_stream):
        """Test event message format."""
        reader, writer = mock_stream

        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = (reader, writer)
            await client.connect()

            event = {
                "event_type": "timeout",
                "can_id": 17,
                "details": {"rtt_ms": 55.0}
            }
            await client.send_event(event)

            # Check the message was written
            assert writer.write.called
            sent_data = writer.write.call_args[0][0].decode()

            # Verify JSON structure
            import json
            message = json.loads(sent_data)
            assert message["type"] == "event"
            assert message["data"]["event_type"] == "timeout"

    @pytest.mark.anyio
    async def test_send_mapping_format(self, client, mock_stream):
        """Test mapping message format."""
        reader, writer = mock_stream

        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = (reader, writer)
            await client.connect()

            mapping = {
                "joint_names": {1: "shoulder_joint", 17: "shoulder_response"}
            }
            await client.send_mapping(mapping)

            # Check the message was written
            assert writer.write.called
            sent_data = writer.write.call_args[0][0].decode()

            # Verify JSON structure
            import json
            message = json.loads(sent_data)
            assert message["type"] == "mapping"
            # JSON serializes dict keys as strings
            assert message["data"]["joint_names"]["1"] == "shoulder_joint"


class TestCANMetricsClientReconnect:
    """Test cases for CANMetricsClient auto-reconnect."""

    @pytest.mark.anyio
    async def test_stop_resets_state(self, client):
        """Test that stop resets connection state."""
        client._connected = True
        client._running = True

        await client.stop()

        assert client._running is False
        assert client._connected is False

    @pytest.mark.anyio
    async def test_reconnect_on_disconnect(self, client):
        """Test that client can detect disconnect and reconnect."""
        # This is a conceptual test - in practice, this would require
        # a more complex setup with a real server
        client._connected = True
        client._running = True

        # Simulate disconnect
        client._connected = False

        # When connect is called again, it should try to reconnect
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = (AsyncMock(), AsyncMock())
            result = await client.connect()

            assert result is True
            assert mock_conn.called

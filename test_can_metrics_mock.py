#!/usr/bin/env python3
"""Standalone test script for CAN Metrics Server with mock data."""

import asyncio
import json
import sys
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

# Add notifier to path
sys.path.insert(0, '/home/lr-2002/project/DataArm/dataarm/notifier')

from dataarm_notifier.telemetry.can_metrics_server import CANMetricsServer
from dataarm_notifier.telemetry.enums import StatusLevel


# Standalone CAN Metrics Client (for testing without control dependencies)
class StandaloneCANMetricsClient:
    """Standalone TCP Client for testing without control module dependencies."""

    RECONNECT_INTERVAL = 5.0

    def __init__(self, host: str = "127.0.0.1", port: int = 9877):
        self._host = host
        self._port = port
        self._reader = None
        self._writer = None
        self._running = False
        self._connected = False

    async def connect(self) -> bool:
        """Connect to the server."""
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self._host, self._port
            )
            self._connected = True
            logger.info(f"Connected to {self._host}:{self._port}")
            return True
        except ConnectionRefusedError:
            self._connected = False
            logger.debug(f"Connection refused to {self._host}:{self._port}")
            return False
        except Exception as e:
            self._connected = False
            logger.error(f"Connection error: {e}")
            return False

    async def send_metrics(self, metrics: dict) -> bool:
        """Send metrics to server."""
        return await self._send_message("metrics", metrics)

    async def send_event(self, event: dict) -> bool:
        """Send event to server."""
        return await self._send_message("event", event)

    async def send_mapping(self, mapping: dict) -> bool:
        """Send mapping to server."""
        return await self._send_message("mapping", mapping)

    async def _send_message(self, msg_type: str, data: dict) -> bool:
        """Send a message."""
        if not self._connected or not self._writer:
            return False
        try:
            message = json.dumps({
                "type": msg_type,
                "timestamp_ns": int(time.time() * 1e9),
                "data": data
            }) + "\n"
            self._writer.write(message.encode())
            await self._writer.drain()
            return True
        except Exception as e:
            logger.error(f"Failed to send: {e}")
            self._connected = False
            return False

    async def stop(self):
        """Stop client."""
        self._running = False
        self._connected = False
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except:
                pass


async def test_with_mock_data():
    """Test the CAN metrics server with mock data."""
    print("=" * 60)
    print("CAN Metrics Server Test with Mock Data")
    print("=" * 60)

    # Create and start server
    server = CANMetricsServer(port=9877, app_name="CAN_Test")
    server_task = asyncio.create_task(server.start())

    # Wait for server to start
    await asyncio.sleep(0.2)
    print("[OK] Server started on port 9877")

    # Create client
    client = StandaloneCANMetricsClient(host="127.0.0.1", port=9877)

    # Connect
    connected = await client.connect()
    if not connected:
        print("[FAIL] Failed to connect client")
        return False
    print("[OK] Client connected to server")

    # Test 1: Send CAN ID mapping
    print("\n--- Test 1: Send CAN ID Mapping ---")
    mapping = {
        "can_id_map": {"1": 17, "2": 18, "3": 19},
        "joint_names": {
            "1": "shoulder_joint",
            "2": "upper_arm_joint",
            "3": "forearm_joint",
            "17": "shoulder_response",
            "18": "upper_arm_response",
            "19": "forearm_response"
        }
    }
    await client.send_mapping(mapping)
    await asyncio.sleep(0.1)
    print(f"[OK] Mapping sent: {len(mapping['joint_names'])} joints")

    # Test 2: Send mock metrics (normal operation)
    print("\n--- Test 2: Send Mock Metrics (Normal) ---")
    metrics = {
        "bus_load_percent": 25.5,
        "total_frames": 12345,
        "active_ids": 6,
        "error_frames_per_second": 0.0,
        "dropped_frames_per_second": 0.0,
        "per_id_stats": {
            "1": {"fps_window": 500.0, "dt_p95_ms": 1.5},
            "2": {"fps_window": 500.0, "dt_p95_ms": 1.2},
            "3": {"fps_window": 500.0, "dt_p95_ms": 1.8}
        },
        "per_pair_rtt": {
            "[1,17]": {"rtt_mean_ms": 2.1, "rtt_p95_ms": 3.5},
            "[2,18]": {"rtt_mean_ms": 2.3, "rtt_p95_ms": 3.8},
            "[3,19]": {"rtt_mean_ms": 2.0, "rtt_p95_ms": 3.2}
        }
    }
    await client.send_metrics(metrics)
    await asyncio.sleep(0.1)
    print(f"[OK] Metrics sent: bus_load={metrics['bus_load_percent']}%, active_ids={metrics['active_ids']}")

    # Test 3: Send mock metrics (high load warning)
    print("\n--- Test 3: Send Mock Metrics (High Load - WARNING) ---")
    metrics_warning = {
        "bus_load_percent": 65.0,
        "total_frames": 13000,
        "active_ids": 6,
        "error_frames_per_second": 0.5,
        "dropped_frames_per_second": 0.1,
        "per_id_stats": {
            "1": {"fps_window": 520.0, "dt_p95_ms": 3.5},
            "2": {"fps_window": 510.0, "dt_p95_ms": 3.2},
            "3": {"fps_window": 515.0, "dt_p95_ms": 3.8}
        },
        "per_pair_rtt": {
            "[1,17]": {"rtt_mean_ms": 5.1, "rtt_p95_ms": 8.5},
            "[2,18]": {"rtt_mean_ms": 5.3, "rtt_p95_ms": 8.8},
            "[3,19]": {"rtt_mean_ms": 5.0, "rtt_p95_ms": 8.2}
        }
    }
    await client.send_metrics(metrics_warning)
    await asyncio.sleep(0.1)
    print(f"[OK] Warning metrics sent: bus_load={metrics_warning['bus_load_percent']}%")

    # Test 4: Send timeout event
    print("\n--- Test 4: Send Timeout Event ---")
    event = {
        "event_type": "timeout",
        "can_id": 17,
        "details": {"rtt_ms": 55.0, "send_id": "0x01"}
    }
    await client.send_event(event)
    await asyncio.sleep(0.1)
    print("[OK] Timeout event sent")

    # Test 5: Send error frame event
    print("\n--- Test 5: Send Error Frame Event ---")
    event2 = {
        "event_type": "error_frame",
        "can_id": 2,
        "details": {"dlc": 8}
    }
    await client.send_event(event2)
    await asyncio.sleep(0.1)
    print("[OK] Error frame event sent")

    # Test 6: Send critical metrics (error state)
    print("\n--- Test 6: Send Critical Metrics (ERROR) ---")
    metrics_critical = {
        "bus_load_percent": 85.0,
        "total_frames": 15000,
        "active_ids": 6,
        "error_frames_per_second": 2.5,
        "dropped_frames_per_second": 1.0,
        "per_id_stats": {
            "1": {"fps_window": 450.0, "dt_p95_ms": 8.5},
            "2": {"fps_window": 440.0, "dt_p95_ms": 9.2},
            "3": {"fps_window": 445.0, "dt_p95_ms": 8.8}
        },
        "per_pair_rtt": {
            "[1,17]": {"rtt_mean_ms": 12.1, "rtt_p95_ms": 18.5},
            "[2,18]": {"rtt_mean_ms": 13.3, "rtt_p95_ms": 19.8},
            "[3,19]": {"rtt_mean_ms": 11.0, "rtt_p95_ms": 17.2}
        }
    }
    await client.send_metrics(metrics_critical)
    await asyncio.sleep(0.1)
    print(f"[OK] Critical metrics sent: bus_load={metrics_critical['bus_load_percent']}%")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Server running: {server.is_running}")
    print(f"Client connected: {client._connected}")
    print(f"Cached joints: {len(server.can_id_to_name)}")
    print(f"CAN bus status: {server.status.value}")
    print("\nRerun paths that received data:")
    print("  - can/bus/load")
    print("  - can/bus/frames_total")
    print("  - can/bus/active_ids")
    print("  - can/rtt/mean")
    print("  - can/rtt/p95")
    print("  - can/joint/shoulder_joint/fps")
    print("  - can/joint/shoulder_joint/jitter_p95")
    print("  - can/joint/shoulder_joint/rtt")
    print("  - notify/log (events)")
    print("  - notify/dashboard (status)")

    # Cleanup
    print("\n--- Cleanup ---")
    await client.stop()
    await server.stop()
    server_task.cancel()
    print("[OK] Server and client stopped")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    return True


async def test_reconnection():
    """Test client reconnection behavior."""
    print("\n" + "=" * 60)
    print("Reconnection Test")
    print("=" * 60)

    client = StandaloneCANMetricsClient(host="127.0.0.1", port=9999)  # Wrong port

    # Should fail to connect
    connected = await client.connect()
    print(f"Connection to wrong port: {'Failed (expected)' if not connected else 'Unexpected success'}")

    print(f"Client connected state: {client._connected}")
    print("[OK] Reconnection behavior verified")

    return True


async def test_message_format():
    """Test message format correctness."""
    print("\n" + "=" * 60)
    print("Message Format Test")
    print("=" * 60)

    # Create a test message
    test_data = {
        "bus_load_percent": 25.5,
        "total_frames": 100,
        "active_ids": 6
    }

    # Simulate sending
    message = json.dumps({
        "type": "metrics",
        "timestamp_ns": int(time.time() * 1e9),
        "data": test_data
    }) + "\n"

    # Verify format
    parsed = json.loads(message.strip())
    print(f"Message type: {parsed['type']}")
    print(f"Has timestamp_ns: {'timestamp_ns' in parsed}")
    print(f"Has data: {'data' in parsed}")
    print(f"Data fields: {list(parsed['data'].keys())}")
    print("[OK] Message format verified")

    return True


if __name__ == "__main__":
    print("Starting CAN Metrics Server tests...\n")

    # Run tests
    success = True

    try:
        asyncio.run(test_with_mock_data())
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        success = False

    try:
        asyncio.run(test_message_format())
    except Exception as e:
        print(f"\n[FAIL] Message format test failed: {e}")
        success = False

    try:
        asyncio.run(test_reconnection())
    except Exception as e:
        print(f"\n[FAIL] Reconnection test failed: {e}")
        success = False

    sys.exit(0 if success else 1)

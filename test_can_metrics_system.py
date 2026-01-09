#!/usr/bin/env python3
"""System-level integration test for CAN Metrics with notifier."""

import asyncio
import json
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("CAN_Metrics_System_Test")

sys.path.insert(0, '/home/lr-2002/project/DataArm/dataarm/notifier')

from dataarm_notifier.telemetry.can_metrics_server import CANMetricsServer
from dataarm_notifier.telemetry.enums import StatusLevel


class CANMetricsTestClient:
    """Test client that simulates can_monitor behavior."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9877):
        self._host = host
        self._port = port
        self._reader = None
        self._writer = None

    async def connect(self) -> bool:
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self._host, self._port
            )
            logger.info(f"Connected to {self._host}:{self._port}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def send_message(self, msg_type: str, data: dict) -> bool:
        if not self._writer:
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
            logger.error(f"Send failed: {e}")
            return False

    async def stop(self):
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()


async def test_system_integration():
    """Run complete system integration test."""
    print("=" * 70)
    print("CAN Metrics System-Level Integration Test")
    print("=" * 70)

    all_passed = True

    # Step 1: Start server
    print("\n[STEP 1] Starting CAN Metrics Server...")
    server = CANMetricsServer(port=9877, app_name="CAN_System_Test")
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.3)

    if server.is_running:
        print("  [PASS] Server started successfully")
    else:
        print("  [FAIL] Server failed to start")
        all_passed = False
        return False

    # Step 2: Connect client
    print("\n[STEP 2] Connecting test client...")
    client = CANMetricsTestClient(host="127.0.0.1", port=9877)
    connected = await client.connect()
    if connected:
        print("  [PASS] Client connected")
    else:
        print("  [FAIL] Client connection failed")
        all_passed = False
        await cleanup(server, server_task, client)
        return False

    # Step 3: Send mapping
    print("\n[STEP 3] Testing CAN ID mapping...")
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
    await client.send_message("mapping", mapping)
    await asyncio.sleep(0.1)
    if len(server.can_id_to_name) == 6:
        print(f"  [PASS] Mapping received: {len(server.can_id_to_name)} joints")
    else:
        print(f"  [FAIL] Mapping incorrect: {len(server.can_id_to_name)} joints")
        all_passed = False

    # Step 4: Test NOMINAL state (bus load < 50%)
    print("\n[STEP 4] Testing NOMINAL state (bus load 25%)...")
    metrics_normal = {
        "bus_load_percent": 25.0,
        "total_frames": 10000,
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
    await client.send_message("metrics", metrics_normal)
    await asyncio.sleep(0.1)

    if server.status == StatusLevel.INFO:
        print(f"  [PASS] Status is NOMINAL (INFO)")
    else:
        print(f"  [FAIL] Status is {server.status.value}, expected INFO")
        all_passed = False

    # Step 5: Test WARNING state (50% <= bus load < 80%)
    print("\n[STEP 5] Testing WARNING state (bus load 60%)...")
    metrics_warning = {
        "bus_load_percent": 60.0,
        "total_frames": 12000,
        "active_ids": 6,
        "error_frames_per_second": 0.2,
        "dropped_frames_per_second": 0.05,
        "per_id_stats": {
            "1": {"fps_window": 520.0, "dt_p95_ms": 2.5},
            "2": {"fps_window": 510.0, "dt_p95_ms": 2.2}
        },
        "per_pair_rtt": {
            "[1,17]": {"rtt_mean_ms": 4.1, "rtt_p95_ms": 6.5},
            "[2,18]": {"rtt_mean_ms": 4.3, "rtt_p95_ms": 6.8}
        }
    }
    await client.send_message("metrics", metrics_warning)
    await asyncio.sleep(0.1)

    if server.status == StatusLevel.WARNING:
        print(f"  [PASS] Status is WARNING")
    else:
        print(f"  [FAIL] Status is {server.status.value}, expected WARNING")
        all_passed = False

    # Step 6: Test ERROR state (bus load >= 80%)
    print("\n[STEP 6] Testing ERROR state (bus load 85%)...")
    metrics_error = {
        "bus_load_percent": 85.0,
        "total_frames": 15000,
        "active_ids": 6,
        "error_frames_per_second": 2.5,
        "dropped_frames_per_second": 1.0,
        "per_id_stats": {
            "1": {"fps_window": 450.0, "dt_p95_ms": 8.5},
            "2": {"fps_window": 440.0, "dt_p95_ms": 9.2}
        },
        "per_pair_rtt": {
            "[1,17]": {"rtt_mean_ms": 12.1, "rtt_p95_ms": 18.5},
            "[2,18]": {"rtt_mean_ms": 13.3, "rtt_p95_ms": 19.8}
        }
    }
    await client.send_message("metrics", metrics_error)
    await asyncio.sleep(0.1)

    if server.status == StatusLevel.ERROR:
        print(f"  [PASS] Status is ERROR")
    else:
        print(f"  [FAIL] Status is {server.status.value}, expected ERROR")
        all_passed = False

    # Step 7: Test timeout event
    print("\n[STEP 7] Testing timeout event...")
    await client.send_message("event", {
        "event_type": "timeout",
        "can_id": 17,
        "details": {"rtt_ms": 55.0, "send_id": "0x01"}
    })
    await asyncio.sleep(0.1)
    print("  [PASS] Timeout event sent")

    # Step 8: Test error frame event
    print("\n[STEP 8] Testing error frame event...")
    await client.send_message("event", {
        "event_type": "error_frame",
        "can_id": 2,
        "details": {"dlc": 8}
    })
    await asyncio.sleep(0.1)
    print("  [PASS] Error frame event sent")

    # Step 9: Test drop event
    print("\n[STEP 9] Testing drop event...")
    await client.send_message("event", {
        "event_type": "drop",
        "can_id": 3,
        "details": {"count": 5}
    })
    await asyncio.sleep(0.1)
    print("  [PASS] Drop event sent")

    # Step 10: Test watchdog event
    print("\n[STEP 10] Testing watchdog event...")
    await client.send_message("event", {
        "event_type": "watchdog",
        "can_id": 1,
        "details": {"timeout_ms": 1000}
    })
    await asyncio.sleep(0.1)
    print("  [PASS] Watchdog event sent")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Server running: {server.is_running}")
    print(f"CAN bus status: {server.status.value}")
    print(f"Cached joints: {len(server.can_id_to_name)}")
    print(f"Joint names: {list(server.can_id_to_name.values())}")

    # Cleanup
    await cleanup(server, server_task, client)

    if all_passed:
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("SOME TESTS FAILED!")
        print("=" * 70)
        return False


async def cleanup(server, server_task, client):
    """Cleanup test resources."""
    print("\n[Cleanup] Stopping server and client...")
    await client.stop()
    await server.stop()
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    print("  [OK] Cleanup complete")


if __name__ == "__main__":
    print("\nStarting CAN Metrics System Integration Test...\n")

    try:
        success = asyncio.run(test_system_integration())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

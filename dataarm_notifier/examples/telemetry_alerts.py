#!/usr/bin/env python3
"""Example: System Health Alerts with Rerun SDK.

This script demonstrates real-time system health monitoring
with status dashboard and event logging.
"""

import time
import numpy as np
import random

from dataarm_notifier.telemetry.producer import TelemetryProducer
from dataarm_notifier.telemetry.enums import StatusLevel


def run_alerts_example():
    """Run system health alerts example."""
    print("=" * 60)
    print("System Health Alerts Example")
    print("=" * 60)

    # Initialize producer
    producer = TelemetryProducer(app_name="Alerts_Example")

    print("\nStarting health monitoring...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            elapsed = time.time()

            # Simulate normal operation with occasional warnings/errors
            # Create scenarios by modifying probability over time
            phase = (elapsed % 30) / 30  # 0-1 over 30 seconds

            if phase < 0.3:
                # Normal operation
                target = np.sin(elapsed * 0.5)
                actual = np.sin(elapsed * 0.5 - 0.1) + np.random.normal(0, 0.01)
                torque = 0.5 + np.random.normal(0, 0.1)
                status_level = StatusLevel.INFO
                message = "System Nominal"

            elif phase < 0.5:
                # Warning condition - high torque
                target = np.sin(elapsed * 0.5)
                actual = np.sin(elapsed * 0.5 - 0.1)
                torque = 2.0 + np.random.normal(0, 0.1)
                status_level = StatusLevel.WARNING
                message = "High Torque Load"

            elif phase < 0.7:
                # Error condition - tracking deviation
                target = np.sin(elapsed * 0.5)
                actual = target + 0.4 + np.random.normal(0, 0.01)  # Large deviation
                torque = 0.5
                status_level = StatusLevel.ERROR
                message = "Tracking Deviation High"

            else:
                # Recovery
                target = np.sin(elapsed * 0.5)
                actual = np.sin(elapsed * 0.5 - 0.1)
                torque = 0.5
                status_level = StatusLevel.INFO
                message = "System Nominal"

            # Log all data
            producer.log_position(target, actual)
            producer.log_dynamics(torque, 0.0)

            # Update status
            producer.update_status(status_level, message)

            # Log event (only for non-INFO)
            if status_level != StatusLevel.INFO:
                producer.log_event(status_level, message)

            time.sleep(0.02)  # 50Hz

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.shutdown()


if __name__ == "__main__":
    run_alerts_example()

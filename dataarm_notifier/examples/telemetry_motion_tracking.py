#!/usr/bin/env python3
"""Example: Motion Tracking Visualization with Rerun SDK.

This script demonstrates real-time visualization of Target vs Actual position
for robot motion tracking using the TelemetryProducer.
"""

import time
import numpy as np

from dataarm_notifier.telemetry.producer import TelemetryProducer


def run_motion_tracking_example():
    """Run motion tracking example."""
    print("=" * 60)
    print("Motion Tracking Visualization Example")
    print("=" * 60)

    # Initialize producer
    producer = TelemetryProducer(app_name="Motion_Tracking_Example")

    print("\nStarting motion tracking...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            # Simulate robot motion (sine wave)
            elapsed = time.time()
            target = np.sin(elapsed * 0.5)  # 0.5 Hz sine wave

            # Simulate actual response with lag and noise
            lag = 0.1  # 100ms lag
            actual = np.sin(elapsed * 0.5 - lag) + np.random.normal(0, 0.02)

            # Log positions
            producer.log_position(target, actual)

            # Check thresholds and update status
            status, message = producer.check_thresholds(target, actual, 0.0)
            producer.update_status(status, message)

            if status.value != "INFO":
                producer.log_event(status, message)

            time.sleep(0.02)  # 50Hz

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.shutdown()


if __name__ == "__main__":
    run_motion_tracking_example()

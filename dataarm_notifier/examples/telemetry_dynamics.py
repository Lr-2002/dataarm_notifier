#!/usr/bin/env python3
"""Example: Dynamics Monitoring Visualization with Rerun SDK.

This script demonstrates real-time visualization of robot dynamics
(velocity, torque, acceleration) using the TelemetryProducer.
"""

import time
import numpy as np

from dataarm_notifier.telemetry.producer import TelemetryProducer


def run_dynamics_example():
    """Run dynamics monitoring example."""
    print("=" * 60)
    print("Dynamics Monitoring Visualization Example")
    print("=" * 60)

    # Initialize producer
    producer = TelemetryProducer(app_name="Dynamics_Example")

    print("\nStarting dynamics monitoring...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            elapsed = time.time()

            # Simulate velocity (derivative of position)
            raw_vel = np.cos(elapsed * 0.5) + np.random.normal(0, 0.1)  # Noisy
            filt_vel = np.cos(elapsed * 0.5)  # Clean

            # Simulate acceleration (derivative of velocity)
            accel = -0.25 * np.sin(elapsed * 0.5)

            # Simulate torque (function of velocity and acceleration)
            torque = abs(accel * 1.5) + abs(raw_vel * 0.1)

            # Log dynamics
            producer.log_velocity(raw_vel, filt_vel)
            producer.log_dynamics(torque, accel)

            # Check thresholds and update status
            status, message = producer.check_thresholds(0, 0, torque)
            producer.update_status(status, message)

            if status.value != "INFO":
                producer.log_event(status, message)

            time.sleep(0.02)  # 50Hz

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.shutdown()


if __name__ == "__main__":
    run_dynamics_example()

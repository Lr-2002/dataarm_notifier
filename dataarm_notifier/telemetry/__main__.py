#!/usr/bin/env python3
"""Telemetry Module - Main entry point.

Run with: python -m dataarm_notifier.telemetry
"""

import sys

from dataarm_notifier.telemetry.producer import TelemetryProducer
from dataarm_notifier.telemetry.simulation import SimulationEngine


def main():
    """Run telemetry in simulation mode."""
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Robot Telemetry Simulation")
    parser.add_argument(
        "--profile",
        type=str,
        default="sine_tracking",
        help="Simulation profile name",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=50.0,
        help="Update frequency in Hz",
    )

    args = parser.parse_args()

    dt = 1.0 / args.frequency
    print(f"Starting telemetry simulation with profile: {args.profile}")

    producer = TelemetryProducer(app_name="Robot_Telemetry")
    engine = SimulationEngine()
    engine.set_profile(args.profile)

    try:
        while True:
            data = engine.step(dt)
            producer.log_simulation_data(data)
            time.sleep(dt)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.shutdown()
        engine.shutdown()


if __name__ == "__main__":
    main()

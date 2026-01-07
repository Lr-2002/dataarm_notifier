#!/usr/bin/env python3
"""Example: Complete Telemetry System with Built-in Simulation.

This script demonstrates the complete telemetry system using
the built-in simulation engine for testing without real hardware.
"""

import time
import argparse

from dataarm_notifier.telemetry.producer import TelemetryProducer
from dataarm_notifier.telemetry.simulation import SimulationEngine


def run_simulation_example(profile: str = "sine_tracking", frequency: float = 50.0):
    """Run complete telemetry simulation.

    Args:
        profile: Simulation profile name
        frequency: Update frequency in Hz
    """
    print("=" * 60)
    print("Complete Telemetry System - Simulation Mode")
    print("=" * 60)
    print(f"\nProfile: {profile}")
    print(f"Frequency: {frequency}Hz")
    print("\nThis example demonstrates:")
    print("  - Motion tracking (Target vs Actual)")
    print("  - Dynamics monitoring (Velocity, Torque, Acceleration)")
    print("  - System health alerts")
    print("\nPress Ctrl+C to stop\n")

    # Initialize producer and simulation
    producer = TelemetryProducer(app_name="Telemetry_Full_Demo")
    engine = SimulationEngine()

    # Set profile
    if not engine.set_profile(profile):
        available = engine.list_profiles()
        print(f"Profile '{profile}' not found. Available: {available}")
        if available:
            engine.set_profile(available[0])
            print(f"Using profile: {available[0]}")
        else:
            print("No profiles available, using default")
            profile = "default"

    dt = 1.0 / frequency
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            frame_start = time.time()

            # Get simulation data
            data = engine.step(dt)

            # Log all data to Rerun (demonstrates all user stories)
            producer.log_simulation_data(data)

            # Progress indicator
            frame_count += 1
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                print(f"Frames: {frame_count}, Time: {elapsed:.1f}s, Status: {data.status.value}")
                print(f"  Target: {data.target_position:.3f}, Actual: {data.actual_position:.3f}")
                print(f"  Torque: {data.torque:.3f}Nm, Velocity: {data.filtered_velocity:.3f}rad/s")

            # Maintain loop rate
            loop_time = time.time() - frame_start
            sleep_time = max(0, dt - loop_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        total_time = time.time() - start_time
        print(f"\nStatistics:")
        print(f"  Total frames: {frame_count}")
        print(f"  Total time: {total_time:.1f}s")
        print(f"  Average FPS: {frame_count / total_time:.1f}")

        producer.shutdown()
        engine.shutdown()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Complete Telemetry System Demo")
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
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit",
    )

    args = parser.parse_args()

    if args.list_profiles:
        engine = SimulationEngine()
        profiles = engine.list_profiles()
        print("Available profiles:")
        for name in profiles:
            print(f"  - {name}")
        return

    run_simulation_example(args.profile, args.frequency)


if __name__ == "__main__":
    main()

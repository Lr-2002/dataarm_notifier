#!/usr/bin/env python3
"""Telemetry CLI - Command-line interface for running telemetry system."""

import argparse
import logging
import sys
import time

from dataarm_notifier.telemetry.producer import TelemetryProducer
from dataarm_notifier.telemetry.simulation import SimulationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_simulation(profile: str = "sine_tracking", frequency: float = 50.0) -> None:
    """Run telemetry in simulation mode.

    Args:
        profile: Simulation profile name
        frequency: Update frequency in Hz
    """
    dt = 1.0 / frequency
    logger.info(f"Starting simulation with profile: {profile}")

    producer = TelemetryProducer(app_name="Robot_Telemetry_Simulation")
    engine = SimulationEngine()

    if not engine.set_profile(profile):
        available = engine.list_profiles()
        logger.warning(f"Profile '{profile}' not found. Available: {available}")
        if available:
            engine.set_profile(available[0])
        else:
            logger.error("No profiles available")
            return

    try:
        logger.info("Simulation started. Press Ctrl+C to stop.")
        while True:
            start = time.time()

            # Get simulation data
            data = engine.step(dt)

            # Log to Rerun
            producer.log_simulation_data(data)

            # Maintain loop rate
            elapsed = time.time() - start
            sleep_time = dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Simulation stopped by user")
    finally:
        producer.shutdown()
        engine.shutdown()


def run_live(connect: str = None, frequency: float = 50.0) -> None:
    """Run telemetry with live robot data.

    Args:
        connect: TCP address to connect to existing Rerun viewer
        frequency: Update frequency in Hz
    """
    dt = 1.0 / frequency
    logger.info("Starting live telemetry mode")

    producer = TelemetryProducer(app_name="Robot_Telemetry_Live", connect=connect)

    try:
        logger.info("Live telemetry started. Press Ctrl+C to stop.")
        logger.info("Waiting for robot data...")

        # In live mode, we would typically receive data from robot control system
        # For now, just keep the viewer running
        while True:
            time.sleep(1.0)

    except KeyboardInterrupt:
        logger.info("Live telemetry stopped by user")
    finally:
        producer.shutdown()


def list_profiles() -> None:
    """List available simulation profiles."""
    engine = SimulationEngine()
    profiles = engine.list_profiles()

    print("Available simulation profiles:")
    if profiles:
        for name in profiles:
            print(f"  - {name}")
    else:
        print("  No profiles configured")


def main() -> int:
    """Main entry point for telemetry CLI."""
    parser = argparse.ArgumentParser(
        description="Robot Telemetry Visualization with Rerun SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--mode",
        choices=["simulation", "live"],
        default="simulation",
        help="Telemetry mode (default: simulation)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="sine_tracking",
        help="Simulation profile name (default: sine_tracking)",
    )
    parser.add_argument(
        "--connect",
        type=str,
        default=None,
        help="TCP address to connect to existing Rerun viewer (e.g., 127.0.0.1:9876)",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=50.0,
        help="Update frequency in Hz (default: 50.0)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available simulation profiles and exit",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list_profiles:
        list_profiles()
        return 0

    if args.mode == "simulation":
        run_simulation(profile=args.profile, frequency=args.frequency)
    else:
        run_live(connect=args.connect, frequency=args.frequency)

    return 0


if __name__ == "__main__":
    sys.exit(main())

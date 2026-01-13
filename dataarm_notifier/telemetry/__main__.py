#!/usr/bin/env python3
"""Telemetry Module - Main entry point.

Run with: python -m dataarm_notifier.telemetry
"""

import argparse
import asyncio
import logging

from dataarm_notifier.telemetry.producer import TelemetryProducer
from dataarm_notifier.telemetry.simulation import SimulationEngine


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DataArm Notifier Telemetry")

    parser.add_argument(
        "--rerun-app-name",
        dest="app_name",
        type=str,
        default="Robot_Telemetry",
        help="Rerun application name (default: Robot_Telemetry)",
    )
    parser.add_argument(
        "--connect",
        type=str,
        default=None,
        help='Connect to existing Rerun viewer (e.g. "127.0.0.1:9876")',
    )

    parser.add_argument(
        "--can-server-port",
        type=int,
        default=None,
        help="Start CAN metrics TCP server on this port (default: disabled)",
    )
    parser.add_argument(
        "--can-server-host",
        type=str,
        default="127.0.0.1",
        help="CAN metrics server bind host (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--can",
        action="store_true",
        help="Shortcut: start CAN server on 9877 and disable simulation",
    )

    parser.add_argument(
        "--arm-server-port",
        type=int,
        default=None,
        help="Start arm telemetry TCP server on this port (default: disabled)",
    )
    parser.add_argument(
        "--arm-server-host",
        type=str,
        default="127.0.0.1",
        help="Arm telemetry server bind host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--arm",
        action="store_true",
        help="Shortcut: start arm telemetry server on 9878 and disable simulation",
    )

    parser.add_argument(
        "--no-simulation",
        action="store_true",
        help="Disable built-in simulation loop (useful for CAN server only)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="sine_tracking",
        help="Simulation profile name (default: sine_tracking)",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=50.0,
        help="Simulation update frequency in Hz (default: 50.0)",
    )

    return parser


async def _run(args: argparse.Namespace) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    producer = TelemetryProducer(app_name=args.app_name, connect=args.connect)

    if args.can:
        if args.can_server_port is None:
            args.can_server_port = 9877
        args.no_simulation = True

    if args.arm:
        if args.arm_server_port is None:
            args.arm_server_port = 9878
        args.no_simulation = True

    if args.can_server_port is not None:
        producer.start_can_server(port=args.can_server_port, host=args.can_server_host)

    if args.arm_server_port is not None:
        producer.start_arm_server(port=args.arm_server_port, host=args.arm_server_host)

    engine = None
    if not args.no_simulation:
        engine = SimulationEngine()
        engine.set_profile(args.profile)

    try:
        if engine is None:
            while True:
                await asyncio.sleep(3600)

        dt = 1.0 / max(args.frequency, 0.1)
        while True:
            data = engine.step(dt)
            producer.log_simulation_data(data)
            await asyncio.sleep(dt)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if producer.can_server is not None:
            try:
                await producer.can_server.stop()
            except Exception:
                pass
        if producer.arm_server is not None:
            try:
                await producer.arm_server.stop()
            except Exception:
                pass
        producer.shutdown()
        if engine is not None:
            engine.shutdown()


def main() -> int:
    args = _build_parser().parse_args()
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

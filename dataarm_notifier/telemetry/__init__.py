"""Telemetry Module - Real-Time Robot Telemetry & Notification with Rerun SDK.

This module provides:
- TelemetryProducer: Send telemetry data to Rerun viewer
- SimulationEngine: Built-in simulation for testing without hardware
- Configuration: YAML-based configuration management
- Data types: Dataclasses for telemetry data structures
- Enums: StatusLevel and ProfileType enumerations

Usage:
    from dataarm_notifier import TelemetryProducer

    producer = TelemetryProducer(app_name="Robot_Telemetry")
    producer.log_position(target, actual)
    producer.shutdown()
"""

from .enums import ProfileType, StatusLevel
from .data_types import (
    DashboardState,
    EventLog,
    SimulationProfile,
    TelemetryDataPoint,
    TelemetryThresholds,
)
from .config import TelemetryConfig
from .producer import TelemetryProducer
from .simulation import SimulationEngine, SimulationData
from .can_metrics_server import CANMetricsServer

__all__ = [
    # Enums
    "StatusLevel",
    "ProfileType",
    # Data types
    "DashboardState",
    "EventLog",
    "SimulationData",
    "SimulationProfile",
    "TelemetryConfig",
    "TelemetryDataPoint",
    "TelemetryThresholds",
    # Core classes
    "TelemetryProducer",
    "SimulationEngine",
    # CAN Metrics
    "CANMetricsServer",
]

__version__ = "1.1.0"

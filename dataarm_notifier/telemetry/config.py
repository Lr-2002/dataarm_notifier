"""Telemetry Configuration - YAML configuration loading and management."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class TelemetryConfig:
    """Main telemetry configuration container."""

    frequency: int = 50
    buffer_size: int = 1000
    thresholds: "TelemetryThresholds" = field(default_factory=lambda: TelemetryThresholds())
    simulation: dict = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "TelemetryConfig":
        """Load configuration from YAML file."""
        if config_path is None:
            # Try default locations
            possible_paths = [
                "telemetry_config.yaml",
                "dataarm_notifier/telemetry_config.yaml",
                os.path.join(os.path.dirname(__file__), "telemetry_config.yaml"),
            ]
            for path in possible_paths:
                if Path(path).exists():
                    config_path = path
                    break

        if config_path is None or not Path(config_path).exists():
            # Return default configuration
            return cls()

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        if data is None:
            return cls()

        # Parse thresholds
        thresholds_data = data.get("thresholds", {})
        thresholds = TelemetryThresholds.from_dict(thresholds_data)

        # Parse simulation profiles
        simulation_data = data.get("simulation", {})
        profiles_data = simulation_data.get("profiles", [])
        profiles = []
        for profile_data in profiles_data:
            from .data_types import SimulationProfile

            profiles.append(SimulationProfile.from_dict(profile_data))

        default_profile = simulation_data.get("default_profile", "")

        return cls(
            frequency=data.get("telemetry", {}).get("frequency", 50),
            buffer_size=data.get("telemetry", {}).get("buffer_size", 1000),
            thresholds=thresholds,
            simulation={"profiles": profiles, "default_profile": default_profile},
        )

    def get_profile(self, name: str) -> Optional["SimulationProfile"]:
        """Get a simulation profile by name."""
        profiles = self.simulation.get("profiles", [])
        for profile in profiles:
            if profile.name == name:
                return profile
        return None

    def list_profiles(self) -> list:
        """List all available profile names."""
        return [p.name for p in self.simulation.get("profiles", [])]


# Import for forward reference
from .data_types import SimulationProfile, TelemetryThresholds

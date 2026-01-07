"""Unit tests for TelemetryConfig."""

import pytest
import tempfile
import os
import yaml

from dataarm_notifier.telemetry.config import TelemetryConfig


class TestTelemetryConfig:
    """Tests for TelemetryConfig class."""

    def test_default_config(self):
        """Test creating default configuration."""
        config = TelemetryConfig()
        assert config.frequency == 50
        assert config.buffer_size == 1000
        assert config.thresholds.tracking_deviation == 0.3
        assert config.thresholds.torque_warning == 1.8

    def test_load_default_when_no_file(self):
        """Test loading returns defaults when no config file exists."""
        config = TelemetryConfig.load("/nonexistent/path.yaml")
        assert config.frequency == 50
        assert config.thresholds.tracking_deviation == 0.3

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "telemetry": {
                "frequency": 100,
                "buffer_size": 2000,
            },
            "thresholds": {
                "tracking_deviation": 0.5,
                "torque_warning": 2.0,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = TelemetryConfig.load(config_path)
            assert config.frequency == 100
            assert config.buffer_size == 2000
            assert config.thresholds.tracking_deviation == 0.5
            assert config.thresholds.torque_warning == 2.0
        finally:
            os.unlink(config_path)

    def test_load_empty_yaml(self):
        """Test loading empty YAML file returns defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            config_path = f.name

        try:
            config = TelemetryConfig.load(config_path)
            assert config.frequency == 50
        finally:
            os.unlink(config_path)

    def test_get_profile_exists(self):
        """Test getting an existing profile."""
        config = TelemetryConfig()
        config.simulation["profiles"] = [
            type("Profile", (), {"name": "test_profile"})(),
        ]
        profile = config.get_profile("test_profile")
        assert profile is not None
        assert profile.name == "test_profile"

    def test_get_profile_not_exists(self):
        """Test getting non-existent profile returns None."""
        config = TelemetryConfig()
        profile = config.get_profile("nonexistent")
        assert profile is None

    def test_list_profiles(self):
        """Test listing all profile names."""
        config = TelemetryConfig()
        config.simulation["profiles"] = [
            type("Profile", (), {"name": "profile1"})(),
            type("Profile", (), {"name": "profile2"})(),
        ]
        profiles = config.list_profiles()
        assert profiles == ["profile1", "profile2"]

    def test_list_profiles_empty(self):
        """Test listing profiles when none exist."""
        config = TelemetryConfig()
        profiles = config.list_profiles()
        assert profiles == []

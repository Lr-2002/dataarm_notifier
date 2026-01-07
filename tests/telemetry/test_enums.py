"""Unit tests for StatusLevel and ProfileType enums."""

import pytest

from dataarm_notifier.telemetry.enums import StatusLevel, ProfileType


class TestStatusLevel:
    """Tests for StatusLevel enum."""

    def test_status_level_values(self):
        """Test that all status levels have correct values."""
        assert StatusLevel.INFO.value == "INFO"
        assert StatusLevel.WARNING.value == "WARNING"
        assert StatusLevel.ERROR.value == "ERROR"

    def test_status_level_from_value_valid(self):
        """Test from_value with valid inputs."""
        assert StatusLevel.from_value("INFO") == StatusLevel.INFO
        assert StatusLevel.from_value("WARNING") == StatusLevel.WARNING
        assert StatusLevel.from_value("ERROR") == StatusLevel.ERROR

    def test_status_level_from_value_case_insensitive(self):
        """Test from_value is case insensitive."""
        assert StatusLevel.from_value("info") == StatusLevel.INFO
        assert StatusLevel.from_value("warning") == StatusLevel.WARNING
        assert StatusLevel.from_value("error") == StatusLevel.ERROR
        assert StatusLevel.from_value("Info") == StatusLevel.INFO

    def test_status_level_from_value_unknown(self):
        """Test from_value returns INFO for unknown values."""
        assert StatusLevel.from_value("UNKNOWN") == StatusLevel.INFO
        assert StatusLevel.from_value("") == StatusLevel.INFO
        assert StatusLevel.from_value("CRITICAL") == StatusLevel.INFO

    def test_status_level_to_emoji(self):
        """Test emoji representation."""
        assert StatusLevel.INFO.to_emoji() == "🟢"
        assert StatusLevel.WARNING.to_emoji() == "🟡"
        assert StatusLevel.ERROR.to_emoji() == "🔴"

    def test_status_level_iteration(self):
        """Test that all status levels can be iterated."""
        levels = list(StatusLevel)
        assert len(levels) == 3
        assert StatusLevel.INFO in levels
        assert StatusLevel.WARNING in levels
        assert StatusLevel.ERROR in levels


class TestProfileType:
    """Tests for ProfileType enum."""

    def test_profile_type_values(self):
        """Test that all profile types have correct values."""
        assert ProfileType.SINE.value == "sine"
        assert ProfileType.STEP.value == "step"
        assert ProfileType.RAMP.value == "ramp"
        assert ProfileType.TORQUE_THRESHOLD.value == "torque_threshold"

    def test_profile_type_from_value_valid(self):
        """Test from_value with valid inputs."""
        assert ProfileType.from_value("sine") == ProfileType.SINE
        assert ProfileType.from_value("step") == ProfileType.STEP
        assert ProfileType.from_value("ramp") == ProfileType.RAMP
        assert ProfileType.from_value("torque_threshold") == ProfileType.TORQUE_THRESHOLD

    def test_profile_type_from_value_case_insensitive(self):
        """Test from_value is case insensitive."""
        assert ProfileType.from_value("SINE") == ProfileType.SINE
        assert ProfileType.from_value("Step") == ProfileType.STEP
        assert ProfileType.from_value("RAMP") == ProfileType.RAMP

    def test_profile_type_from_value_unknown(self):
        """Test from_value returns SINE for unknown values."""
        assert ProfileType.from_value("unknown") == ProfileType.SINE
        assert ProfileType.from_value("") == ProfileType.SINE
        assert ProfileType.from_value("custom") == ProfileType.SINE

    def test_profile_type_iteration(self):
        """Test that all profile types can be iterated."""
        profiles = list(ProfileType)
        assert len(profiles) == 4
        assert ProfileType.SINE in profiles
        assert ProfileType.STEP in profiles
        assert ProfileType.RAMP in profiles
        assert ProfileType.TORQUE_THRESHOLD in profiles

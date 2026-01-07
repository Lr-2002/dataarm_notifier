"""Telemetry Enums - Status and Profile type definitions."""

from enum import Enum


class StatusLevel(Enum):
    """System health status levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

    @classmethod
    def from_value(cls, value: str) -> "StatusLevel":
        """Create StatusLevel from string value."""
        value_upper = value.upper()
        for member in cls:
            if member.value == value_upper:
                return member
        return cls.INFO  # Default to INFO for unknown values

    def to_emoji(self) -> str:
        """Get emoji representation for dashboard."""
        emoji_map = {
            self.INFO: "🟢",
            self.WARNING: "🟡",
            self.ERROR: "🔴",
        }
        return emoji_map.get(self, "⚪")


class ProfileType(Enum):
    """Simulation profile types."""

    SINE = "sine"
    STEP = "step"
    RAMP = "ramp"
    TORQUE_THRESHOLD = "torque_threshold"

    @classmethod
    def from_value(cls, value: str) -> "ProfileType":
        """Create ProfileType from string value."""
        value_lower = value.lower()
        for member in cls:
            if member.value == value_lower:
                return member
        return cls.SINE  # Default to SINE for unknown values

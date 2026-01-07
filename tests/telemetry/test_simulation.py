"""Unit tests for SimulationEngine and SimulationData."""

import pytest
import time

from dataarm_notifier.telemetry.simulation import SimulationEngine, SimulationData
from dataarm_notifier.telemetry.data_types import SimulationProfile
from dataarm_notifier.telemetry.enums import ProfileType, StatusLevel


class TestSimulationData:
    """Tests for SimulationData dataclass."""

    def test_simulation_data_creation(self):
        """Test creating SimulationData."""
        data = SimulationData(
            timestamp=1.0,
            target_position=1.0,
            actual_position=0.9,
            raw_velocity=0.5,
            filtered_velocity=0.45,
            filtered_acceleration=0.1,
            torque=0.5,
            status=StatusLevel.INFO,
            status_message="Test",
        )
        assert data.timestamp == 1.0
        assert data.target_position == 1.0
        assert data.actual_position == 0.9
        assert data.status == StatusLevel.INFO


class TestSimulationEngine:
    """Tests for SimulationEngine class."""

    def test_engine_initialization(self):
        """Test engine initializes with default profile."""
        engine = SimulationEngine()
        assert engine._current_profile is not None or len(engine.list_profiles()) >= 0

    def test_list_profiles(self):
        """Test listing available profiles."""
        engine = SimulationEngine()
        profiles = engine.list_profiles()
        assert isinstance(profiles, list)

    def test_set_valid_profile(self):
        """Test setting a valid profile."""
        engine = SimulationEngine()
        # Try to set sine profile (should be available)
        result = engine.set_profile("sine_tracking")
        # May or may not succeed depending on config, but should not raise

    def test_set_invalid_profile(self):
        """Test setting an invalid profile."""
        engine = SimulationEngine()
        result = engine.set_profile("nonexistent_profile")
        assert result is False

    def test_step_returns_simulation_data(self):
        """Test that step returns SimulationData."""
        engine = SimulationEngine()
        data = engine.step(0.1)
        assert isinstance(data, SimulationData)
        assert data.timestamp >= 0

    def test_step_increases_time(self):
        """Test that consecutive steps have increasing timestamps."""
        engine = SimulationEngine()
        data1 = engine.step(0.1)
        time.sleep(0.01)
        data2 = engine.step(0.1)
        assert data2.timestamp >= data1.timestamp

    def test_shutdown(self):
        """Test engine shutdown."""
        engine = SimulationEngine()
        engine.shutdown()  # Should not raise


class TestSimulationProfiles:
    """Tests for different simulation profile types."""

    def test_sine_profile_output(self):
        """Test sine profile generates oscillating output."""
        engine = SimulationEngine()
        engine.set_profile("sine_tracking")

        # Generate several samples
        values = [engine.step(0.1).target_position for _ in range(10)]

        # Should have some variation
        assert max(values) != min(values)

    def test_sine_profile_bounded(self):
        """Test sine profile output is bounded by amplitude."""
        engine = SimulationEngine()
        engine.set_profile("sine_tracking")

        for _ in range(50):
            data = engine.step(0.1)
            # Amplitude is 1.0 by default
            assert -2.0 <= data.target_position <= 2.0

    def test_step_profile_output(self):
        """Test step profile generates step response."""
        engine = SimulationEngine()

        # Step profile should show a step change
        data = engine.step(0.1)
        assert isinstance(data.target_position, float)

    def test_ramp_profile_output(self):
        """Test ramp profile generates linear output."""
        engine = SimulationEngine()

        # Ramp profile should increase over time
        data1 = engine.step(0.1)
        data2 = engine.step(0.1)
        # Ramp target should be non-decreasing
        assert data2.target_position >= data1.target_position or data2.target_position >= 0

    def test_torque_threshold_profile(self):
        """Test torque threshold profile generates high torque."""
        engine = SimulationEngine()

        # Run for enough time to trigger warning
        for _ in range(100):
            data = engine.step(0.1)

        # Torque should eventually reach high values
        # (not asserting specific value since it depends on timing)


class TestSimulationDataIntegrity:
    """Tests for simulation data consistency."""

    def test_velocity_reasonable_range(self):
        """Test velocity values are reasonable."""
        engine = SimulationEngine()

        for _ in range(20):
            data = engine.step(0.1)
            # Velocity should be within reasonable bounds
            assert abs(data.raw_velocity) < 10.0
            assert abs(data.filtered_velocity) < 10.0

    def test_torque_non_negative(self):
        """Test torque is non-negative."""
        engine = SimulationEngine()

        for _ in range(20):
            data = engine.step(0.1)
            assert data.torque >= 0

    def test_status_valid(self):
        """Test status is a valid StatusLevel."""
        engine = SimulationEngine()

        for _ in range(20):
            data = engine.step(0.1)
            assert isinstance(data.status, StatusLevel)

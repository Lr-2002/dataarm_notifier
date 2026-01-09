# Feature Specification: CAN Monitor Integration

**Feature Branch**: `001-can-monitor-integration`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "read /home/lr-2002/project/DataArm/dataarm/control/hardware/can_monitor it will send data to you, you should define the interface the to communicate ,and you should think about how to show these can infos on our notifiers"

## Overview

Integrate the Notifier's Telemetry system with the DataArm CAN Monitor module. The Notifier will receive CAN bus metrics (bus load, RTT, frame statistics) from the can_monitor and display them on the Rerun-based dashboard alongside robot telemetry data.

## User Scenarios & Testing

### User Story 1 - Real-time CAN Bus Health Monitoring (Priority: P1)

As a robot operator, I want to see real-time CAN bus statistics (bus load, frame rates, active IDs) alongside robot motion data, so that I can verify communication health during operation.

**Why this priority**: This is the primary monitoring use case - users need immediate visibility into CAN bus health to detect communication issues before they cause robot failures.

**Independent Test**: Can be tested by running can_monitor with traffic generator and verifying Rerun plots show bus load, active IDs, and frame counts updating.

**Acceptance Scenarios**:

1. **Given** can_monitor is capturing frames, **When** the notifier connects, **Then** the notifier SHOULD receive AggregatedMetrics at the configured publish frequency.

2. **Given** CAN frames are being received, **When** the user views the Rerun dashboard, **Then** the user SHOULD see bus load percentage and total frame count in the CAN section.

3. **Given** CAN traffic is flowing normally, **When** the user monitors the system, **Then** the CAN status SHOULD remain "NOMINAL".

---

### User Story 2 - Round-Trip Time Monitoring (Priority: P1)

As a robot operator, I want to see the round-trip time (RTT) for motor commands, so that I can identify communication delays with specific joints.

**Why this priority**: RTT directly impacts robot control responsiveness.

**Independent Test**: Can be tested by introducing artificial delays and verifying RTT plots show elevated values.

**Acceptance Scenarios**:

1. **Given** RTT data is being collected, **When** the user views the dashboard, **Then** the user SHOULD see mean and P95 RTT for each joint.

2. **Given** RTT exceeds the threshold, **When** a timeout occurs, **Then** the system SHOULD log a TIMEOUT event.

---

### User Story 3 - CAN Event Alerts (Priority: P2)

As a robot operator, I want to receive alerts for CAN anomalies (timeouts, error frames, dropped frames), so that I can quickly identify communication problems.

**Why this priority**: Early detection of CAN errors prevents cascading failures.

**Independent Test**: Can be tested by disconnecting a motor CAN cable and verifying error events appear.

**Acceptance Scenarios**:

1. **Given** an error frame is received, **When** processed, **Then** an ERROR event SHOULD be logged with CAN ID and details.

2. **Given** frames are dropped, **When** reported, **Then** a DROP event SHOULD be logged with the count.

---

### User Story 4 - Per-Joint CAN Statistics (Priority: P2)

As a robot operator, I want to see per-joint CAN statistics (FPS, jitter), so that I can identify which specific joint has communication issues.

**Why this priority**: Users need to know which joint is problematic to fix it.

**Independent Test**: Can be tested by isolating traffic from one motor and verifying only that joint's statistics update.

**Acceptance Scenarios**:

1. **Given** frames are received from joint 0, **When** statistics are displayed, **Then** joint 0's FPS and jitter SHOULD be shown with the joint name.

2. **Given** multiple joints are active, **When** comparing statistics, **Then** the user SHOULD be able to overlay plots for different joints.

---

### Edge Cases

- What happens when can_monitor is not running?
- How does the system handle CAN bus complete failure?
- What happens when the Rerun viewer disconnects?
- How does the system handle missing joint name mappings?

## Requirements

### Functional Requirements

- **FR-001**: The notifier MUST provide a `CANMetricsHandler` class that implements `CANMonitorNotifierAPI` to receive metrics.
- **FR-002**: The notifier MUST log CAN bus statistics (bus load %, total frames, active IDs) to Rerun at configured frequency (10-50Hz).
- **FR-003**: The notifier MUST log per-ID statistics (FPS, jitter P95) using joint names when mapping is available.
- **FR-004**: The notifier MUST track and display round-trip times (mean, P50, P95, max) for each send_id/recv_id pair.
- **FR-005**: The notifier MUST forward CAN events (TIMEOUT, ERROR_FRAME, DROP) to the event log with appropriate severity.
- **FR-006**: The notifier MUST provide a visual CAN bus health indicator (NOMINAL, WARNING, ERROR).
- **FR-007**: The notifier MUST handle graceful degradation when can_monitor is unavailable.

### Key Entities

- **CANMetricsHandler**: Bridge class receiving AggregatedMetrics from can_monitor and logging to Rerun.
- **CANEventHandler**: Converts CANEvent objects to Rerun TextLog entries.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can view CAN bus statistics within 2 seconds of connecting to can_monitor.
- **SC-002**: CAN metrics update at configured rate (within 10% tolerance).
- **SC-003**: All CAN events appear in event log within 500ms of occurrence.
- **SC-004**: RTT values display with sub-millisecond precision.
- **SC-005**: System remains stable during CAN bus errors (no crashes).

## Assumptions

1. can_monitor module runs as a separate process on the same machine.
2. Communication via shared memory, socket, or direct function call (interface defined below).
3. Rerun viewer is initialized by existing TelemetryProducer.
4. CAN ID to joint name mapping is provided by dataarm configuration.

## Dependencies

- dataarm can_monitor: provides `CANMonitorNotifierAPI`, `AggregatedMetrics`, `CANEvent`
- notifier telemetry: provides `TelemetryProducer`, Rerun integration

## Out of Scope

- Modifying CAN frame capture logic (dataarm responsibility)
- Changes to USB lamp control functionality
- Cloud monitoring integration
- Historical data storage

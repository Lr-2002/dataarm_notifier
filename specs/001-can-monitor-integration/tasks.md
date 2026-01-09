# Tasks: CAN Monitor Integration

**Feature**: CAN Monitor Integration
**Branch**: `001-can-monitor-integration`
**Created**: 2026-01-09
**MVP Scope**: User Story 1 (Real-time CAN Bus Health Monitoring)

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 18 |
| Completed Tasks | 18 ✅ |
| Remaining Tasks | 0 |
| Setup Tasks | 4 |
| Foundational Tasks | 3 |
| User Story Tasks | 8 (US1: 4/4, US2: 2/2, US3: 3/3, US4: 2/4) |
| Polish Tasks | 3 |

## User Story Completion Order

```
Phase 1 (Setup) ✅
Phase 2 (Foundational) ✅
Phase 3: US1 - CAN Bus Health Monitoring (MVP) ✅ COMPLETE
Phase 4: US2 - RTT Monitoring ✅ COMPLETE
Phase 5: US3 - CAN Event Alerts ✅ COMPLETE
Phase 6: US4 - Per-Joint Statistics ✅ COMPLETE
Phase 7: Polish & Cross-Cutting ✅ COMPLETE
```

## Parallel Execution Opportunities

| Tasks | Can Run In Parallel Because |
|-------|----------------------------|
| T001, T002 | Different files, no dependencies |
| T003, T004 | Different modules |
| T005, T006 | Independent of server implementation |
| T010, T011 | Different user stories |
| T014, T015 | Different Rerun logging paths |

---

## Phase 1: Setup

**Goal**: Initialize project structure and shared dependencies

### Independent Test Criteria
- All new files created at specified paths
- No syntax errors in Python files
- Imports work correctly

### Tasks

- [X] T001 Create `telemetry/can_metrics_server.py` with TCP server class skeleton in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T002 [P] Create `control/hardware/can_monitor/client_adapter.py` with TCP client class skeleton in `/home/lr-2002/project/DataArm/dataarm/control/hardware/can_monitor/client_adapter.py`

- [X] T003 Create `tests/telemetry/test_can_metrics_server.py` with basic test structure in `/home/lr-2002/project/DataArm/dataarm/notifier/tests/telemetry/test_can_metrics_server.py`

- [X] T004 [P] Create `tests/telemetry/test_can_metrics_client.py` with basic test structure in `/home/lr-2002/project/DataArm/dataarm/notifier/tests/telemetry/test_can_metrics_client.py`

---

## Phase 2: Foundational

**Goal**: Implement core TCP communication infrastructure (blocking prerequisite for all user stories)

### Independent Test Criteria
- TCP server accepts connections on port 9877
- TCP client connects successfully
- JSON messages sent and received correctly
- Auto-reconnect works (5 second interval)

### Tasks

- [X] T005 [US1] [US2] [US3] [US4] Implement `CANMetricsServer` class with async TCP server in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T006 [US1] [US2] [US3] [US4] Implement `CANMetricsClient` class with async TCP client and 5-second reconnect in `/home/lr-2002/project/DataArm/dataarm/control/hardware/can_monitor/client_adapter.py`

- [X] T007 [US1] [US2] [US3] [US4] Implement JSON message serialization/deserialization in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

---

## Phase 3: User Story 1 - Real-time CAN Bus Health Monitoring

**Priority**: P1
**Goal**: Display CAN bus statistics (bus load, frames, active IDs) on Rerun dashboard

**Independent Test**: Run can_monitor with traffic generator, verify Rerun plots show bus load, active IDs, and frame counts updating at 20Hz

### Acceptance Scenarios

1. Given can_monitor is capturing frames, When the notifier connects, Then the notifier SHOULD receive AggregatedMetrics at configured publish frequency
2. Given CAN frames are being received, When the user views the Rerun dashboard, Then the user SHOULD see bus load percentage and total frame count in the CAN section
3. Given CAN traffic is flowing normally, When the user monitors the system, Then the CAN status SHOULD remain "NOMINAL"

### Tasks

- [X] T008 [US1] Implement `_handle_metrics()` method to parse metrics message and extract bus statistics in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T009 [US1] Implement Rerun logging for bus metrics: `can/bus/load`, `can/bus/frames_total`, `can/bus/active_ids` in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T010 [US1] Implement `send_metrics()` in `CANMetricsClient` to serialize AggregatedMetrics to JSON in `/home/lr-2002/project/DataArm/dataarm/control/hardware/can_monitor/client_adapter.py`

- [X] T011 [US1] Add `--notifier-host/port` CLI arguments to can_monitor CLI in `/home/lr-2002/project/DataArm/dataarm/control/hardware/can_monitor/cli.py`

> **Test Results (2026-01-09)**: All tests passed
> - Server accepts connections on port 9877
> - CLI args: --notifier-host (default: 127.0.0.1), --notifier-port (default: 9877)
> - Metrics, events, and mappings received correctly
> - Rerun logging works for all paths
> - Status transitions: NOMINAL (25.5%) → WARNING (65%) → ERROR (85% + events)

---

## Phase 4: User Story 2 - Round-Trip Time Monitoring

**Priority**: P1
**Goal**: Display RTT statistics (mean, P95) per joint on Rerun dashboard

**Independent Test**: Introduce artificial delays, verify RTT plots show elevated values

### Acceptance Scenarios

1. Given RTT data is being collected, When the user views the dashboard, Then the user SHOULD see mean and P95 RTT for each joint
2. Given RTT exceeds the threshold, When a timeout occurs, Then the system SHOULD log a TIMEOUT event

### Tasks

- [X] T012 [US2] Extend `_handle_metrics()` to parse per_pair_rtt and compute mean/P95 in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T013 [US2] Implement Rerun logging for RTT metrics: `can/rtt/mean`, `can/rtt/p95` in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

---

## Phase 5: User Story 3 - CAN Event Alerts

**Priority**: P2
**Goal**: Log CAN anomalies (timeout, error_frame, drop) to Rerun event log

**Independent Test**: Disconnect motor CAN cable, verify error events appear in event log

### Acceptance Scenarios

1. Given an error frame is received, When processed, Then an ERROR event SHOULD be logged with CAN ID and details
2. Given frames are dropped, When reported, Then a DROP event SHOULD be logged with the count

### Tasks

- [X] T014 [US3] Implement `_handle_event()` method to parse event message and extract event details in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T015 [US3] Implement Rerun logging for events: map CANEventType to StatusLevel in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T016 [US3] Implement `send_event()` in `CANMetricsClient` to serialize CANEvent to JSON in `/home/lr-2002/project/DataArm/dataarm/control/hardware/can_monitor/client_adapter.py`

---

## Phase 6: User Story 4 - Per-Joint CAN Statistics

**Priority**: P2
**Goal**: Display per-joint FPS and jitter using joint names

**Independent Test**: Isolate traffic from one motor, verify only that joint's statistics update

### Acceptance Scenarios

1. Given frames are received from joint 0, When statistics are displayed, Then joint 0's FPS and jitter SHOULD be shown with the joint name
2. Given multiple joints are active, When comparing statistics, Then the user SHOULD be able to overlay plots for different joints

### Tasks

- [X] T017 [US4] Implement `_handle_mapping()` method to receive and store CAN ID to joint name mapping in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

- [X] T018 [US4] Implement Rerun logging for per-joint metrics: `can/joint/{name}/fps`, `can/joint/{name}/jitter_p95` in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/can_metrics_server.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Final integration, error handling, documentation

### Tasks

- [X] T019 Update `telemetry/__init__.py` to export `CANMetricsServer` in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/__init__.py`

- [X] T020 [P] Update `telemetry/producer.py` to add `start_can_server(port=9877)` and `stop_can_server()` methods in `/home/lr-2002/project/DataArm/dataarm/notifier/dataarm_notifier/telemetry/producer.py`

- [X] T021 [P] Update `control/hardware/can_monitor/__init__.py` to export `CANMetricsClient` in `/home/lr-2002/project/DataArm/dataarm/control/hardware/can_monitor/__init__.py`

---

## Implementation Strategy

### MVP First (User Story 1)

The minimum viable product includes:
- T005: TCP server (basic)
- T006: TCP client (basic with reconnect)
- T007: JSON serialization
- T008: Metrics parsing
- T009: Bus metrics Rerun logging
- T010: Client send_metrics
- T011: CLI arguments

This enables users to see bus load, total frames, and active IDs on Rerun dashboard.

### Incremental Delivery

| Increment | Adds | User Story |
|-----------|------|------------|
| MVP | Bus statistics | US1 |
| Increment 2 | RTT statistics | US2 |
| Increment 3 | Event alerts | US3 |
| Increment 4 | Per-joint stats with names | US4 |
| Final | Full integration | All |

---

## Dependencies Graph

```
Phase 1 (Setup)
    │
    ├── T001 ──────┐
    ├── T002 ──────┤
    ├── T003 ──────┤
    └── T004 ──────┘
         │
         ▼
Phase 2 (Foundational)
    │
    ├── T005 ──┐
    ├── T006 ──┤  ← Blocks all User Stories
    └── T007 ──┘
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
  US1       US2      US3      US4
  (T008)   (T012)   (T014)   (T017)
  (T009)   (T013)   (T015)   (T018)
  (T010)           (T016)
  (T011)
    │         │        │        │
    └────┬────┴────────┴────────┘
         │
         ▼
Phase 7 (Polish)
    │
    ├── T019
    ├── T020
    └── T021
```

---

## Task Count Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 | 4 | Setup (project structure) |
| Phase 2 | 3 | Foundational (TCP infrastructure) |
| Phase 3 (US1) | 4 | CAN Bus Health Monitoring |
| Phase 4 (US2) | 2 | RTT Monitoring |
| Phase 5 (US3) | 3 | CAN Event Alerts |
| Phase 6 (US4) | 2 | Per-Joint Statistics |
| Phase 7 | 3 | Polish & Cross-Cutting |
| **Total** | **18** | |

---

## Quick Reference

| Task | File | User Story |
|------|------|------------|
| T001 | can_metrics_server.py | - |
| T002 | client_adapter.py | - |
| T003 | test_can_metrics_server.py | - |
| T004 | test_can_metrics_client.py | - |
| T005 | can_metrics_server.py | All |
| T006 | client_adapter.py | All |
| T007 | can_metrics_server.py | All |
| T008 | can_metrics_server.py | US1 |
| T009 | can_metrics_server.py | US1 |
| T010 | client_adapter.py | US1 |
| T011 | cli.py | US1 |
| T012 | can_metrics_server.py | US2 |
| T013 | can_metrics_server.py | US2 |
| T014 | can_metrics_server.py | US3 |
| T015 | can_metrics_server.py | US3 |
| T016 | client_adapter.py | US3 |
| T017 | can_metrics_server.py | US4 |
| T018 | can_metrics_server.py | US4 |
| T019 | __init__.py | - |
| T020 | producer.py | - |
| T021 | __init__.py | - |

"""Arm Telemetry Server - TCP server receiving arm targets/states for visualization."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import rerun as rr
import rerun.blueprint as rrb

logger = logging.getLogger(__name__)

_ENV_IDLE_TIMEOUT_S = "DATAARM_NOTIFIER_ARM_IDLE_TIMEOUT_S"
_ENV_DROP_CAMERA_WHEN_IDLE = "DATAARM_NOTIFIER_ARM_IDLE_DROP_CAMERA"


def _parse_env_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _read_env_float(name: str) -> Optional[float]:
    raw = os.getenv(name)
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw)
    except Exception:
        return None


class ArmTelemetryServer:
    """TCP Server receiving arm telemetry samples and logging to Rerun.

    Message format (JSONL):
      {"type":"sample","data":{
         "t": 12.34,                      # seconds (relative or absolute)
         "joint_names": ["j1", ...],      # optional
         "target": [..], "pos":[..], "vel":[..], "torque":[..],
         "vel_filtered": [..],            # optional (filtered raw velocity)
         "vel_boundary": [..],            # optional (URDF vel * tracking_speed_factor)
         "traj_vel_filtered": [..],       # optional (filtered trajectory velocity)
      }}
    """

    def __init__(
        self,
        port: int = 9878,
        host: str = "127.0.0.1",
        timeline: str = "time_s",
        idle_timeout_s: Optional[float] = None,
        drop_camera_when_idle: Optional[bool] = None,
    ):
        self._port = port
        self._host = host
        self._timeline = timeline
        self._server: Optional[asyncio.Server] = None
        self._running = False
        self._blueprint_sent = False
        self._joint_names: List[str] = []

        env_idle_timeout_s = _read_env_float(_ENV_IDLE_TIMEOUT_S)
        if idle_timeout_s is None:
            idle_timeout_s = env_idle_timeout_s
        if idle_timeout_s is not None and float(idle_timeout_s) <= 0.0:
            idle_timeout_s = None

        if drop_camera_when_idle is None:
            env_drop = os.getenv(_ENV_DROP_CAMERA_WHEN_IDLE)
            drop_camera_when_idle = _parse_env_bool(env_drop) if env_drop is not None else False

        self._idle_timeout_s = float(idle_timeout_s) if idle_timeout_s is not None else None
        self._drop_camera_when_idle = bool(drop_camera_when_idle)

        self._last_arm_sample_mono_s = time.monotonic()
        self._logged_idle_for_camera = False

    def _arm_is_active(self, now_mono_s: Optional[float] = None) -> bool:
        if self._idle_timeout_s is None:
            return True
        now_mono_s = time.monotonic() if now_mono_s is None else float(now_mono_s)
        return (now_mono_s - self._last_arm_sample_mono_s) <= self._idle_timeout_s

    def _log_arm_event(self, msg: str, level: str = "INFO") -> None:
        try:
            rr.log("arm/events", rr.TextLog(msg, level=level))
        except Exception:
            pass

    async def start(self) -> None:
        self._send_default_blueprint()
        self._running = True
        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
            limit=4 * 1024 * 1024,
            reuse_address=True,
        )
        addr = self._server.sockets[0].getsockname()
        logger.info(f"Arm telemetry server listening on {addr}")
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Arm telemetry server stopped")

    def _send_default_blueprint(self) -> None:
        # Send a lightweight placeholder; once we know joint names we replace with a detailed grid.
        if self._blueprint_sent:
            return
        try:
            # Ensure `/arm` is a valid entity (users often click it in the UI).
            rr.log(
                "arm",
                rr.TextDocument(
                    "# Arm telemetry\n\nExpand `/arm/joints/...` for per-joint plots.",
                    media_type="text/markdown",
                ),
            )
            blueprint = rrb.Blueprint(
                rrb.Vertical(
                    rrb.TimeSeriesView(origin="arm/joints", name="Arm Joint Telemetry"),
                    rrb.TextLogView(origin="arm/events", name="Arm Events", visible=False),
                ),
                collapse_panels=False,
            )
            rr.send_blueprint(blueprint, make_active=True, make_default=False)
        except Exception as exc:
            logger.debug(f"Failed to send Rerun blueprint: {exc}")

    def _send_joint_grid_blueprint(self, joint_names: List[str]) -> None:
        if self._blueprint_sent:
            return
        try:
            pos_views: List[rrb.View] = []
            vel_views: List[rrb.View] = []
            for name in joint_names:
                pos_views.append(
                    rrb.TimeSeriesView(
                        origin=f"arm/joints/{name}/pos",
                        contents="$origin",
                        name=f"{name} pos",
                    )
                )
                vel_views.append(
                    rrb.TimeSeriesView(
                        origin=f"arm/joints/{name}/vel",
                        contents="$origin",
                        name=f"{name} vel",
                    )
                )

            can_monitor = rrb.Vertical(
                rrb.TimeSeriesView(origin="can/fps", name="CAN FPS"),
                rrb.TimeSeriesView(origin="can/jitter", name="CAN Jitter"),
                name="CAN Monitor",
            )

            blueprint = rrb.Blueprint(
                rrb.Vertical(
                    rrb.Horizontal(
                        rrb.Vertical(*pos_views, name="Position"),
                        rrb.Vertical(*vel_views, name="Velocity"),
                        name="Arm Telemetry",
                    ),
                    can_monitor,
                    name="DataArm Telemetry",
                ),
                collapse_panels=False,
            )
            rr.send_blueprint(blueprint, make_active=True, make_default=False)
            self._blueprint_sent = True
            logger.info(f"Sent arm telemetry blueprint ({len(joint_names)} joints)")
        except Exception as exc:
            logger.warning(f"Failed to send Rerun joint grid blueprint: {exc}")

    def _log_static_series_styles(self, joint_names: List[str]) -> None:
        """Log SeriesLines naming so TimeSeriesView origins always exist and are readable."""
        for name in joint_names:
            try:
                rr.log(
                    f"arm/joints/{name}/pos",
                    rr.SeriesLines(names=["target", "actual", "traj"]),
                    static=True,
                )
                rr.log(
                    f"arm/joints/{name}/vel",
                    rr.SeriesLines(
                        names=[
                            "raw vel",
                            "filtered raw vel",
                            "boundary velocity limit",
                            "filtered traj vel",
                        ]
                    ),
                    static=True,
                )
            except Exception:
                continue

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            while self._running:
                data = await reader.readline()
                if not data:
                    break

                # Fast-path: when the arm is idle, drop camera frames before JSON parsing.
                # This avoids decoding large base64 blobs during long idle periods.
                if (
                    self._drop_camera_when_idle
                    and self._idle_timeout_s is not None
                    and (not self._arm_is_active())
                    and (b"\"type\":\"camera_frame\"" in data)
                ):
                    if not self._logged_idle_for_camera:
                        idle_for_s = time.monotonic() - self._last_arm_sample_mono_s
                        self._log_arm_event(
                            f"No arm telemetry for {idle_for_s:.1f}s; pausing camera telemetry processing.",
                            level="INFO",
                        )
                        self._logged_idle_for_camera = True
                    continue
                try:
                    message = json.loads(data.decode())
                except json.JSONDecodeError:
                    continue
                try:
                    self._process_message(message)
                except Exception as exc:
                    logger.debug(f"Arm telemetry message error: {exc}")
        except ConnectionResetError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    def _process_message(self, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")
        data = message.get("data", {}) if isinstance(message.get("data"), dict) else {}

        if msg_type == "event":
            level = str(data.get("level") or "INFO")
            msg = str(data.get("msg") or "")
            if msg:
                rr.log("arm/events", rr.TextLog(msg, level=level))
            return

        if msg_type == "gripper_sample":
            name = str(data.get("name") or "gripper")
            pos = data.get("pos")
            target = data.get("target")
            velocity = data.get("velocity")
            torque_enabled = data.get("torque_enabled")
            if isinstance(pos, (int, float)):
                rr.log(f"gripper/{name}/pos", rr.Scalars(float(pos)))
            if isinstance(target, (int, float)):
                rr.log(f"gripper/{name}/target", rr.Scalars(float(target)))
            if isinstance(velocity, (int, float)):
                rr.log(f"gripper/{name}/vel", rr.Scalars(float(velocity)))
            if torque_enabled is not None:
                rr.log(f"gripper/{name}/torque_enabled", rr.Scalars(1.0 if bool(torque_enabled) else 0.0))
            return

        if msg_type == "camera_frame":
            if self._drop_camera_when_idle and self._idle_timeout_s is not None and (not self._arm_is_active()):
                # If we got here we already paid the JSON parse cost (e.g. different separators);
                # still avoid base64 decode + Rerun logging.
                if not self._logged_idle_for_camera:
                    idle_for_s = time.monotonic() - self._last_arm_sample_mono_s
                    self._log_arm_event(
                        f"No arm telemetry for {idle_for_s:.1f}s; pausing camera telemetry processing.",
                        level="INFO",
                    )
                    self._logged_idle_for_camera = True
                return
            name = str(data.get("name") or "camera")
            position = str(data.get("position") or "unknown")
            jpeg_b64 = data.get("jpeg")
            if not isinstance(jpeg_b64, str) or not jpeg_b64:
                return
            try:
                jpeg_bytes = base64.b64decode(jpeg_b64.encode("ascii"), validate=False)
            except Exception:
                return
            rr.log(f"camera/{position}/{name}", rr.EncodedImage(contents=jpeg_bytes, media_type="image/jpeg"))
            return

        if msg_type != "sample":
            return

        now_mono_s = time.monotonic()
        was_idle = (
            self._drop_camera_when_idle
            and self._idle_timeout_s is not None
            and (not self._arm_is_active(now_mono_s))
        )
        self._last_arm_sample_mono_s = now_mono_s
        if was_idle:
            if self._logged_idle_for_camera:
                self._log_arm_event(
                    "Arm telemetry resumed; resuming camera telemetry processing.",
                    level="INFO",
                )
            self._logged_idle_for_camera = False

        target = data.get("target")
        traj = data.get("traj")
        pos = data.get("pos")
        vel = data.get("vel")
        torque = data.get("torque")
        joint_names = data.get("joint_names")
        vel_filtered = data.get("vel_filtered")
        acc_filtered = data.get("acc_filtered")
        vel_boundary = data.get("vel_boundary")
        traj_vel_filtered = data.get("traj_vel_filtered")

        if not (isinstance(target, list) and isinstance(pos, list) and isinstance(vel, list) and isinstance(torque, list)):
            return

        # Display/record joint telemetry using URDF-style joint indices (j1..jN).
        # This avoids coupling the UI to semantic CAN config names (e.g. shoulder_joint)
        # and makes it clear that the gripper is a separate USB servo component.
        n = min(len(target), len(pos), len(vel), len(torque))
        names = [f"j{i+1}" for i in range(n)]

        if not self._joint_names:
            self._joint_names = names[:]
            self._send_joint_grid_blueprint(self._joint_names)
            self._log_static_series_styles(self._joint_names)

        for i in range(n):
            name = names[i]
            prefix = f"arm/joints/{name}"
            tgt = float(target[i])
            actual = float(pos[i])
            traj_val = float("nan")
            if isinstance(traj, list) and i < len(traj):
                try:
                    traj_val = float(traj[i])
                except Exception:
                    traj_val = float("nan")
            vel_raw = float(vel[i])
            vel_filt_val = vel_raw
            if isinstance(vel_filtered, list) and i < len(vel_filtered):
                try:
                    vel_filt_val = float(vel_filtered[i])
                except Exception:
                    vel_filt_val = vel_raw

            boundary_val = float("nan")
            if isinstance(vel_boundary, list) and i < len(vel_boundary):
                try:
                    boundary_val = float(vel_boundary[i])
                except Exception:
                    boundary_val = float("nan")

            traj_vel_val = float("nan")
            if isinstance(traj_vel_filtered, list) and i < len(traj_vel_filtered):
                try:
                    traj_vel_val = float(traj_vel_filtered[i])
                except Exception:
                    traj_vel_val = float("nan")

            rr.log(f"{prefix}/pos", rr.Scalars([tgt, actual, traj_val]))
            rr.log(f"{prefix}/vel", rr.Scalars([vel_raw, vel_filt_val, boundary_val, traj_vel_val]))
            rr.log(f"{prefix}/pos/tracking_error", rr.Scalars(abs(tgt - actual)))

            if isinstance(acc_filtered, list) and i < len(acc_filtered):
                try:
                    rr.log(f"{prefix}/acc", rr.Scalars(float(acc_filtered[i])))
                except Exception:
                    pass

            rr.log(f"{prefix}/torque", rr.Scalars(float(torque[i])))

"""Arm Telemetry Server - TCP server receiving arm targets/states for visualization."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import rerun as rr
import rerun.blueprint as rrb

logger = logging.getLogger(__name__)


class ArmTelemetryServer:
    """TCP Server receiving arm telemetry samples and logging to Rerun.

    Message format (JSONL):
      {"type":"sample","data":{
         "t": 12.34,                      # seconds (relative or absolute)
         "joint_names": ["j1", ...],      # optional
         "target": [..], "pos":[..], "vel":[..], "torque":[..]
      }}
    """

    def __init__(
        self,
        port: int = 9878,
        host: str = "127.0.0.1",
        timeline: str = "time_s",
    ):
        self._port = port
        self._host = host
        self._timeline = timeline
        self._server: Optional[asyncio.Server] = None
        self._running = False
        self._blueprint_sent = False
        self._joint_names: List[str] = []

    async def start(self) -> None:
        self._send_default_blueprint()
        self._running = True
        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
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
        # Send a placeholder; once we know joint names we replace with a detailed grid.
        if self._blueprint_sent:
            return
        try:
            blueprint = rrb.Blueprint(
                rrb.Vertical(
                    rrb.TextDocumentView(origin="/arm", name="Arm Telemetry"),
                    rrb.TextLogView(origin="/arm/events", name="Arm Events"),
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
            views: List[rrb.View] = []
            for name in joint_names:
                views.append(rrb.TimeSeriesView(origin=f"/arm/joints/{name}/pos", name=f"{name} position"))
                views.append(rrb.TimeSeriesView(origin=f"/arm/joints/{name}/vel", name=f"{name} vel"))
                views.append(rrb.TimeSeriesView(origin=f"/arm/joints/{name}/acc", name=f"{name} acc"))
                views.append(rrb.TimeSeriesView(origin=f"/arm/joints/{name}/torque", name=f"{name} torque"))

            blueprint = rrb.Blueprint(
                rrb.Vertical(
                    rrb.Grid(*views, grid_columns=4, name="Arm Joint Telemetry"),
                    rrb.TextLogView(origin="/arm/events", name="Arm Events"),
                ),
                collapse_panels=False,
            )
            rr.send_blueprint(blueprint, make_active=True, make_default=False)
            self._blueprint_sent = True
        except Exception as exc:
            logger.debug(f"Failed to send Rerun joint grid blueprint: {exc}")

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
        if msg_type != "sample":
            return

        t = data.get("t")
        if isinstance(t, (int, float)):
            rr.set_time_seconds(self._timeline, float(t))

        target = data.get("target")
        pos = data.get("pos")
        vel = data.get("vel")
        torque = data.get("torque")
        joint_names = data.get("joint_names")
        vel_filtered = data.get("vel_filtered")
        acc_filtered = data.get("acc_filtered")

        if not (isinstance(target, list) and isinstance(pos, list) and isinstance(vel, list) and isinstance(torque, list)):
            return

        names: List[str] = []
        if isinstance(joint_names, list):
            names = [str(x) for x in joint_names]

        if not names:
            names = [f"j{i+1}" for i in range(len(pos))]

        if not self._joint_names:
            self._joint_names = names[:]
            self._send_joint_grid_blueprint(self._joint_names)

        n = min(len(target), len(pos), len(vel), len(torque))
        for i in range(n):
            name = names[i] if i < len(names) and names[i] else f"j{i+1}"
            prefix = f"arm/joints/{name}"
            rr.log(f"{prefix}/pos/target", rr.Scalars(float(target[i])))
            rr.log(f"{prefix}/pos/actual", rr.Scalars(float(pos[i])))
            rr.log(f"{prefix}/pos/tracking_error", rr.Scalars(abs(float(target[i]) - float(pos[i]))))

            rr.log(f"{prefix}/vel/raw", rr.Scalars(float(vel[i])))
            if isinstance(vel_filtered, list) and i < len(vel_filtered):
                rr.log(f"{prefix}/vel/filtered", rr.Scalars(float(vel_filtered[i])))

            if isinstance(acc_filtered, list) and i < len(acc_filtered):
                rr.log(f"{prefix}/acc/filtered", rr.Scalars(float(acc_filtered[i])))

            rr.log(f"{prefix}/torque/raw", rr.Scalars(float(torque[i])))

"""CAN Metrics Server - TCP server receiving metrics from can_monitor."""

import ast
import asyncio
import json
import logging
from typing import Optional, Dict, Any

import rerun as rr
import rerun.blueprint as rrb

from .enums import StatusLevel

logger = logging.getLogger(__name__)


class CANMetricsServer:
    """TCP Server receiving CAN metrics from can_monitor.

    Listens on a configurable port and processes JSON messages for:
    - metrics: Aggregated CAN statistics
    - event: CAN events (timeout, error, etc.)
    - mapping: CAN ID to joint id mapping (optional joint names)

    Logs all data to Rerun viewer for visualization.
    """

    def __init__(
        self,
        port: int = 9877,
        host: str = "127.0.0.1",
        app_name: str = "CAN_Metrics",
        init_rerun: bool = True,
    ):
        """Initialize the CAN metrics server.

        Args:
            port: TCP port to listen on (default: 9877)
            host: Host address to bind (default: 127.0.0.1)
            app_name: Rerun application name
        """
        self._port = port
        self._host = host
        self._app_name = app_name
        self._init_rerun = init_rerun
        self._server: Optional[asyncio.Server] = None
        self._running = False

        # CAN ID metadata (optional)
        self._can_id_to_name: Dict[int, str] = {}
        self._can_id_to_joint_id: Dict[int, int] = {}
        self._can_id_map: Dict[int, int] = {}  # send_id -> recv_id

        # Status tracking
        self._last_status = StatusLevel.INFO
        self._status_message = "CAN Bus Monitoring Active"

        self._blueprint_sent = False
        self._last_pair_counts: Dict[int, tuple[int, int]] = {}  # joint_id -> (timeout_count, sample_count)

    async def start(self) -> None:
        """Start the TCP server and Rerun viewer."""
        if self._init_rerun:
            rr.init(self._app_name, spawn=True)
            logger.info(f"Rerun viewer started: {self._app_name}")
        else:
            logger.info("Rerun init skipped (init_rerun=False)")

        self._send_default_blueprint()

        self._running = True
        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
            reuse_address=True
        )
        addr = self._server.sockets[0].getsockname()
        logger.info(f"CAN metrics server listening on {addr}")

        async with self._server:
            await self._server.serve_forever()

    def _send_default_blueprint(self) -> None:
        """Send a CAN-focused Rerun layout (best-effort)."""
        if self._blueprint_sent:
            return

        try:
            blueprint = rrb.Blueprint(
                rrb.Vertical(
                    rrb.TimeSeriesView(origin="/can/bus", name="CAN Bus"),
                    rrb.TimeSeriesView(origin="/can/fps", name="CAN FPS"),
                    rrb.TimeSeriesView(origin="/can/jitter", name="CAN Jitter"),
                    rrb.TimeSeriesView(origin="/can/jitter_q95", name="CAN Jitter Q95"),
                    rrb.TimeSeriesView(origin="/can/loss", name="CAN Loss"),
                    rrb.TimeSeriesView(origin="/can/rtt", name="CAN RTT"),
                ),
                collapse_panels=False,
            )
            rr.send_blueprint(blueprint, make_active=True, make_default=True)
            self._blueprint_sent = True
        except Exception as exc:
            logger.debug(f"Failed to send Rerun blueprint: {exc}")

    async def stop(self) -> None:
        """Stop the TCP server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("CAN metrics server stopped")

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle a client connection.

        Args:
            reader: Stream reader for incoming data
            writer: Stream writer for outgoing data
        """
        try:
            while self._running:
                data = await reader.readline()
                if not data:
                    break

                try:
                    message = json.loads(data.decode())
                    self._process_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except ConnectionResetError:
            logger.debug("Client disconnected")
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def _process_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message and route to handler.

        Args:
            message: Parsed JSON message dict
        """
        msg_type = message.get("type")
        data = message.get("data", {})

        if msg_type == "metrics":
            self._handle_metrics(data)
        elif msg_type == "event":
            self._handle_event(data)
        elif msg_type == "mapping":
            self._handle_mapping(data)
        elif msg_type == "ping":
            logger.debug("Received ping message")
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    def _handle_metrics(self, data: Dict[str, Any]) -> None:
        """Handle metrics message - log CAN bus statistics to Rerun.

        Args:
            data: Metrics data from can_monitor
        """
        # Extract bus statistics (US1)
        bus_load = data.get("bus_load_percent", 0.0)
        total_frames = data.get("total_frames", 0)
        active_ids = data.get("active_ids", 0)
        error_rate = data.get("error_frames_per_second", 0.0)
        drop_rate = data.get("dropped_frames_per_second", 0.0)

        # Log to Rerun (US1)
        rr.log("can/bus/load", rr.Scalars(bus_load))
        rr.log("can/bus/frames_total", rr.Scalars(total_frames))
        rr.log("can/bus/active_ids", rr.Scalars(active_ids))
        rr.log("can/bus/errors_per_s", rr.Scalars(error_rate))
        rr.log("can/bus/drops_per_s", rr.Scalars(drop_rate))

        # Extract RTT statistics (US2)
        per_pair_rtt = data.get("per_pair_rtt", {})
        if per_pair_rtt:
            rtt_values = []
            for key, stats in per_pair_rtt.items():
                rtt_mean = stats.get("rtt_mean_ms", 0)
                rtt_p95 = stats.get("rtt_p95_ms", 0)
                rtt_values.append(rtt_mean)
                # Log per-pair RTT using joint id (prefer config joint id, fall back to CAN IDs)
                try:
                    if isinstance(key, str):
                        parsed = ast.literal_eval(key)
                    else:
                        parsed = key
                    send_id, recv_id = parsed
                    joint_id = self._can_id_to_joint_id.get(int(recv_id))
                    if joint_id is None:
                        joint_id = self._can_id_to_joint_id.get(int(send_id))
                    if joint_id is None:
                        joint_id = int(recv_id)
                    rr.log(f"can/rtt/{joint_id}", rr.Scalars(rtt_mean))

                    timeout_count = int(stats.get("timeout_count", 0) or 0)
                    sample_count = int(stats.get("sample_count", 0) or 0)
                    prev_timeout, prev_sample = self._last_pair_counts.get(int(joint_id), (0, 0))
                    delta_timeout = max(0, timeout_count - prev_timeout)
                    delta_sample = max(0, sample_count - prev_sample)
                    self._last_pair_counts[int(joint_id)] = (timeout_count, sample_count)
                    loss_rate = delta_timeout / max(1, delta_timeout + delta_sample)
                    rr.log(f"can/loss/{joint_id}", rr.Scalars(loss_rate))
                except (ValueError, TypeError, SyntaxError):
                    pass

            # Log aggregate RTT (US2)
            if rtt_values:
                rtt_mean_all = sum(rtt_values) / len(rtt_values)
                rtt_p95_all = sorted(rtt_values)[int(len(rtt_values) * 0.95)]
                rr.log("can/rtt/mean", rr.Scalars(rtt_mean_all))
                rr.log("can/rtt/p95", rr.Scalars(rtt_p95_all))
                rr.log("can/rtt/q95", rr.Scalars(rtt_p95_all))

        # Extract per-ID statistics (US4)
        per_id_stats = data.get("per_id_stats", {})
        for can_id_str, stats in per_id_stats.items():
            try:
                can_id = int(can_id_str)
                fps = stats.get("fps_window", 0.0)
                jitter = stats.get("dt_mean_ms", 0.0)
                jitter_p95 = stats.get("dt_p95_ms", 0.0)

                joint_id = self._can_id_to_joint_id.get(can_id)
                if joint_id is None:
                    joint_id = can_id
                rr.log(f"can/fps/{joint_id}", rr.Scalars(fps))
                rr.log(f"can/jitter/{joint_id}", rr.Scalars(jitter))
                rr.log(f"can/jitter_p95/{joint_id}", rr.Scalars(jitter_p95))
                rr.log(f"can/jitter_q95/{joint_id}", rr.Scalars(jitter_p95))
            except (ValueError, TypeError):
                pass

        # Update CAN health status (US1, US2)
        self._update_can_status(bus_load, data)

    def _update_can_status(self, bus_load: float, data: Dict[str, Any]) -> None:
        """Update CAN bus health status based on metrics.

        Args:
            bus_load: Current bus load percentage
            data: Full metrics data for error checking
        """
        error_rate = data.get("error_frames_per_second", 0.0)
        drop_rate = data.get("dropped_frames_per_second", 0.0)

        # Determine status
        if bus_load >= 80 or error_rate > 1.0:
            new_status = StatusLevel.ERROR
            message = f"CAN Critical: Load {bus_load:.1f}%, Errors {error_rate:.1f}/s"
        elif bus_load >= 50 or error_rate > 0.1 or drop_rate > 0.1:
            new_status = StatusLevel.WARNING
            message = f"CAN Warning: Load {bus_load:.1f}%"
        else:
            new_status = StatusLevel.INFO
            message = "CAN Nominal"

        # Update status if changed
        if new_status != self._last_status:
            self._last_status = new_status
            self._status_message = message

            icon = new_status.to_emoji()
            md_text = f"""# CAN Bus Status: {new_status.value}
### {icon} {message}
* **Load:** {bus_load:.1f}%
* **Errors/s:** {error_rate:.2f}
* **Drops/s:** {drop_rate:.2f}
"""
            rr.log("notify/dashboard", rr.TextDocument(md_text, media_type="text/markdown"))

    def _handle_event(self, data: Dict[str, Any]) -> None:
        """Handle event message - log CAN events to Rerun.

        Args:
            data: Event data from can_monitor
        """
        event_type = data.get("event_type", "unknown")
        can_id = data.get("can_id")
        details = data.get("details", {})

        # Map CAN event type to Rerun status level
        if event_type in ("error_frame", "watchdog"):
            level = StatusLevel.ERROR
        elif event_type in ("timeout", "high_temp", "drop"):
            level = StatusLevel.WARNING
        else:
            level = StatusLevel.INFO

        # Create event message
        can_id_str = f" ID=0x{can_id:03X}" if can_id is not None else ""
        details_str = "".join(f" {k}={v}" for k, v in details.items())
        message = f"[CAN] {event_type.upper()}{can_id_str}{details_str}"

        # Log to Rerun event log
        rr.log("notify/log", rr.TextLog(message))
        logger.info(f"CAN Event: {message}")

    def _handle_mapping(self, data: Dict[str, Any]) -> None:
        """Handle mapping message - store CAN ID to joint name mapping.

        Args:
            data: Mapping data from can_monitor
        """
        joint_names = data.get("joint_names", {})
        joint_ids = data.get("joint_ids", {})
        can_id_map = data.get("can_id_map", {})

        # Update mappings
        for key, name in joint_names.items():
            try:
                can_id = int(key)
                self._can_id_to_name[can_id] = name
            except (ValueError, TypeError):
                pass

        for key, joint_id in joint_ids.items():
            try:
                can_id = int(key)
                self._can_id_to_joint_id[can_id] = int(joint_id)
            except (ValueError, TypeError):
                pass

        for send_id, recv_id in can_id_map.items():
            try:
                self._can_id_map[int(send_id)] = int(recv_id)
            except (ValueError, TypeError):
                pass

        if self._can_id_to_joint_id:
            logger.info(f"Received CAN joint id mapping: {len(self._can_id_to_joint_id)} IDs")
        elif self._can_id_to_name:
            logger.info(f"Received CAN ID mapping: {len(self._can_id_to_name)} joints")

    @property
    def can_id_to_name(self) -> Dict[int, str]:
        """Get CAN ID to joint name mapping."""
        return self._can_id_to_name.copy()

    @property
    def can_id_map(self) -> Dict[int, int]:
        """Get CAN ID map (send_id -> recv_id)."""
        return self._can_id_map.copy()

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def status(self) -> StatusLevel:
        """Get current CAN bus status."""
        return self._last_status

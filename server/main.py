import asyncio
import json
import time
from typing import Any

import websockets

from network import AirPenTracker


HOST = "0.0.0.0"
PORT = 8765


tracker = AirPenTracker()
clients: set[websockets.WebSocketServerProtocol] = set()
last_imu_time: float | None = None


def _safe_float(value: Any, default: float = 0.0) -> float:
	try:
		if value is None:
			return default
		return float(value)
	except (TypeError, ValueError):
		return default


async def broadcast(payload: dict[str, Any]) -> None:
	if not clients:
		return
	message = json.dumps(payload)
	stale: list[websockets.WebSocketServerProtocol] = []
	for client in clients:
		try:
			await client.send(message)
		except websockets.ConnectionClosed:
			stale.append(client)
	for client in stale:
		clients.discard(client)


def process_imu(data: dict[str, Any]) -> dict[str, Any]:
	global last_imu_time

	ax = _safe_float(data.get("ax"), 0.0)
	ay = _safe_float(data.get("ay"), 0.0)

	now = time.time()
	incoming_dt = _safe_float(data.get("dt"), 0.0)
	if incoming_dt > 0:
		dt = incoming_dt
	elif last_imu_time is not None:
		dt = now - last_imu_time
	else:
		dt = 0.016
	last_imu_time = now

	point = tracker.update(ax=ax, ay=ay, dt=dt)
	return {
		"type": "point",
		**point,
	}


async def handler(websocket: websockets.WebSocketServerProtocol) -> None:
	clients.add(websocket)
	print(f"Client connected ({len(clients)} total)")

	await websocket.send(
		json.dumps(
			{
				"type": "status",
				"message": "connected",
				"clients": len(clients),
			}
		)
	)

	try:
		async for message in websocket:
			try:
				data = json.loads(message)
			except json.JSONDecodeError:
				continue

			msg_type = data.get("type", "imu")

			if msg_type == "imu":
				point = process_imu(data)
				await broadcast(point)
			elif msg_type == "reset":
				tracker.reset()
				await broadcast({"type": "reset"})
			elif msg_type == "ping":
				await websocket.send(json.dumps({"type": "pong"}))
	except websockets.ConnectionClosed:
		pass
	finally:
		clients.discard(websocket)
		print(f"Client disconnected ({len(clients)} total)")


async def main() -> None:
	print(f"AirPen server listening on ws://{HOST}:{PORT}")
	async with websockets.serve(handler, HOST, PORT):
		await asyncio.Future()


if __name__ == "__main__":
	asyncio.run(main())

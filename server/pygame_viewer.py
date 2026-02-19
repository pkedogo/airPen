from __future__ import annotations

import asyncio
import json
import queue
import threading
from dataclasses import dataclass
from typing import Any

import pygame
import websockets


@dataclass
class ViewerConfig:
    ws_url: str = "ws://127.0.0.1:8765"
    width: int = 1280
    height: int = 800
    fullscreen: bool = True
    max_position: float = 2.0
    background: tuple[int, int, int] = (11, 15, 24)
    stroke: tuple[int, int, int] = (96, 165, 250)
    stroke_width: int = 3


class WebSocketReceiver(threading.Thread):
    def __init__(
        self,
        url: str,
        incoming: queue.Queue[dict[str, Any]],
        outgoing: queue.Queue[dict[str, Any]],
        stop_event: threading.Event,
    ) -> None:
        super().__init__(daemon=True)
        self.url = url
        self.incoming = incoming
        self.outgoing = outgoing
        self.stop_event = stop_event

    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                async with websockets.connect(self.url) as ws:
                    self.incoming.put({"type": "status", "message": "connected"})
                    while not self.stop_event.is_set():
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=0.02)
                            data = json.loads(raw)
                            if isinstance(data, dict):
                                self.incoming.put(data)
                        except asyncio.TimeoutError:
                            pass
                        except json.JSONDecodeError:
                            pass

                        while True:
                            try:
                                outbound = self.outgoing.get_nowait()
                            except queue.Empty:
                                break
                            await ws.send(json.dumps(outbound))

            except (OSError, websockets.WebSocketException) as error:
                self.incoming.put({"type": "status", "message": f"disconnected: {error}"})
                await asyncio.sleep(1.0)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def to_screen(x: float, y: float, width: int, height: int, max_position: float) -> tuple[int, int]:
    norm_x = clamp(x / max_position, -1.0, 1.0)
    norm_y = clamp(y / max_position, -1.0, 1.0)
    screen_x = int((norm_x + 1.0) * 0.5 * width)
    screen_y = int((1.0 - norm_y) * 0.5 * height)
    return screen_x, screen_y


def run_viewer(config: ViewerConfig) -> None:
    pygame.init()
    pygame.display.set_caption("AirPen Pygame Viewer")

    if config.fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((config.width, config.height), pygame.RESIZABLE)
    canvas = pygame.Surface(screen.get_size())
    canvas.fill(config.background)

    font = pygame.font.SysFont(None, 26)
    clock = pygame.time.Clock()

    incoming: queue.Queue[dict[str, Any]] = queue.Queue()
    outgoing: queue.Queue[dict[str, Any]] = queue.Queue()
    stop_event = threading.Event()
    worker = WebSocketReceiver(config.ws_url, incoming, outgoing, stop_event)
    worker.start()

    last_point: tuple[int, int] | None = None
    status_text = "Connecting..."
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    canvas.fill(config.background)
                    last_point = None
                elif event.key == pygame.K_r:
                    outgoing.put({"type": "reset"})
                    last_point = None
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                canvas = pygame.transform.smoothscale(canvas, (event.w, event.h))
                last_point = None

        while True:
            try:
                data = incoming.get_nowait()
            except queue.Empty:
                break

            message_type = data.get("type")
            if message_type == "status":
                status_text = str(data.get("message", ""))
            elif message_type == "point":
                x = float(data.get("x", 0.0))
                y = float(data.get("y", 0.0))
                point = to_screen(x, y, canvas.get_width(), canvas.get_height(), config.max_position)
                if last_point is not None:
                    pygame.draw.line(canvas, config.stroke, last_point, point, config.stroke_width)
                last_point = point
            elif message_type == "reset":
                last_point = None

        screen.blit(canvas, (0, 0))
        overlay = font.render(f"{status_text} | C: clear  R: reset tracker  Esc: quit", True, (243, 244, 246))
        screen.blit(overlay, (16, 12))
        pygame.display.flip()
        clock.tick(120)

    stop_event.set()
    worker.join(timeout=2.0)
    pygame.quit()


if __name__ == "__main__":
    run_viewer(ViewerConfig())

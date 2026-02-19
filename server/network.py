from __future__ import annotations

from dataclasses import dataclass
from math import exp


@dataclass
class TrackerConfig:
	deadband: float = 0.12
	velocity_damping: float = 4.0
	position_scale: float = 1.0
	max_velocity: float = 3.5
	max_position: float = 2.0
	stationary_threshold: float = 0.08
	stationary_frames_to_zero: int = 10


class AirPenTracker:
	def __init__(self, config: TrackerConfig | None = None) -> None:
		self.config = config or TrackerConfig()
		self.x = 0.0
		self.y = 0.0
		self.vx = 0.0
		self.vy = 0.0
		self._stationary_frames = 0

	def reset(self) -> None:
		self.x = 0.0
		self.y = 0.0
		self.vx = 0.0
		self.vy = 0.0
		self._stationary_frames = 0

	def update(self, ax: float, ay: float, dt: float) -> dict[str, float]:
		dt = max(0.005, min(dt, 0.06))

		ax = self._apply_deadband(ax, self.config.deadband)
		ay = self._apply_deadband(ay, self.config.deadband)

		if abs(ax) < self.config.stationary_threshold and abs(ay) < self.config.stationary_threshold:
			self._stationary_frames += 1
		else:
			self._stationary_frames = 0

		if self._stationary_frames >= self.config.stationary_frames_to_zero:
			self.vx = 0.0
			self.vy = 0.0
		else:
			self.vx += ax * dt
			self.vy += ay * dt

		damping = exp(-self.config.velocity_damping * dt)
		self.vx *= damping
		self.vy *= damping

		self.vx = self._clamp(self.vx, -self.config.max_velocity, self.config.max_velocity)
		self.vy = self._clamp(self.vy, -self.config.max_velocity, self.config.max_velocity)

		self.x += self.vx * dt * self.config.position_scale
		self.y += self.vy * dt * self.config.position_scale

		self.x = self._clamp(self.x, -self.config.max_position, self.config.max_position)
		self.y = self._clamp(self.y, -self.config.max_position, self.config.max_position)

		return {
			"x": self.x,
			"y": self.y,
			"vx": self.vx,
			"vy": self.vy,
			"ax": ax,
			"ay": ay,
			"dt": dt,
		}

	@staticmethod
	def _apply_deadband(value: float, threshold: float) -> float:
		if abs(value) <= threshold:
			return 0.0
		return value - threshold if value > 0 else value + threshold

	@staticmethod
	def _clamp(value: float, low: float, high: float) -> float:
		return max(low, min(high, value))
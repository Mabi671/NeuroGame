"""Grid pathfinding helpers for isometric scenes."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Iterable

from neurogame.engine import IsometricScene, Tile

GridPosition = tuple[int, int]


@dataclass(frozen=True)
class GridPathfinder:
    """Find paths across scene tiles using A* search."""

    tiles: dict[GridPosition, Tile]
    blocked_sprites: frozenset[str] = frozenset({"tile_water"})

    @classmethod
    def from_scene(
        cls,
        scene: IsometricScene,
        *,
        blocked_sprites: Iterable[str] = ("tile_water",),
    ) -> GridPathfinder:
        return cls(
            tiles={(tile.x, tile.y): tile for tile in scene.tiles},
            blocked_sprites=frozenset(blocked_sprites),
        )

    def is_walkable(self, position: GridPosition) -> bool:
        tile = self.tiles.get(position)
        return tile is not None and tile.sprite not in self.blocked_sprites

    def neighbors(self, position: GridPosition) -> tuple[GridPosition, ...]:
        x, y = position
        candidates = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        return tuple(candidate for candidate in candidates if self.is_walkable(candidate))

    def find_path(self, start: GridPosition, goal: GridPosition) -> list[GridPosition]:
        """Return a path from start to goal, including both endpoints.

        An empty list means either endpoint is not walkable or no route exists.
        """

        if not self.is_walkable(start) or not self.is_walkable(goal):
            return []
        if start == goal:
            return [start]

        frontier: list[tuple[int, int, GridPosition]] = []
        sequence = count()
        heappush(frontier, (0, next(sequence), start))
        came_from: dict[GridPosition, GridPosition | None] = {start: None}
        cost_so_far: dict[GridPosition, int] = {start: 0}

        while frontier:
            _, _, current = heappop(frontier)
            if current == goal:
                break

            for neighbor in self.neighbors(current):
                new_cost = cost_so_far[current] + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self._heuristic(neighbor, goal)
                    heappush(frontier, (priority, next(sequence), neighbor))
                    came_from[neighbor] = current

        if goal not in came_from:
            return []

        path: list[GridPosition] = []
        current: GridPosition | None = goal
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    @staticmethod
    def _heuristic(left: GridPosition, right: GridPosition) -> int:
        return abs(left[0] - right[0]) + abs(left[1] - right[1])

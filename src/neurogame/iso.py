"""Coordinate transforms for isometric scenes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenPoint:
    """A projected point in screen-space pixels."""

    x: float
    y: float


@dataclass(frozen=True)
class GridPoint:
    """A point on the isometric grid."""

    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class IsoCamera:
    """Projects between grid coordinates and a 2:1 isometric view.

    The grid uses x/y for ground-plane tile positions and z for elevation.
    `origin_x` and `origin_y` define where grid coordinate (0, 0, 0) appears
    on screen.
    """

    tile_width: int = 64
    tile_height: int = 32
    origin_x: float = 0.0
    origin_y: float = 0.0
    elevation_height: int = 32

    def __post_init__(self) -> None:
        if self.tile_width <= 0:
            raise ValueError("tile_width must be positive")
        if self.tile_height <= 0:
            raise ValueError("tile_height must be positive")
        if self.elevation_height <= 0:
            raise ValueError("elevation_height must be positive")

    @property
    def half_tile_width(self) -> float:
        return self.tile_width / 2

    @property
    def half_tile_height(self) -> float:
        return self.tile_height / 2

    def grid_to_screen(self, x: float, y: float, z: float = 0.0) -> ScreenPoint:
        """Project an isometric grid coordinate into screen space."""

        screen_x = (x - y) * self.half_tile_width + self.origin_x
        screen_y = (
            (x + y) * self.half_tile_height
            - z * self.elevation_height
            + self.origin_y
        )
        return ScreenPoint(screen_x, screen_y)

    def screen_to_grid(self, screen_x: float, screen_y: float, z: float = 0.0) -> GridPoint:
        """Unproject a screen coordinate back onto a grid plane at elevation z."""

        normalized_x = (screen_x - self.origin_x) / self.half_tile_width
        normalized_y = (
            screen_y - self.origin_y + z * self.elevation_height
        ) / self.half_tile_height

        grid_x = (normalized_x + normalized_y) / 2
        grid_y = (normalized_y - normalized_x) / 2
        return GridPoint(grid_x, grid_y, z)

    def draw_sort_key(
        self,
        x: float,
        y: float,
        z: float = 0.0,
        layer: int = 0,
    ) -> tuple[float, float, float, int]:
        """Return a stable painter's-algorithm key for isometric objects."""

        return (x + y + z, y, x, layer)

"""Selectable spirit actors and movement behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from neurogame.engine import Entity, IsometricScene
from neurogame.pathfinding import GridPathfinder, GridPosition


@dataclass
class AirSpirit:
    """A selectable spirit that can pathfind to clicked tile destinations."""

    scene: IsometricScene
    entity_id: str = "spirit-air"
    blocked_sprites: Iterable[str] = ("tile_water",)
    selected: bool = False
    path: list[GridPosition] = field(default_factory=list)

    @classmethod
    def spawn(
        cls,
        scene: IsometricScene,
        *,
        entity_id: str = "spirit-air",
        x: float,
        y: float,
        z: float = 0.2,
    ) -> AirSpirit:
        scene.add_entity(
            Entity(
                entity_id=entity_id,
                x=x,
                y=y,
                z=z,
                sprite="spirit_placeholder",
            )
        )
        return cls(scene=scene, entity_id=entity_id)

    @property
    def entity(self) -> Entity:
        return self.scene.get_entity(self.entity_id)

    @property
    def current_tile(self) -> GridPosition:
        entity = self.entity
        return (round(entity.x), round(entity.y))

    def select_at_screen(self, screen_x: float, screen_y: float) -> bool:
        """Select the spirit if the screen coordinate lands on its placeholder."""

        entity = self.entity
        sprite = self.scene.sprites.get(entity.sprite)
        screen = self.scene.camera.grid_to_screen(entity.x, entity.y, entity.z)
        padding = 10
        left = screen.x - sprite.width * sprite.anchor_x - padding
        top = screen.y - sprite.height * sprite.anchor_y - padding
        right = left + sprite.width + padding * 2
        bottom = top + sprite.height + padding * 2

        self.selected = left <= screen_x <= right and top <= screen_y <= bottom
        if not self.selected:
            self.path.clear()
        return self.selected

    def clear_selection(self) -> None:
        self.selected = False
        self.path.clear()

    def destination_from_screen(self, screen_x: float, screen_y: float) -> GridPosition:
        grid = self.scene.camera.screen_to_grid(screen_x, screen_y)
        return (round(grid.x), round(grid.y))

    def travel_to_screen(self, screen_x: float, screen_y: float) -> list[GridPosition]:
        return self.travel_to(self.destination_from_screen(screen_x, screen_y))

    def travel_to(self, destination: GridPosition) -> list[GridPosition]:
        """Plan movement to a destination tile if the spirit is selected."""

        if not self.selected:
            return []

        pathfinder = GridPathfinder.from_scene(
            self.scene,
            blocked_sprites=self.blocked_sprites,
        )
        path = pathfinder.find_path(self.current_tile, destination)
        self.path = path[1:] if path else []
        return path

    def step_along_path(self) -> bool:
        """Move one tile along the current path."""

        if not self.path:
            return False

        next_x, next_y = self.path.pop(0)
        entity = self.entity
        self.scene.move_entity(self.entity_id, next_x, next_y, entity.z)
        return True

    def draw_overlay(self, canvas: object) -> None:
        """Draw selection and route hints on a Tkinter-like canvas."""

        if not self.selected:
            return

        entity = self.entity
        sprite = self.scene.sprites.get(entity.sprite)
        screen = self.scene.camera.grid_to_screen(entity.x, entity.y, entity.z)
        left = screen.x - sprite.width * sprite.anchor_x - 7
        top = screen.y - sprite.height * sprite.anchor_y - 7
        right = left + sprite.width + 14
        bottom = top + sprite.height + 14

        canvas.create_oval(
            left,
            top,
            right,
            bottom,
            outline="#f9f871",
            width=3,
        )

        if self.path:
            points: list[float] = [screen.x, screen.y]
            for x, y in self.path:
                path_screen = self.scene.camera.grid_to_screen(x, y, entity.z)
                points.extend([path_screen.x, path_screen.y])
            canvas.create_line(*points, fill="#f9f871", width=2, dash=(6, 4))
            destination = self.path[-1]
            destination_screen = self.scene.camera.grid_to_screen(
                destination[0],
                destination[1],
                0,
            )
            canvas.create_oval(
                destination_screen.x - 8,
                destination_screen.y - 8,
                destination_screen.x + 8,
                destination_screen.y + 8,
                outline="#f9f871",
                width=2,
            )

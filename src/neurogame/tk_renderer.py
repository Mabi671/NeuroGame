"""Tkinter renderer for the isometric engine demo."""

from __future__ import annotations

import random
from tkinter import Canvas, Tk

from neurogame.engine import DrawCommand, IsometricScene
from neurogame.sprites import SpriteDefinition


def _motion_points_along_grid_path(
    path: list[tuple[int, int]],
    *,
    steps_per_edge: int,
) -> list[tuple[float, float]]:
    """Linearly interpolate each grid edge into float positions for smooth motion."""

    if steps_per_edge <= 0:
        raise ValueError("steps_per_edge must be positive")
    if len(path) < 2:
        return []

    points: list[tuple[float, float]] = []
    for index in range(len(path) - 1):
        x0, y0 = path[index]
        x1, y1 = path[index + 1]
        for step in range(1, steps_per_edge + 1):
            t = step / steps_per_edge
            points.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return points


class TkinterRenderer:
    """Render an isometric scene to a Tkinter canvas."""

    def __init__(
        self,
        scene: IsometricScene,
        *,
        width: int = 960,
        height: int = 640,
        title: str = "NeuroGame Isometric Demo",
        background: str = "#111827",
    ) -> None:
        self.scene = scene
        self._highlight_entity_id: str | None = None
        self.root = Tk()
        self.root.title(title)
        self.canvas = Canvas(
            self.root,
            width=width,
            height=height,
            background=background,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

    def render(self) -> None:
        self.canvas.delete("all")
        commands = self.scene.build_draw_commands()
        for command in commands:
            self._draw_command(command)
        highlight_id = self._highlight_entity_id
        if highlight_id:
            for command in commands:
                if (
                    command.kind == "entity"
                    and command.object_id == highlight_id
                    and command.sprite.shape == "spirit"
                ):
                    self._draw_spirit_highlight_ring(
                        command.screen.x,
                        command.screen.y,
                        command.sprite,
                    )
                    break

    def run(
        self,
        *,
        pathfinding_entity_id: str | None = "player",
        path_steps_per_grid_edge: int = 14,
        path_micro_step_ms: int = 12,
        autonomous_spirit_ids: tuple[str, ...] = (),
        autonomous_spirit_tick_ms: int | None = None,
    ) -> None:
        self._path_motion_queue: list[tuple[float, float]] = []
        self._path_after_id: object | None = None
        self._pathfinding_entity_id = pathfinding_entity_id
        self._highlight_entity_id = pathfinding_entity_id
        self._path_steps_per_grid_edge = path_steps_per_grid_edge
        self._path_micro_step_ms = path_micro_step_ms
        self._auto_spirit_ids = tuple(autonomous_spirit_ids)
        self._auto_spirit_queues: dict[str, list[tuple[float, float]]] = {
            entity_id: [] for entity_id in self._auto_spirit_ids
        }
        self._auto_spirit_after_id: object | None = None
        self._auto_spirit_tick_ms = (
            autonomous_spirit_tick_ms
            if autonomous_spirit_tick_ms is not None
            else path_micro_step_ms
        )
        if pathfinding_entity_id:
            self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.render()
        if self._auto_spirit_ids:
            self._schedule_autonomous_spirits()
        self.root.mainloop()

    def _on_canvas_click(self, event) -> None:
        entity_id = self._pathfinding_entity_id
        if not entity_id:
            return

        grid = self.scene.camera.screen_to_grid(float(event.x), float(event.y))
        goal_x = int(round(grid.x))
        goal_y = int(round(grid.y))

        path = self.scene.pathfind_entity_to_cell(entity_id, goal_x, goal_y)
        if not path:
            return

        if self._path_after_id is not None:
            self.root.after_cancel(self._path_after_id)
            self._path_after_id = None

        self._path_motion_queue = _motion_points_along_grid_path(
            path,
            steps_per_edge=self._path_steps_per_grid_edge,
        )
        self._advance_path_motion()

    def _advance_path_motion(self) -> None:
        entity_id = self._pathfinding_entity_id
        if not entity_id or not self._path_motion_queue:
            return

        next_x, next_y = self._path_motion_queue.pop(0)
        self.scene.move_entity(entity_id, float(next_x), float(next_y))
        self.render()

        if self._path_motion_queue:
            self._path_after_id = self.root.after(self._path_micro_step_ms, self._advance_path_motion)
        else:
            self._path_after_id = None

    def _schedule_autonomous_spirits(self) -> None:
        self._auto_spirit_after_id = self.root.after(
            self._auto_spirit_tick_ms,
            self._advance_autonomous_spirits,
        )

    def _advance_autonomous_spirits(self) -> None:
        self._auto_spirit_after_id = None
        if not self._auto_spirit_ids:
            return

        for entity_id in self._auto_spirit_ids:
            queue = self._auto_spirit_queues.setdefault(entity_id, [])
            if not queue:
                self._assign_random_autonomous_path(entity_id)
                queue = self._auto_spirit_queues.setdefault(entity_id, [])

            if queue:
                next_x, next_y = queue.pop(0)
                self.scene.move_entity(entity_id, float(next_x), float(next_y))

        self.render()
        self._schedule_autonomous_spirits()

    def _assign_random_autonomous_path(self, entity_id: str) -> None:
        bounds = self.scene.floor_grid_bounds()
        if bounds is None:
            return

        min_x, max_x, min_y, max_y = bounds
        for _ in range(120):
            goal_x = random.randint(min_x, max_x)
            goal_y = random.randint(min_y, max_y)
            path = self.scene.pathfind_entity_to_cell(entity_id, goal_x, goal_y)
            if path is None:
                continue
            if len(path) < 2:
                continue
            self._auto_spirit_queues[entity_id] = _motion_points_along_grid_path(
                path,
                steps_per_edge=self._path_steps_per_grid_edge,
            )
            return

    def _draw_command(self, command: DrawCommand) -> None:
        sprite = command.sprite
        if sprite.shape == "diamond":
            self._draw_diamond(command.screen.x, command.screen.y, sprite)
        elif sprite.shape == "pawn":
            self._draw_pawn(command.screen.x, command.screen.y, sprite)
        elif sprite.shape == "spirit":
            self._draw_spirit(command.screen.x, command.screen.y, sprite)
        else:
            self._draw_box(command.screen.x, command.screen.y, sprite)

    def _draw_diamond(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        half_w = sprite.width / 2
        half_h = sprite.height / 2
        self.canvas.create_polygon(
            x,
            y - half_h,
            x + half_w,
            y,
            x,
            y + half_h,
            x - half_w,
            y,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )

    def _draw_pawn(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        left, top = self._anchored_bounds(x, y, sprite)
        right = left + sprite.width
        bottom = top + sprite.height
        head_size = sprite.width * 0.58
        head_left = x - head_size / 2
        head_top = top
        head_right = x + head_size / 2
        head_bottom = top + head_size

        self.canvas.create_oval(
            head_left,
            head_top,
            head_right,
            head_bottom,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )
        self.canvas.create_polygon(
            x,
            top + head_size * 0.7,
            right,
            bottom,
            left,
            bottom,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )

    def _draw_spirit(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        left, top = self._anchored_bounds(x, y, sprite)
        right = left + sprite.width
        bottom = top + sprite.height
        glow_margin = 8

        self.canvas.create_oval(
            left - glow_margin,
            top - glow_margin,
            right + glow_margin,
            bottom + glow_margin,
            fill="",
            outline=sprite.fill,
            width=1,
        )
        self.canvas.create_oval(
            left,
            top,
            right,
            bottom,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )
        self.canvas.create_oval(
            x - 8,
            top + sprite.height * 0.33,
            x - 3,
            top + sprite.height * 0.44,
            fill=sprite.outline,
            outline=sprite.outline,
        )
        self.canvas.create_oval(
            x + 3,
            top + sprite.height * 0.33,
            x + 8,
            top + sprite.height * 0.44,
            fill=sprite.outline,
            outline=sprite.outline,
        )
        self.canvas.create_line(
            left + 4,
            bottom - 4,
            x,
            bottom + 8,
            right - 4,
            bottom - 4,
            fill=sprite.outline,
            width=2,
            smooth=True,
        )

    def _draw_spirit_highlight_ring(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        """Gold ring drawn only for the player-controlled spirit."""

        left, top = self._anchored_bounds(x, y, sprite)
        right = left + sprite.width
        bottom = top + sprite.height
        margin = 10
        self.canvas.create_oval(
            left - margin,
            top - margin,
            right + margin,
            bottom + margin,
            fill="",
            outline="#f5d547",
            width=3,
        )

    def _draw_box(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        left, top = self._anchored_bounds(x, y, sprite)
        self.canvas.create_rectangle(
            left,
            top,
            left + sprite.width,
            top + sprite.height,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )

    @staticmethod
    def _anchored_bounds(
        x: float,
        y: float,
        sprite: SpriteDefinition,
    ) -> tuple[float, float]:
        return (
            x - sprite.width * sprite.anchor_x,
            y - sprite.height * sprite.anchor_y,
        )

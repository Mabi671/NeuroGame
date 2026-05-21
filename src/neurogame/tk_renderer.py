"""Tkinter renderer for the isometric engine demo."""

from __future__ import annotations

from tkinter import Canvas, Tk

from neurogame.engine import DrawCommand, IsometricScene
from neurogame.sprites import SpriteDefinition


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
        for command in self.scene.build_draw_commands():
            self._draw_command(command)

    def run(self) -> None:
        self.render()
        self.root.mainloop()

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

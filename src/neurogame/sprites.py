"""Sprite definitions and placeholder metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SpriteDefinition:
    """Metadata for a drawable sprite or placeholder shape.

    `asset_path` can point at future artwork. While it is unset, renderers can
    use the placeholder colors and shape to keep the scene visible.

    When ``blocks_pathfinding`` is true, grid pathfinding treats the owning
    tile or entity cell as impassable (except the moving entity may still stand
    on its own start cell).

    When ``spirit_drain_half_max_hp`` is true on a ground tile, a spirit that
    enters that grid cell loses half of its max health (see scene hazard logic).
    """

    name: str
    width: int
    height: int
    fill: str
    outline: str = "#1d2433"
    shape: str = "diamond"
    anchor_x: float = 0.5
    anchor_y: float = 1.0
    asset_path: Path | None = None
    blocks_pathfinding: bool = False
    spirit_drain_half_max_hp: bool = False

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("sprite width must be positive")
        if self.height <= 0:
            raise ValueError("sprite height must be positive")
        if not 0 <= self.anchor_x <= 1:
            raise ValueError("anchor_x must be between 0 and 1")
        if not 0 <= self.anchor_y <= 1:
            raise ValueError("anchor_y must be between 0 and 1")


class SpriteLibrary:
    """Named lookup table for sprite definitions."""

    def __init__(self, sprites: Iterable[SpriteDefinition] | None = None) -> None:
        self._sprites: dict[str, SpriteDefinition] = {}
        for sprite in sprites or ():
            self.register(sprite)

    def register(self, sprite: SpriteDefinition) -> None:
        self._sprites[sprite.name] = sprite

    def get(self, name: str) -> SpriteDefinition:
        try:
            return self._sprites[name]
        except KeyError as exc:
            available = ", ".join(sorted(self._sprites)) or "none"
            raise KeyError(f"Unknown sprite '{name}'. Available sprites: {available}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._sprites))


def build_default_sprite_library() -> SpriteLibrary:
    """Build placeholder sprites for the first playable prototype."""

    return SpriteLibrary(
        [
            SpriteDefinition(
                name="tile_grass",
                width=32,
                height=16,
                fill="#62b15f",
                outline="#2f6f3e",
                shape="diamond",
            ),
            SpriteDefinition(
                name="tile_water",
                width=32,
                height=16,
                fill="#4f9ddf",
                outline="#2f5f96",
                shape="diamond",
                blocks_pathfinding=True,
            ),
            SpriteDefinition(
                name="tile_stone",
                width=32,
                height=16,
                fill="#8e95a3",
                outline="#555b66",
                shape="diamond",
            ),
            SpriteDefinition(
                name="tile_blue_patch",
                width=32,
                height=16,
                fill="#6aa6ff",
                outline="#3a5fbf",
                shape="diamond",
                blocks_pathfinding=True,
            ),
            SpriteDefinition(
                name="tile_red_drain",
                width=32,
                height=16,
                fill="#c94c4c",
                outline="#7a1f1f",
                shape="diamond",
                spirit_drain_half_max_hp=True,
            ),
            SpriteDefinition(
                name="player_placeholder",
                width=16,
                height=28,
                fill="#f2c14e",
                outline="#735c19",
                shape="pawn",
            ),
            SpriteDefinition(
                name="npc_placeholder",
                width=16,
                height=25,
                fill="#d66ba0",
                outline="#74324f",
                shape="pawn",
            ),
            SpriteDefinition(
                name="spirit_placeholder",
                width=17,
                height=21,
                fill="#b8f7ff",
                outline="#4c9cac",
                shape="spirit",
                blocks_pathfinding=True,
            ),
            SpriteDefinition(
                name="spirit_fire_placeholder",
                width=17,
                height=21,
                fill="#ff9a56",
                outline="#9e3e1d",
                shape="spirit",
                blocks_pathfinding=True,
            ),
            SpriteDefinition(
                name="spirit_forest_placeholder",
                width=17,
                height=21,
                fill="#93e06c",
                outline="#3d7c35",
                shape="spirit",
                blocks_pathfinding=True,
            ),
            SpriteDefinition(
                name="prop_boulder",
                width=18,
                height=22,
                fill="#6b5b4f",
                outline="#3a3028",
                shape="pawn",
                blocks_pathfinding=True,
            ),
        ]
    )

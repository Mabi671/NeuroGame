"""Scene graph and draw command generation for isometric games."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from neurogame.iso import IsoCamera, ScreenPoint
from neurogame.sprites import SpriteDefinition, SpriteLibrary, build_default_sprite_library


@dataclass(frozen=True)
class Tile:
    """A ground-plane tile in the isometric scene."""

    x: int
    y: int
    z: int = 0
    sprite: str = "tile_grass"


@dataclass(frozen=True)
class Entity:
    """A moveable or interactive object in the scene."""

    entity_id: str
    x: float
    y: float
    z: float = 0.0
    sprite: str = "player_placeholder"
    layer: int = 10


@dataclass(frozen=True)
class DrawCommand:
    """A renderer-neutral instruction for drawing one scene object."""

    sort_key: tuple[float, float, float, int]
    screen: ScreenPoint
    sprite: SpriteDefinition
    kind: str
    object_id: str
    grid_position: tuple[float, float, float]


@dataclass
class IsometricScene:
    """Container for tiles, entities, camera, and draw command generation."""

    camera: IsoCamera = field(default_factory=IsoCamera)
    sprites: SpriteLibrary = field(default_factory=build_default_sprite_library)
    tiles: list[Tile] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)

    @classmethod
    def flat_map(
        cls,
        width: int,
        height: int,
        *,
        camera: IsoCamera | None = None,
        default_sprite: str = "tile_grass",
    ) -> IsometricScene:
        """Create a scene with a rectangular floor of placeholder tiles."""

        if width <= 0:
            raise ValueError("width must be positive")
        if height <= 0:
            raise ValueError("height must be positive")

        scene = cls(camera=camera or IsoCamera())
        for y in range(height):
            for x in range(width):
                scene.add_tile(Tile(x=x, y=y, sprite=default_sprite))
        return scene

    def add_tile(self, tile: Tile) -> None:
        self.sprites.get(tile.sprite)
        self.tiles.append(tile)

    def set_tile(self, tile: Tile) -> None:
        """Add or replace a tile at the same grid position."""

        self.sprites.get(tile.sprite)
        self.tiles = [
            existing
            for existing in self.tiles
            if (existing.x, existing.y, existing.z) != (tile.x, tile.y, tile.z)
        ]
        self.tiles.append(tile)

    def add_tiles(self, tiles: Iterable[Tile]) -> None:
        for tile in tiles:
            self.add_tile(tile)

    def add_entity(self, entity: Entity) -> None:
        self.sprites.get(entity.sprite)
        self.entities.append(entity)

    def get_entity(self, entity_id: str) -> Entity:
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        raise KeyError(f"Unknown entity '{entity_id}'")

    def move_entity(self, entity_id: str, x: float, y: float, z: float = 0.0) -> None:
        """Move an entity while preserving its other metadata."""

        for index, entity in enumerate(self.entities):
            if entity.entity_id == entity_id:
                self.entities[index] = Entity(
                    entity_id=entity.entity_id,
                    x=x,
                    y=y,
                    z=z,
                    sprite=entity.sprite,
                    layer=entity.layer,
                )
                return
        raise KeyError(f"Unknown entity '{entity_id}'")

    def build_draw_commands(self) -> list[DrawCommand]:
        """Build renderer-neutral draw commands in safe isometric order."""

        commands: list[DrawCommand] = []

        for tile in self.tiles:
            screen = self.camera.grid_to_screen(tile.x, tile.y, tile.z)
            commands.append(
                DrawCommand(
                    sort_key=self.camera.draw_sort_key(tile.x, tile.y, tile.z, layer=0),
                    screen=screen,
                    sprite=self.sprites.get(tile.sprite),
                    kind="tile",
                    object_id=f"tile:{tile.x}:{tile.y}:{tile.z}",
                    grid_position=(tile.x, tile.y, tile.z),
                )
            )

        for entity in self.entities:
            screen = self.camera.grid_to_screen(entity.x, entity.y, entity.z)
            commands.append(
                DrawCommand(
                    sort_key=self.camera.draw_sort_key(
                        entity.x,
                        entity.y,
                        entity.z,
                        layer=entity.layer,
                    ),
                    screen=screen,
                    sprite=self.sprites.get(entity.sprite),
                    kind="entity",
                    object_id=entity.entity_id,
                    grid_position=(entity.x, entity.y, entity.z),
                )
            )

        return sorted(commands, key=lambda command: command.sort_key)

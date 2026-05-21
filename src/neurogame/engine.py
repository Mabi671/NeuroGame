"""Scene graph and draw command generation for isometric games."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from neurogame.iso import IsoCamera, ScreenPoint
from neurogame.pathfinding import find_path_on_grid
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

    def move_entity(self, entity_id: str, x: float, y: float, z: float | None = None) -> None:
        """Move an entity while preserving its other metadata.

        When ``z`` is omitted, the entity keeps its current elevation so floating
        units keep their height above the floor during horizontal motion.
        """

        for index, entity in enumerate(self.entities):
            if entity.entity_id == entity_id:
                new_z = entity.z if z is None else z
                self.entities[index] = Entity(
                    entity_id=entity.entity_id,
                    x=x,
                    y=y,
                    z=new_z,
                    sprite=entity.sprite,
                    layer=entity.layer,
                )
                return
        raise KeyError(f"Unknown entity '{entity_id}'")

    def floor_grid_bounds(self) -> tuple[int, int, int, int] | None:
        """Return ``(min_x, max_x, min_y, max_y)`` for ground tiles at ``z == 0``."""

        ground = [tile for tile in self.tiles if tile.z == 0]
        if not ground:
            return None
        xs = [tile.x for tile in ground]
        ys = [tile.y for tile in ground]
        return min(xs), max(xs), min(ys), max(ys)

    def blocked_cells_for_pathfinding(self, *, moving_entity_id: str | None = None) -> set[tuple[int, int]]:
        """Collect grid cells that pathfinding should not enter."""

        blocked: set[tuple[int, int]] = set()

        for tile in self.tiles:
            if tile.z != 0:
                continue
            if self.sprites.get(tile.sprite).blocks_pathfinding:
                blocked.add((tile.x, tile.y))

        for entity in self.entities:
            if moving_entity_id is not None and entity.entity_id == moving_entity_id:
                continue
            if not self.sprites.get(entity.sprite).blocks_pathfinding:
                continue
            cell = (int(round(entity.x)), int(round(entity.y)))
            blocked.add(cell)

        return blocked

    def pathfind_entity_to_cell(
        self,
        entity_id: str,
        goal_x: int,
        goal_y: int,
    ) -> list[tuple[int, int]] | None:
        """Plan a 4-connected grid path for ``entity_id`` to ``(goal_x, goal_y)``."""

        bounds = self.floor_grid_bounds()
        if bounds is None:
            return None

        min_x, max_x, min_y, max_y = bounds
        entity = self._entity_by_id(entity_id)
        start = (int(round(entity.x)), int(round(entity.y)))
        goal = (goal_x, goal_y)
        blocked = self.blocked_cells_for_pathfinding(moving_entity_id=entity_id)

        return find_path_on_grid(start, goal, min_x, max_x, min_y, max_y, blocked)

    def _entity_by_id(self, entity_id: str) -> Entity:
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
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

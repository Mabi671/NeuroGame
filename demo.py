"""Run a small isometric scene using placeholder sprites.

Click the map to move the cyan player spirit (gold ring); paths avoid water,
blue tiles, boulders, and every other spirit's cell. Ten wandering spirits pick
random goals with the same rules. Spirits use a high draw layer above tiles.
"""

from __future__ import annotations

import random

from neurogame import Entity, IsoCamera, IsometricScene, Tile
from neurogame.tk_renderer import TkinterRenderer

MAP_WIDTH = 18
MAP_HEIGHT = 18
SPIRIT_DRAW_LAYER = 120
WANDERING_SPIRIT_COUNT = 10
WANDERING_SPIRIT_SPRITES = (
    "spirit_placeholder",
    "spirit_forest_placeholder",
    "spirit_fire_placeholder",
)


def build_demo_scene() -> tuple[IsometricScene, tuple[str, ...]]:
    camera = IsoCamera(tile_width=72, tile_height=36, origin_x=640, origin_y=96)
    scene = IsometricScene.flat_map(MAP_WIDTH, MAP_HEIGHT, camera=camera)

    water_tiles = [
        Tile(x=0, y=12, sprite="tile_water"),
        Tile(x=1, y=12, sprite="tile_water"),
        Tile(x=2, y=12, sprite="tile_water"),
        Tile(x=0, y=13, sprite="tile_water"),
        Tile(x=1, y=13, sprite="tile_water"),
        Tile(x=2, y=13, sprite="tile_water"),
        Tile(x=3, y=13, sprite="tile_water"),
        Tile(x=0, y=14, sprite="tile_water"),
        Tile(x=1, y=14, sprite="tile_water"),
        Tile(x=2, y=14, sprite="tile_water"),
        Tile(x=1, y=15, sprite="tile_water"),
        Tile(x=2, y=15, sprite="tile_water"),
        Tile(x=3, y=15, sprite="tile_water"),
        Tile(x=2, y=16, sprite="tile_water"),
        Tile(x=3, y=16, sprite="tile_water"),
    ]
    stone_path = [
        Tile(x=6, y=6, sprite="tile_stone"),
        Tile(x=8, y=6, sprite="tile_stone"),
        Tile(x=8, y=8, sprite="tile_stone"),
        Tile(x=10, y=8, sprite="tile_stone"),
        Tile(x=10, y=10, sprite="tile_stone"),
    ]

    reserved_blue: set[tuple[int, int]] = {(tile.x, tile.y) for tile in water_tiles + stone_path}

    for tile in water_tiles + stone_path:
        scene.set_tile(tile)

    rng = random.Random()
    candidates = [
        (x, y)
        for x in range(MAP_WIDTH)
        for y in range(MAP_HEIGHT)
        if (x, y) not in reserved_blue
    ]
    blue_count = min(52, len(candidates))
    for x, y in rng.sample(candidates, blue_count):
        scene.set_tile(Tile(x=x, y=y, sprite="tile_blue_patch"))

    scene.add_entity(Entity(entity_id="player", x=9, y=9, sprite="player_placeholder"))
    scene.add_entity(Entity(entity_id="villager", x=12, y=6, sprite="npc_placeholder"))
    scene.add_entity(Entity(entity_id="boulder-a", x=8, y=4, sprite="prop_boulder"))
    scene.add_entity(Entity(entity_id="boulder-b", x=10, y=4, sprite="prop_boulder"))
    scene.add_entity(
        Entity(
            entity_id="spirit-mover",
            x=7.0,
            y=9.0,
            z=0.2,
            sprite="spirit_placeholder",
            layer=SPIRIT_DRAW_LAYER,
        )
    )

    static_blocked = scene.blocked_cells_for_pathfinding()
    reserved_spawn = {
        (9, 9),
        (12, 6),
        (8, 4),
        (10, 4),
        (7, 9),
    }
    walkable_spawns = [
        (x, y)
        for x in range(MAP_WIDTH)
        for y in range(MAP_HEIGHT)
        if (x, y) not in static_blocked and (x, y) not in reserved_spawn
    ]
    if len(walkable_spawns) < WANDERING_SPIRIT_COUNT:
        walkable_spawns = [
            (x, y)
            for x in range(MAP_WIDTH)
            for y in range(MAP_HEIGHT)
            if (x, y) not in static_blocked
        ]
    spawn_count = min(WANDERING_SPIRIT_COUNT, len(walkable_spawns))
    spawn_points = rng.sample(walkable_spawns, k=spawn_count)
    for index, (sx, sy) in enumerate(spawn_points):
        sprite = WANDERING_SPIRIT_SPRITES[index % len(WANDERING_SPIRIT_SPRITES)]
        scene.add_entity(
            Entity(
                entity_id=f"wandering-spirit-{index}",
                x=float(sx),
                y=float(sy),
                z=0.25,
                sprite=sprite,
                layer=SPIRIT_DRAW_LAYER,
            )
        )
    wandering_ids = tuple(f"wandering-spirit-{index}" for index in range(spawn_count))
    return scene, wandering_ids


if __name__ == "__main__":
    demo_scene, autonomous_ids = build_demo_scene()
    TkinterRenderer(demo_scene, width=1280, height=820).run(
        pathfinding_entity_id="spirit-mover",
        path_steps_per_grid_edge=16,
        path_micro_step_ms=10,
        autonomous_spirit_ids=autonomous_ids,
        autonomous_spirit_tick_ms=10,
    )

"""Run a small isometric scene using placeholder sprites.

Click the map to move the cyan player spirit (gold ring); paths avoid water,
blue tiles, boulders, and every other spirit's cell. Red tiles are walkable but
drain half of a spirit's max HP when stepped on; at 0 HP a spirit is removed.
Ten slower wandering spirits pick random goals. Each spirit shows a health bar.

Use the window menu: **Mode → Paint tiles** and **Brush** to pick a floor tile,
then click the map to paint. Switch **Mode → Move spirit** to path again.
"""

from __future__ import annotations

import random

from neurogame import Entity, IsoCamera, IsometricScene, Tile
from neurogame.tk_renderer import TkinterRenderer

MAP_WIDTH = 22
MAP_HEIGHT = 22
SPIRIT_DRAW_LAYER = 120
SPIRIT_HP = 100.0
WANDERING_SPIRIT_COUNT = 10
RED_TILE_COUNT = 14
WANDERING_SPIRIT_SPRITES = (
    "spirit_placeholder",
    "spirit_forest_placeholder",
    "spirit_fire_placeholder",
)


def build_demo_scene() -> tuple[IsometricScene, tuple[str, ...]]:
    camera = IsoCamera(tile_width=72, tile_height=36, origin_x=720, origin_y=110)
    scene = IsometricScene.flat_map(MAP_WIDTH, MAP_HEIGHT, camera=camera)

    water_tiles = [
        Tile(x=0, y=17, sprite="tile_water"),
        Tile(x=1, y=17, sprite="tile_water"),
        Tile(x=2, y=17, sprite="tile_water"),
        Tile(x=0, y=18, sprite="tile_water"),
        Tile(x=1, y=18, sprite="tile_water"),
        Tile(x=2, y=18, sprite="tile_water"),
        Tile(x=3, y=18, sprite="tile_water"),
        Tile(x=0, y=19, sprite="tile_water"),
        Tile(x=1, y=19, sprite="tile_water"),
        Tile(x=2, y=19, sprite="tile_water"),
        Tile(x=1, y=20, sprite="tile_water"),
        Tile(x=2, y=20, sprite="tile_water"),
        Tile(x=3, y=20, sprite="tile_water"),
        Tile(x=2, y=21, sprite="tile_water"),
        Tile(x=3, y=21, sprite="tile_water"),
    ]
    stone_path = [
        Tile(x=9, y=9, sprite="tile_stone"),
        Tile(x=11, y=9, sprite="tile_stone"),
        Tile(x=11, y=11, sprite="tile_stone"),
        Tile(x=13, y=11, sprite="tile_stone"),
        Tile(x=13, y=13, sprite="tile_stone"),
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
    blue_count = min(26, len(candidates))
    blue_cells: list[tuple[int, int]] = rng.sample(candidates, blue_count)
    placed_blue = set(blue_cells)
    for x, y in blue_cells:
        scene.set_tile(Tile(x=x, y=y, sprite="tile_blue_patch"))

    red_candidates = [
        (x, y)
        for x in range(MAP_WIDTH)
        for y in range(MAP_HEIGHT)
        if (x, y) not in reserved_blue and (x, y) not in placed_blue
    ]
    red_count = min(RED_TILE_COUNT, len(red_candidates))
    for x, y in rng.sample(red_candidates, red_count):
        scene.set_tile(Tile(x=x, y=y, sprite="tile_red_drain"))

    scene.add_entity(Entity(entity_id="player", x=11, y=11, sprite="player_placeholder"))
    scene.add_entity(Entity(entity_id="villager", x=17, y=9, sprite="npc_placeholder"))
    scene.add_entity(Entity(entity_id="boulder-a", x=11, y=6, sprite="prop_boulder"))
    scene.add_entity(Entity(entity_id="boulder-b", x=14, y=6, sprite="prop_boulder"))
    scene.add_entity(
        Entity(
            entity_id="spirit-mover",
            x=8.0,
            y=12.0,
            z=0.2,
            sprite="spirit_placeholder",
            layer=SPIRIT_DRAW_LAYER,
            health=SPIRIT_HP,
            max_health=SPIRIT_HP,
        )
    )

    static_blocked = scene.blocked_cells_for_pathfinding()
    reserved_spawn = {
        (11, 11),
        (17, 9),
        (11, 6),
        (14, 6),
        (8, 12),
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
                health=SPIRIT_HP,
                max_health=SPIRIT_HP,
            )
        )
    wandering_ids = tuple(f"wandering-spirit-{index}" for index in range(spawn_count))
    return scene, wandering_ids


if __name__ == "__main__":
    demo_scene, autonomous_ids = build_demo_scene()
    TkinterRenderer(demo_scene, width=1380, height=880).run(
        pathfinding_entity_id="spirit-mover",
        path_steps_per_grid_edge=16,
        path_micro_step_ms=10,
        autonomous_spirit_ids=autonomous_ids,
        autonomous_spirit_tick_ms=32,
    )

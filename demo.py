"""Run a small isometric scene using placeholder sprites.

The floor is **all grass** until you use the in-window **Painting** panel
(**Paint tiles** mode and a row in the brush table) to place water, stone, blue,
or red hazard tiles by **clicking or click-dragging** on the map. Click the map to move the cyan
player spirit (gold ring); paths avoid blocking tiles, boulders, and other
spirits. Red hazard tiles drain half max HP when entered; at 0 HP a spirit is
removed. Ten slower wandering spirits roam with health bars.
"""

from __future__ import annotations

import random

from neurogame import Entity, IsoCamera, IsometricScene
from neurogame.tk_renderer import TkinterRenderer

MAP_WIDTH = 22
MAP_HEIGHT = 22
SPIRIT_DRAW_LAYER = 120
SPIRIT_HP = 100.0
WANDERING_SPIRIT_COUNT = 10
WANDERING_SPIRIT_SPRITES = (
    "spirit_placeholder",
    "spirit_forest_placeholder",
    "spirit_fire_placeholder",
)


def build_demo_scene() -> tuple[IsometricScene, tuple[str, ...]]:
    camera = IsoCamera(tile_width=72, tile_height=36, origin_x=720, origin_y=110)
    scene = IsometricScene.flat_map(MAP_WIDTH, MAP_HEIGHT, camera=camera)

    rng = random.Random()

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

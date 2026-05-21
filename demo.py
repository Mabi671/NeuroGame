"""Run a small isometric scene using placeholder sprites.

Click the map to move the cyan spirit; paths avoid water, blue tiles, boulders,
and the orange obstacle spirit. The demo uses an 18x18 floor with random blue
tiles and smooth interpolated movement along each planned path segment.
"""

from __future__ import annotations

import random

from neurogame import Entity, IsoCamera, IsometricScene, Tile
from neurogame.tk_renderer import TkinterRenderer

MAP_WIDTH = 18
MAP_HEIGHT = 18


def build_demo_scene() -> IsometricScene:
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
        Entity(entity_id="spirit-mover", x=7.0, y=9.0, z=0.2, sprite="spirit_placeholder")
    )
    scene.add_entity(
        Entity(
            entity_id="spirit-obstacle",
            x=11.0,
            y=7.0,
            z=0.2,
            sprite="spirit_fire_placeholder",
        )
    )
    return scene


if __name__ == "__main__":
    TkinterRenderer(build_demo_scene(), width=1280, height=820).run(
        pathfinding_entity_id="spirit-mover",
        path_steps_per_grid_edge=16,
        path_micro_step_ms=10,
    )

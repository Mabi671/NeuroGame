"""Run a small isometric scene using placeholder sprites.

Click the map to move the player; paths avoid water tiles and boulder props.
"""

from neurogame import Entity, IsoCamera, IsometricScene, Tile
from neurogame.tk_renderer import TkinterRenderer


def build_demo_scene() -> IsometricScene:
    camera = IsoCamera(tile_width=72, tile_height=36, origin_x=480, origin_y=90)
    scene = IsometricScene.flat_map(9, 9, camera=camera)

    water_tiles = [
        Tile(x=0, y=6, sprite="tile_water"),
        Tile(x=1, y=6, sprite="tile_water"),
        Tile(x=0, y=7, sprite="tile_water"),
        Tile(x=1, y=7, sprite="tile_water"),
        Tile(x=2, y=7, sprite="tile_water"),
        Tile(x=1, y=8, sprite="tile_water"),
    ]
    stone_path = [
        Tile(x=3, y=3, sprite="tile_stone"),
        Tile(x=4, y=3, sprite="tile_stone"),
        Tile(x=4, y=4, sprite="tile_stone"),
        Tile(x=5, y=4, sprite="tile_stone"),
    ]

    for tile in water_tiles + stone_path:
        scene.set_tile(tile)
    scene.add_entity(Entity(entity_id="player", x=4, y=4, sprite="player_placeholder"))
    scene.add_entity(Entity(entity_id="villager", x=6, y=3, sprite="npc_placeholder"))
    scene.add_entity(Entity(entity_id="boulder-a", x=4, y=2, sprite="prop_boulder"))
    scene.add_entity(Entity(entity_id="boulder-b", x=5, y=2, sprite="prop_boulder"))
    scene.add_entity(
        Entity(entity_id="spirit-air", x=3.4, y=5.2, z=0.2, sprite="spirit_placeholder")
    )
    scene.add_entity(
        Entity(
            entity_id="spirit-fire",
            x=5.7,
            y=5.5,
            z=0.2,
            sprite="spirit_fire_placeholder",
        )
    )
    scene.add_entity(
        Entity(
            entity_id="spirit-forest",
            x=2.5,
            y=2.5,
            z=0.2,
            sprite="spirit_forest_placeholder",
        )
    )
    return scene


if __name__ == "__main__":
    TkinterRenderer(build_demo_scene()).run()

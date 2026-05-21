import unittest

from neurogame import Entity, IsoCamera, IsometricScene, Tile


class IsometricSceneTests(unittest.TestCase):
    def test_flat_map_creates_expected_tiles(self) -> None:
        scene = IsometricScene.flat_map(3, 2)

        self.assertEqual(len(scene.tiles), 6)
        self.assertEqual(scene.tiles[0], Tile(x=0, y=0, sprite="tile_grass"))
        self.assertEqual(scene.tiles[-1], Tile(x=2, y=1, sprite="tile_grass"))

    def test_set_tile_replaces_existing_tile_at_position(self) -> None:
        scene = IsometricScene.flat_map(2, 2)

        scene.set_tile(Tile(x=1, y=1, sprite="tile_water"))

        matching = [tile for tile in scene.tiles if (tile.x, tile.y, tile.z) == (1, 1, 0)]
        self.assertEqual(matching, [Tile(x=1, y=1, sprite="tile_water")])

    def test_draw_commands_include_entities_after_same_position_tile(self) -> None:
        scene = IsometricScene.flat_map(
            1,
            1,
            camera=IsoCamera(tile_width=64, tile_height=32, origin_x=10, origin_y=20),
        )
        scene.add_entity(Entity(entity_id="hero", x=0, y=0, sprite="player_placeholder"))

        commands = scene.build_draw_commands()

        self.assertEqual([command.kind for command in commands], ["tile", "entity"])
        self.assertEqual(commands[1].object_id, "hero")
        self.assertEqual(commands[1].screen.x, 10)
        self.assertEqual(commands[1].screen.y, 20)
        self.assertIsNone(commands[1].health)
        self.assertIsNone(commands[1].max_health)

    def test_unknown_sprites_are_rejected_when_added(self) -> None:
        scene = IsometricScene()

        with self.assertRaises(KeyError):
            scene.add_entity(Entity(entity_id="bad", x=0, y=0, sprite="missing"))


if __name__ == "__main__":
    unittest.main()

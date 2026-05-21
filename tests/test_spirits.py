import unittest

from neurogame import AirSpirit, IsoCamera, IsometricScene, Tile


class AirSpiritTests(unittest.TestCase):
    def test_select_at_screen_hits_spirit_placeholder(self) -> None:
        scene = IsometricScene.flat_map(
            3,
            3,
            camera=IsoCamera(tile_width=64, tile_height=32, origin_x=100, origin_y=40),
        )
        spirit = AirSpirit.spawn(scene, x=1, y=1)
        screen = scene.camera.grid_to_screen(1, 1, 0.2)

        self.assertTrue(spirit.select_at_screen(screen.x, screen.y - 20))
        self.assertTrue(spirit.selected)

    def test_travel_to_uses_pathfinding_and_step_moves_entity(self) -> None:
        scene = IsometricScene.flat_map(4, 3)
        scene.set_tile(Tile(x=1, y=0, sprite="tile_water"))
        spirit = AirSpirit.spawn(scene, x=0, y=0)
        spirit.selected = True

        path = spirit.travel_to((3, 0))

        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (3, 0))
        self.assertNotIn((1, 0), path)

        self.assertTrue(spirit.step_along_path())
        moved = scene.get_entity("spirit-air")
        self.assertEqual((moved.x, moved.y), path[1])

    def test_unselected_spirit_does_not_plan_route(self) -> None:
        scene = IsometricScene.flat_map(2, 1)
        spirit = AirSpirit.spawn(scene, x=0, y=0)

        self.assertEqual(spirit.travel_to((1, 0)), [])
        self.assertEqual(spirit.path, [])


if __name__ == "__main__":
    unittest.main()

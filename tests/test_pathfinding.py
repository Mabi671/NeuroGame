import unittest

from neurogame import IsometricScene, Tile
from neurogame.pathfinding import GridPathfinder


class GridPathfinderTests(unittest.TestCase):
    def test_finds_path_around_blocked_water_tiles(self) -> None:
        scene = IsometricScene.flat_map(4, 3)
        scene.set_tile(Tile(x=1, y=0, sprite="tile_water"))
        scene.set_tile(Tile(x=1, y=1, sprite="tile_water"))

        pathfinder = GridPathfinder.from_scene(scene)
        path = pathfinder.find_path((0, 0), (3, 0))

        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (3, 0))
        self.assertNotIn((1, 0), path)
        self.assertNotIn((1, 1), path)

    def test_returns_empty_path_for_blocked_destination(self) -> None:
        scene = IsometricScene.flat_map(2, 1)
        scene.set_tile(Tile(x=1, y=0, sprite="tile_water"))

        pathfinder = GridPathfinder.from_scene(scene)

        self.assertEqual(pathfinder.find_path((0, 0), (1, 0)), [])


if __name__ == "__main__":
    unittest.main()

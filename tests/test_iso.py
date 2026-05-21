import unittest

from neurogame.iso import IsoCamera


class IsoCameraTests(unittest.TestCase):
    def test_grid_to_screen_uses_isometric_projection(self) -> None:
        camera = IsoCamera(tile_width=32, tile_height=16, origin_x=100, origin_y=50)

        origin = camera.grid_to_screen(0, 0)
        east = camera.grid_to_screen(1, 0)
        south = camera.grid_to_screen(0, 1)

        self.assertEqual((origin.x, origin.y), (100, 50))
        self.assertEqual((east.x, east.y), (116, 58))
        self.assertEqual((south.x, south.y), (84, 58))

    def test_screen_to_grid_round_trips_on_same_elevation(self) -> None:
        camera = IsoCamera(tile_width=40, tile_height=20, origin_x=320, origin_y=120)

        for point in [(0, 0, 0), (3, 4, 0), (2.5, 1.25, 0), (5, 2, 1)]:
            with self.subTest(point=point):
                screen = camera.grid_to_screen(*point)
                grid = camera.screen_to_grid(screen.x, screen.y, z=point[2])
                self.assertAlmostEqual(grid.x, point[0])
                self.assertAlmostEqual(grid.y, point[1])
                self.assertAlmostEqual(grid.z, point[2])

    def test_invalid_camera_sizes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IsoCamera(tile_width=0)
        with self.assertRaises(ValueError):
            IsoCamera(tile_height=0)
        with self.assertRaises(ValueError):
            IsoCamera(elevation_height=0)


if __name__ == "__main__":
    unittest.main()

import unittest

from neurogame import Entity, IsometricScene, Tile
from neurogame.pathfinding import find_path_on_grid


class FindPathOnGridTests(unittest.TestCase):
    def test_straight_line_when_unblocked(self) -> None:
        blocked: set[tuple[int, int]] = set()
        path = find_path_on_grid((0, 0), (2, 0), 0, 3, 0, 3, blocked)

        self.assertEqual(path, [(0, 0), (1, 0), (2, 0)])

    def test_returns_none_when_goal_blocked(self) -> None:
        blocked = {(2, 2)}
        path = find_path_on_grid((0, 0), (2, 2), 0, 3, 0, 3, blocked)

        self.assertIsNone(path)

    def test_routes_around_obstacle(self) -> None:
        blocked = {(1, 0)}
        path = find_path_on_grid((0, 0), (2, 0), 0, 2, 0, 1, blocked)

        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 0))
        self.assertNotIn((1, 0), path)

    def test_allows_leaving_start_even_if_start_cell_is_blocked(self) -> None:
        """Start is treated as walkable so entities can escape misconfigured tiles."""

        blocked = {(0, 0), (1, 0)}
        path = find_path_on_grid((0, 0), (0, 1), 0, 1, 0, 1, blocked)

        self.assertEqual(path, [(0, 0), (0, 1)])


class ScenePathfindingTests(unittest.TestCase):
    def test_water_tile_blocks_pathfinding_cell(self) -> None:
        scene = IsometricScene.flat_map(3, 3)
        scene.set_tile(Tile(x=1, y=1, sprite="tile_water"))

        blocked = scene.blocked_cells_for_pathfinding()

        self.assertIn((1, 1), blocked)

    def test_path_routes_around_water_and_boulder_sprites(self) -> None:
        scene = IsometricScene.flat_map(5, 3)
        scene.set_tile(Tile(x=2, y=1, sprite="tile_water"))
        scene.add_entity(Entity(entity_id="rock", x=1, y=1, sprite="prop_boulder"))
        scene.add_entity(Entity(entity_id="player", x=0, y=1, sprite="player_placeholder"))

        path = scene.pathfind_entity_to_cell("player", 3, 1)

        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path[0], (0, 1))
        self.assertEqual(path[-1], (3, 1))
        self.assertNotIn((2, 1), path)
        self.assertNotIn((1, 1), path)

    def test_moving_entity_is_not_blocked_by_own_sprite(self) -> None:
        scene = IsometricScene.flat_map(2, 1)
        scene.add_entity(
            Entity(entity_id="walker", x=0, y=0, sprite="prop_boulder"),
        )

        blocked = scene.blocked_cells_for_pathfinding(moving_entity_id="walker")

        self.assertNotIn((0, 0), blocked)


if __name__ == "__main__":
    unittest.main()

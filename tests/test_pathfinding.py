import unittest

from neurogame import Entity, IsometricScene, Tile
from neurogame.pathfinding import find_path_on_grid
from neurogame.tk_renderer import _motion_points_along_grid_path, _queued_step_targets_blocked_cell


class MotionAlongPathTests(unittest.TestCase):
    def test_lead_in_from_current_float_before_grid_edges(self) -> None:
        path = [(0, 0), (1, 0)]
        pts = _motion_points_along_grid_path(
            path,
            steps_per_edge=4,
            origin_x=0.25,
            origin_y=0.0,
        )

        # Short lead (0.25 grid units) uses one micro-step to (0,0), then four along the edge.
        self.assertEqual(len(pts), 5)
        self.assertAlmostEqual(pts[0][0], 0.0)
        self.assertAlmostEqual(pts[0][1], 0.0)
        self.assertAlmostEqual(pts[-1][0], 1.0)
        self.assertAlmostEqual(pts[-1][1], 0.0)

    def test_long_lead_in_uses_full_subdivision_count(self) -> None:
        path = [(0, 0), (1, 0)]
        pts = _motion_points_along_grid_path(
            path,
            steps_per_edge=4,
            origin_x=-1.0,
            origin_y=0.0,
        )

        self.assertEqual(len(pts), 8)
        self.assertAlmostEqual(pts[0][0], -0.75)
        self.assertAlmostEqual(pts[0][1], 0.0)
        self.assertAlmostEqual(pts[3][0], 0.0)
        self.assertAlmostEqual(pts[3][1], 0.0)


class QueuedStepBlockedTests(unittest.TestCase):
    def test_next_position_uses_current_blocked_set(self) -> None:
        scene = IsometricScene.flat_map(3, 3)
        scene.set_tile(Tile(x=2, y=1, sprite="tile_water"))
        scene.add_entity(Entity(entity_id="m", x=1, y=1, sprite="spirit_placeholder"))

        self.assertFalse(_queued_step_targets_blocked_cell(scene, "m", 1.0, 1.0))
        self.assertTrue(_queued_step_targets_blocked_cell(scene, "m", 2.0, 1.0))


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
    def test_pathfind_returns_none_for_missing_entity(self) -> None:
        scene = IsometricScene.flat_map(2, 2)

        path = scene.pathfind_entity_to_cell("nobody", 0, 0)

        self.assertIsNone(path)

    def test_red_drain_tile_does_not_block_pathfinding(self) -> None:
        scene = IsometricScene.flat_map(2, 2)
        scene.set_tile(Tile(x=0, y=0, sprite="tile_red_drain"))

        blocked = scene.blocked_cells_for_pathfinding()

        self.assertNotIn((0, 0), blocked)

    def test_red_tile_drains_half_max_on_new_cell_entry(self) -> None:
        scene = IsometricScene.flat_map(2, 2)
        scene.set_tile(Tile(x=1, y=0, sprite="tile_red_drain"))
        scene.add_entity(
            Entity(
                entity_id="s",
                x=0.0,
                y=0.0,
                sprite="spirit_placeholder",
                health=100.0,
                max_health=100.0,
            ),
        )
        scene.move_entity("s", 1.0, 0.0)
        scene.apply_spirit_tile_hazards_after_move("s")

        entity = next(entity for entity in scene.entities if entity.entity_id == "s")
        self.assertEqual(entity.health, 50.0)

    def test_red_tile_second_visit_drains_to_zero_and_removes_spirit(self) -> None:
        scene = IsometricScene.flat_map(2, 2)
        scene.set_tile(Tile(x=1, y=0, sprite="tile_red_drain"))
        scene.add_entity(
            Entity(
                entity_id="s",
                x=0.0,
                y=0.0,
                sprite="spirit_placeholder",
                health=100.0,
                max_health=100.0,
            ),
        )
        scene.move_entity("s", 1.0, 0.0)
        scene.apply_spirit_tile_hazards_after_move("s")
        scene.move_entity("s", 0.0, 0.0)
        scene.apply_spirit_tile_hazards_after_move("s")
        scene.move_entity("s", 1.0, 0.0)
        scene.apply_spirit_tile_hazards_after_move("s")

        self.assertFalse(scene.has_entity("s"))

    def test_water_tile_blocks_pathfinding_cell(self) -> None:
        scene = IsometricScene.flat_map(3, 3)
        scene.set_tile(Tile(x=1, y=1, sprite="tile_water"))

        blocked = scene.blocked_cells_for_pathfinding()

        self.assertIn((1, 1), blocked)

    def test_blue_tile_blocks_pathfinding_cell(self) -> None:
        scene = IsometricScene.flat_map(2, 2)
        scene.set_tile(Tile(x=0, y=0, sprite="tile_blue_patch"))

        blocked = scene.blocked_cells_for_pathfinding()

        self.assertIn((0, 0), blocked)

    def test_spirit_placeholder_blocks_pathfinding_cell(self) -> None:
        scene = IsometricScene.flat_map(3, 3)
        scene.add_entity(
            Entity(entity_id="s", x=1, y=1, sprite="spirit_placeholder"),
        )

        blocked = scene.blocked_cells_for_pathfinding()

        self.assertIn((1, 1), blocked)

    def test_other_spirit_blocks_path_for_moving_spirit(self) -> None:
        scene = IsometricScene.flat_map(3, 3)
        scene.add_entity(Entity(entity_id="mover", x=0, y=1, sprite="spirit_placeholder"))
        scene.add_entity(
            Entity(entity_id="other", x=1, y=1, sprite="spirit_forest_placeholder"),
        )

        path = scene.pathfind_entity_to_cell("mover", 2, 1)

        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path[0], (0, 1))
        self.assertEqual(path[-1], (2, 1))
        self.assertNotIn((1, 1), path)

    def test_moving_spirit_is_not_blocked_by_own_cell(self) -> None:
        scene = IsometricScene.flat_map(2, 1)
        scene.add_entity(Entity(entity_id="m", x=0, y=0, sprite="spirit_placeholder"))

        blocked = scene.blocked_cells_for_pathfinding(moving_entity_id="m")

        self.assertNotIn((0, 0), blocked)

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

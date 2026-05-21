"""Projectile spawn, flight, and spirit damage."""

from __future__ import annotations

import unittest

from neurogame import Entity, IsometricScene


class ProjectileCombatTests(unittest.TestCase):
    def test_projectile_deals_twenty_damage_to_npc_spirit(self) -> None:
        scene = IsometricScene.flat_map(10, 10)
        scene.add_entity(
            Entity(
                entity_id="hero",
                x=1.0,
                y=1.0,
                z=0.2,
                sprite="spirit_placeholder",
                layer=50,
                health=100.0,
                max_health=100.0,
            )
        )
        scene.add_entity(
            Entity(
                entity_id="npc",
                x=4.0,
                y=1.0,
                z=0.2,
                sprite="spirit_fire_placeholder",
                layer=50,
                health=100.0,
                max_health=100.0,
            )
        )
        aim = scene.camera.grid_to_screen(9.0, 1.0, 0.2)
        self.assertTrue(scene.spawn_projectile_toward_screen("hero", aim.x, aim.y))
        for _ in range(200):
            scene.advance_projectiles(damage=20.0)
        npc = next(e for e in scene.entities if e.entity_id == "npc")
        self.assertEqual(npc.health, 80.0)

    def test_projectile_removes_spirit_at_zero_health(self) -> None:
        scene = IsometricScene.flat_map(10, 10)
        scene.add_entity(
            Entity(
                entity_id="hero",
                x=1.0,
                y=1.0,
                z=0.2,
                sprite="spirit_placeholder",
                layer=50,
                health=100.0,
                max_health=100.0,
            )
        )
        scene.add_entity(
            Entity(
                entity_id="fragile",
                x=3.5,
                y=1.0,
                z=0.2,
                sprite="spirit_forest_placeholder",
                layer=50,
                health=15.0,
                max_health=100.0,
            )
        )
        aim = scene.camera.grid_to_screen(8.0, 1.0, 0.2)
        self.assertTrue(scene.spawn_projectile_toward_screen("hero", aim.x, aim.y))
        for _ in range(200):
            scene.advance_projectiles(damage=20.0)
        self.assertFalse(scene.has_entity("fragile"))

    def test_spawn_fails_when_aim_matches_owner_cell(self) -> None:
        scene = IsometricScene.flat_map(6, 6)
        scene.add_entity(
            Entity(
                entity_id="hero",
                x=2.0,
                y=2.0,
                z=0.2,
                sprite="spirit_placeholder",
                layer=50,
                health=100.0,
                max_health=100.0,
            )
        )
        aim = scene.camera.grid_to_screen(2.0, 2.0, 0.2)
        self.assertFalse(scene.spawn_projectile_toward_screen("hero", aim.x, aim.y))
        self.assertEqual(len(scene.projectiles), 0)


if __name__ == "__main__":
    unittest.main()

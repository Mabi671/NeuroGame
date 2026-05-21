"""Run a small isometric scene using placeholder sprites."""

from neurogame import AirSpirit, Entity, IsoCamera, IsometricScene, Tile
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
    AirSpirit.spawn(scene, entity_id="spirit-air", x=3, y=5)
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


def attach_spirit_controls(renderer: TkinterRenderer, spirit: AirSpirit) -> None:
    animation = {"running": False}

    def redraw() -> None:
        renderer.render()
        spirit.draw_overlay(renderer.canvas)
        renderer.canvas.create_text(
            18,
            18,
            anchor="nw",
            fill="#f8fafc",
            text="Right-click the blue air spirit to select it. Left-click a tile to move.",
        )

    def animate_step() -> None:
        if spirit.step_along_path():
            redraw()
            renderer.root.after(140, animate_step)
            return
        animation["running"] = False
        redraw()

    def begin_animation() -> None:
        if animation["running"]:
            return
        animation["running"] = True
        animate_step()

    def on_right_click(event: object) -> None:
        if not spirit.select_at_screen(event.x, event.y):
            spirit.clear_selection()
        redraw()

    def on_left_click(event: object) -> None:
        if not spirit.selected:
            return
        path = spirit.travel_to_screen(event.x, event.y)
        redraw()
        if path:
            begin_animation()

    renderer.canvas.bind("<Button-3>", on_right_click)
    renderer.canvas.bind("<Button-1>", on_left_click)
    redraw()


if __name__ == "__main__":
    demo_scene = build_demo_scene()
    air_spirit = AirSpirit(scene=demo_scene, entity_id="spirit-air")
    demo_renderer = TkinterRenderer(demo_scene)
    attach_spirit_controls(demo_renderer, air_spirit)
    demo_renderer.root.mainloop()

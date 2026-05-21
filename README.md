# NeuroGame

A Python game prototype with a small isometric graphics engine foundation.

## What is included

- Isometric camera projection from grid coordinates to screen coordinates.
- A scene graph for tiles and entities.
- Renderer-neutral draw commands with isometric draw ordering.
- A* pathfinding over the tile grid for click-to-move actors.
- A Tkinter demo renderer that uses only the Python standard library.
- Placeholder sprite definitions, including spirit placeholders you can replace
  with final art later.

## Run the demo

```bash
PYTHONPATH=src python3 demo.py
```

The demo opens a Tkinter window with an isometric map, character placeholders,
and three spirit placeholders. Right-click the blue air spirit to select it, then
left-click a destination tile to pathfind and move there. Water tiles are blocked.

## Engine quick start

```python
from neurogame import Entity, IsoCamera, IsometricScene

camera = IsoCamera(tile_width=64, tile_height=32, origin_x=400, origin_y=80)
scene = IsometricScene.flat_map(8, 8, camera=camera)
scene.add_entity(Entity(entity_id="spirit", x=3, y=4, sprite="spirit_placeholder"))

draw_commands = scene.build_draw_commands()
```

## Sprite placeholders

Placeholder sprite metadata lives in `src/neurogame/sprites.py`. Editable asset
notes live in `assets/sprites/placeholders/`.

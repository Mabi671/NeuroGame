"""Tkinter renderer for the isometric engine demo.

When ``tile_edit_menu`` is enabled in ``run()``, a styled **Floor palette** panel
sits above the canvas with mode radios and a ``Treeview`` brush table (select a
row, then click or **click-drag** on the map in paint mode).

``player_path_cooldown_s`` (default 0.3) enforces a minimum delay between
accepted player spirit path changes to avoid rapid replanning from click spam.

While following a queued path, each step is checked against the **current**
blocked-cell set so movement stops or replans (NPCs) when obstacles change
mid-route (e.g. painted tiles or other spirits).

**Right-click** the map (with a controllable spirit) to fire a short-range
projectile toward the cursor; other spirits lose 20 HP per hit and are removed
at 0 HP.

New paths are sampled from the entity's **current float** position: a short
lead-in blends into the first path cell before edge interpolation so destination
changes do not snap to grid centers. Lead-in micro-step count scales with how
far the spirit still is from that first cell so mid-route replans stay snappy.
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from tkinter import Canvas, StringVar, Tk, ttk

from neurogame.engine import DrawCommand, IsometricScene, Projectile, Tile
from neurogame.sprites import SpriteDefinition


def _motion_points_along_grid_path(
    path: list[tuple[int, int]],
    *,
    steps_per_edge: int,
    origin_x: float,
    origin_y: float,
) -> list[tuple[float, float]]:
    """Interpolate from the entity's current float position, then along each path edge.

    ``origin_x`` / ``origin_y`` should be the entity's position when the path was
    planned so destination changes blend smoothly from the in-tile offset
    instead of snapping to cell centers.
    """

    if steps_per_edge <= 0:
        raise ValueError("steps_per_edge must be positive")
    if len(path) < 2:
        return []

    points: list[tuple[float, float]] = []
    first_x, first_y = float(path[0][0]), float(path[0][1])
    lead_dist = math.hypot(origin_x - first_x, origin_y - first_y)
    if lead_dist > 1e-10:
        # Use fewer micro-steps when the lead-in is shorter than a full grid edge so
        # replanning mid-tile does not spend ``steps_per_edge`` ticks crawling a
        # fraction of a cell (which felt like a big slowdown vs. along-edge speed).
        lead_steps = max(
            1,
            min(
                steps_per_edge,
                int(round(steps_per_edge * min(lead_dist, 1.0))),
            ),
        )
        for step in range(1, lead_steps + 1):
            t = step / lead_steps
            points.append(
                (
                    origin_x + (first_x - origin_x) * t,
                    origin_y + (first_y - origin_y) * t,
                )
            )

    for index in range(len(path) - 1):
        x0, y0 = float(path[index][0]), float(path[index][1])
        x1, y1 = float(path[index + 1][0]), float(path[index + 1][1])
        for step in range(1, steps_per_edge + 1):
            t = step / steps_per_edge
            points.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return points


def _queued_step_targets_blocked_cell(
    scene: IsometricScene,
    entity_id: str,
    next_x: float,
    next_y: float,
) -> bool:
    """True if the rounded grid cell for ``(next_x, next_y)`` is currently impassable."""

    blocked = scene.blocked_cells_for_pathfinding(moving_entity_id=entity_id)
    return (int(round(next_x)), int(round(next_y))) in blocked


TILE_BRUSH_MENU: tuple[tuple[str, str, str], ...] = (
    ("tile_grass", "Grass", "Walkable"),
    ("tile_water", "Water", "Blocks pathfinding"),
    ("tile_stone", "Stone", "Walkable"),
    ("tile_blue_patch", "Blue patch", "Blocks pathfinding"),
    ("tile_red_drain", "Red hazard", "Walkable; drains spirit HP"),
)


def _apply_paint_panel_styles(root: tk.Misc) -> None:
    """Dark slate + teal accents to match the isometric canvas (#111827)."""

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    panel = "#1a2332"
    inner = "#222b3d"
    text = "#e2e8f0"
    muted = "#94a3b8"
    accent = "#5eead4"
    accent_dark = "#0f766e"
    tree_bg = "#0c1220"
    border = "#334155"

    style.configure("Palette.TFrame", background=panel)
    style.configure(
        "Palette.TLabelframe",
        background=panel,
        foreground=text,
        bordercolor=border,
        borderwidth=1,
        relief="solid",
        darkcolor=border,
        lightcolor=border,
    )
    style.configure(
        "Palette.TLabelframe.Label",
        background=panel,
        foreground=accent,
        font=("", 11, "bold"),
    )
    style.configure(
        "PaletteInner.TLabelframe",
        background=inner,
        foreground=text,
        bordercolor=border,
        borderwidth=1,
        relief="solid",
        darkcolor=border,
        lightcolor=border,
    )
    style.configure(
        "PaletteInner.TLabelframe.Label",
        background=inner,
        foreground=muted,
        font=("", 9, "bold"),
    )
    style.configure(
        "Palette.TRadiobutton",
        background=inner,
        foreground=text,
        focuscolor=accent,
        indicatorrelief="flat",
        borderwidth=0,
    )
    style.map(
        "Palette.TRadiobutton",
        background=[("active", panel), ("selected", inner), ("!selected", inner)],
        indicatorcolor=[("selected", accent), ("!selected", tree_bg)],
    )
    style.configure(
        "Palette.Treeview",
        background=tree_bg,
        fieldbackground=tree_bg,
        foreground=text,
        borderwidth=0,
        rowheight=26,
    )
    style.configure(
        "Palette.Treeview.Heading",
        background=accent_dark,
        foreground=accent,
        relief="flat",
        borderwidth=0,
        font=("", 10, "bold"),
    )
    style.map(
        "Palette.Treeview",
        background=[("selected", accent_dark)],
        foreground=[("selected", "#ecfeff")],
    )
    style.configure(
        "Palette.Vertical.TScrollbar",
        background=panel,
        troughcolor=tree_bg,
        bordercolor=border,
        arrowcolor=muted,
        relief="flat",
        borderwidth=0,
    )
    style.map(
        "Palette.Vertical.TScrollbar",
        background=[("active", inner), ("pressed", accent_dark)],
        arrowcolor=[("active", accent)],
    )
    style.configure("Palette.TSeparator", background=accent_dark)


class TkinterRenderer:
    """Render an isometric scene to a Tkinter canvas."""

    def __init__(
        self,
        scene: IsometricScene,
        *,
        width: int = 480,
        height: int = 320,
        title: str = "NeuroGame Isometric Demo",
        background: str = "#111827",
    ) -> None:
        self.scene = scene
        self._highlight_entity_id: str | None = None
        self._tile_edit_menu = False
        self.root = Tk()
        self.root.title(title)
        self.canvas = Canvas(
            self.root,
            width=width,
            height=height,
            background=background,
            highlightthickness=0,
        )
        self._brush_table: ttk.Treeview | None = None

    def render(self) -> None:
        self.canvas.delete("all")
        commands = self.scene.build_draw_commands()
        for command in commands:
            self._draw_command(command)
        highlight_id = self._highlight_entity_id
        if highlight_id and self.scene.has_entity(highlight_id):
            for command in commands:
                if (
                    command.kind == "entity"
                    and command.object_id == highlight_id
                    and command.sprite.shape == "spirit"
                ):
                    self._draw_spirit_highlight_ring(
                        command.screen.x,
                        command.screen.y,
                        command.sprite,
                    )
                    break

        for projectile in self.scene.projectiles:
            self._draw_projectile(projectile)

    def _draw_projectile(self, projectile: Projectile) -> None:
        z = 0.42
        point = self.scene.camera.grid_to_screen(projectile.x, projectile.y, z)
        radius = 3.0
        self.canvas.create_oval(
            point.x - radius,
            point.y - radius,
            point.x + radius,
            point.y + radius,
            fill="#fcd34d",
            outline="#ea580c",
            width=1,
        )

    def _schedule_projectile_tick(self) -> None:
        self._projectile_after_id = self.root.after(
            self._projectile_tick_ms,
            self._tick_projectiles,
        )

    def _tick_projectiles(self) -> None:
        self._projectile_after_id = None
        self.scene.advance_projectiles(damage=self._projectile_damage)
        self.render()
        self._schedule_projectile_tick()

    def _on_canvas_right_click(self, event: object) -> None:
        entity_id = self._pathfinding_entity_id
        if not entity_id or not self.scene.has_entity(entity_id):
            return
        x = getattr(event, "x", None)
        y = getattr(event, "y", None)
        if x is None or y is None:
            return
        self.scene.spawn_projectile_toward_screen(entity_id, float(x), float(y))
        self.render()

    def run(
        self,
        *,
        pathfinding_entity_id: str | None = "player",
        path_steps_per_grid_edge: int = 14,
        path_micro_step_ms: int = 12,
        autonomous_spirit_ids: tuple[str, ...] = (),
        autonomous_spirit_tick_ms: int | None = None,
        tile_edit_menu: bool = True,
        player_path_cooldown_s: float | None = 0.3,
        projectile_tick_ms: int = 18,
        projectile_damage: float = 20.0,
    ) -> None:
        self._path_motion_queue: list[tuple[float, float]] = []
        self._path_after_id: object | None = None
        self._player_path_cooldown_s = player_path_cooldown_s
        self._last_player_path_change_monotonic: float | None = None
        self._pathfinding_entity_id = pathfinding_entity_id
        self._highlight_entity_id = pathfinding_entity_id
        self._path_steps_per_grid_edge = path_steps_per_grid_edge
        self._path_micro_step_ms = path_micro_step_ms
        self._projectile_tick_ms = projectile_tick_ms
        self._projectile_damage = projectile_damage
        self._projectile_after_id: object | None = None
        self._auto_spirit_id_list = list(autonomous_spirit_ids)
        self._auto_spirit_queues: dict[str, list[tuple[float, float]]] = {
            entity_id: [] for entity_id in self._auto_spirit_id_list
        }
        self._auto_spirit_after_id: object | None = None
        self._auto_spirit_tick_ms = (
            autonomous_spirit_tick_ms
            if autonomous_spirit_tick_ms is not None
            else path_micro_step_ms
        )
        self._tile_edit_menu = tile_edit_menu
        self._paint_drag_last_cell: tuple[int, int] | None = None
        self._input_mode_var = StringVar(master=self.root, value="move")
        self._brush_sprite_var = StringVar(master=self.root, value="tile_grass")
        if tile_edit_menu:
            self.root.configure(background="#111827")
            _apply_paint_panel_styles(self.root)
            shell = ttk.Frame(self.root, style="Palette.TFrame")
            shell.pack(side=tk.TOP, fill=tk.X)
            paint_panel = ttk.LabelFrame(
                shell,
                text="Floor palette — paint mode + drag map; right-click map to shoot other spirits (−20 HP)",
                style="Palette.TLabelframe",
            )
            paint_panel.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 8))
            self._build_tile_paint_panel(paint_panel)
            ttk.Separator(self.root, orient=tk.HORIZONTAL, style="Palette.TSeparator").pack(
                side=tk.TOP,
                fill=tk.X,
                padx=20,
                pady=(0, 6),
            )
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        if pathfinding_entity_id or tile_edit_menu:
            self.canvas.bind("<Button-1>", self._on_canvas_click)
        if pathfinding_entity_id:
            self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        if tile_edit_menu:
            self.canvas.bind("<B1-Motion>", self._on_canvas_paint_b1_motion)
        self.render()
        if self._auto_spirit_id_list:
            self._schedule_autonomous_spirits()
        if pathfinding_entity_id:
            self._schedule_projectile_tick()
        self.root.mainloop()

    def _build_tile_paint_panel(self, parent: ttk.LabelFrame) -> None:
        body = ttk.Frame(parent, style="Palette.TFrame")
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        mode_box = ttk.LabelFrame(body, text="Mode", style="PaletteInner.TLabelframe")
        mode_box.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        ttk.Radiobutton(
            mode_box,
            text="Move spirit",
            style="Palette.TRadiobutton",
            variable=self._input_mode_var,
            value="move",
            command=self.render,
        ).pack(anchor=tk.W, padx=8, pady=4)
        ttk.Radiobutton(
            mode_box,
            text="Paint tiles",
            style="Palette.TRadiobutton",
            variable=self._input_mode_var,
            value="paint",
            command=self.render,
        ).pack(anchor=tk.W, padx=8, pady=4)

        table_box = ttk.LabelFrame(body, text="Brushes", style="PaletteInner.TLabelframe")
        table_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("sprite", "name", "path")
        tree = ttk.Treeview(
            table_box,
            columns=columns,
            show="headings",
            height=len(TILE_BRUSH_MENU),
            selectmode="browse",
            style="Palette.Treeview",
        )
        tree.heading("sprite", text="Sprite id")
        tree.heading("name", text="Name")
        tree.heading("path", text="Path / hazard")
        tree.column("sprite", width=130, stretch=False, minwidth=80)
        tree.column("name", width=120, stretch=False, minwidth=70)
        tree.column("path", width=260, stretch=True, minwidth=120)

        tree.tag_configure("p_even", background="#0c1220")
        tree.tag_configure("p_odd", background="#152032")
        for index, (sprite_id, name, path_hint) in enumerate(TILE_BRUSH_MENU):
            tag = "p_even" if index % 2 == 0 else "p_odd"
            tree.insert("", tk.END, iid=sprite_id, values=(sprite_id, name, path_hint), tags=(tag,))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2), pady=4)
        scroll = ttk.Scrollbar(
            table_box,
            orient=tk.VERTICAL,
            style="Palette.Vertical.TScrollbar",
            command=tree.yview,
        )
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=4)
        tree.configure(yscrollcommand=scroll.set)

        self._brush_table = tree
        tree.bind("<<TreeviewSelect>>", self._on_brush_table_select)

        default_brush = self._brush_sprite_var.get()
        if tree.exists(default_brush):
            tree.selection_set(default_brush)
            tree.focus(default_brush)
            tree.see(default_brush)

    def _on_brush_table_select(self, _event: object | None = None) -> None:
        tree = self._brush_table
        if tree is None:
            return
        selection = tree.selection()
        if not selection:
            return
        sprite_id = selection[0]
        self._brush_sprite_var.set(sprite_id)
        self.render()

    def _floor_cell_at_screen(self, screen_x: float, screen_y: float) -> tuple[int, int] | None:
        """Grid cell under the pointer, or ``None`` if off the floor grid."""

        bounds = self.scene.floor_grid_bounds()
        if bounds is None:
            return None
        min_x, max_x, min_y, max_y = bounds
        grid = self.scene.camera.screen_to_grid(screen_x, screen_y)
        gx = int(round(grid.x))
        gy = int(round(grid.y))
        if not (min_x <= gx <= max_x and min_y <= gy <= max_y):
            return None
        return (gx, gy)

    def _paint_tile_at_screen(self, screen_x: float, screen_y: float) -> None:
        cell = self._floor_cell_at_screen(screen_x, screen_y)
        if cell is None:
            self._paint_drag_last_cell = None
            return
        gx, gy = cell
        sprite_name = self._brush_sprite_var.get()
        self.scene.sprites.get(sprite_name)
        self.scene.set_tile(Tile(x=gx, y=gy, z=0, sprite=sprite_name))
        self._paint_drag_last_cell = cell
        self.render()

    def _paint_tile_drag(self, screen_x: float, screen_y: float) -> None:
        """Paint during ``B1-Motion``; only updates when the cell changes."""

        cell = self._floor_cell_at_screen(screen_x, screen_y)
        if cell is None:
            return
        if cell == self._paint_drag_last_cell:
            return
        gx, gy = cell
        sprite_name = self._brush_sprite_var.get()
        self.scene.sprites.get(sprite_name)
        self.scene.set_tile(Tile(x=gx, y=gy, z=0, sprite=sprite_name))
        self._paint_drag_last_cell = cell
        self.render()

    def _on_canvas_paint_b1_motion(self, event: object) -> None:
        if not self._tile_edit_menu or self._input_mode_var.get() != "paint":
            return
        x = getattr(event, "x", None)
        y = getattr(event, "y", None)
        if x is None or y is None:
            return
        self._paint_tile_drag(float(x), float(y))

    def _on_canvas_click(self, event) -> None:
        if self._tile_edit_menu and self._input_mode_var.get() == "paint":
            self._paint_tile_at_screen(float(event.x), float(event.y))
            return

        entity_id = self._pathfinding_entity_id
        if not entity_id or not self.scene.has_entity(entity_id):
            return

        if self._player_path_cooldown_s is not None:
            now = time.monotonic()
            if self._last_player_path_change_monotonic is not None:
                if now - self._last_player_path_change_monotonic < self._player_path_cooldown_s:
                    return

        grid = self.scene.camera.screen_to_grid(float(event.x), float(event.y))
        goal_x = int(round(grid.x))
        goal_y = int(round(grid.y))

        path = self.scene.pathfind_entity_to_cell(entity_id, goal_x, goal_y)
        if not path:
            return

        if self._path_after_id is not None:
            self.root.after_cancel(self._path_after_id)
            self._path_after_id = None

        origin_x, origin_y = self._entity_xy(entity_id)
        self._path_motion_queue = _motion_points_along_grid_path(
            path,
            steps_per_edge=self._path_steps_per_grid_edge,
            origin_x=origin_x,
            origin_y=origin_y,
        )
        if self._player_path_cooldown_s is not None:
            self._last_player_path_change_monotonic = time.monotonic()
        self._advance_path_motion()

    def _schedule_player_motion(self) -> None:
        if not self._path_motion_queue:
            return
        if self._path_after_id is not None:
            self.root.after_cancel(self._path_after_id)
        self._path_after_id = self.root.after(
            self._path_micro_step_ms,
            self._advance_path_motion,
        )

    def _advance_path_motion(self) -> None:
        self._path_after_id = None
        entity_id = self._pathfinding_entity_id
        if not entity_id or not self._path_motion_queue:
            return
        if not self.scene.has_entity(entity_id):
            self._path_motion_queue.clear()
            return

        if self._path_motion_queue:
            peek_x, peek_y = self._path_motion_queue[0]
            if _queued_step_targets_blocked_cell(self.scene, entity_id, peek_x, peek_y):
                self._path_motion_queue.clear()
                self.render()
                return

        next_x, next_y = self._path_motion_queue.pop(0)
        self.scene.move_entity(entity_id, float(next_x), float(next_y))
        self.scene.apply_spirit_tile_hazards_after_move(entity_id)
        if not self.scene.has_entity(entity_id):
            self._path_motion_queue.clear()
            self._pathfinding_entity_id = None
            self._highlight_entity_id = None
            self.render()
            return

        self.render()

        if self._path_motion_queue:
            self._schedule_player_motion()

    def _schedule_autonomous_spirits(self) -> None:
        self._auto_spirit_after_id = self.root.after(
            self._auto_spirit_tick_ms,
            self._advance_autonomous_spirits,
        )

    def _advance_autonomous_spirits(self) -> None:
        self._auto_spirit_after_id = None
        if not self._auto_spirit_id_list:
            return

        for entity_id in list(self._auto_spirit_id_list):
            if not self.scene.has_entity(entity_id):
                self._auto_spirit_id_list.remove(entity_id)
                self._auto_spirit_queues.pop(entity_id, None)
                continue

            queue = self._auto_spirit_queues.setdefault(entity_id, [])
            if not queue:
                self._assign_random_autonomous_path(entity_id)
                queue = self._auto_spirit_queues.setdefault(entity_id, [])

            if queue:
                peek_x, peek_y = queue[0]
                if _queued_step_targets_blocked_cell(self.scene, entity_id, peek_x, peek_y):
                    self._auto_spirit_queues[entity_id] = []
                    self._assign_random_autonomous_path(entity_id)
                else:
                    next_x, next_y = queue.pop(0)
                    self.scene.move_entity(entity_id, float(next_x), float(next_y))
                    self.scene.apply_spirit_tile_hazards_after_move(entity_id)
                    if not self.scene.has_entity(entity_id):
                        self._auto_spirit_id_list.remove(entity_id)
                        self._auto_spirit_queues.pop(entity_id, None)

        self.render()
        if self._auto_spirit_id_list:
            self._schedule_autonomous_spirits()

    def _assign_random_autonomous_path(self, entity_id: str) -> None:
        if not self.scene.has_entity(entity_id):
            return

        bounds = self.scene.floor_grid_bounds()
        if bounds is None:
            return

        min_x, max_x, min_y, max_y = bounds
        for _ in range(120):
            goal_x = random.randint(min_x, max_x)
            goal_y = random.randint(min_y, max_y)
            path = self.scene.pathfind_entity_to_cell(entity_id, goal_x, goal_y)
            if path is None:
                continue
            if len(path) < 2:
                continue
            ox, oy = self._entity_xy(entity_id)
            self._auto_spirit_queues[entity_id] = _motion_points_along_grid_path(
                path,
                steps_per_edge=self._path_steps_per_grid_edge,
                origin_x=ox,
                origin_y=oy,
            )
            return

    def _entity_xy(self, entity_id: str) -> tuple[float, float]:
        for entity in self.scene.entities:
            if entity.entity_id == entity_id:
                return entity.x, entity.y
        raise KeyError(f"Unknown entity '{entity_id}'")

    def _draw_command(self, command: DrawCommand) -> None:
        sprite = command.sprite
        if sprite.shape == "diamond":
            self._draw_diamond(command.screen.x, command.screen.y, sprite)
        elif sprite.shape == "pawn":
            self._draw_pawn(command.screen.x, command.screen.y, sprite)
        elif sprite.shape == "spirit":
            self._draw_spirit(command.screen.x, command.screen.y, sprite)
            if (
                command.health is not None
                and command.max_health is not None
                and command.health > 0
            ):
                self._draw_spirit_health_bar(
                    command.screen.x,
                    command.screen.y,
                    sprite,
                    command.health,
                    command.max_health,
                )
        else:
            self._draw_box(command.screen.x, command.screen.y, sprite)

    def _draw_diamond(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        half_w = sprite.width / 2
        half_h = sprite.height / 2
        self.canvas.create_polygon(
            x,
            y - half_h,
            x + half_w,
            y,
            x,
            y + half_h,
            x - half_w,
            y,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )

    def _draw_pawn(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        left, top = self._anchored_bounds(x, y, sprite)
        right = left + sprite.width
        bottom = top + sprite.height
        head_size = sprite.width * 0.58
        head_left = x - head_size / 2
        head_top = top
        head_right = x + head_size / 2
        head_bottom = top + head_size

        self.canvas.create_oval(
            head_left,
            head_top,
            head_right,
            head_bottom,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )
        self.canvas.create_polygon(
            x,
            top + head_size * 0.7,
            right,
            bottom,
            left,
            bottom,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )

    def _draw_spirit(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        left, top = self._anchored_bounds(x, y, sprite)
        right = left + sprite.width
        bottom = top + sprite.height
        glow_margin = max(2.0, sprite.width * 0.25)

        self.canvas.create_oval(
            left - glow_margin,
            top - glow_margin,
            right + glow_margin,
            bottom + glow_margin,
            fill="",
            outline=sprite.fill,
            width=1,
        )
        self.canvas.create_oval(
            left,
            top,
            right,
            bottom,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )
        eye_dx = max(2.0, sprite.width * 0.24)
        eye_in = max(1.0, sprite.width * 0.09)
        self.canvas.create_oval(
            x - eye_dx,
            top + sprite.height * 0.33,
            x - eye_in,
            top + sprite.height * 0.44,
            fill=sprite.outline,
            outline=sprite.outline,
        )
        self.canvas.create_oval(
            x + eye_in,
            top + sprite.height * 0.33,
            x + eye_dx,
            top + sprite.height * 0.44,
            fill=sprite.outline,
            outline=sprite.outline,
        )
        lip = max(2.0, sprite.width * 0.12)
        toe = max(2.0, sprite.height * 0.1)
        smile = max(3.0, sprite.height * 0.2)
        self.canvas.create_line(
            left + lip,
            bottom - toe,
            x,
            bottom + smile,
            right - lip,
            bottom - toe,
            fill=sprite.outline,
            width=2,
            smooth=True,
        )

    def _draw_spirit_health_bar(
        self,
        x: float,
        y: float,
        sprite: SpriteDefinition,
        health: float,
        max_health: float,
    ) -> None:
        """Thin bar above the spirit body."""

        left, top = self._anchored_bounds(x, y, sprite)
        bar_width = sprite.width
        bar_height = max(3.0, sprite.height * 0.14)
        gap = max(2.0, sprite.height * 0.12)
        bar_top = top - bar_height - gap
        ratio = 0.0 if max_health <= 0 else max(0.0, min(1.0, health / max_health))

        self.canvas.create_rectangle(
            left,
            bar_top,
            left + bar_width,
            bar_top + bar_height,
            fill="#111827",
            outline="#374151",
            width=1,
        )
        inner = max(1.0, min(2.0, sprite.height * 0.06))
        inner_width = max(0.0, (bar_width - inner * 2) * ratio)
        self.canvas.create_rectangle(
            left + inner,
            bar_top + inner,
            left + inner + inner_width,
            bar_top + bar_height - inner,
            fill="#34d399",
            outline="",
        )

    def _draw_spirit_highlight_ring(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        """Gold ring drawn only for the player-controlled spirit."""

        left, top = self._anchored_bounds(x, y, sprite)
        right = left + sprite.width
        bottom = top + sprite.height
        margin = max(4.0, sprite.width * 0.3)
        self.canvas.create_oval(
            left - margin,
            top - margin,
            right + margin,
            bottom + margin,
            fill="",
            outline="#f5d547",
            width=2,
        )

    def _draw_box(self, x: float, y: float, sprite: SpriteDefinition) -> None:
        left, top = self._anchored_bounds(x, y, sprite)
        self.canvas.create_rectangle(
            left,
            top,
            left + sprite.width,
            top + sprite.height,
            fill=sprite.fill,
            outline=sprite.outline,
            width=2,
        )

    @staticmethod
    def _anchored_bounds(
        x: float,
        y: float,
        sprite: SpriteDefinition,
    ) -> tuple[float, float]:
        return (
            x - sprite.width * sprite.anchor_x,
            y - sprite.height * sprite.anchor_y,
        )

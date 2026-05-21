"""Integer grid pathfinding for scene navigation."""

from __future__ import annotations

import heapq
from collections.abc import Generator


def find_path_on_grid(
    start: tuple[int, int],
    goal: tuple[int, int],
    min_x: int,
    max_x: int,
    min_y: int,
    max_y: int,
    blocked: set[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    """Run A* with Manhattan distance on a 4-connected grid.

    Cells in ``blocked`` cannot be entered except that the ``start`` cell is
    always treated as walkable so an entity can path away from a mis-tagged
    tile without getting stuck.
    """

    if not _in_bounds(start[0], start[1], min_x, max_x, min_y, max_y):
        return None
    if not _in_bounds(goal[0], goal[1], min_x, max_x, min_y, max_y):
        return None
    if goal in blocked:
        return None

    if start == goal:
        return [start]

    blocked_without_start = blocked - {start}

    def heuristic(x: int, y: int) -> int:
        return abs(x - goal[0]) + abs(y - goal[1])

    open_heap: list[tuple[int, int, int, int]] = []
    counter = 0
    heapq.heappush(open_heap, (heuristic(*start), counter, start[0], start[1]))
    counter += 1

    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], int] = {start: 0}

    while open_heap:
        _, _, current_x, current_y = heapq.heappop(open_heap)
        current = (current_x, current_y)
        if current == goal:
            return _reconstruct_path(came_from, start, goal)

        current_g = g_score[current]
        for neighbor in _neighbors(
            current_x,
            current_y,
            min_x,
            max_x,
            min_y,
            max_y,
            blocked_without_start,
        ):
            tentative = current_g + 1
            previous = g_score.get(neighbor)
            if previous is None or tentative < previous:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f = tentative + heuristic(*neighbor)
                heapq.heappush(open_heap, (f, counter, neighbor[0], neighbor[1]))
                counter += 1

    return None


def _in_bounds(x: int, y: int, min_x: int, max_x: int, min_y: int, max_y: int) -> bool:
    return min_x <= x <= max_x and min_y <= y <= max_y


def _neighbors(
    x: int,
    y: int,
    min_x: int,
    max_x: int,
    min_y: int,
    max_y: int,
    blocked: set[tuple[int, int]],
) -> Generator[tuple[int, int], None, None]:
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if not _in_bounds(nx, ny, min_x, max_x, min_y, max_y):
            continue
        if (nx, ny) in blocked:
            continue
        yield (nx, ny)


def _reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    path = [goal]
    current = goal
    while current != start:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path

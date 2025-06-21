import heapq
from shared.maps_campaign import SUBTILES_PER_TILE, is_walkable_subtile

def find_path(grid, start, goal):
    def neighbors(pos):
        x, y, sx, sy = pos
        for dx, dy, dsx, dsy in [
            (0, 0, 1, 0), (0, 0, -1, 0), (0, 0, 0, 1), (0, 0, 0, -1),
            (1, 0, 0, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, -1, 0, 0)
        ]:
            nx, ny, nsx, nsy = x+dx, y+dy, sx+dsx, sy+dsy
            if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid) and 0 <= nsx < SUBTILES_PER_TILE and 0 <= nsy < SUBTILES_PER_TILE:
                if is_walkable_subtile(grid, nx, ny, nsx, nsy):
                    yield (nx, ny, nsx, nsy)
    def heuristic(a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2]) + abs(a[3]-b[3])
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        for neighbor in neighbors(current):
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heapq.heappush(open_set, (tentative_g + heuristic(neighbor, goal), neighbor))
    return []

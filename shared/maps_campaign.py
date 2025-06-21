# shared/maps_campaign.py
"""
Static campaign maps for the isometric roguelike game.
Each act has 10 zones, with a boss in the 10th zone.
The theme is 'Imperial American' with comically evil supervillains.
"""

# Tile codes: 0 = floor, 1 = wall, 2 = exit, 3 = boss

# Example: Each act/zone is a simple room, boss room is special
CAMPAIGN_MAPS = []
BOSS_NAMES = [
    "General Liberty",  # Act 1 boss
    "Admiral Freedom",  # Act 2 boss
    "President Doom"    # Act 3 boss (ultimate boss)
]

for act in range(3):
    for zone in range(10):
        # Default: 10x7 room
        grid = [
            [1]*10,
            [1,0,0,0,0,0,0,0,2,1],
            [1,0,1,1,0,1,1,0,0,1],
            [1,0,1,0,0,0,1,0,0,1],
            [1,0,1,0,1,0,1,0,0,1],
            [1,0,0,0,1,0,0,0,0,1],
            [1]*10
        ]
        # Boss room (zone 9)
        if zone == 9:
            # Place boss tile (3) in the center
            grid[3][5] = 3
            # Place exit (2) at far right
            grid[3][8] = 2
        CAMPAIGN_MAPS.append({
            "act": act+1,
            "zone": zone+1,
            "boss": BOSS_NAMES[act] if zone == 9 else None,
            "width": 10,
            "height": 7,
            "grid": grid
        })

def get_campaign_map(act, zone):
    """Return the map dict for the given act (1-based) and zone (1-based)."""
    for m in CAMPAIGN_MAPS:
        if m["act"] == act and m["zone"] == zone:
            return m
    return None

# --- Act 1 zone skeletons with unique features and boss battle ---
ACT1_ZONE_COUNT = 10
TILE_FLOOR = 0
TILE_WALL = 1
TILE_WAYPOINT = 2
TILE_EVENT = 3  # e.g., key, puzzle, miniboss, etc.
TILE_BOSS = 4

def get_act1_zone(zone):
    """
    Return a dict with map data and metadata for the given Act 1 zone (1-based).
    """
    if zone < 1 or zone > ACT1_ZONE_COUNT:
        raise ValueError("Invalid Act 1 zone")
    if zone == 10:
        return boss_zone()
    return regular_zone(zone)

def regular_zone(zone):
    width, height = 10, 10
    grid = [[TILE_FLOOR for _ in range(width)] for _ in range(height)]
    # Walls around edge
    for y in range(height):
        for x in range(width):
            if x == 0 or y == 0 or x == width-1 or y == height-1:
                grid[y][x] = TILE_WALL
    # Place a waypoint to next zone
    grid[height-2][width-2] = TILE_WAYPOINT
    # Place a unique event/tile for this zone
    grid[1][zone] = TILE_EVENT  # Example: event tile moves across zones
    # Example: add a miniboss in zone 5
    if zone == 5:
        grid[height//2][width//2] = TILE_EVENT
    # Add some flavor: extra walls or obstacles
    if zone % 2 == 0:
        for i in range(2, 8):
            grid[3][i] = TILE_WALL
    return {
        "grid": grid,
        "width": width,
        "height": height,
        "zone": zone,
        "act": 1,
        "waypoint": (width-2, height-2),
        "event": (1, zone),
        "city": False,
        "boss": False
    }

def boss_zone():
    width, height = 12, 12
    grid = [[TILE_FLOOR for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if x == 0 or y == 0 or x == width-1 or y == height-1:
                grid[y][x] = TILE_WALL
    # Boss in the center
    grid[height//2][width//2] = TILE_BOSS
    # Waypoint appears after boss is defeated (server logic)
    # For now, place it in the corner
    grid[1][1] = TILE_WAYPOINT
    return {
        "grid": grid,
        "width": width,
        "height": height,
        "zone": 10,
        "act": 1,
        "waypoint": (1, 1),
        "event": (height//2, width//2),
        "city": False,
        "boss": True
    }

# Each tile is subdivided into 3x3 sub-tiles for fine movement
SUBTILES_PER_TILE = 3

def is_walkable_tile(grid, x, y):
    """Return True if the tile at (x, y) is walkable (floor or exit)."""
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        return grid[y][x] in (0, 2)
    return False

def get_subtile_positions(x, y):
    """Return all 9 sub-tile positions for a given tile (x, y)."""
    return [(x, y, sx, sy) for sx in range(SUBTILES_PER_TILE) for sy in range(SUBTILES_PER_TILE)]

def is_walkable_subtile(grid, x, y, sx, sy):
    """Return True if the subtile at (x, y, sx, sy) is walkable (parent tile is floor or exit)."""
    return is_walkable_tile(grid, x, y)

# Example usage: get_subtile_positions(3, 4) returns all 9 sub-tile positions in tile (3,4)
# Pathfinding and movement should use (x, y, sx, sy) positions for precision.
# Example usage: is_walkable_subtile(grid, 3, 4, 1, 2)
# You may want to add more logic here later for obstacles or partial blocking.

"""
Static city map for the isometric roguelike game.
The city is a social hub with gear shop, rest area, vendors, and waypoint to campaign.
"""

# Tile codes: 0 = floor, 1 = wall, 2 = waypoint (warp to campaign), 4 = shop, 5 = rest

CITY_MAP = {
    "name": "Imperial Americanopolis",
    "width": 12,
    "height": 8,
    "grid": [
        [1]*12,
        [1,0,0,0,0,0,0,0,0,2,0,1],
        [1,0,4,0,0,0,0,0,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,0,0,5,0,0,0,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,1],
        [1,0,0,0,0,0,0,0,0,0,0,1],
        [1]*12
    ]
}

def get_city_map():
    return CITY_MAP

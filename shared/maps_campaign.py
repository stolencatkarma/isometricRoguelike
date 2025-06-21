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

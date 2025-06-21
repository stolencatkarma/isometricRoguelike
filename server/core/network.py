import asyncio
import websockets
import uuid
import json
import time
from shared.map import GameMap
from shared.maps_campaign import get_campaign_map, SUBTILES_PER_TILE, is_walkable_subtile
from shared.maps_city import get_city_map
from shared.maps_endgame import generate_endgame_map

def start_server(handler):
    print("Server starting on ws://localhost:8765 ...")
    return websockets.serve(handler, "localhost", 8765)

# ...move more server logic here as needed...

def init_state():
    return {
        'connected_clients': {},
        'player_states': {},
        'player_progress': {},
        'parties': {},
        'player_xp': {},
        'monsters': {},
        'emotes': {},
        'player_hp': {},
        'player_max_hp': {},
        'player_info': {},
        'player_in_city': {},
        'CITY_INSTANCE': {
            'map': None,
            'members': set()
        },
        # ...add more server state as needed...
    }

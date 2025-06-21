def get_party_id(act, zone, endgame_depth=None):
    if act > 3:
        return f"endgame_{endgame_depth or 1}"
    return f"act{act}_zone{zone}"

# ...move more party/instance logic here as needed...

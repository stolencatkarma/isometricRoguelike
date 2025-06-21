# isometricRoguelike

A 90s-style isometric multiplayer roguelike game with in-depth crafting, a 3-chapter campaign, and repeatable end-game. Built in Python using pygame for graphics and websockets for multiplayer.

## Features
- Isometric 2D graphics (simple, retro style)
- Multiplayer (up to 4 players per party)
- Roguelike mechanics (static campaign maps, penalties, progression)
- Deep crafting system (WIP)
- 3-act campaign + repeatable end-game
- City hub for socializing, gearing, and resting
- Party system, class selection, XP/level/stat progression
- Basic monster logic and instanced maps
- Scene-based client UI: main menu, character select, main game
- Shared logic in `shared/` for both client and server
- Modular codebase (all logic in core/ modules)

## Project Structure
- `client/` – Python client using pygame for isometric rendering and UI
  - `core/` – Modularized: sprites, render, game, pathfinding, input, update, network
- `server/` – Python server using websockets for multiplayer
  - `core/` – Modularized: server, state, party, classes, network
- `shared/` – Shared code (data models, maps, campaign, city, endgame)
- `assets/` – Sprites and palettes

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Setup
1. Clone the repository
2. Install dependencies for both client and server:
   ```sh
   pip install -r client/requirements.txt
   pip install -r server/requirements.txt
   ```
3. Run the server:
   ```sh
   python server/main.py
   ```
4. Run the client:
   ```sh
   python client/main.py
   ```

## Development Notes
- All logic is modularized in `core/` modules for both client and server.
- Scene management: main menu → character select → main game.
- The city is a separate map; players can only warp to the city at campaign waypoints.
- The crafting system and campaign structure are under active development.
- See `shared/` for common data models and utilities.
- Debugging: client and server print debug output for scene transitions, input, and network events.
- `.gitignore` is set up for Python, OS, and editor files.

---

Contributions welcome!

# isometricRoguelike

A 90s-style isometric multiplayer roguelike game with in-depth crafting, a 3-chapter campaign, and repeatable end-game. Built in Python using pygame for graphics and websockets for multiplayer.

## Features
- Isometric 2D graphics (simple, retro style)
- Multiplayer (up to 4 players per party)
- Roguelike mechanics (procedural generation, penalties, progression)
- Deep crafting system
- 3-chapter campaign + repeatable end-game
- Long-term progression and power growth

## Project Structure
- `client/` – Python client using pygame for isometric rendering
- `server/` – Python server using websockets for multiplayer
- `shared/` – Shared code (data models, utilities)

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
- Graphics are placeholder and should be replaced with your own assets.
- The crafting system and campaign structure are under active development.
- See `shared/` for common data models and utilities.

---

Contributions welcome!

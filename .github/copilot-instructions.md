<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a Python monorepo for a multiplayer isometric roguelike game. The client uses pygame for rendering and UI, and the server uses websockets for multiplayer networking. Shared logic (maps, campaign, etc.) is in the shared/ directory as importable Python modules.

Current state (June 2025):
- The campaign is a 3-act, 10-zone static map system with a main city hub. Each party gets its own instanced campaign map.
- The city is a separate map where players start, can gear up, rest, and socialize. Players can only warp to the city at campaign waypoints (no portals/scrolls).
- The client supports isometric rendering, party UI, emotes, zoom, and city/campaign transitions. The city UI is placeholder but functional.
- The server manages player/party state, instanced maps, city/campaign transitions, and relays state to clients.
- Party system, class selection, XP/level/stat progression, and basic monster logic are implemented.
- Next steps: expand city features (shops, rest, vendors), add combat, crafting, and more campaign/endgame content.

Follow the above architecture and keep shared logic in shared/ for both client and server use.

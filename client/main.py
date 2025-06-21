# Entry point for the Python client
# Uses pygame for isometric rendering and websockets for networking
import asyncio
import websockets
import json
import pygame
import sys

# Isometric tile settings
TILE_WIDTH = 64
TILE_HEIGHT = 32
MAP_WIDTH = 10
MAP_HEIGHT = 10

# Colors
BG_COLOR = (30, 30, 30)
TILE_COLOR = (100, 200, 255)
PLAYER_COLOR = (255, 100, 100)

# Dummy player state (updated only from server)
player_pos = [5, 5]

async def network_loop(uri, send_queue, recv_queue):
    async with websockets.connect(uri) as websocket:
        welcome = await websocket.recv()
        welcome_data = json.loads(welcome)
        client_id = welcome_data["payload"]["client_id"]
        # Send join message
        join_msg = json.dumps({
            "type": "join",
            "sender": client_id,
            "payload": {"name": "Player"}
        })
        await websocket.send(join_msg)
        # Start send/receive loop
        async def sender():
            while True:
                msg = await send_queue.get()
                await websocket.send(msg)
        async def receiver():
            while True:
                msg = await websocket.recv()
                await recv_queue.put(msg)
        await asyncio.gather(sender(), receiver())

def draw_isometric_grid(screen):
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            sx = (x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2
            sy = (x + y) * (TILE_HEIGHT // 2) + 50
            points = [
                (sx, sy + TILE_HEIGHT // 2),
                (sx + TILE_WIDTH // 2, sy),
                (sx + TILE_WIDTH, sy + TILE_HEIGHT // 2),
                (sx + TILE_WIDTH // 2, sy + TILE_HEIGHT)
            ]
            pygame.draw.polygon(screen, TILE_COLOR, points, 1)

def draw_player(screen, pos):
    x, y = pos
    sx = (x - y) * (TILE_WIDTH // 2) + screen.get_width() // 2
    sy = (x + y) * (TILE_HEIGHT // 2) + 50
    pygame.draw.circle(screen, PLAYER_COLOR, (sx + TILE_WIDTH // 2, sy + TILE_HEIGHT // 2), 12)

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Isometric Roguelike Client")
    clock = pygame.time.Clock()
    send_queue = asyncio.Queue()
    recv_queue = asyncio.Queue()
    uri = "ws://localhost:8765"

    # Start networking in background
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(network_loop(uri, send_queue, recv_queue))

    global player_pos
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                move = None
                if event.key == pygame.K_UP:
                    move = (0, -1)
                elif event.key == pygame.K_DOWN:
                    move = (0, 1)
                elif event.key == pygame.K_LEFT:
                    move = (-1, 0)
                elif event.key == pygame.K_RIGHT:
                    move = (1, 0)
                if move:
                    # Send move request to server
                    msg = json.dumps({
                        "type": "move",
                        "payload": {"dx": move[0], "dy": move[1]}
                    })
                    loop.create_task(send_queue.put(msg))
        # Handle messages from server
        try:
            while True:
                msg = recv_queue.get_nowait()
                data = json.loads(msg)
                if data.get("type") == "state":
                    # Update player position from server state
                    player = data["payload"].get("player")
                    if player:
                        player_pos = player["pos"]
        except asyncio.QueueEmpty:
            pass
        screen.fill(BG_COLOR)
        draw_isometric_grid(screen)
        draw_player(screen, player_pos)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from core.server import start_server
from core.state import init_state

async def main():
    state = init_state()
    await start_server(state)

if __name__ == "__main__":
    asyncio.run(main())

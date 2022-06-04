import asyncio
import socket
import json
import websockets as ws
import platform

from server import server

'''
All messages are of the form:
{
    "type": "offer" | ...,
    "body": {}
}
'''

# When running on windows, hardcode the name of the camera
# (To find the name, go to device manager > cameras)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0] 
    s.close()
    return ip

ip = get_ip()
port = 3001

start_message = f"""XRSee websocket server started 🎉
> Local:   ws://localhost:{port}"""


async def main():
    async with ws.serve(server, "localhost", port):
        print(start_message)
        await asyncio.Future()

asyncio.run(main())
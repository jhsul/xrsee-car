import asyncio
import socket
import json
import websockets as ws
import platform
import argparse

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



async def main(args):
    addr = "localhost" if args["localhost"] else ip

    print(f"XRSee websocket server started on ws://{addr}:{port}")
    async with ws.serve(server, addr, port):
        await asyncio.Future()


parser = argparse.ArgumentParser(description="XRSee car script")
parser.add_argument("--localhost", action="store_true", help=f"use localhost:{port}. Leave blank to use {ip}:{port}")
args = vars(parser.parse_args())

asyncio.run(main(args))
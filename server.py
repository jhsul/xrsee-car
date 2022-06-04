import json
from webrtc import handle_offer


async def server(websocket):
    async for message in websocket:
        #print(f"Received message from {websocket.id}")
        message_json = json.loads(message)
        print(f"Received {message_json['type']} message from {websocket.id}")
        #print(json.dumps(message_json, indent=2))

        if message_json["type"] == "offer":
            answer_message = await handle_offer(message_json)
            await websocket.send(answer_message)
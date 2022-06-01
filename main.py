import asyncio
import socket
import json
import websockets as ws
import platform

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender

'''
All messages are of the form:
{
    "type": "offer" | ...,
    "body": {}
}
'''

# When running on windows, hardcode the name of the camera
# (To find the name, go to device manager > cameras)
WINDOWS_CAMERA_NAME = "USB  Live camera"

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0] 
    s.close()
    return ip

ip = get_ip()
port = 3001

start_message = f"""XRSee websocket server started 🎉
> Network:  ws://{ip}:{port}
> Local:    ws://localhost:{port}"""

relay = None
webcam = None

# This is the set of all active peer connections
pcs = set() 

def create_local_tracks(play_from, decode):
    global relay, webcam

    if play_from:
        player = MediaPlayer(play_from, decode=decode)
        return player.audio, player.video
    else:
        #options = {"framerate": "30", "video_size": "640x480"}
        options = { "video_size": "640x480"}
        if relay is None:
            if platform.system() == "Darwin":
                webcam = MediaPlayer(
                    "default:none", format="avfoundation", options=options
                )
            elif platform.system() == "Windows":
                webcam = MediaPlayer(
                    #"video=Integrated Camera", format="dshow", options=options
                    f"video={WINDOWS_CAMERA_NAME}", format="dshow", options=options
                )
            else:
                webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            relay = MediaRelay()
        return None, relay.subscribe(webcam.video)


def force_codec(pc, sender, forced_codec):
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )
#stop = asyncio.Future() # awaitable stop conditino

async def server(websocket):
    async for message in websocket:
        #print(f"Received message from {websocket.id}")
        message_json = json.loads(message)
        print(f"Received {message_json['type']} message from {websocket.id}")
        #print(json.dumps(message_json, indent=2))

        if message_json["type"] == "offer":
            offer = RTCSessionDescription(sdp=message_json["body"]["sdp"], type=message_json["body"]["type"])
            pc = RTCPeerConnection()

            pcs.add(pc)
            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                print("Connection state is %s" % pc.connectionState)
                if pc.connectionState == "failed":
                    print(f"Closing connection")
                    await pc.close()
                    pcs.discard(pc)

            # open media source
            audio, video = create_local_tracks(
                None, decode=not None
            )

            if audio:
                audio_sender = pc.addTrack(audio)
                #if args.audio_codec:
                #    force_codec(pc, audio_sender, args.audio_codec)
                #elif args.play_without_decoding:
                #    raise Exception("You must specify the audio codec using --audio-codec")

            if video:
                video_sender = pc.addTrack(video)
                #if args.video_codec:
                #    force_codec(pc, video_sender, args.video_codec)
                #elif args.play_without_decoding:
                #    raise Exception("You must specify the video codec using --video-codec")

            await pc.setRemoteDescription(offer)

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            answer_message = json.dumps({
                "type": "answer",
                "body": {
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type
                }
            })
            await websocket.send(answer_message)

async def main():
    async with ws.serve(server, "localhost", port):
        print(start_message)
        await asyncio.Future()

asyncio.run(main())
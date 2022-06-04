import json
import platform
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender

WINDOWS_CAMERA_NAME = "USB  Live camera"

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

async def handle_offer(message_json):
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
        
    if video:
        video_sender = pc.addTrack(video)
        
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
    return answer_message
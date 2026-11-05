import asyncio
import json
import os
import threading
import queue
import websockets
import numpy as np
import sounddevice as sd
import aubio

# Load configuration file if it exists
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "vts_websocket_uri": "ws://localhost:8001",
    "min_frequency": 550.50,
    "max_frequency": 1310.42,
    "confidence_threshold": 0.8,
    "parameter_name": "ParamOcarinaNote"
}

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = DEFAULT_CONFIG

URI = config["vts_websocket_uri"]
MIN_FREQ = config["min_frequency"]
MAX_FREQ = config["max_frequency"]
CONFIDENCE_THRESHOLD = config["confidence_threshold"]
PARAM_NAME = config["parameter_name"]

PLUGIN_INFO = {
    "pluginName": "OcarinaAudioTracker",
    "pluginDeveloper": "Live2DCreator",
    "pluginIcon": None
}

SAMPLE_RATE = 44100
BUFFER_SIZE = 2048
HOP_SIZE = 512

def frequency_to_normalized_parameter(freq):
    if freq <= 0:
        return 0.0
    clamped_freq = max(MIN_FREQ, min(freq, MAX_FREQ))
    return float((clamped_freq - MIN_FREQ) / (MAX_FREQ - MIN_FREQ))

def audio_processing_worker(data_queue):
    pitch_o = aubio.pitch("yin", BUFFER_SIZE, HOP_SIZE, SAMPLE_RATE)
    pitch_o.set_unit("Hz")

    print("Audio capture active")
    try:
        with sd.InputStream(channels=1, samplerate=SAMPLE_RATE, blocksize=HOP_SIZE) as stream:
            while True:
                audio_data, _ = stream.read(HOP_SIZE)
                signal = np.ascontiguousarray(audio_data[:, 0], dtype=np.float32)
                
                pitch = pitch_o(signal)[0]
                confidence = pitch_o.get_confidence()

                if confidence > 0.1:
                    print(f"[Audio Debug] Pitch: {pitch:.2f} Hz | Confidence: {confidence:.2f}")

                if confidence > CONFIDENCE_THRESHOLD and pitch > 0:
                    normalized_val = frequency_to_normalized_parameter(pitch)
                    try:
                        data_queue.put_nowait(normalized_val)
                    except queue.Full:
                        pass
    except Exception as e:
        print(f"Audio stream error: {e}")

async def authenticate(websocket):
    token_request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "TokenRequestID",
        "messageType": "AuthenticationTokenRequest",
        "data": PLUGIN_INFO
    }
    await websocket.send(json.dumps(token_request))
    response = await websocket.recv()
    response_data = json.loads(response)
    
    if "data" in response_data and "authenticationToken" in response_data["data"]:
        token = response_data["data"]["authenticationToken"]
        print("Authentication token received. Please accept the prompt in VTube Studio.")
        
        auth_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "AuthRequestID",
            "messageType": "AuthenticationRequest",
            "data": {
                **PLUGIN_INFO,
                "authenticationToken": token
            }
        }
        await websocket.send(json.dumps(auth_request))
        auth_response = await websocket.recv()
        print("Authentication status:", auth_response)

async def register_custom_parameter(websocket):
    creation_request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "CreateParamID",
        "messageType": "ParameterCreationRequest",
        "data": {
            "parameterName": PARAM_NAME,
            "explanation": "Ocarina pitch detection input parameter",
            "min": 0.0,
            "max": 1.0,
            "defaultValue": 0.0
        }
    }
    await websocket.send(json.dumps(creation_request))
    response = await websocket.recv()
    print("Parameter Registration Response:", response)

async def main():
    data_queue = queue.Queue(maxsize=10)
    audio_thread = threading.Thread(target=audio_processing_worker, args=(data_queue,), daemon=True)
    audio_thread.start()

    async with websockets.connect(URI) as websocket:
        await authenticate(websocket)
        await register_custom_parameter(websocket)
        print("Connected to VTube Studio. Streaming pitch data...")

        last_sent_val = -1.0

        while True:
            try:
                while not data_queue.empty():
                    normalized_val = data_queue.get_nowait()
                    if abs(normalized_val - last_sent_val) > 0.005:
                        last_sent_val = normalized_val
                        print(f"Sending to VTS [{PARAM_NAME}]: {normalized_val:.3f}")
                        
                        injection_request = {
                            "apiName": "VTubeStudioPublicAPI",
                            "apiVersion": "1.0",
                            "requestID": "InjectDataID",
                            "messageType": "InjectParameterDataRequest",
                            "data": {
                                "parameterValues": [
                                    {
                                        "id": PARAM_NAME,
                                        "value": normalized_val
                                    }
                                ]
                            }
                        }
                        await websocket.send(json.dumps(injection_request))
                        _ = await websocket.recv()
            except Exception as e:
                print(f"WebSocket send error: {e}")

            await asyncio.sleep(0.033)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down application...")
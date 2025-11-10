# app.py
# FastAPI WebSocket server for VisualAid: receives frames from mobile client and broadcasts detections to dashboard + mobile.
# Uses YOLO (ultralytics) for object detection and Gemini (google-generativeai) for smart narration.
# Environment variables loaded via .env (GEMINI_API_KEY required).

import os
import base64
import json
import asyncio
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import numpy as np
import cv2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- YOLO (ultralytics) ---
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

# --- Gemini (google-generativeai) ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # ✅ FIXED: Use env var name, not the key itself
USE_GEMINI = bool(GEMINI_API_KEY)
model_gemini = None

if USE_GEMINI:
    try:
        import google.generativeai as genai
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        # ✅ Force Gemini SDK to use the stable v1 API (not v1beta)
        genai.configure(
            api_key=GEMINI_API_KEY,
            client_options={"api_endpoint": "https://generativelanguage.googleapis.com/v1/"}
        )

        # ✅ Load correct model with "models/" prefix
        model_gemini = genai.GenerativeModel('models/gemini-1.5-pro-latest')

        print("✅ Gemini model initialized using v1 API.")
    except Exception as e:
        print('❌ Failed to initialize Gemini SDK:', e)
        USE_GEMINI = False

# --- FastAPI setup ---
app = FastAPI()
app.mount('/static', StaticFiles(directory='templates'), name='static')

rooms: Dict[str, Set[WebSocket]] = {}

# --- Load YOLO model ---
model = None
if YOLO is not None:
    try:
        model = YOLO('yolov8n.pt')  # lightweight version
        print('✅ YOLO model loaded.')
    except Exception as e:
        print('❌ Failed to load YOLO model at startup:', e)


async def call_llm_gemini(prompt: str) -> str:
    """Call Gemini to summarize detected objects into short narration."""
    if not USE_GEMINI or model_gemini is None:
        return prompt  # fallback if Gemini unavailable

    try:
        system_prompt = (
            "You are an assistive narrator for a visually impaired user. "
            "Given the detected objects, produce a concise, friendly English sentence "
            "under 20 words. Avoid speculation or uncertainty."
        )

        response = model_gemini.generate_content(
            [system_prompt, prompt],
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        text = (getattr(response, "text", "") or "").strip()
        return text[:220] if text else prompt
    except Exception as e:
        print('⚠️ Gemini call failed:', e)
        return prompt


def b64_to_bgr(data_b64: str):
    """Decode base64 image data to OpenCV BGR format."""
    try:
        header, encoded = data_b64.split(',', 1) if ',' in data_b64 else (None, data_b64)
        data = base64.b64decode(encoded)
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


async def process_frame_and_respond(img_bgr) -> Dict:
    """Run YOLO detection and build response payload."""
    payload = {'objects': [], 'summary': ''}
    global model

    if img_bgr is None:
        payload['summary'] = 'Invalid frame received.'
        return payload
    if model is None:
        payload['summary'] = 'Model not loaded on server.'
        return payload

    # YOLO inference
    try:
        results = model(img_bgr, verbose=False)[0]
        boxes = results.boxes
        names = results.names if hasattr(results, 'names') else {}
        objs = []
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0]) if hasattr(box, 'conf') else float(box.conf)
            cls = int(box.cls[0]) if hasattr(box, 'cls') else int(box.cls)
            label = names.get(cls, str(cls))
            objs.append({'label': label, 'conf': round(conf, 2), 'bbox': [x1, y1, x2, y2]})
        payload['objects'] = objs
    except Exception as e:
        print('YOLO inference error:', e)
        payload['summary'] = 'Detection error.'
        return payload

    # Build object count prompt
    counts = {}
    for o in payload['objects']:
        counts[o['label']] = counts.get(o['label'], 0) + 1

    if counts:
        parts = [f"{v} {k}{'s' if v > 1 else ''}" for k, v in counts.items()]
        prompt = 'I see ' + ', '.join(parts) + '.'
    else:
        prompt = 'No notable objects detected.'

    # Gemini summarization
    summary = await call_llm_gemini(prompt)
    payload['summary'] = summary
    return payload


@app.get('/')
async def index():
    return FileResponse('templates/dashboard.html')


@app.get('/mobile')
async def mobile():
    return FileResponse('templates/mobile.html')


@app.get("/ws/{room}")
async def ws_probe(room: str):
    """Probe endpoint for tunnel handshake."""
    return JSONResponse({"message": f"WebSocket endpoint ready for room {room}"})


@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    """WebSocket connection handler for live vision stream."""
    await asyncio.sleep(0.1)
    await websocket.accept()

    if room not in rooms:
        rooms[room] = set()
    rooms[room].add(websocket)
    print(f"🔌 Client connected to room {room}. Total clients: {len(rooms[room])}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                js = json.loads(data)
            except Exception:
                continue

            typ = js.get('type')
            if typ == 'frame':
                b64 = js.get('b64')
                if not b64:
                    continue
                img = b64_to_bgr(b64)
                payload = await process_frame_and_respond(img)
                message = json.dumps({'type': 'detection', 'payload': payload})

                # Broadcast to all sockets in this room
                to_remove = []
                for ws in list(rooms.get(room, [])):
                    try:
                        await ws.send_text(message)
                    except Exception:
                        to_remove.append(ws)
                for r in to_remove:
                    rooms[room].discard(r)

            elif typ == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))

    except WebSocketDisconnect:
        print(f"⚠️ Client disconnected from room {room}")
    finally:
        rooms.get(room, set()).discard(websocket)


if __name__ == '__main__':
    print("\nDashboard:  http://localhost:8000/")
    print("Mobile page: http://localhost:8000/mobile")
    uvicorn.run('app:app', host='0.0.0.0', port=8000, reload=False)

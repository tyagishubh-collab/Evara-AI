# Visual Aid — Laptop (server) + Mobile (camera) with Gemini (English TTS on both sides)

## Setup
1. Python 3.10+ recommended
2. Create venv and install deps:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configure Gemini key:
   ```bash
   cp .env.example .env
   # edit .env and put your GEMINI_API_KEY
   ```

## Run (with localtunnel for HTTPS on phone)
```bash
bash start_localtunnel.sh
```
- This launches the server at `http://localhost:8000` and opens a **public HTTPS** URL via localtunnel.
- On your **phone**, open: `https://<your-lt-url>/mobile?room=demo` (allow camera).
- On your **laptop**, open: `http://localhost:8000/` and click **Connect** (room: demo).

## Demo flow
- Phone: tap **Connect** → allow camera → phone starts speaking English summaries.
- Laptop: hit **Connect** → see detections + hear the same English summary.
- Both devices speak; uncheck the “Speak” checkbox to mute locally.

## Troubleshooting
- **Camera blocked on phone**: ensure you’re using the HTTPS localtunnel URL and allowed camera permissions.
- **YOLO downloads weights** on first run; keep internet on initially.
- **Gemini fallback**: if the key is missing/invalid, summaries will fallback to raw prompt (“I see …”).
- **Bandwidth**: frames are ~320×240 JPEG at ~4 fps to keep latency low.

## Notes
- Privacy: Frames are processed in-memory and not stored.
- Modular: Swap YOLO model or replace Gemini easily in `app.py`.

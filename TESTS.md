# Manual Test Cases

1) Room connectivity
- Open dashboard (localhost) and mobile (localtunnel URL) with same room id (demo).
- Expect: dashboard logs connection; summaries appear.

2) Mobile camera permission (HTTPS)
- On phone, tap Connect and allow camera.
- Expect: phone streams frames; no permission error.

3) YOLO detection
- Show a bottle/person/chair.
- Expect: dashboard logs objects with confidences; summaries mention them.

4) Gemini summary (English)
- With GEMINI_API_KEY set, summaries should be short English sentences.
- If key absent, fallback text equals prompt (“I see …”).

5) Speech on both sides
- Confirm both devices speak in English; toggle speak checkbox to mute per device.

6) Resilience
- Toggle phone screen, disconnect Wi‑Fi, reconnect.
- Expect: app handles reconnection; server remains stable.

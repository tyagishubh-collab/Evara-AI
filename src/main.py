"""Main entry point for Pathfinder."""
import cv2
import time
import signal
import sys

# Note: Import paths will work when run from project root as: python -m src.main
# For standalone, you may need to adjust sys.path

try:
    from config import VISION_MODEL, DANGER_DISTANCE_M, TTS_FORCE_SAPI, TTS_VOICE_INDEX
    from perception.detector import Detector
    from sensors.ultrasonic import Ultrasonic
    from fusion.occupancy import (
        sectors_from_detections, fuse_with_range
    )
    from i_o.tts import (
        speak, speak_async, init_tts, list_voices, set_voice,
        start_tts_worker, stop_tts_worker, adjust_rate, adjust_volume,
    )
    from i_o.haptics import Haptics
    from i_o.sos import SOS
    from i_o.stt import CommandRecognizer
    from i_o.narration import generate_sync as narr_sync
except ImportError:
    # Fallback for direct execution
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from config import VISION_MODEL, DANGER_DISTANCE_M, TTS_FORCE_SAPI, TTS_VOICE_INDEX
    from perception.detector import Detector
    from sensors.ultrasonic import Ultrasonic
    from fusion.occupancy import (
        sectors_from_detections, fuse_with_range
    )
    from i_o.tts import (
        speak, speak_async, init_tts, list_voices, set_voice,
        start_tts_worker, stop_tts_worker, adjust_rate, adjust_volume,
    )
    from i_o.haptics import Haptics
    from i_o.sos import SOS
    from i_o.stt import CommandRecognizer
    from i_o.narration import generate_sync as narr_sync

def describe(occ):
    """Generate description of occupancy state."""
    labels = []
    if occ[1]: labels.append("ahead")
    if occ[0]: labels.append("left")
    if occ[2]: labels.append("right")
    return " and ".join(labels) if labels else "clear"


def _open_camera():
    """Try multiple camera indices and backends for Windows reliability."""
    candidates = [0, 1, 2]
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]
    for idx in candidates:
        for be in backends:
            try:
                cap = cv2.VideoCapture(idx if be is None else idx, be) if be is not None else cv2.VideoCapture(idx)
                if cap.isOpened():
                    ok, _ = cap.read()
                    if ok:
                        print(f"✅ Camera opened (index={idx}, backend={'default' if be is None else be})")
                        return cap
                cap.release()
            except Exception:
                pass
    return None

def run():
    """Main processing loop matching specification."""
    print("🚀 Initializing Pathfinder MVP...")
    
    det = Detector(VISION_MODEL)
    rng = Ultrasonic()
    cap = _open_camera()
    hpx = Haptics(enabled=True)
    sos = SOS(enabled=True)
    # Start background STT listener for "help" if available
    stt = None
    try:
        from config import STT_MODEL
        stt = CommandRecognizer(model_dir=STT_MODEL, enabled=True)
    except Exception:
        stt = None
    
    if cap is None or not cap.isOpened():
        print("❌ Failed to open camera. Try freeing the webcam or a different device index.")
        return
    
    # Configure camera for stability/perf
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass

    # Initialize TTS according to config and announce readiness
    try:
        init_tts(force_sapi=TTS_FORCE_SAPI, voice_index=TTS_VOICE_INDEX)
        start_tts_worker()
    except Exception:
        pass

    print("✅ Pathfinder initialized")
    print("📹 Camera opened. Press ESC to exit")
    try:
        speak_async("Pathfinder ready")
    except Exception:
        pass
    
    last_spoken = 0
    last_haptic = 0
    last_obj_spoken = 0.0
    last_obj_key = None  # (label, sector)
    frame_count = 0
    cached_dets = []
    tts_muted = False
    current_voice_index = TTS_VOICE_INDEX if isinstance(TTS_VOICE_INDEX, int) else 0
    
    try:
        target_dt = 1.0 / 15.0  # ~15 FPS target
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            
            # Detect objects
            if frame_count % 3 == 0:
                dets = det.infer(frame, imgsz=416)
                cached_dets = dets
            else:
                dets = cached_dets
            
            # Sector analysis
            occ = sectors_from_detections(frame.shape[1], dets)
            
            # Range sensing
            dist = rng.median()
            
            # Fusion
            fused = fuse_with_range(occ, dist, DANGER_DISTANCE_M)
            
            # Rate-limited TTS
            now = time.time()
            # Prefer announcing specific object names promptly
            top = max(dets, key=lambda d: d.get("conf", 0.0), default=None)
            if top is not None:
                x1, _, x2, _ = top["bbox"]
                cx = (x1 + x2) / 2.0
                width = frame.shape[1]
                sector = "left" if cx < width/3 else ("right" if cx > 2*width/3 else "ahead")
                key = (top.get("label", "object"), sector)
                if key != last_obj_key or (now - last_obj_spoken) > 1.5:
                    # Build narration context for Gemini (optional)
                    ctx = {"label": key[0], "sector": sector, "distance_m": dist, "obstacle": True}
                    msg = narr_sync(ctx) or (
                        f"{key[0]} {sector}" + (f", {dist:.1f} meters" if dist else "")
                    )
                    if not tts_muted:
                        speak_async(msg, dedupe_window_s=0.8)
                    last_obj_key = key
                    last_obj_spoken = now
                    last_spoken = now  # also update generic timer to avoid double speak
            elif now - last_spoken > 1.2:
                # Fallback to generic occupancy summary
                ctx = {"label": "", "sector": "ahead", "distance_m": dist, "obstacle": any(fused)}
                msg = narr_sync(ctx) or (
                    f"{'Obstacle ' if any(fused) else ''}{describe(fused)}" + (f", {dist:.1f} meters" if dist else "")
                )
                if not tts_muted:
                    speak_async(msg, dedupe_window_s=1.0)
                last_spoken = now

            # Haptics at ~10 Hz
            if now - last_haptic >= 0.1:
                l = hpx.map_intensity(fused[0], dist, DANGER_DISTANCE_M)
                c = hpx.map_intensity(fused[1], dist, DANGER_DISTANCE_M)
                r = hpx.map_intensity(fused[2], dist, DANGER_DISTANCE_M)
                hpx.send(l, c, r)
                last_haptic = now
            
            # Debug visualization
            _draw_debug(frame, dets, fused, dist)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            if key == ord('s'):
                sos.press()
            if key == ord('h'):
                sos.trigger("Manual help requested")
            if key == ord('t'):
                if not tts_muted:
                    speak_async("Test: text to speech is working")
            if key == ord('m'):
                tts_muted = not tts_muted
                print(f"[TTS] {'Muted' if tts_muted else 'Unmuted'}")
                if not tts_muted:
                    speak_async("Voice unmuted")
            if key == ord('v'):
                voices = list_voices()
                if voices:
                    current_voice_index = (current_voice_index + 1) % len(voices)
                    if set_voice(current_voice_index):
                        name = voices[current_voice_index][1]
                        print(f"[TTS] Voice -> {current_voice_index}: {name}")
                        if not tts_muted:
                            speak_async(f"Voice {name}")
            if key == ord('+') or key == ord('='):
                adjust_rate(+10)
                print("[TTS] Rate +10")
            if key == ord('-'):
                adjust_rate(-10)
                print("[TTS] Rate -10")
            if key == ord(']'):
                adjust_volume(+0.05)
                print("[TTS] Volume +0.05")
            if key == ord('['):
                adjust_volume(-0.05)
                print("[TTS] Volume -0.05")
            if key == ord('1'):
                rng.set_sim_distance(0.5)
                print("[SIM] Distance set to 0.5 m")
            if key == ord('2'):
                rng.set_sim_distance(1.0)
                print("[SIM] Distance set to 1.0 m")
            if key == ord('3'):
                rng.set_sim_distance(2.0)
                print("[SIM] Distance set to 2.0 m")
            if key == ord('0'):
                rng.clear_sim_override()
                print("[SIM] Distance auto-oscillation enabled")
            
            # STT: listen for "help" every ~2s without blocking UI heavily
            if stt and (frame_count % 30 == 0):
                try:
                    cmd = stt.listen_once(timeout_s=0.8)
                    if cmd == "help":
                        sos.trigger("Voice help requested")
                except Exception:
                    pass

            # FPS throttle
            frame_count += 1
            # busy loop barrier to approximately 15 FPS
            time.sleep(max(0.0, target_dt - 0.001))
                
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        rng.cleanup()
        try:
            stop_tts_worker()
        except Exception:
            pass
        print("✅ Cleanup complete")
    

def _draw_debug(frame, detections, occupancy, distance):
    """Draw debug visualization."""
    # Draw detections
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = det.get("label", f"cls_{det.get('cls', '?')}")
        cv2.putText(frame, label, (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Draw sectors
    width = frame.shape[1]
    cv2.line(frame, (width//3, 0), (width//3, frame.shape[0]), (255, 0, 0), 2)
    cv2.line(frame, (2*width//3, 0), (2*width//3, frame.shape[0]), (255, 0, 0), 2)
    
    # Draw occupancy
    colors = [(0, 0, 255) if occ else (0, 255, 0) for occ in occupancy]
    for i, color in enumerate(colors):
        x = (i * width // 3) + (width // 6)
        cv2.circle(frame, (x, frame.shape[0]//2), 30, color, -1)
    
    # Draw distance
    if distance:
        cv2.putText(frame, f"{distance:.1f}m", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow("Pathfinder Debug", frame)


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C)."""
    print("\n⚠️ Shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    run()

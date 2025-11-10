"""Text-to-speech using offline pyttsx3."""

_engine = None
_queue = None
_worker = None
_stop_flag = False
_last_text = ""
_last_time = 0.0

def init_tts(force_sapi: bool = False, voice_index: int | None = None):
    """Initialize the TTS engine with optional SAPI forcing and voice selection."""
    global _engine
    if _engine is not None:
        if voice_index is not None:
            set_voice(voice_index)
        return
    try:
        import pyttsx3, platform
        driver = 'sapi5' if (force_sapi and platform.system() == 'Windows') else None
        _engine = pyttsx3.init(driver) if driver else pyttsx3.init()
        if voice_index is not None:
            set_voice(voice_index)
    except Exception:
        # Defer to lazy init in speak()
        _engine = None

def start_tts_worker():
    """Start background TTS worker thread (idempotent)."""
    global _queue, _worker, _stop_flag
    if _worker is not None:
        return
    import queue, threading
    _queue = queue.Queue(maxsize=16)
    _stop_flag = False
    def _run():
        import time
        while not _stop_flag:
            try:
                text = _queue.get(timeout=0.1)
            except Exception:
                continue
            try:
                speak(text)
            except Exception:
                pass
            finally:
                _queue.task_done()
            time.sleep(0.01)
    _worker = threading.Thread(target=_run, daemon=True)
    _worker.start()

def stop_tts_worker():
    """Signal worker to stop."""
    global _stop_flag
    _stop_flag = True

def list_voices():
    """Return a list of available voice names and ids."""
    try:
        import pyttsx3
        eng = _engine or pyttsx3.init()
        voices = eng.getProperty('voices') or []
        return [(i, getattr(v, 'name', str(i)), getattr(v, 'id', '')) for i, v in enumerate(voices)]
    except Exception:
        return []

def set_voice(index: int) -> bool:
    """Set current voice by index. Returns True on success."""
    global _engine
    try:
        import pyttsx3
        if _engine is None:
            _engine = pyttsx3.init()
        voices = _engine.getProperty('voices') or []
        if 0 <= index < len(voices):
            _engine.setProperty('voice', voices[index].id)
            return True
    except Exception:
        pass
    return False

def speak(text: str):
    """
    Speak text using offline TTS engine.
    
    Args:
        text: Text to speak
    """
    global _engine
    
    if not text:
        return
    
    try:
        # If force-SAPI is enabled on Windows, use direct SAPI and return
        try:
            from config import TTS_FORCE_SAPI
        except Exception:
            TTS_FORCE_SAPI = False
        if TTS_FORCE_SAPI:
            import platform
            if platform.system() == 'Windows':
                print(f"[TTS:SAPI] {text}")
                import comtypes.client as cc
                voice = cc.CreateObject("SAPI.SpVoice")
                voice.Speak(text)
                return

        if _engine is None:
            # Lazy init, honoring config if available
            try:
                from config import TTS_FORCE_SAPI as _F, TTS_VOICE_INDEX as _V
            except Exception:
                _F, _V = False, None
            init_tts(_F, _V)
            if _engine is None:
                import pyttsx3
                globals()["_engine"] = pyttsx3.init()
        
        # Primary path (pyttsx3)
        print(f"[TTS] {text}")
        _engine.say(text)
        _engine.runAndWait()
    except ImportError:
        print(f"⚠️ pyttsx3 not installed. Install: pip install pyttsx3")
        print(f"[TTS] {text}")  # Fallback to print
    except Exception as e:
        print(f"⚠️ TTS error: {e} — trying SAPI fallback")
        # Windows-specific SAPI fallback via comtypes
        try:
            import platform
            if platform.system() == 'Windows':
                import comtypes.client as cc
                voice = cc.CreateObject("SAPI.SpVoice")
                # Do not override user preferences aggressively; use SAPI defaults
                voice.Speak(text)
                return
        except Exception as e2:
            print(f"⚠️ SAPI fallback failed: {e2}")
        # Final fallback: print only
        print(f"[TTS] {text}")

def speak_async(text: str, dedupe_window_s: float = 1.0):
    """Queue a phrase for speaking without blocking the main loop.
    Dedupe identical phrases within a short window to avoid chatter.
    """
    global _queue, _last_text, _last_time
    if not text:
        return
    try:
        import time
        now = time.time()
        if text == _last_text and (now - _last_time) < dedupe_window_s:
            return
        _last_text, _last_time = text, now
        if _queue is None:
            start_tts_worker()
        # Drop if queue full to avoid backlog
        try:
            _queue.put_nowait(text)
        except Exception:
            pass
    except Exception:
        # Fallback to sync speak on error
        speak(text)

def adjust_rate(delta: int):
    """Adjust speaking rate relatively."""
    global _engine
    try:
        if _engine is None:
            init_tts()
        rate = int(_engine.getProperty('rate'))
        _engine.setProperty('rate', max(80, min(300, rate + delta)))
    except Exception:
        pass

def adjust_volume(delta: float):
    """Adjust volume relatively (0.0-1.0)."""
    global _engine
    try:
        if _engine is None:
            init_tts()
        vol = float(_engine.getProperty('volume'))
        _engine.setProperty('volume', max(0.0, min(1.0, vol + delta)))
    except Exception:
        pass

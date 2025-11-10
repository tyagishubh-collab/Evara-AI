import threading
import time
from typing import Optional, Dict, Any

try:
    from config import GEMINI_API_KEY, USE_GEMINI
except Exception:
    GEMINI_API_KEY = None
    USE_GEMINI = False

# Lazy holder for the Gemini client, only if available
_gemini_client = None
_gemini_ready = False
_gemini_warned = False


def _ensure_gemini():
    global _gemini_client, _gemini_ready, _gemini_warned
    if _gemini_ready:
        return True
    if not USE_GEMINI or not GEMINI_API_KEY:
        return False
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        # Choose a lightweight text model
        _gemini_client = genai.GenerativeModel("gemini-1.5-flash")
        _gemini_ready = True
        return True
    except Exception:
        if not _gemini_warned:
            print("⚠️ Gemini client not available. Install: pip install google-generativeai")
            _gemini_warned = True
        return False


def _build_prompt(context: Dict[str, Any]) -> str:
    # Keep the prompt short and deterministic to reduce latency
    label = context.get("label", "object")
    sector = context.get("sector", "ahead")
    dist = context.get("distance_m")
    obstacle = context.get("obstacle", True)
    base = f"{label} {sector}"
    if isinstance(dist, (int, float)):
        base += f", {dist:.1f} meters"
    if not obstacle:
        base = f"clear {sector}"
    return (
        "You are a navigation assistant for a visually impaired user. "
        "Speak one very short phrase (max 6 words), no punctuation other than commas. "
        "Say the object and direction; include distance like '1.2 meters' if provided. "
        f"Context: {base}."
    )


def generate_sync(context: Dict[str, Any], timeout_s: float = 0.25) -> Optional[str]:
    """Try to get a concise narration from Gemini quickly. Return None if not ready or slow."""
    if not _ensure_gemini():
        return None
    try:
        prompt = _build_prompt(context)
        start = time.time()
        resp = _gemini_client.generate_content(prompt)
        if time.time() - start > timeout_s:
            return None
        text = (resp.text or "").strip()
        # Safety: cap length
        return text[:80] if text else None
    except Exception:
        return None


def generate_async(context: Dict[str, Any], speak_fn, delay_fallback: Optional[str] = None):
    """Fire-and-forget: ask Gemini and speak when ready. Optionally speak a fallback now."""
    if delay_fallback:
        try:
            speak_fn(delay_fallback)
        except Exception:
            pass
    if not _ensure_gemini():
        return

    def _worker():
        text = generate_sync(context, timeout_s=2.5)
        if text:
            try:
                speak_fn(text)
            except Exception:
                pass
    threading.Thread(target=_worker, daemon=True).start()

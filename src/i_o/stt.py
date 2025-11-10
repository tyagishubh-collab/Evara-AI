from typing import Optional

COMMANDS = {"left", "right", "stop", "repeat"}

class CommandRecognizer:
    def __init__(self, model_dir: str | None = None, enabled: bool = True):
        self.model_dir = model_dir
        self.enabled = enabled
        self._vosk_ready = False
        self._warned = False

    def _ensure_model(self):
        if not self.enabled or self._vosk_ready:
            return
        try:
            import vosk  # noqa: F401
            self._vosk_ready = True
        except Exception:
            if not self._warned:
                print("⚠️ Vosk not available; STT disabled")
                self._warned = True
            self.enabled = False

    def listen_once(self, timeout_s: float = 2.0) -> Optional[str]:
        self._ensure_model()
        if not self.enabled:
            return None
        try:
            import vosk, sounddevice as sd, json
            model = vosk.Model(self.model_dir) if self.model_dir else vosk.Model()
            rec = vosk.KaldiRecognizer(model, 16000)
            rec.SetWords(False)

            def callback(indata, frames, time, status):  # noqa: ARG001
                if rec.AcceptWaveform(indata.tobytes()):
                    pass

            with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
                sd.sleep(int(timeout_s * 1000))

            try:
                res = rec.Result()
                parsed = json.loads(res)
                text = parsed.get("text", "").strip().lower()
            except Exception:
                text = ""

            for cmd in COMMANDS:
                if cmd in text:
                    return cmd
            return None
        except Exception:
            if not self._warned:
                print("⚠️ STT runtime error; disabling STT")
                self._warned = True
            self.enabled = False
            return None

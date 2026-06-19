"""
Ditado por voz local (estilo Wispr Flow), com faster-whisper.

Fica residente na bandeja do sistema. Voce aperta um atalho global para
COMECAR a gravar, fala a vontade, aperta o MESMO atalho de novo para PARAR;
ai ele transcreve o trecho inteiro e digita o texto no app que estiver em foco
(via colar do clipboard, que e robusto para acentuacao PT).

    Modo de ativacao : toggle (aperta liga / aperta desliga)
    Saida            : texto limpo, injetado de uma vez ao parar
    Modelo           : mesmo do transcrever.py (large-v3-turbo, cuda, int8_float16, pt)

Uso:
    ditar                      # inicia o daemon (atalho default: ctrl+alt+space)
    ditar --hotkey ctrl+alt+d  # outro atalho
    ditar --check              # so verifica dependencias + carrega o modelo e sai
    ditar --no-tray            # sem icone na bandeja (so console + atalho)

Atalho default: CTRL+ALT+ESPACO para ligar/desligar a gravacao.
Para sair: menu do icone na bandeja -> Sair, ou Ctrl+C no console.
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

# Reusa a injecao das DLLs do cuBLAS/cuDNN/nvrtc do transcrever.py (importar o
# modulo ja roda _add_cuda_dlls_to_path() no nivel de modulo) para o CUDA achar
# as libs instaladas via pip. Mantem uma fonte unica de verdade dessa logica.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import transcrever  # noqa: E402  (efeito colateral: configura PATH das DLLs CUDA)

import numpy as np  # noqa: E402
import sounddevice as sd  # noqa: E402
import keyboard  # noqa: E402
import pyperclip  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

try:
    import winsound  # built-in no Windows
except ImportError:  # pragma: no cover
    winsound = None


SAMPLE_RATE = 16_000  # faster-whisper espera 16 kHz mono float32 em [-1, 1]


# ---------------------------------------------------------------------------
# Estado global do daemon
# ---------------------------------------------------------------------------
class Ditador:
    def __init__(self, model: WhisperModel, language: str | None, use_tray: bool):
        self.model = model
        self.language = language
        self.use_tray = use_tray

        self._lock = threading.Lock()
        self._state = "idle"            # idle | recording | transcribing
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._tray = None               # pystray.Icon, se houver

    # -- feedback sonoro (nao bloqueia o fluxo) -----------------------------
    @staticmethod
    def _beep(freq: int, dur: int) -> None:
        if winsound is None:
            return
        threading.Thread(
            target=lambda: winsound.Beep(freq, dur), daemon=True
        ).start()

    # -- captura do microfone ----------------------------------------------
    def _on_audio(self, indata, frames, time_info, status) -> None:
        # roda na thread do PortAudio; so acumula os blocos
        if status:
            # overflow/underflow ocasional nao e fatal para ditado curto
            pass
        self._frames.append(indata.copy())

    def _start_recording(self) -> None:
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._on_audio,
        )
        self._stream.start()

    def _stop_recording(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._frames, axis=0).flatten()

    # -- transcricao + injecao ---------------------------------------------
    def _transcribe(self, audio: np.ndarray) -> str:
        if audio.size < SAMPLE_RATE // 5:  # < 0.2s -> ignora
            return ""
        segments, _info = self.model.transcribe(
            audio,
            language=self.language,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        return " ".join(seg.text.strip() for seg in segments).strip()

    @staticmethod
    def _inject(text: str) -> None:
        """Cola o texto no app em foco via clipboard + Ctrl+V e restaura o clipboard."""
        if not text:
            return
        try:
            saved = pyperclip.paste()
        except Exception:
            saved = ""
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            keyboard.send("ctrl+v")
            time.sleep(0.20)  # da tempo do app processar o paste antes de restaurar
        finally:
            try:
                pyperclip.copy(saved)
            except Exception:
                pass

    def _do_transcribe(self, audio: np.ndarray) -> None:
        try:
            t0 = time.time()
            text = self._transcribe(audio)
            if text:
                self._inject(text)
                dur = audio.size / SAMPLE_RATE
                print(
                    f"[ditar] {dur:.1f}s de audio -> '{text}' "
                    f"(transcrito em {time.time() - t0:.1f}s)"
                )
            else:
                print("[ditar] nada reconhecido (silencio/trecho curto).")
        except Exception as e:  # nao derruba o daemon por um erro pontual
            print(f"[ditar] erro na transcricao: {e}", file=sys.stderr)
        finally:
            with self._lock:
                self._state = "idle"
            self._refresh_tray()

    # -- maquina de estados (toggle) ---------------------------------------
    def toggle(self) -> None:
        with self._lock:
            state = self._state
            if state == "idle":
                self._state = "recording"
                self._start_recording()
                self._beep(880, 120)
                print("[ditar] gravando... (aperte o atalho de novo para parar)")
                self._refresh_tray()
                return
            if state == "recording":
                self._state = "transcribing"
                self._beep(440, 120)
                audio = self._stop_recording()
                print("[ditar] transcrevendo...")
                self._refresh_tray()
                threading.Thread(
                    target=self._do_transcribe, args=(audio,), daemon=True
                ).start()
                return
            # state == "transcribing": ignora o toggle ate terminar

    # -- icone na bandeja ---------------------------------------------------
    def _tray_image(self):
        from PIL import Image, ImageDraw

        colors = {
            "idle": (90, 120, 200),        # azul: pronto
            "recording": (220, 60, 60),    # vermelho: gravando
            "transcribing": (230, 160, 40),  # laranja: processando
        }
        color = colors.get(self._state, (120, 120, 120))
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((8, 8, 56, 56), fill=color)
        # glifo simples de microfone
        d.rounded_rectangle((27, 18, 37, 40), radius=5, fill=(255, 255, 255))
        d.line((32, 40, 32, 48), fill=(255, 255, 255), width=3)
        d.line((24, 48, 40, 48), fill=(255, 255, 255), width=3)
        return img

    def _tray_title(self) -> str:
        return {
            "idle": "Ditar: pronto",
            "recording": "Ditar: GRAVANDO",
            "transcribing": "Ditar: transcrevendo...",
        }.get(self._state, "Ditar")

    def _refresh_tray(self) -> None:
        if self._tray is None:
            return
        try:
            self._tray.icon = self._tray_image()
            self._tray.title = self._tray_title()
        except Exception:
            pass

    def run_tray(self) -> None:
        import pystray

        menu = pystray.Menu(
            pystray.MenuItem("Ligar/Desligar gravacao", lambda: self.toggle()),
            pystray.MenuItem("Sair", lambda icon: icon.stop()),
        )
        self._tray = pystray.Icon(
            "ditar", self._tray_image(), self._tray_title(), menu
        )
        self._tray.run()  # bloqueia na thread principal ate "Sair"


# ---------------------------------------------------------------------------
def load_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
    print(
        f"[ditar] carregando modelo: {model_name} | device: {device} | "
        f"compute_type: {compute_type}"
    )
    t0 = time.time()
    try:
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
    except Exception as e:
        msg = str(e).lower()
        if device == "cuda" and ("cuda" in msg or "cublas" in msg or "cudnn" in msg):
            print(f"[ditar] erro CUDA ({e}); caindo para CPU/medium.", file=sys.stderr)
            model = WhisperModel("medium", device="cpu", compute_type="int8")
        else:
            raise
    print(f"[ditar] modelo carregado em {time.time() - t0:.1f}s")
    return model


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ditado por voz local (toggle) com faster-whisper.")
    p.add_argument(
        "--hotkey",
        default="ctrl+alt+space",
        help="atalho global para ligar/desligar a gravacao (default: ctrl+alt+space)",
    )
    p.add_argument("--model", default="large-v3-turbo", help="modelo (default: large-v3-turbo)")
    p.add_argument("--language", default="pt", help="idioma (default: pt; 'auto' p/ detectar)")
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu", "auto"])
    p.add_argument(
        "--compute-type",
        default=None,
        help="tipo numerico (default: int8_float16 em cuda, int8 em cpu)",
    )
    p.add_argument("--no-tray", action="store_true", help="rodar sem icone na bandeja")
    p.add_argument(
        "--check",
        action="store_true",
        help="so verifica dependencias + carrega o modelo e sai (nao inicia o daemon)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    language = None if args.language.lower() == "auto" else args.language
    compute_type = args.compute_type or (
        "int8_float16" if args.device == "cuda" else "int8"
    )

    model = load_model(args.model, args.device, compute_type)

    if args.check:
        # mini smoke-test: transcreve 0.5s de silencio so para exercitar o caminho
        _seg, _info = model.transcribe(np.zeros(SAMPLE_RATE // 2, dtype=np.float32),
                                       language=language)
        list(_seg)
        print("[ditar] OK: dependencias e modelo prontos.")
        return

    use_tray = not args.no_tray
    ditador = Ditador(model, language=language, use_tray=use_tray)

    keyboard.add_hotkey(args.hotkey, ditador.toggle)
    print(f"[ditar] pronto. Atalho: {args.hotkey.upper()} para ligar/desligar.")
    print("[ditar] fale apos o bipe agudo; aperte de novo para transcrever e digitar.")

    if use_tray:
        try:
            ditador.run_tray()  # bloqueia ate "Sair"
        except Exception as e:
            print(f"[ditar] sem bandeja ({e}); rodando so com o atalho. Ctrl+C para sair.")
            keyboard.wait()
    else:
        print("[ditar] Ctrl+C para sair.")
        keyboard.wait()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        # faster-whisper/CTranslate2 podem crashar no teardown do contexto CUDA no
        # Windows (mesmo motivo do transcrever.py); encerra limpo apos o trabalho.
        sys.stdout.flush()
        sys.stderr.flush()
        import os
        os._exit(0)

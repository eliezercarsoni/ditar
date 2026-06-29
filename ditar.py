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
import firstrun  # noqa: E402  (garante o modelo no cache; splash de download no 1o uso)
import config  # noqa: E402   (preferencias persistentes: mic, som, atalho)
import hud  # noqa: E402       (HUD flutuante "Ouvindo.../Escrevendo...")
import version  # noqa: E402   (versao do app, p/ auto-update)
import updater  # noqa: E402   (auto-update via GitHub Releases — ADR-0003/0004)
import db  # noqa: E402         (historico de ditados em SQLite)

import numpy as np  # noqa: E402
import sounddevice as sd  # noqa: E402
import keyboard  # noqa: E402
import pyperclip  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402


SAMPLE_RATE = 16_000  # faster-whisper espera 16 kHz mono float32 em [-1, 1]


def _soft_cue(start: bool, enabled: bool) -> None:
    """Som curto e suave (seno com fade) ao iniciar/parar — substitui o bip agudo."""
    if not enabled:
        return

    def _play() -> None:
        try:
            sr = 44_100
            dur = 0.14
            freq = 587.33 if start else 415.30  # sobe ao gravar, desce ao parar
            t = np.linspace(0, dur, int(sr * dur), endpoint=False)
            env = np.ones_like(t)
            a, d = int(0.02 * sr), int(0.06 * sr)
            env[:a] = np.linspace(0, 1, a)
            env[-d:] = np.linspace(1, 0, d)
            wave = (0.07 * np.sin(2 * np.pi * freq * t) * env).astype(np.float32)
            sd.play(wave, sr)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def _foreground_app() -> str:
    """Titulo da janela em foco (onde o texto sera colado) — p/ rotular o historico."""
    try:
        import ctypes

        u = ctypes.windll.user32
        hwnd = u.GetForegroundWindow()
        n = u.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value or ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Estado global do daemon
# ---------------------------------------------------------------------------
class Ditador:
    def __init__(self, model: WhisperModel, language: str | None, use_tray: bool,
                 sound: bool = True, mic_device: int | None = None,
                 hotkey: str = "ctrl+alt+d", hud_ctl: "hud.HUD | None" = None,
                 model_name: str = ""):
        self.model = model
        self.language = language
        self.use_tray = use_tray
        self.sound = sound
        self.mic_device = mic_device
        self.hotkey = hotkey
        self._hud = hud_ctl
        self.model_name = model_name

        self._lock = threading.Lock()
        self._state = "idle"            # idle | recording | transcribing
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._tray = None               # pystray.Icon, se houver

    # -- captura do microfone ----------------------------------------------
    def _on_audio(self, indata, frames, time_info, status) -> None:
        # roda na thread do PortAudio; so acumula os blocos
        if status:
            # overflow/underflow ocasional nao e fatal para ditado curto
            pass
        self._frames.append(indata.copy())

    def _start_recording(self) -> None:
        # rele a config a cada gravacao p/ refletir mudancas da janela de Configuracoes
        try:
            cfg = config.load()
            self.mic_device = cfg.get("mic_device")
            self.sound = bool(cfg.get("sound", True))
        except Exception:
            pass
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=self.mic_device,
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
                app = _foreground_app()
                self._inject(text)
                db.add(text, app=app, model=self.model_name)  # historico (nao derruba o fluxo)
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
                _soft_cue(True, self.sound)
                print("[ditar] gravando... (aperte o atalho de novo para parar)")
                self._refresh_tray()
                return
            if state == "recording":
                self._state = "transcribing"
                _soft_cue(False, self.sound)
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
        # HUD reflete o mesmo estado (thread-safe); chamado em toda transicao.
        if self._hud is not None:
            try:
                self._hud.set_state(self._state)
            except Exception:
                pass
        if self._tray is None:
            return
        try:
            self._tray.icon = self._tray_image()
            self._tray.title = self._tray_title()
        except Exception:
            pass

    # -- modo "segurar para falar" (push-to-talk) ---------------------------
    def hold_press(self) -> None:
        """Disparado ao apertar o atalho: comeca a gravar; uma thread espera soltar."""
        started = False
        with self._lock:
            if self._state == "idle":
                self._state = "recording"
                self._start_recording()
                _soft_cue(True, self.sound)
                print("[ditar] gravando (segure e fale)...")
                self._refresh_tray()
                started = True
        if started:
            threading.Thread(target=self._hold_monitor, daemon=True).start()

    def _hold_monitor(self) -> None:
        keys = [k.strip() for k in self.hotkey.split("+") if k.strip()]
        t0 = time.time()
        MAX_S = 60.0  # failsafe: nao grava pra sempre se o "soltar" se perder
        while time.time() - t0 < MAX_S:
            try:
                if not all(keyboard.is_pressed(k) for k in keys):
                    break
            except Exception:
                break
            time.sleep(0.03)
        self._hold_release()

    def _hold_release(self) -> None:
        with self._lock:
            if self._state != "recording":
                return
            self._state = "transcribing"
            _soft_cue(False, self.sound)
            audio = self._stop_recording()
            print("[ditar] transcrevendo...")
            self._refresh_tray()
        threading.Thread(target=self._do_transcribe, args=(audio,), daemon=True).start()

    @staticmethod
    def _spawn_self(extra_args: list[str]) -> None:
        """Lanca outra instancia do Ditar com flags (Tk/checagens em processo separado, sem CUDA)."""
        import subprocess

        try:
            if getattr(sys, "frozen", False):
                subprocess.Popen([sys.executable, *extra_args])
            else:
                subprocess.Popen([sys.executable, str(Path(__file__).resolve()), *extra_args])
        except Exception as e:
            print(f"[ditar] nao consegui lancar {extra_args}: {e}", file=sys.stderr)

    def run_tray(self) -> None:
        import pystray

        menu = pystray.Menu(
            pystray.MenuItem("Ligar/Desligar gravacao", lambda: self.toggle()),
            pystray.MenuItem("Configuracoes...", lambda: self._spawn_self(["--settings"])),
            pystray.MenuItem("Historico", lambda: self._spawn_self(["--history"])),
            pystray.MenuItem("Verificar atualizacoes", lambda: self._spawn_self(["--check-update"])),
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


def _setup_frozen_logging() -> None:
    """No bundle windowed (console=False) nao ha stdout/stderr; redireciona p/ um log.

    So age no executavel congelado E quando o subsistema GUI zerou os fluxos padrao;
    no venv ou no bundle com console (spike) nao mexe em nada.
    """
    if not getattr(sys, "frozen", False):
        return
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        import os
        logdir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Ditar"
        logdir.mkdir(parents=True, exist_ok=True)
        logfile = open(logdir / "ditar.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = logfile
        sys.stderr = logfile
        print(f"\n===== sessao {time.strftime('%Y-%m-%d %H:%M:%S')} =====")
    except Exception:
        pass


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ditado por voz local (toggle) com faster-whisper.")
    p.add_argument(
        "--hotkey",
        default="ctrl+alt+d",
        help="atalho global p/ ligar/desligar (default: ctrl+alt+d; config.json tem prioridade)",
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
    p.add_argument("--list-mics", action="store_true", help="lista os microfones e sai")
    p.add_argument("--settings", action="store_true", help="abre a janela de configuracoes e sai")
    p.add_argument("--mic", type=int, default=None, metavar="N",
                   help="define o microfone (indice de --list-mics), salva e sai")
    p.add_argument("--history", action="store_true", help="abre a janela de historico e sai")
    p.add_argument("--onboarding", action="store_true", help="abre a tela de boas-vindas e sai")
    p.add_argument("--check-update", action="store_true", help="checa atualizacao e mostra o resultado")
    p.add_argument("--silent-if-current", action="store_true",
                   help="com --check-update: nao mostra nada se ja estiver atualizado")
    return p.parse_args()


def _print_mics() -> None:
    default_in = sd.default.device[0] if isinstance(sd.default.device, (list, tuple)) else None
    print("[ditar] microfones de entrada disponiveis:")
    for i, d in enumerate(sd.query_devices()):
        if d.get("max_input_channels", 0) > 0:
            mark = "  <- padrao do Windows" if i == default_in else ""
            print(f"  [{i}] {d['name']}{mark}")
    print("\nDefina com: Ditar --mic <N>   (ou pelo menu Configuracoes da bandeja)")


def _acquire_single_instance() -> bool:
    """True se somos a unica instancia do daemon; False se ja existe outra rodando.

    Usa um mutex nomeado do Windows (liberado automaticamente quando o processo morre).
    Evita dois daemons competindo pelo mesmo atalho global.
    """
    try:
        import ctypes
        from ctypes import wintypes

        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateMutexW.restype = wintypes.HANDLE
        k.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        k.CreateMutexW(None, False, "DitarVoiceDaemonSingleton")  # handle vaza de proposito (vive ate sair)
        return ctypes.get_last_error() != 183  # 183 = ERROR_ALREADY_EXISTS
    except Exception:
        return True  # na duvida, deixa rodar


def main() -> None:
    _setup_frozen_logging()
    args = parse_args()

    # Modos que nao precisam do modelo/CUDA — resolvem e saem cedo.
    if args.list_mics:
        _print_mics()
        return
    if args.settings:
        import settings
        settings.open_settings()
        return
    if args.mic is not None:
        cfg = config.load()
        cfg["mic_device"] = args.mic
        config.save(cfg)
        print(f"[ditar] microfone definido para o indice {args.mic} (salvo em config.json).")
        return
    if args.history:
        import history
        history.open_history()
        return
    if args.onboarding:
        import onboarding
        onboarding.open_onboarding()
        return
    if args.check_update:
        updater.show_result(version.VERSION, silent_if_current=args.silent_if_current)
        return

    cfg = config.load()

    # Uma instancia so do daemon (evita dois competindo pelo mesmo atalho). --check passa direto.
    if not args.check and not _acquire_single_instance():
        print("[ditar] ja esta aberto (outra instancia em execucao). Saindo.")
        return

    language = None if args.language.lower() == "auto" else args.language
    compute_type = args.compute_type or (
        "int8_float16" if args.device == "cuda" else "int8"
    )

    # 1o uso (modelo ainda nao baixado): mostra splash de progresso em vez de "travar".
    firstrun.ensure_model(args.model)

    model = load_model(args.model, args.device, compute_type)

    if args.check:
        # mini smoke-test: transcreve 0.5s de silencio so para exercitar o caminho
        _seg, _info = model.transcribe(np.zeros(SAMPLE_RATE // 2, dtype=np.float32),
                                       language=language)
        list(_seg)
        print("[ditar] OK: dependencias e modelo prontos.")
        return

    use_tray = not args.no_tray
    hotkey = cfg.get("hotkey") or args.hotkey
    mode = (cfg.get("mode") or "toggle").lower()

    # HUD flutuante (so no modo GUI/bandeja) — thread dedicada, ver hud.py.
    the_hud = None
    if use_tray:
        the_hud = hud.HUD()
        the_hud.start()

    ditador = Ditador(model, language=language, use_tray=use_tray,
                      sound=bool(cfg.get("sound", True)), mic_device=cfg.get("mic_device"),
                      hotkey=hotkey, hud_ctl=the_hud, model_name=args.model)

    def _apply_activation(hk: str, md: str) -> str:
        """(Re)registra o atalho conforme o modo. Pode ser chamado ao vivo."""
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass  # keyboard 0.13.5 levanta AttributeError se nada foi registrado ainda
        ditador.hotkey = hk
        if md == "hold":
            keyboard.add_hotkey(hk, ditador.hold_press, trigger_on_release=False)
            return "SEGURAR p/ falar"
        keyboard.add_hotkey(hk, ditador.toggle)
        return "toggle (aperta/aperta)"

    modo_txt = _apply_activation(hotkey, mode)
    mic_txt = "padrao do Windows" if cfg.get("mic_device") is None else f"indice {cfg['mic_device']}"
    print(f"[ditar] pronto. Atalho: {hotkey.upper()} | modo: {modo_txt} | mic: {mic_txt}.")

    # Aplica mudancas de Configuracoes AO VIVO (sem reiniciar): observa o config.json.
    def _watch_config() -> None:
        try:
            last_m = config.CONFIG_PATH.stat().st_mtime
        except Exception:
            last_m = 0.0
        applied = (mode, hotkey)
        while True:
            time.sleep(1.5)
            try:
                m = config.CONFIG_PATH.stat().st_mtime
            except Exception:
                continue
            if m == last_m:
                continue
            last_m = m
            c = config.load()
            nm = (c.get("mode") or "toggle").lower()
            nh = c.get("hotkey") or hotkey
            if (nm, nh) != applied:
                t = _apply_activation(nh, nm)
                applied = (nm, nh)
                print(f"[ditar] config aplicada ao vivo: modo {t}, atalho {nh.upper()}.")

    threading.Thread(target=_watch_config, daemon=True).start()

    # Auto-check de atualizacao no startup (subprocesso; so avisa se houver versao nova).
    ditador._spawn_self(["--check-update", "--silent-if-current"])

    # 1o uso: tela de boas-vindas / privacidade (uma vez so).
    if not cfg.get("onboarded"):
        ditador._spawn_self(["--onboarding"])
        cfg["onboarded"] = True
        config.save(cfg)

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
        # Encerra via TerminateProcess (transcrever.hard_exit): evita o crash de
        # teardown do contexto CUDA no Windows, depois do trabalho ja feito.
        transcrever.hard_exit(0)

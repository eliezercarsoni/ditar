"""
Configuracao persistente do Ditar em %LOCALAPPDATA%\\Ditar\\config.json.

Fonte unica das preferencias do usuario (microfone, modo de ativacao, atalho, som).
Tolerante a arquivo ausente/corrompido: sempre devolve os defaults preenchidos.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Ditar"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS: dict = {
    "mic_device": None,          # None = dispositivo padrao do Windows; ou indice (int)
    "mode": "toggle",            # "toggle" | "hold" (hold chega na fatia 2)
    "hotkey": "ctrl+alt+d",      # ctrl+alt+space colidia com o atalho global do Claude Desktop
    "sound": True,               # som suave ao gravar/parar
    "model": "large-v3-turbo",   # modelo faster-whisper (troca exige reiniciar o Ditar)
    "language": "pt",            # "pt" | "en" | "auto" (auto = detectar; aplica ao vivo)
    "onboarded": False,          # tela de boas-vindas (privacidade) ja foi mostrada?
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    except Exception:
        pass
    return cfg


def save(cfg: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        clean = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
        CONFIG_PATH.write_text(
            json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass

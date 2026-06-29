"""
Janela de configuracoes do Ditar (Tk). Roda como invocacao SEPARADA (`--settings`),
sem carregar CUDA — evita o conflito Tk+pystray+CUDA no processo do daemon. O daemon
abre esta janela como subprocesso (menu da bandeja → "Configuracoes").

Fatia 1: escolher microfone + ligar/desligar som. (Modo hold/toggle e HUD: fatia 2.)
"""

from __future__ import annotations

import config


def _input_devices() -> list[tuple[int, str]]:
    import sounddevice as sd

    out = []
    for i, d in enumerate(sd.query_devices()):
        if d.get("max_input_channels", 0) > 0:
            out.append((i, d["name"]))
    return out


def open_settings() -> None:
    import tkinter as tk
    from tkinter import ttk

    cfg = config.load()
    devices = _input_devices()

    root = tk.Tk()
    root.title("Ditar — Configuracoes")
    root.resizable(False, False)
    frm = ttk.Frame(root, padding=16)
    frm.grid()

    ttk.Label(frm, text="Microfone de entrada", font=("Segoe UI", 10, "bold")).grid(
        column=0, row=0, sticky="w"
    )
    options = ["(padrao do Windows)"] + [f"[{i}] {n}" for i, n in devices]
    var_mic = tk.StringVar()
    cur = cfg.get("mic_device")
    if cur is None:
        var_mic.set(options[0])
    else:
        var_mic.set(next((o for o in options if o.startswith(f"[{cur}]")), options[0]))
    ttk.Combobox(frm, values=options, textvariable=var_mic, state="readonly", width=50).grid(
        column=0, row=1, sticky="we", pady=(2, 12)
    )

    ttk.Label(frm, text="Atalho", font=("Segoe UI", 10, "bold")).grid(column=0, row=2, sticky="w")
    var_hotkey = tk.StringVar(value=str(cfg.get("hotkey", "ctrl+alt+d")))
    ttk.Entry(frm, textvariable=var_hotkey, width=24).grid(column=0, row=3, sticky="w", pady=(2, 2))
    ttk.Label(frm, text="ex.: ctrl+alt+d  (evite ctrl+alt+space — e do Claude).",
              foreground="#888").grid(column=0, row=4, sticky="w", pady=(0, 12))

    ttk.Label(frm, text="Modo de ativacao", font=("Segoe UI", 10, "bold")).grid(
        column=0, row=5, sticky="w")
    var_mode = tk.StringVar(value=("hold" if cfg.get("mode") == "hold" else "toggle"))
    ttk.Radiobutton(frm, text="Toggle — aperta para iniciar, aperta de novo para parar",
                    variable=var_mode, value="toggle").grid(column=0, row=6, sticky="w")
    ttk.Radiobutton(frm, text="Segurar — segura o atalho enquanto fala, solta para transcrever",
                    variable=var_mode, value="hold").grid(column=0, row=7, sticky="w", pady=(0, 12))

    var_sound = tk.BooleanVar(value=bool(cfg.get("sound", True)))
    ttk.Checkbutton(frm, text="Som suave ao gravar / parar", variable=var_sound).grid(
        column=0, row=8, sticky="w", pady=(0, 12)
    )

    status = ttk.Label(frm, text="", foreground="#2a7")
    status.grid(column=0, row=10, sticky="w", pady=(8, 0))

    def salvar() -> None:
        sel = var_mic.get()
        cfg["mic_device"] = None if sel.startswith("(padrao") else int(sel.split("]")[0][1:])
        cfg["sound"] = bool(var_sound.get())
        cfg["mode"] = var_mode.get()
        hk = var_hotkey.get().strip().lower()
        if hk:
            cfg["hotkey"] = hk
        config.save(cfg)
        status.config(text="Salvo. Aplica em ~2s, sem reiniciar o Ditar.")

    btns = ttk.Frame(frm)
    btns.grid(column=0, row=9, sticky="w")
    ttk.Button(btns, text="Salvar", command=salvar).grid(column=0, row=0)
    ttk.Button(btns, text="Fechar", command=root.destroy).grid(column=1, row=0, padx=(8, 0))

    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    root.mainloop()


if __name__ == "__main__":
    open_settings()

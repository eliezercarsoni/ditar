"""
Primeiro uso: garante que o modelo de voz esteja no cache antes de carregar.

No bundle windowed (Ditar.exe sem console), baixar ~1,5 GB sem feedback faria o app
parecer travado. Mostramos um splash Tk (barra indeterminada) enquanto o download roda
numa thread. Se o modelo ja estiver em cache, e um no-op instantaneo.

Obs.: baixar o modelo na mesma execucao curta pode disparar um crash de teardown CUDA
(0xC0000409) na SAIDA, *depois* que o download terminou (cosmetico, nao-deterministico —
ver governance/_specs/R1-tem-exe/tasks.md). O daemon normal so baixa no 1o uso e sai
muito depois (modelo ja em cache), entao nao e afetado na pratica.

Ver governance/_specs/R1-tem-exe/spec.md (AC-5) e tasks.md (task 8).
"""

from __future__ import annotations

import threading


def is_cached(model_name: str) -> bool:
    """True se o modelo ja esta no cache local (sem tocar a rede)."""
    try:
        from faster_whisper import download_model

        download_model(model_name, local_files_only=True)
        return True
    except Exception:
        return False


def ensure_model(model_name: str) -> None:
    """Baixa o modelo se faltar; mostra splash de progresso enquanto baixa.

    No-op se ja estiver em cache. Em ambiente sem GUI, apenas aguarda o download.
    """
    if is_cached(model_name):
        return

    from faster_whisper import download_model

    result: dict[str, BaseException | None] = {"err": None}

    def worker() -> None:
        try:
            download_model(model_name)
        except BaseException as e:  # noqa: BLE001 — propaga depois de fechar o splash
            result["err"] = e

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    try:
        _splash_while(t, model_name)
    except Exception:
        t.join()  # sem GUI disponivel: so espera

    if result["err"] is not None:
        raise result["err"]


def _splash_while(t: threading.Thread, model_name: str) -> None:
    """Janela simples com barra indeterminada, fechada quando a thread `t` termina."""
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Ditar")
    root.resizable(False, False)

    frm = ttk.Frame(root, padding=20)
    frm.grid()
    ttk.Label(frm, text="Preparando o Ditar", font=("Segoe UI", 12, "bold")).grid(
        column=0, row=0, sticky="w"
    )
    ttk.Label(
        frm,
        text=f"Baixando o modelo de voz ({model_name}).\nIsso acontece so na primeira vez.",
        justify="left",
    ).grid(column=0, row=1, sticky="w", pady=(6, 12))
    bar = ttk.Progressbar(frm, mode="indeterminate", length=340)
    bar.grid(column=0, row=2, sticky="we")
    bar.start(12)

    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"+{x}+{y}")

    def poll() -> None:
        if t.is_alive():
            root.after(200, poll)
        else:
            root.destroy()

    root.after(200, poll)
    root.mainloop()


if __name__ == "__main__":
    # Demo manual do splash (sem baixar nada): mostra a janela por ~3s.
    import time

    fake = threading.Thread(target=lambda: time.sleep(3))
    fake.start()
    _splash_while(fake, "demo")

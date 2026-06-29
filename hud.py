"""
HUD do ditado: uma pílula flutuante (sempre no topo) que mostra "Ouvindo…" /
"Escrevendo…" perto do rodapé, e some quando ocioso.

Coexistencia (o ponto tecnico da fatia 2): o pystray ocupa a thread PRINCIPAL com seu
proprio loop de mensagens; o Tk roda numa THREAD DEDICADA com seu proprio mainloop. Tk
nao e thread-safe, entao a unica comunicacao de fora e `set_state()` (escreve um campo sob
lock); todo desenho acontece dentro da thread do Tk, via `after()` lendo esse campo.
"""

from __future__ import annotations

import threading


class HUD:
    def __init__(self) -> None:
        self._state = "idle"
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def set_state(self, state: str) -> None:
        """Thread-safe: chamado pelo daemon; a thread do Tk le e redesenha."""
        with self._lock:
            self._state = state

    # ------------------------------------------------------------------ Tk thread
    def _run(self) -> None:
        try:
            import tkinter as tk
        except Exception:
            return
        try:
            root = tk.Tk()
            root.overrideredirect(True)            # sem barra de titulo
            root.attributes("-topmost", True)
            TRANSP = "#010203"                     # cor "magica" -> vira transparente
            root.configure(bg=TRANSP)
            try:
                root.attributes("-transparentcolor", TRANSP)
            except Exception:
                pass

            W, H, R = 210, 54, 18
            cv = tk.Canvas(root, width=W, height=H, bg=TRANSP, highlightthickness=0)
            cv.pack()

            # retangulo arredondado (pilula escura)
            pts = [
                R, 0, W - R, 0, W, 0, W, R, W, H - R, W, H,
                W - R, H, R, H, 0, H, 0, H - R, 0, R, 0, 0,
            ]
            cv.create_polygon(pts, smooth=True, fill="#1c1c1e")
            dot = cv.create_oval(20, H // 2 - 6, 32, H // 2 + 6, fill="#888", outline="")
            txt = cv.create_text(46, H // 2, text="", anchor="w", fill="#f2f2f2",
                                 font=("Segoe UI", 12))

            root.withdraw()
            shown = {"v": False}

            def place() -> None:
                sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
                root.geometry(f"{W}x{H}+{(sw - W) // 2}+{sh - H - 80}")

            def poll() -> None:
                with self._lock:
                    st = self._state
                if st == "recording":
                    cv.itemconfig(dot, fill="#e23b3b")
                    cv.itemconfig(txt, text="Ouvindo…")
                    if not shown["v"]:
                        root.deiconify(); place(); shown["v"] = True
                elif st == "transcribing":
                    cv.itemconfig(dot, fill="#e6a028")
                    cv.itemconfig(txt, text="Escrevendo…")
                    if not shown["v"]:
                        root.deiconify(); place(); shown["v"] = True
                else:
                    if shown["v"]:
                        root.withdraw(); shown["v"] = False
                root.after(100, poll)

            root.after(100, poll)
            root.mainloop()
        except Exception:
            pass

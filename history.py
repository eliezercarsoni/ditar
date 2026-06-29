"""
Janela de Histórico de ditados (Tk). Roda como processo separado (`Ditar --history`),
sem CUDA — mesma estratégia da janela de Configurações.
"""

from __future__ import annotations

import time

import db


def open_history() -> None:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Ditar — Historico")
    root.geometry("560x430")
    frm = ttk.Frame(root, padding=12)
    frm.grid(sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    frm.columnconfigure(0, weight=1)
    frm.rowconfigure(2, weight=1)

    ttk.Label(frm, text="Buscar:").grid(column=0, row=0, sticky="w")
    var_q = tk.StringVar()
    ttk.Entry(frm, textvariable=var_q).grid(column=0, row=1, sticky="we", pady=(2, 8))

    lst = tk.Listbox(frm, activestyle="none")
    lst.grid(column=0, row=2, sticky="nsew")
    sb = ttk.Scrollbar(frm, orient="vertical", command=lst.yview)
    sb.grid(column=1, row=2, sticky="ns")
    lst.config(yscrollcommand=sb.set)

    rows: list[tuple] = []
    status = ttk.Label(frm, text="", foreground="#2a7")

    def refresh() -> None:
        nonlocal rows
        rows = db.recent(300, var_q.get().strip())
        lst.delete(0, tk.END)
        for ts, text, app in rows:
            when = time.strftime("%d/%m %H:%M", time.localtime(ts))
            snippet = " ".join((text or "").split())[:80]
            tag = f" - {app[:25]}" if app else ""
            lst.insert(tk.END, f"[{when}{tag}]  {snippet}")
        status.config(text=f"{len(rows)} ditado(s)")

    var_q.trace_add("write", lambda *a: refresh())

    def copy_sel(_evt=None) -> None:
        sel = lst.curselection()
        if not sel:
            return
        text = rows[sel[0]][1]
        try:
            import pyperclip
            pyperclip.copy(text)
            status.config(text="Copiado para o clipboard.")
        except Exception as e:  # noqa: BLE001
            status.config(text=f"Falha ao copiar: {e}")

    lst.bind("<Double-Button-1>", copy_sel)
    btns = ttk.Frame(frm)
    btns.grid(column=0, row=3, sticky="w", pady=(8, 0))
    ttk.Button(btns, text="Copiar selecionado", command=copy_sel).grid(column=0, row=0)
    ttk.Button(btns, text="Fechar", command=root.destroy).grid(column=1, row=0, padx=(8, 0))
    status.grid(column=0, row=4, sticky="w", pady=(6, 0))

    refresh()
    root.mainloop()


if __name__ == "__main__":
    open_history()

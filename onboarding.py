"""
Tela de boas-vindas / privacidade (Tk), mostrada UMA vez no 1o uso. Roda como processo
separado (`Ditar --onboarding`), sem CUDA. Reforça o diferencial: 100% local.
"""

from __future__ import annotations


def open_onboarding() -> None:
    import tkinter as tk
    import webbrowser
    from tkinter import ttk

    root = tk.Tk()
    root.title("Bem-vindo ao Ditar")
    root.resizable(False, False)
    frm = ttk.Frame(root, padding=22)
    frm.grid()

    ttk.Label(frm, text="100% local e privado", font=("Segoe UI", 14, "bold")).grid(
        column=0, row=0, sticky="w"
    )
    ttk.Label(
        frm,
        text=("Seu audio e processado na sua maquina e NUNCA sai dela —\n"
              "sem nuvem, sem conta, sem custo por uso."),
        justify="left",
        font=("Segoe UI", 10),
    ).grid(column=0, row=1, sticky="w", pady=(8, 14))

    ttk.Label(frm, text="Como ditar", font=("Segoe UI", 11, "bold")).grid(column=0, row=2, sticky="w")
    ttk.Label(
        frm,
        text=("Segure CTRL+ALT+D, fale, e solte — o texto aparece no app em foco.\n"
              "Um icone fica na bandeja do sistema (perto do relogio)."),
        justify="left",
        font=("Segoe UI", 10),
    ).grid(column=0, row=3, sticky="w", pady=(8, 16))

    btns = ttk.Frame(frm)
    btns.grid(column=0, row=4, sticky="w")

    def settings() -> None:
        import subprocess
        import sys
        from pathlib import Path
        try:
            if getattr(sys, "frozen", False):
                subprocess.Popen([sys.executable, "--settings"])
            else:
                subprocess.Popen([sys.executable, str(Path(__file__).resolve().parent / "ditar.py"), "--settings"])
        except Exception:
            pass
        root.destroy()

    ttk.Button(btns, text="Comecar", command=root.destroy).grid(column=0, row=0)
    ttk.Button(btns, text="Configuracoes", command=settings).grid(column=1, row=0, padx=(8, 0))

    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    root.mainloop()


if __name__ == "__main__":
    open_onboarding()

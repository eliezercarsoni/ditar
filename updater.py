"""
Auto-update por DELTA via GitHub Releases (ADR-0004). Baixa só os arquivos que mudaram
(uns MB: os .exe que embutem o codigo Python), nao o bundle inteiro (~1 GB de CUDA estavel).

Cada release publica: `update.json` ({version, from_version, delta, delta_size}) + `delta-<ver>.zip`
(arquivos alterados) + (opcional) o instalador completo p/ novos usuarios / fallback.

Cliente: le `update.json` da release mais nova; se o delta cobre o salto (instalada == from_version),
baixa o zip pequeno e aplica via .bat destacado (mata Ditar → extrai sobre a pasta → reabre).
Degrada em silencio: sem release / offline / erro → "esta atualizado".
"""

from __future__ import annotations

import json
import time
import urllib.request

REPO = "eliezercarsoni/ditar"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"


def _parse_ver(tag: str) -> tuple:
    t = (tag or "").lstrip("vV").split("-")[0].split("+")[0]
    out = []
    for p in t.split("."):
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out) or (0,)


def _get_json(url: str, timeout: float = 8.0):
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Ditar-Updater"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def check_for_update(current: str, timeout: float = 8.0) -> dict | None:
    """{version, from_version, delta_url, delta_size, installer_url, notes} se houver versão
    > current; None se não houver / erro / offline."""
    try:
        data = _get_json(API_LATEST, timeout)
    except Exception:
        return None
    latest = (data.get("tag_name") or "").lstrip("vV")
    if not latest or _parse_ver(latest) <= _parse_ver(current):
        return None

    assets = {a.get("name", ""): a for a in data.get("assets", [])}
    info = {
        "version": latest,
        "from_version": None,
        "delta_url": None,
        "delta_size": 0,
        "installer_url": None,
        "notes": data.get("body", "") or "",
    }
    # metadados de delta
    if "update.json" in assets:
        try:
            uj = _get_json(assets["update.json"]["browser_download_url"], timeout)
            info["from_version"] = uj.get("from_version")
            dname = uj.get("delta")
            if dname and dname in assets:
                info["delta_url"] = assets[dname]["browser_download_url"]
                info["delta_size"] = assets[dname].get("size", 0)
        except Exception:
            pass
    # instalador completo (fallback / novos usuarios)
    for name, a in assets.items():
        if name.lower().endswith(".exe"):
            info["installer_url"] = a["browser_download_url"]
            break
    return info


def download(url: str, dest: str, on_progress=None, timeout: float = 120.0,
             retries: int = 4) -> None:
    """Download robusto: timeout generoso + retomada (HTTP Range) + retentativas."""
    read = 0
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            headers = {"User-Agent": "Ditar-Updater"}
            if read:
                headers["Range"] = f"bytes={read}-"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resuming = read > 0 and getattr(r, "status", 200) == 206
                if read and not resuming:
                    read = 0
                total = int(r.headers.get("Content-Length") or 0) + read
                with open(dest, "ab" if resuming else "wb") as f:
                    while True:
                        chunk = r.read(262144)
                        if not chunk:
                            return
                        f.write(chunk)
                        read += len(chunk)
                        if on_progress:
                            on_progress(read, total)
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5)
    raise last_err if last_err else RuntimeError("download falhou")


def _app_dir() -> str:
    import os
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Ditar")


def apply_delta(zip_path: str) -> None:
    """Aplica o delta: .bat destacado mata o Ditar, extrai o zip sobre a pasta e reabre."""
    import os
    import subprocess
    import tempfile

    app = _app_dir()
    bat = os.path.join(tempfile.gettempdir(), "ditar_delta.bat")
    lines = [
        "@echo off",
        "taskkill /IM Ditar.exe /F >nul 2>&1",
        "ping 127.0.0.1 -n 3 >nul",
        f'tar -xf "{zip_path}" -C "{app}"',  # tar.exe (bsdtar) extrai .zip no Win10+
        f'start "" "{os.path.join(app, "Ditar.exe")}"',
        'del "%~f0" >nul 2>&1',
    ]
    with open(bat, "w", encoding="ascii") as f:
        f.write("\r\n".join(lines) + "\r\n")
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x00000008, close_fds=True)


def show_result(current: str, silent_if_current: bool = False) -> None:
    info = check_for_update(current)
    if info is None:
        if silent_if_current:
            return
        _dialog(f"Voce esta na versao mais recente ({current}).", None)
        return
    _dialog(f"Nova versao disponivel: {info['version']} (voce tem a {current}).", info)


def _can_delta(info: dict, current: str) -> bool:
    return bool(info.get("delta_url") and info.get("from_version") == current)


def _dialog(msg: str, info: dict | None) -> None:
    import os
    import tempfile
    import threading
    import tkinter as tk
    import webbrowser
    from tkinter import ttk

    root = tk.Tk()
    root.title("Ditar — Atualizacao")
    root.resizable(False, False)
    frm = ttk.Frame(root, padding=18)
    frm.grid()
    lbl = ttk.Label(frm, text=msg, justify="left", font=("Segoe UI", 10))
    lbl.grid(column=0, row=0, sticky="w", pady=(0, 12))
    bar = ttk.Progressbar(frm, mode="determinate", length=340, maximum=100)
    btns = ttk.Frame(frm)
    btns.grid(column=0, row=2, sticky="w")

    if info is None:
        ttk.Button(btns, text="OK", command=root.destroy).grid(column=0, row=0)
    else:
        import version as _v
        delta_ok = _can_delta(info, _v.VERSION)
        st = {"read": 0, "total": 0, "done": False, "err": None, "path": None}

        def run(url: str, dest: str, after) -> None:
            for w in btns.winfo_children():
                w.destroy()
            ttk.Label(btns, text="Baixando...").grid(column=0, row=0, sticky="w")
            bar.grid(column=0, row=1, sticky="we", pady=(10, 0))
            st["path"] = dest

            def worker() -> None:
                try:
                    download(url, dest, lambda r, t: st.update(read=r, total=t))
                    st["done"] = True
                except Exception as e:  # noqa: BLE001
                    st["err"] = e

            threading.Thread(target=worker, daemon=True).start()

            def poll() -> None:
                if st["err"] is not None:
                    lbl.config(text=f"Falha no download: {st['err']}")
                    return
                if st["total"]:
                    bar["value"] = st["read"] * 100 / st["total"]
                if st["done"]:
                    lbl.config(text="Aplicando e reiniciando o Ditar...")
                    after(dest)
                    root.after(900, root.destroy)
                    return
                root.after(150, poll)

            poll()

        if delta_ok:
            mb = info["delta_size"] / 1048576 if info["delta_size"] else 0
            txt = f"Atualizar (delta ~{mb:.0f} MB)" if mb else "Atualizar (delta)"
            ttk.Button(btns, text=txt, command=lambda: run(
                info["delta_url"],
                os.path.join(tempfile.gettempdir(), f"ditar-delta-{info['version']}.zip"),
                apply_delta,
            )).grid(column=0, row=0)
        elif info.get("installer_url"):
            # sem delta aplicavel: abre a pagina de releases (download completo e pesado)
            ttk.Button(btns, text="Ver no GitHub",
                       command=lambda: (webbrowser.open(RELEASES_PAGE), root.destroy())).grid(column=0, row=0)
        else:
            ttk.Button(btns, text="Ver no GitHub",
                       command=lambda: (webbrowser.open(RELEASES_PAGE), root.destroy())).grid(column=0, row=0)
        ttk.Button(btns, text="Depois", command=root.destroy).grid(column=1, row=0, padx=(8, 0))

    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    root.mainloop()

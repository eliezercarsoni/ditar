# -*- mode: python ; coding: utf-8 -*-
# Bundle do Ditar (R1 "Tem .exe") — PyInstaller onedir, 2 exes (Ditar + Transcrever),
# pasta compartilhada. Ver governance/_specs/R1-tem-exe/design.md.
#
# Build:
#   .venv\Scripts\pyinstaller.exe build\ditar.spec --distpath build\dist --workpath build\work --noconfirm
from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

PROJ = Path(SPECPATH).parent                       # .../audio
NVIDIA = PROJ / ".venv" / "Lib" / "site-packages" / "nvidia"

# --- DLLs CUDA → _internal\nvidia\<sub>\bin (mesmo layout que o hook do PyInstaller
# usa p/ cublas/cudnn → COLLECT deduplica; cuda_nvrtc o hook NAO pega, entao a coleta
# explicita garante as 3). Frozen: _add_cuda_dlls_to_path() registra esses 3 dirs. ---
cuda_binaries = []
for sub in ("cublas", "cudnn", "cuda_nvrtc"):
    binp = NVIDIA / sub / "bin"
    if binp.is_dir():
        cuda_binaries += [(str(dll), f"nvidia/{sub}/bin") for dll in binp.glob("*.dll")]

binaries = list(cuda_binaries)
for pkg in ("ctranslate2", "onnxruntime", "av", "sounddevice"):
    binaries += collect_dynamic_libs(pkg)

datas = []
datas += collect_data_files("faster_whisper")      # assets/silero_vad_v6.onnx
datas += collect_data_files("sounddevice")

hiddenimports = ["pystray._win32", "config", "settings", "firstrun", "hud", "version", "updater", "db", "history", "onboarding"]

# ditar.py é superconjunto de imports do transcrever.py → seu fecho cobre os dois exes.
a = Analysis(
    [str(PROJ / "ditar.py")],
    pathex=[str(PROJ)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
b = Analysis(
    [str(PROJ / "transcrever.py")],
    pathex=[str(PROJ)],
    noarchive=False,
)

pyz_a = PYZ(a.pure)
pyz_b = PYZ(b.pure)

ICON = str(PROJ / "app.ico")
# Ditar = app de bandeja → windowed (console=False); logs vao p/ %LOCALAPPDATA%\Ditar\ditar.log.
# Transcrever = CLI → mantem console p/ ver progresso/tqdm.
exe_ditar = EXE(
    pyz_a, a.scripts, [], exclude_binaries=True,
    name="Ditar", console=False, icon=ICON,
)
exe_transcrever = EXE(
    pyz_b, b.scripts, [], exclude_binaries=True,
    name="Transcrever", console=True, icon=ICON,
)

# Uma pasta só: binaries/datas vêm do fecho do 'a' (cobre ambos). dedup por destino.
coll = COLLECT(
    exe_ditar,
    exe_transcrever,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="Ditar",
)

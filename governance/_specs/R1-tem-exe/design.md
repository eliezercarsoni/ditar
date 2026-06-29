---
name: design-r1-tem-exe
description: Design técnico do empacotamento (AC-1/AC-2, tier arquitetural) — como o bundle congelado acha CUDA, VAD, ffmpeg e áudio. Puxe ao mexer no ditar.spec ou no empacotamento.
alwaysApply: false
---

# Design — Empacotamento do Ditar (R1, AC-1/AC-2)

> Tier **arquitetural** (ADR-0002). Este doc detalha **como** o bundle PyInstaller
> `onedir` resolve as dependências nativas em runtime, sem Python do sistema.

## 1. Problema
Um app congelado precisa achar, em runtime, sem venv:
1. **DLLs CUDA** (cuBLAS, cuDNN, nvrtc) que o `ctranslate2.dll` carrega por demanda.
2. **Asset do VAD** (`silero_vad_v6.onnx`) + **onnxruntime** (o `vad_filter=True` o usa).
3. **ffmpeg/PyAV** (decodificar arquivos no `transcrever`).
4. **PortAudio** (`sounddevice`, captura de mic no `ditar`) e backend win32 do `pystray`.

## 2. Achados do ambiente (medidos em 2026-06-28)
- Python **3.12.10** no venv; faster-whisper 1.2.1, CTranslate2 4.7.1, onnxruntime 1.26.0.
- **DLLs CUDA em `.venv\Lib\site-packages\nvidia\{cublas,cudnn,cuda_nvrtc}\bin` — ~1,83 GB:**
  - `cublasLt64_12.dll` **637 MB**, `cublas64_12.dll` 98 MB
  - `cudnn_engines_precompiled64_9.dll` **490 MB**, `cudnn_adv64_9.dll` 269 MB, `cudnn_ops64_9.dll` 121 MB, `cudnn_heuristic64_9.dll` 54 MB, + menores
  - `nvrtc64_120_0.dll` 86 MB (+ `.alt` 86 MB), `nvrtc-builtins64_129.dll` 7 MB
- `ctranslate2.dll` já traz **`cudnn64_9.dll`** (loader) + **`libiomp5md.dll`** (OpenMP).
- VAD: `faster_whisper\assets\silero_vad_v6.onnx`.
- Modelo em cache: `models--mobiuslabsgmbh--faster-whisper-large-v3-turbo` (~1,55 GB) — **NÃO** entra no bundle.

## 3. Decisão de design
**Estratégia "espelhar o layout do venv":** empacotar as DLLs CUDA em
`_internal\nvidia\<sub>\bin` — o **mesmo** caminho que o hook nativo do PyInstaller
já usa para `cublas`/`cudnn`. Como o `COLLECT` deduplica entradas com destino+origem
idênticos, não há cópia duplicada; `cuda_nvrtc` (que o hook **não** coleta) entra pela
coleta explícita. O frozen e o venv ficam paralelos (`_MEIPASS/nvidia/...` ↔
`site-packages/nvidia/...`).

> **Por que não "achatar na raiz do _internal":** a primeira tentativa pôs as DLLs na
> raiz (`.`) e funcionou, mas o hook do PyInstaller também as colocou em `nvidia/.../bin`
> → **858 MB duplicados** (2,99 GB). Espelhar o layout do hook deduplica → 2,13 GB.

**Mudança de código (mínima, cirúrgica) em `transcrever.py`:**
`_add_cuda_dlls_to_path()` ganha um branch para `getattr(sys, "frozen", False)`:
- **Frozen:** `base = Path(sys._MEIPASS)/"nvidia"`; registra `base/{cublas,cudnn,cuda_nvrtc}/bin`.
- **Venv (inalterado):** continua varrendo `site-packages/nvidia/.../bin`.
O `ditar.py` herda isso de graça (já faz `import transcrever` pelo efeito colateral).

**`build/ditar.spec` (onedir, 2 exes, bundle compartilhado):**
- `binaries`: as DLLs dos 3 dirs CUDA, destino `nvidia/<sub>/bin` (dedup com o hook).
- `collect_dynamic_libs` + `collect_data_files` para: `ctranslate2`, `onnxruntime`, `av`, `sounddevice`.
- `collect_data_files("faster_whisper")` → leva `assets/silero_vad_v6.onnx`.
- `hiddenimports`: `pystray._win32`, providers do onnxruntime se necessário.
- Dois `EXE` (`Ditar`, `Transcrever`) + um `COLLECT` (dedup por nome) → uma pasta só.
- **Spike:** ambos com `console=True` para capturar erro. **Produção:** `Ditar` vira
  `console=False` (task 7).

## 4. Orçamento de tamanho
- CUDA ~1,83 GB + Python/deps ~0,3 GB ⇒ **onedir ~2,1–2,3 GB**.
- Instalador (Inno Setup LZMA) deve comprimir p/ **< 2 GB** (AC-8). Se estourar, aplicar §5.

## 5. Oportunidades de trim (só se AC-8 apertar — não no spike)
- `cudnn_adv64_9.dll` (269 MB): CTranslate2 (encoder/decoder Whisper) provavelmente **não** usa
  RNN/atenção avançada do cuDNN — candidato a remover e testar.
- `nvrtc64_120_0.alt.dll` (86 MB) e `nvblas64_12.dll`: prováveis dispensáveis.
- Validar cada remoção com o gate da task 4 (transcrição GPU continua verde?).

## 6. Riscos e mitigação
| Risco | Mitigação |
|---|---|
| Loader não acha cuBLAS/cuDNN no frozen | DLLs no mesmo dir do `ctranslate2.dll` + `add_dll_directory(_MEIPASS)` |
| `ditar --check` mascara falha CUDA (cai p/ CPU) | Validar via `Transcrever.exe` (RTF baixo prova GPU) antes do `--check` |
| onnxruntime/portaudio não coletados | `collect_dynamic_libs` explícito; gate cobre VAD (transcrição usa `vad_filter=True`) |
| Bundle > limite de disco/tempo | Aceitável no spike; trim na §5 se preciso |

## 7. Rastreabilidade
- Decisão de rota: [ADR-0002](../../adr/0002-empacotamento-pyinstaller-inno-winsparkle.md)
- Contrato: [spec.md](spec.md) (AC-1, AC-2, AC-7)
- Código afetado: [`transcrever.py`](../../../transcrever.py) (`_add_cuda_dlls_to_path`)

## 8. Resultado do spike (2026-06-28) — viabilidade PROVADA
- Ambiente validado: PyInstaller 6.21.0, Python 3.12.10, RTX 3050.
- **AC-1 (GPU) ✅:** `Transcrever.exe teste.ogg` → 60,4s de áudio em **3,6s (RTF=0,06x)**,
  `device: cuda | int8_float16`, sem erro CUDA — rodando **sem Python do sistema**.
- **AC-1 (daemon) ✅:** `Ditar.exe --check` carrega o modelo na GPU e reporta "OK".
- **AC-7 ✅:** `Transcrever.exe` gera `.srt` + `.md` a partir do bundle.
- **Tamanho:** bundle onedir = **2,13 GB** (após dedup). Instalador comprimido (Inno LZMA)
  deve ficar < 2 GB (AC-8 a confirmar na task 10); trim da §5 disponível como margem.
- **Pendências:** AC-2 (fallback CPU no frozen) não testado no spike — exige baixar o
  modelo `medium`; fica para a task 6.

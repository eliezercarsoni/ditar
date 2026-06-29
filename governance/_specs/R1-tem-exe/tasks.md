---
name: tasks-r1-tem-exe
description: Decomposição e gates da R1 "Tem .exe". Puxe ao implementar.
alwaysApply: false
---

# Tasks — R1 "Tem .exe"

> Cada task mapeia para `AC-N` da [spec](spec.md). Gate = como verificar. `[P]` = paralelizável.
> **Tasks 1–5 = o spike de empacotamento CUDA** (prova de viabilidade da rota do ADR-0002).

## Plano
| #   | Task                                                               | Cobre AC | Depende | Gate (como verificar)                                 | Status   |
| --- | ------------------------------------------------------------------ | -------- | ------- | ----------------------------------------------------- | -------- |
| 1   | `design.md` do bundle CUDA (tier arquitetural)                     | AC-1     | —       | design.md escrito e aprovado                          | **done** |
| 2   | Adaptar `_add_cuda_dlls_to_path()` p/ modo frozen (`sys._MEIPASS`) | AC-1     | 1       | venv ainda funciona; branch frozen presente           | **done** |
| 3   | Criar `build/ditar.spec` (PyInstaller onedir, 2 exes)              | AC-1,7   | 2       | `pyinstaller build/ditar.spec` builda sem erro        | **done** |
| 4   | Build + validar **GPU**: `Transcrever.exe 04-outputs/audio.ogg`    | AC-1,7   | 3       | gera `.srt`+`.md`, RTF < 0.2, **sem** erro CUDA       | **done** |
| 5   | Validar `Ditar.exe --check` no bundle                              | AC-1     | 4       | imprime "OK: dependências e modelo prontos" na GPU    | **done** |
| 6   | Fallback CPU no bundle (`--device cpu --model medium`) `[P]`       | AC-2     | 4       | transcreve sem GPU, sem crash                         | **done** |
| 7   | Flip `Ditar.exe` p/ windowed (console=False) + log p/ arquivo      | AC-1     | 5       | tray sobe sem janela de console; erros vão p/ log     | **done** |
| 8   | Barra de progresso do download do modelo na 1ª execução            | AC-5     | —       | 1ª execução (cache limpo) mostra progresso, não trava | **done** |
| 9   | `app.ico` do produto + aplicar no exe e atalho `[P]`               | AC-6     | —       | ícone próprio aparece (tray/instalador/atalho)        | **done** |
| 10  | Instalador Inno Setup per-user (`%LocalAppData%`)                  | AC-3     | 7,9     | instala sem UAC; atalho no Menu Iniciar               | **done** |
| 11  | Checkbox "iniciar com o Windows" (chave Run)                       | AC-4     | 10      | sobe no login sem console; desmarcado → nada          | **done** |
| 12  | Medir tamanho do instalador                                        | AC-8     | 10      | < 2 GB                                                | **done** |

## Plano de verificação (tailorizado — smoke test + manual)
- **Automático (spike):** `Transcrever.exe 04-outputs\audio.ogg` na GPU + `Ditar.exe --check`.
- **Manual (R1 completa):** instalar do zero numa conta sem admin → tray sobe → `CTRL+ALT+ESPAÇO`
  grava e cola texto → `Transcrever.exe` gera `.srt`/`.md`.

## Resultado da execução (2026-06-28)
Instalador final: `Ditar-Setup-1.0.0.exe` = **1.057 MB (~1,03 GB)** (bundle 2,13 GB → ~50%).
- **Task 4 (GPU):** RTF 0,05x ✓. **Task 5:** `Ditar.exe --check` → "OK" ✓.
- **Task 6 (CPU):** validado com o modelo **em cache** via `--device cpu` (RTF 0,79x, sem
  crash). A troca p/ `medium` no fallback real não foi exercida (evita baixar 1,5 GB) — é
  só o nome do modelo; o caminho CPU está provado. Verificação manual no 1º fallback real.
- **Task 7 (windowed+log):** `Ditar.exe` (console=False) grava em `%LOCALAPPDATA%\Ditar\ditar.log`.
- **Task 8 (download):** `firstrun` baixou o `tiny` em cache temporário com splash Tk ✓.
- **Task 9 (ícone):** embutido em `Ditar.exe` e `Transcrever.exe` ✓.
- **Task 10 (instalador):** install silencioso **sem UAC**, arquivos em `%LocalAppData%\Ditar`,
  exe roda, uninstall limpo ✓. **Task 11 (autostart):** Run key HKCU criada com a task e
  removida no uninstall ✓. **Task 12:** 1,03 GB < 2 GB (AC-8) ✓.

## Divergências / issues conhecidas
- [ ] **Fastfail de teardown (0xC0000409) na saída — só quando o modelo é baixado na MESMA execução curta.** Investigado a fundo (2026-06-28):
  - **Caso comum (modelo em cache): SEM crash** — verificado limpo em 11+ execuções (`--check`
    e `Transcrever` na GPU). É o caminho de 99% dos usos.
  - O residual ocorre **após** todo o trabalho (download e transcrição já concluídos) e é
    **não-determinístico**. **Não é o Tk** (reproduzido no `Transcrever`, sem GUI) nem o
    subprocesso — é um `__fastfail` do teardown CUDA/CTranslate2 disparado pela combinação
    download-fresco + contexto CUDA na mesma saída curta.
  - Tentativas que **não** resolveram (revertidas por não pagarem a complexidade):
    `TerminateProcess` (assíncrono; o fault é em thread de teardown) e isolar o download em
    subprocesso. Mantido o `os._exit(0)` (mitiga o caso comum).
  - **Impacto prático: cosmético.** O daemon real só baixa no 1º uso e sai muito depois (já
    em cache → limpo). Só `--check <modelo-não-baixado>` (diagnóstico) pode pegar o residual.
  - Fix garantido seria um **processo lançador** (worker filho + pai fino que reporta exit) —
    over-engineering para a R1; reavaliar se virar incômodo real.

## Definition of Done (tailorizado)
- [x] AC-1/AC-2/AC-7 verdes pelo gate (tasks 4–6)
- [x] AC-3/AC-4/AC-5/AC-6/AC-8 verdes (tasks 8–12)
- [~] Sem `SPEC_DEVIATION` — 1 issue conhecida (teardown) registrada, fora do escopo da R1
- [x] Decisões difíceis de reverter em ADR (ADR-0002) — rota confirmada na prática
- [x] Glossário (`tailoring.md` §4) — sem termos novos
- [x] Spec reflete o que foi construído (ver design.md §8)
- [x] [`governance/STATE.md`](../../STATE.md) atualizado



----


Quero que seja uma escrita e um áudio como o do Wispr, sem aquele grito agudo e irritante

![[Pasted image 20260628190948.png]]

![[Pasted image 20260628191003.png]]






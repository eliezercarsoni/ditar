---
name: STATE
description: Memória de trabalho volátil do projeto Ditar — onde paramos, próximo passo, bloqueios. Leia ao retomar, atualize ao pausar.
alwaysApply: true
---

# STATE — Memória viva do projeto Ditar

> Memória **entre sessões** (Eliezer + Claude Code). **Volátil**: atualize ao pausar,
> leia ao retomar. Decisão estrutural vai para **ADR** (durável); estado do trabalho
> fica **aqui**.

**Última atualização:** 2026-06-29 por Eliezer (via Claude Code) — R4: instalador completo publicado + fonte público sincronizado

## Em andamento / próximo passo
> **Resumo:** o `audio/` virou um **software Windows instalável** (era um par de scripts Python).
> **R1, R2 e R3 entregues**; versão atual **1.3.6**. Releases públicas em `github.com/eliezercarsoni/ditar`.

- **R1 "Tem .exe" ✅** — PyInstaller onedir (CUDA no bundle ~2,1 GB) + instalador Inno per-user
  (sem UAC), ícone, autostart. Instalador ~1 GB. Ver [ADR-0002](adr/0002-empacotamento-pyinstaller-inno-winsparkle.md).
- **R2 "Ditado estilo Wispr" ✅** — seleção de mic, som suave, HUD flutuante, modos hold+toggle,
  config ao vivo, instância única. Confirmado pelo usuário. (R2-exec ≠ R2-original do BC — ver §11.)
- **R3 "Parece app + se mantém" ✅ COMPLETA:**
  - **Auto-update** por **delta** ([ADR-0004](adr/0004-auto-update-delta.md)): baixa só ~11 MB,
    não 1 GB (CUDA nunca muda). `build/make_delta.py` + `updater.py`. **Confirmado pelo usuário.**
  - **Histórico SQLite** (`db.py` + `history.py`, menu → Histórico): grava cada ditado, busca, copiar.
  - **Onboarding de privacidade** (US-2.2, `onboarding.py`): tela "100% local" no 1º uso.
- **R4 (refinos) — em andamento:**
  - ✅ **Instalador completo publicado** (2026-06-29): `Ditar-Setup-1.3.6.exe` (~1 GB) anexado à
    release v1.3.6, ao lado do delta. Lacuna fechada — usuário novo instala do zero; quem já tem
    usa o delta. **Política:** toda release que vira "Latest" carrega o full + o delta (o
    `updater.py` lê `releases/latest` e já expõe `installer_url` — sem mudança de código).
  - ✅ **Fonte público sincronizado** (2026-06-29, commit `d826909`): a reescrita R1–R3 (módulos,
    `build/` sem binários, `governance/`) + README corrigido foram commitados/pushados na `main`
    (39 arquivos, +2750). Antes o repo tinha só 2 commits — agora reflete o software lançado.
  - ✅ **Escada de fallback de injeção** (US-5.1): clipboard → SendInput Unicode; cobre o caso comum
    "clipboard ocupado por outro app" (antes sumia). UIA (3º degrau) adiado. `ditar.py:_inject` +
    `_inject_sendinput`. Verificado: round-trip Unicode (acentos PT) + escalonamento na exceção.
  - ✅ **US-2.3 modelo/idioma na config**: dropdowns na janela de Configurações; idioma aplica ao
    vivo (re-lido por gravação), modelo exige reiniciar. `config.py` (model/language) + `settings.py`
    + resolução no `ditar.py:main` (arg CLI sobrepõe; `firstrun.ensure_model` baixa o escolhido).
  - ⬜ Code signing (Azure Trusted Signing) · ⬜ US-3.3 (áudio+poda) · ⬜ auto-mute música ao ditar.
- **Build/release:** `pyinstaller build/ditar.spec` → ISCC `installer.iss` (full) → `make_delta.py <ver> <ant>`
  → `gh release create` **+ anexar o `Ditar-Setup-<ver>.exe` à release** (senão usuário novo trava).
  Versão única em `version.py` (sincronizar `installer.iss`). Rollback: reinstalar release anterior.

## Decisões recentes
- 2026-06-28: Adotar governança SDD **tailorizada** do `spec-driven` → [ADR-0001](adr/0001-adotar-governanca-sdd-tailorizada.md).
- 2026-06-28: Rota de empacotamento = PyInstaller onedir + Inno Setup + WinSparkle
  **ratificada** → [ADR-0002](adr/0002-empacotamento-pyinstaller-inno-winsparkle.md) (status: aceito).
- 2026-06-28: Spike CUDA validou a rota — DLLs em `_MEIPASS\nvidia\<sub>\bin` (espelha o venv,
  deduplica com o hook do PyInstaller). Detalhes e medições em [design.md §8](_specs/R1-tem-exe/design.md).

## Pendências técnicas da R1
- [ ] **Verificação manual end-to-end** do instalador (instalar → ditar num app real).
- [ ] Task 6: fallback CPU real testado só com modelo em cache; o download de `medium` no
  fallback real fica para verificação manual (evitou baixar 1,5 GB no automatizado).

## Bloqueios
- [ ] Nenhum no momento.

## Ideias adiadas / backlog técnico
- **Fastfail de teardown (0xC0000409) na saída — só no download-fresco-mesma-execução.**
  Investigado e classificado como **cosmético** (caso comum em cache = limpo, 11+ runs).
  Não é Tk nem subprocesso; `TerminateProcess`/isolamento foram tentados e revertidos. Fix
  garantido = processo lançador (over-engineering p/ agora). Detalhes em tasks.md §issues.
- Trim de DLLs cuDNN (`cudnn_adv` 269 MB, `nvrtc.alt` 86 MB) — só se o tamanho apertar (design §5).
- Modularizar `src/` em camadas (DDD) — **gatilho:** só se config + histórico crescerem (tailoring §2).
- Code signing (Azure Trusted Signing) — **gatilho:** R4 / quando o SmartScreen virar incômodo.
- Empacotar engine CPU-only como build alternativo — **gatilho:** demanda de usuários sem GPU NVIDIA.
- **3º degrau da injeção (UI Automation)** — **gatilho:** caso real onde clipboard E SendInput
  falhem (ex.: controle custom sem entrada de teclado). Não vence o UIPI de app em admin e exigiria
  `comtypes`/`uiautomation` no bundle — por isso ficou fora da US-5.1 inicial.

## Todos soltos
- [x] Criar o `app.ico` do produto → feito (`audio/app.ico`, gerado por `build/make_icon.py`).
- [ ] Decidir nome do repo de releases (o atual é `eliezercarsoni/ditar`).
- [ ] R3: trocar `MyAppVersion` do `installer.iss` por algo automatizado a cada release.

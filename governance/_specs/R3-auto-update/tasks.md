---
name: tasks-r3-auto-update
description: Decomposição e gates da R3 auto-update. Puxe ao implementar.
alwaysApply: false
---

# Tasks — R3 / Auto-update

## Fatia 1 — check + notify (US-4.1)
| #  | Task | Cobre AC | Gate | Status |
|----|------|----------|------|--------|
| 1  | `version.py` (VERSION única; installer.iss em sincronia) | — | app sabe sua versão | **done** |
| 2  | `updater.py`: `check_for_update(current)` via GitHub API + compara SemVer | AC-1 | sem release/offline → None; release nova → dict | **done** |
| 3  | Modo `Ditar --check-update [--silent-if-current]` (Tk, processo separado) | AC-1,2 | mostra dialog; silencioso se atualizado e flag | **done** |
| 4  | Check no startup (thread → subprocesso) + menu bandeja "Verificar atualizações" | AC-1,2 | startup não trava; menu abre o check | **done** |

**Gate fatia 1 — VERDE (2026-06-28):** `_parse_ver` + `check_for_update` testados (mock de release
nova → detecta + extrai asset .exe; versão igual/maior → None; API real do repo sem releases →
None, sem erro). `--check-update` abre dialog "está atualizado"; `--silent-if-current` sai quieto
(exit 0); daemon sobe normal com o auto-check em background. **Ainda em dev** (não reinstalado —
será empacotado junto da fatia 2, que tem valor visível só com releases publicadas).

## Fatia 2 — download + apply (US-4.2) + publicar release
| #  | Task | Cobre AC | Gate | Status |
|----|------|----------|------|--------|
| 5  | Download do `.exe` da release com progresso (Tk) | AC-3 | baixa p/ temp, barra anda | **done** |
| 6  | Aplicar via **.bat destacado** (mata Ditar → instala `/VERYSILENT` → reabre) | AC-3 | fecha, atualiza, reabre | **done** |
| 7  | ~~Inno CloseApplications/RestartApplications~~ → **descartado** (app sem janela; o `.bat` resolve) | AC-3 | — | **done** |
| 8  | Publicar release (`gh release create`) | AC-1..3 | release visível na API | **done** |
| 9  | Doc de rollback (reinstalar release anterior) | AC-4 | nota no STATE | **done** |

> **Defeito achado e corrigido:** rodar o instalador direto **não** fecha o daemon (windowed=False,
> sem janela → Restart Manager/Inno `CloseApplications` não o pegam) nem sobrescreve o `.exe` travado.
> Solução: `apply_update` escreve um **`.bat` destacado** (roda do cmd, fora da pasta do app) que faz
> `taskkill` → instala → relança. **Validado:** daemon PID 13224 → após apply, novo PID 40900 rodando.

**Validação fatia 2 (2026-06-28):** download testado (unit) + asset real; `apply_update` validado
(kill→install→relaunch, PID novo); **v1.3.0 publicada** e depois **substituída por v1.3.2** (a 1.3.0
tinha o apply antigo). Instalada 1.3.1 (apply corrigido) → detecta 1.3.2 → atualiza. v1.3.0 deletada.

## Definition of Done — R3 auto-update
- [x] AC-1/AC-2 (fatia 1: check + notify) verdes
- [x] AC-3 (download + apply) verde — apply validado localmente
- [x] AC-4 (rollback) — reinstalar release anterior do GitHub (releases ficam disponíveis)
- [x] Release publicada; instalada enxerga o update
- [~] **Confirmação humana pendente:** clicar "Atualizar (delta)" e ver o app voltar já atualizado
- [x] [`STATE.md`](../../STATE.md) atualizado

## Fatia 3 — DELTA (ADR-0004) — substitui o download do instalador inteiro
**Motivo:** baixar 1 GB pela CDN do GitHub (~0,1 MB/s no Brasil) era inviável. Medido: entre
versões mudam só ~12 MB (os `.exe` que embutem o código Python); as DLLs CUDA (1 GB) nunca mudam.

| #  | Task | Gate | Status |
|----|------|------|--------|
| 10 | `build/make_delta.py` (manifesto + zip só dos arquivos mudados) | gera `delta-<ver>.zip` + `update.json` | **done** |
| 11 | `updater.py` delta-aware (lê `update.json`, baixa só o delta) | check retorna delta_url/from_version | **done** |
| 12 | `apply_delta` via `.bat` (mata → `tar -xf` sobre a pasta → reabre) | extrai os arquivos certos; relança | **done** |
| 13 | Publicar release delta (`delta-<ver>.zip` + `update.json`) | release pequena no GitHub | **done** |

**Validação fatia 3 (2026-06-28):** delta 1.3.3→1.3.4 = **11,3 MB** (2 arquivos) vs 1 GB. Check real:
instalada 1.3.3 detecta v1.3.4 com delta_url + from_version=1.3.3. `tar -xf` extrai e o `Ditar.exe`
bate por hash com o build 1.3.4. Download robusto (timeout 120s + retomada Range + retries).
**v1.3.4 publicada** (delta + update.json). Instalada 1.3.3 (rodando) → pronta p/ o update delta.
**Pendência:** clique humano em "Atualizar (delta ~11 MB)" → app volta em 1.3.4.

> **Distribuição de novos usuários:** a release delta não traz instalador completo. Para novos
> usuários, publicar periodicamente um instalador completo (full ~1 GB) — refinamento futuro.

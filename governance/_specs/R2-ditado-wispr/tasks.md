---
name: tasks-r2-ditado-wispr
description: Decomposição e gates da R2 "Ditado estilo Wispr". Puxe ao implementar.
alwaysApply: false
---

# Tasks — R2 "Ditado estilo Wispr"

> Cada task mapeia para `AC-N` da [spec](spec.md). Entregue em fatias.

## Fatia 1 — desbloqueio (mic + som) ✅
| #  | Task | Cobre AC | Gate | Status |
|----|------|----------|------|--------|
| 1  | `config.py` (config.json: mic, som, modo, atalho) | AC-5 | load/save round-trip | **done** |
| 2  | Som suave (seno c/ fade) substitui o bip; `_soft_cue` | AC-2 | toca sem erro; opção desligar | **done** |
| 3  | Gravação usa o mic do config; recarrega a cada gravação | AC-1 | `InputStream(device=...)`; live | **done** |
| 4  | `--list-mics` + `--mic N` (salva no config) | AC-1 | lista devices; salva índice | **done** |
| 5  | Janela `--settings` (Tk, processo separado) — mic + som | AC-1,5 | abre sem crash; salva config | **done** |
| 6  | Menu da bandeja "Configuracoes..." abre `--settings` | AC-5 | item presente; lança subprocesso | **done** |

**Validação fatia 1 (2026-06-28): CONFIRMADA pelo usuário ✅** — ditado cola texto, som suave,
e o conflito de atalho com o Claude Desktop foi resolvido (default → `ctrl+alt+d`, configurável).
A causa do "não rodou" era o mic padrão do Windows (Intel Smart Sound) entregar silêncio; o
usuário ajustou o mic certo no Som do Windows. (Automático: build ok, lista 11 devices,
`--settings` abre, `--check` exit 0, GPU RTF 0,05x.)

> **Bug corrigido na fatia 1:** `ctrl+alt+space` colidia com o atalho global do Claude Desktop
> (abria a janelinha do Claude). Default mudado p/ `ctrl+alt+d` + campo de atalho em Configurações.

## Fatia 2 — feel completo (modos + HUD)
| #  | Task | Cobre AC | Gate | Status |
|----|------|----------|------|--------|
| 7  | Modo **hold** (segurar p/ falar) além do toggle | AC-3 | segura→grava, solta→transcreve; failsafe | **done** |
| 8  | Atalho hold-friendly (ex.: ctrl+alt) configurável | AC-3 | sem conflito; em config | **done** |
| 9  | **HUD** pílula flutuante (Tk em thread dedicada) | AC-4 | mostra estado, some no idle | **done** |
| 10 | HUD coexistir com pystray (main) + CUDA — **risco** | AC-4 | tray + HUD + modelo sem travar | **done** |
| 11 | Settings: incluir modo + atalho | AC-3,5 | salva e aplica | **done** |
| 12 | Repackage instalador c/ a R2 completa | — | instalador novo < 2 GB | **done** |

> **Risco técnico (task 10) RESOLVIDO:** HUD em thread dedicada (`hud.py`) com estado lido sob
> lock via `after()`; pystray segue na main; CUDA no processo. Validado: daemon congelado sobe
> com HUD+bandeja+CUDA e fica estável; o `__fastfail` de saída segue cosmético (R1).

**Validação fatia 2 (2026-06-28):** `hud.py` ciclou no venv; coexistência HUD+pystray+CUDA OK no
bundle; `--check` exit 0. HUD confirmado pelo usuário ("bem legal").

**Bug do "hold reverte p/ toggle" — corrigido (1.2.1):** o usuário salvava hold mas o daemon
seguia toggle. Causa: (a) instâncias concorrentes — daemon antigo (toggle) sobrevivia ao
"reiniciar"; (b) `keyboard.unhook_all_hotkeys()` (lib 0.13.5) levanta `AttributeError` se chamado
antes de qualquer hotkey existir, derrubando o daemon antes do "pronto" na 1ª tentativa de fix.
Correções:
- **Instância única** (`_acquire_single_instance`, mutex nomeado do Windows) — 2º daemon sai sozinho.
- **Config ao vivo** (`_watch_config` observa `config.json` por mtime) — **mic/som/modo/atalho
  aplicam em ~2s, SEM reiniciar**. `_apply_activation` re-registra o atalho; unhook protegido por try/except.
- Validado no bundle: inicia em hold; troca toggle↔hold ao vivo; 2ª instância recusada.
- Instalador **1.2.1** reinstalado; rodando em modo SEGURAR.
**Falta:** confirmação humana do modo "segurar" (segurar CTRL+ALT+D e falar).

## Definition of Done — R2 FECHADA ✅ (2026-06-28)
- [x] AC-1..AC-5 implementados (fatia 1 + fatia 2)
- [x] **Confirmação humana COMPLETA:** mic + som + HUD + modo hold (segurar e falar) — tudo OK pelo usuário
- [x] Instalador repackage (`Ditar-Setup-1.2.1.exe`, 1,03 GB, instalado e rodando)
- [x] [`STATE.md`](../../STATE.md) atualizado
- [x] Reconciliação com o business case feita (R2-exec ≠ R2-original; ver business-case §11)



---

Testando o HUD do aplicativo

Está funcionando, esse HUD está bem legal

agora vai funcionar quando estiver falando ou só quando reiniciar


Ao terminar o editado e soltar o atalho, o texto deveria ser colado agora no Obsidian.

Agora testando com o Tugler, vou fechar o atalho novamente sem estar clicando nele para testar se o texto vai ser escrito sem a necessidade de ficar apertando o botão.



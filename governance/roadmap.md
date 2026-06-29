---
name: roadmap
description: Roadmap incremental do Ditar em horizontes Now/Next/Later, mapeando as releases R1–R4 do business case. Contexto base — leia em toda sessão.
alwaysApply: true
---

# Roadmap — Ditar (audio → software instalável)

> Horizontes Now/Next/Later. Detalhe de escopo e AC fica no `spec.md` de cada release.
> Justificativa e estimativas no [business case](business-case.md).

## ✅ Feito — R1 "Tem .exe"
Empacotamento provado (PyInstaller onedir + CUDA), instalador per-user 1,03 GB, sem UAC,
autostart, ícone. Ver [`_specs/R1-tem-exe/`](_specs/R1-tem-exe/spec.md).

## ✅ Feito — R2 "Ditado estilo Wispr" (1.2.1)
Mic selecionável, som suave, HUD flutuante, modos toggle+hold, config ao vivo, instância única.
**Confirmado pelo usuário.** Ver [`_specs/R2-ditado-wispr/`](_specs/R2-ditado-wispr/spec.md).

## ✅ Feito — R3 "Parece app + se mantém" (1.3.6)
- **Auto-update por delta** (É4): baixa só ~11 MB, não 1 GB ([ADR-0004](adr/0004-auto-update-delta.md)). Confirmado pelo usuário.
- **Histórico SQLite** (É3 US-3.1/3.2): grava cada ditado + janela pesquisável (menu → Histórico). US-3.3 (áudio+poda) → backlog.
- **Onboarding de privacidade** (US-2.2): tela "100% local" no 1º uso.

## 🟢 Now — R4 "Polido / distribuição"
- ✅ **Instalador completo publicado** (1.3.6): `Ditar-Setup-1.3.6.exe` (~1 GB) anexado à release
  v1.3.6, ao lado do delta. Política: toda release "Latest" carrega full + delta.
- ✅ **Fonte público sincronizado** (commit `d826909`): reescrita R1–R3 + governança commitadas/pushadas na `main`.
- US-5.3 code signing (Azure Trusted Signing) · US-5.1 fallback de injeção · US-2.3 (modelo/idioma na config) · US-3.3 (áudio+poda) · auto-mute música ao ditar.

## Princípio de priorização
A dor real do usuário fura a fila: o feedback do teste (mic + UX do ditado) virou a R2,
empurrando onboarding/histórico/update para a R3 (reconciliado no business case §11).

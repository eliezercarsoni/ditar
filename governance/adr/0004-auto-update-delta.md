---
name: adr-0004-auto-update-delta
description: ADR-0004 — auto-update por delta (só arquivos que mudaram), substitui o download do instalador inteiro do ADR-0003.
alwaysApply: false
---

# ADR-0004: Auto-update por delta (arquivos que mudaram), não o instalador inteiro

- **Status:** aceito
- **Data:** 2026-06-28
- **Decisores:** Eliezer Carsoni (dono do produto / GP), Claude Code
- **Substitui:** a etapa de *download* do [ADR-0003](0003-auto-update-github-releases-custom.md)
  (check + notificação + apply continuam válidos).

## Contexto
A fatia 2 do ADR-0003 baixava o instalador **inteiro** (~1 GB) a cada update. Na prática isso é
inviável: a CDN de releases do GitHub entrega ~**0,04–0,16 MB/s** para o usuário (Brasil) →
1 GB levaria **horas**. E é arquiteturalmente errado: ~1,8 GB do bundle são **DLLs CUDA que
NUNCA mudam** entre versões; só o código Python (embutido nos `.exe`) muda — poucos MB.

## Decisão
**Baixar só o que mudou.** Mecanismo:
1. **Build-time:** um script diffa o novo `dist/Ditar` contra o anterior (por hash) e gera
   `delta-<ver>.zip` (apenas os arquivos alterados/novos) + `manifest-<ver>.json` (hash de todos
   os arquivos) + `from_version`. Publica esses dois (pequenos) como assets da release.
2. **Cliente:** lê o manifesto da release mais nova; compara com os arquivos locais (por hash);
   se o `delta-<ver>.zip` cobre o salto (usuário na versão anterior) → baixa só ele (~MB),
   extrai sobre a pasta de instalação **via o .bat destacado** (mata → extrai → reabre).
3. **Fallback:** salto não-sequencial / delta não cobre → cai para o instalador inteiro (lento,
   raro) ou encadeia deltas.

Hospedagem segue no **GitHub Releases** (agora assets pequenos → upload e download rápidos).

**Alternativas descartadas:**
- *tufup (TUF + bsdiff):* a ferramenta "certa", com patches binários e segurança TUF, mas exige
  gestão de chaves + estrutura de repositório TUF — peso desproporcional agora.
- *Instalador inteiro (ADR-0003 fatia 2):* inviável (1 GB na CDN lenta).
- *Trocar de CDN:* reduz a lentidão, não o tamanho.

## Consequências
- **+** Download de **~MB** (não 1 GB) — prático mesmo na conexão lenta; resolve a dor real.
- **+** Mantém GitHub Releases; uploads de release viram rápidos (assets pequenos).
- **−** Tooling de diff no build + complexidade no cliente (extrair/substituir arquivos).
- **−** Salto não-sequencial precisa de fallback (instalador inteiro) — caso raro.
- **−** Sem assinatura/TUF (como no ADR-0003) até a R4; download via HTTPS do GitHub.

## Rastreabilidade
- Spec/tasks: [`_specs/R3-auto-update/`](../_specs/R3-auto-update/spec.md)
- Código: `build/make_delta.py` (novo), `updater.py` (apply de delta), `version.py`.
- Medição que motivou: delta 1.3.1→1.3.2 (ver tasks.md / compare de bundles).

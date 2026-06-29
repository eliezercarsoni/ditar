---
name: spec-r3-auto-update
description: Contrato da R3-auto-update — checar GitHub Releases, notificar e aplicar atualização. Base enquanto ativa.
alwaysApply: true
---

# Spec — R3 / Auto-update (É4)

> **Fonte da verdade.** Status: **em implementação** (fatia 1: check+notify). Tier: ver
> [ADR-0003](../../adr/0003-auto-update-github-releases-custom.md) (mecanismo, arquitetural).

## Resumo
O Ditar sabe sua versão, descobre quando há uma versão mais nova no GitHub Releases, avisa o
usuário e (fatia 2) baixa+aplica a atualização — sem reinstalar à mão.

## Critérios de aceite

### AC-1: Check automático no início *(US-4.1 — fatia 1)*
- **Dado** o daemon iniciado e conectado à internet
- **Quando** existe uma release com versão > a atual
- **Então** aparece uma notificação discreta ("Nova versão X disponível"); **sem** release,
  offline ou erro → **nada** acontece (degrada em silêncio, nunca trava nem erra).

### AC-2: Check manual pela bandeja *(US-4.1 — fatia 1)*
- **Dado** o menu da bandeja
- **Quando** o usuário clica "Verificar atualizações"
- **Então** vê o resultado: "Você está na versão mais recente" **ou** "Nova versão X disponível".

### AC-3: Baixar e aplicar *(US-4.2 — fatia 2)*
- **Dado** uma versão nova detectada
- **Quando** o usuário clica "Baixar e instalar"
- **Então** o instalador é baixado (com progresso), roda em silêncio fechando/reabrindo o Ditar,
  e o app volta já atualizado.

### AC-4: Rollback *(US-4.2 — fatia 2)*
- **Dado** uma atualização problemática
- **Quando** o usuário quer voltar
- **Então** pode reinstalar uma release anterior (o GitHub guarda todas) — documentado.

## Casos de borda
- Sem internet / sem releases / 404 → silencioso (AC-1), mensagem clara no check manual (AC-2).
- Versão da release malformada → tratar como "sem update".
- Download interrompido → não aplicar; manter a versão atual.

## Fora de escopo (R3)
- Verificação criptográfica da release (Authenticode) → R4 (code signing).
- Atualização delta / a nível de arquivo → não (reinstala o `.exe`).

## Dependência externa
Auto-update só tem efeito com **releases publicadas**. Hoje o repo `eliezercarsoni/ditar` não
tem nenhuma → publicar a primeira faz parte da fatia 2 (passo externo, ~1 GB, requer OK).

## Rastreabilidade
- Mecanismo: [ADR-0003](../../adr/0003-auto-update-github-releases-custom.md)
- Origem: business case É4 (US-4.1, US-4.2)
- Código: `version.py`, `updater.py`, `ditar.py`

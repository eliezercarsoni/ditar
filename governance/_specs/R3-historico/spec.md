---
name: spec-r3-historico
description: Contrato do Histórico de ditados (É3) — salvar em SQLite e janela pesquisável. Base enquanto ativa.
alwaysApply: true
---

# Spec — R3 / Histórico de ditados (É3)

> **Fonte da verdade.** Status: **AC-1 + AC-2 feitos** (1.3.5). Tier: Pequeno. Origem: business
> case É3 (recurso "nº1 que falta").
>
> **Validação (2026-06-28):** `db.py` (SQLite) round-trip OK (add/recent/busca); `ditar.py` grava
> cada ditado no `_do_transcribe` (texto + app em foco + modelo); janela `--history` abre no bundle
> congelado. Entregue na **v1.3.5** (delta 11 MB). US-3.3 (áudio + poda) fica no backlog.

## Resumo
Cada ditado é salvo localmente em SQLite (texto, data, app de origem, modelo) e há uma janela
para **buscar** ditados antigos e **copiar de novo**.

## Critérios de aceite

### AC-1: Salvar cada ditado *(US-3.1)*
- **Dado** o ditado ativo
- **Quando** um trecho é transcrito e colado
- **Então** ele é gravado em `%LocalAppData%\Ditar\history.db` (texto, timestamp, app em foco, modelo),
  sem travar o fluxo nem falhar o ditado se o DB der erro.

### AC-2: Janela de histórico pesquisável *(US-3.2)*
- **Dado** o menu da bandeja → "Histórico"
- **Quando** o usuário abre e digita um termo
- **Então** vê os ditados recentes filtrados (mais novos primeiro), com data e app de origem,
  e pode **copiar** o texto de um item para o clipboard.

### AC-3 (fora desta fatia — É3 completo): áudio opcional + poda por orçamento *(US-3.3)*
→ backlog (R4/depois).

## Casos de borda
- DB inexistente/corrompido → recria/ignora, nunca derruba o daemon.
- Texto vazio / "nada reconhecido" → não grava.
- Sem app em foco detectável → grava app vazio.

## Fora de escopo
- Áudio do ditado + poda (US-3.3) · export · edição de itens.

## Rastreabilidade
- Origem: business case É3 (US-3.1/3.2).
- Código: `db.py` (dados), `history.py` (janela), `ditar.py` (grava no `_do_transcribe`).

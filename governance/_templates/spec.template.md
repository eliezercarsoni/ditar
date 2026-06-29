---
name: spec
description: Contrato da release/feature (critérios de aceite). Base enquanto a release está ativa.
alwaysApply: true
---

# Spec — R<NN> <nome da release/feature>

> **Fonte da verdade.** Status: rascunho | em review | aprovado | implementado
> Os critérios de aceite são (a) o contrato, (b) o oráculo de teste, (c) o prompt para
> o agente implementar. Escreva-os para serem verificáveis.

## Resumo
<Uma frase: o que o produto passará a fazer.>

## Critérios de aceite
> Given/When/Then. Cada `AC-N` é um ID rastreável: reaparece em `tasks.md` (coluna
> "Cobre AC") e na mensagem de commit. Não renumere ACs já implementados.

### AC-1: <título do cenário>
- **Dado** <estado/pré-condição>
- **Quando** <ação/evento>
- **Então** <resultado observável e verificável>

### AC-2: <título>
- **Dado** …
- **Quando** …
- **Então** …

## Casos de borda e erros
- <ex.: sem GPU NVIDIA → fallback CPU/medium>
- <ex.: modelo ainda não baixado → barra de progresso, não trava>
- <ex.: app em foco roda como admin → comportamento esperado>

## Fora de escopo
> Vinculante. Não implemente nada aqui.
- <…>

## Rastreabilidade
- Business case: [`../business-case.md`](../business-case.md) (o "por quê")
- Design (se tier arquitetural): `./design.md`
- ADRs relacionados: <links para governance/adr/…>

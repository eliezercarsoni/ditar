---
name: governance-index
description: Índice da governança do projeto Ditar. Aponta para business case, tailoring, STATE, roadmap, ADRs e templates.
alwaysApply: false
---

# Governança — Projeto Ditar (audio → software instalável)

Esta pasta é a **governança** do projeto que transforma o `audio/` (hoje script
Python) em um **software Windows instalável**. O modelo foi **tailorizado** a partir
do scaffold [`@igoruehara/spec-driven`](../../spec-driven) (esteira SDD) para o
contexto **solo + Claude Code, brownfield, baixa cerimônia**.

> Princípio herdado do SDD: **a spec é o contrato, o ADR é a memória, o resto é andaime.**
> Documentação não apodrece porque ela *governa*, não *descreve*.

## Mapa dos artefatos

| Arquivo | Pergunta que responde | Tipo de memória |
|---|---|---|
| [`business-case.md`](business-case.md) | **Por quê** fazer e **para quem**? Custos, benefícios, métricas | Ponto no tempo (justificativa) |
| [`tailoring.md`](tailoring.md) | **Qual governança** adotamos do spec-driven e por quê | Decisão de processo |
| [`roadmap.md`](roadmap.md) | Em **que ordem** entregamos (Now/Next/Later → R1–R4) | Vivo |
| [`STATE.md`](STATE.md) | **Onde paramos**, próximo passo, bloqueios | Volátil |
| [`adr/`](adr/) | **Por que** decidimos X (decisões difíceis de reverter) | Durável / imutável |
| [`_templates/`](_templates/) | Andaime de `spec.md` + `tasks.md` para cada release | Template |

## Fluxo de trabalho (tailorizado)

```
business-case (já feito)  →  roadmap (R1–R4)  →  por release: spec.md + tasks.md  →  implementar  →  ADR + STATE
```

1. **Antes de codar**, descubra o **tier** da mudança (ver `tailoring.md` §Tiers).
2. Release não-trivial abre uma pasta `_specs/RNN-nome/` com `spec.md` (+ `tasks.md`).
3. Decisão difícil de reverter (empacotador, updater, assinatura) **vira ADR**.
4. Ao pausar/retomar a sessão com o Claude Code, atualize/leia o `STATE.md`.

## Estado atual

Fase **discovery concluída** (este business case). Próximo passo registrado em
[`STATE.md`](STATE.md). Nada foi implementado ainda — "antes de planejar de fato".

---
name: adr-0001-governanca-sdd-tailorizada
description: ADR-0001 — adoção de uma governança SDD tailorizada (do spec-driven) para o projeto Ditar.
alwaysApply: false
---

# ADR-0001: Adotar governança SDD tailorizada (do `spec-driven`)

- **Status:** aceito
- **Data:** 2026-06-28
- **Decisores:** Eliezer Carsoni (dono do produto / GP), Claude Code

## Contexto
O projeto vai sair de um par de scripts Python para um software Windows instalável, o que aumenta a quantidade de decisões técnicas difíceis de reverter (empacotador, updater, assinatura) e o valor de continuidade entre sessões intermitentes com o Claude Code. Sem governança, essas decisões e o "onde paramos" se perdem.

Existe à mão o scaffold [`@igoruehara/spec-driven`](../../../spec-driven) — uma esteira SDD madura (Lean Inception → DDD → TDD → SDD), porém desenhada para **times**, com camadas DDD, métricas de fluxo, gates de PR, multi-cliente e integrações de ferramentas.
Aplicá-la inteira a um projeto **solo, pequeno, brownfield e de domínio raso** seria
burocracia que viola o princípio de simplicidade do `C:\fabrica\CLAUDE.md`.

## Decisão
Vamos adotar uma **versão tailorizada** do `spec-driven`, documentada em
[`tailoring.md`](../tailoring.md). Em resumo:

- **Adotado:** tiers de cerimônia, `spec.md` (AC Given/When/Then), `tasks.md`, `STATE.md`,
  ADRs, `roadmap.md` Now/Next/Later, princípio "spec é a fonte da verdade" + verificação
  de conhecimento.
- **Adaptado:** DoR/DoD (gate = testes passam + verificação manual do instalador, em vez
  de cobertura/SAST/PR review); glossário inline; `product.md` = o business case;
  `design.md` só no tier arquitetural; CI = build do instalador, não gate de spec.
- **Descartado:** camadas DDD em `src/`, `/metricas`, `/revisar-pr`, `/integracoes` +
  trava MCP, geração multi-cliente, `/camada-agentica`.

A governança vive em `audio/governance/` (não na estrutura `docs/`+`specs/` do
spec-driven), para concentrar tudo num lugar e não competir com a estrutura existente da pasta.

**Alternativas descartadas:**
- *Adotar o spec-driven por inteiro (rodar `npx`):* gera 15 skills, camadas DDD e CI de gate — cerimônia desproporcional ao projeto solo.
- *Não ter governança formal:* perde rastreabilidade das decisões técnicas e a
  continuidade entre sessões — exatamente o que mais dói neste projeto.

## Consequências
- **+** Cerimônia proporcional ao risco; decisões técnicas ganham um lar (ADR) e o
  trabalho ganha continuidade (STATE) sem peso de processo de time.
- **+** Fidelidade ao SDD onde ele agrega (spec como contrato testável), o que torna trivial gerar as specs das releases R1–R4.
- **−** A governança fica "à mão" (mantida manualmente), sem as skills/automações do spec-driven (`/auditar`, `/nova-feature` etc.).
- **−** Se o app crescer muito (UI de config + histórico), a ausência de camadas em `src/` pode cobrar refatoração — gatilho de reavaliação já registrado no `tailoring.md`.

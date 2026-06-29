---
name: tailoring
description: Decisão de tailoring — quais elementos da esteira spec-driven foram adotados, adaptados ou descartados para o projeto Ditar, e por quê. Puxe ao discutir processo/cerimônia.
alwaysApply: false
---

# Tailoring da Governança — do `spec-driven` para o Ditar

> **Tailoring** (PMBOK): adaptar deliberadamente processos, artefatos e gates ao
> **contexto** do projeto — não aplicar um framework por inteiro só porque ele existe.
> Aqui, partimos da esteira [`@igoruehara/spec-driven`](../../spec-driven) (SDD completa,
> desenhada para **times**) e a reduzimos ao que faz sentido para **este** projeto.

## 1. Contexto que dirige o tailoring

| Fator do projeto | Valor | Implicação para a cerimônia |
|---|---|---|
| Time | 1 pessoa (Eliezer) + Claude Code | Sem PR entre pessoas, sem review assíncrono de RFC, sem fluxo de aprovação |
| Tamanho | Pequeno (`transcrever.py` + `ditar.py`, ~600 linhas) | Decomposição leve; nada de pipeline pesado |
| Maturidade | **Brownfield** — engine já funciona | Discovery já feito (este business case); foco é empacotar/maturar, não modelar domínio novo |
| Domínio | Raso (transcrição/ditado) | DDD tático (bounded contexts, camadas) é overkill |
| Risco | Concentrado em **empacotamento/distribuição** (CUDA, PyInstaller, updater, assinatura) | As decisões difíceis de reverter são **técnicas**, não de domínio → ADR é o artefato-chave |
| Natureza | Open-source pessoal | Sem compliance, SLA ou métricas de fluxo corporativas |

**Conclusão de tailoring:** manter os artefatos **leves e de alto valor** (spec, ADR,
STATE, roadmap, tiers) e **cortar a maquinaria de time** (DDD em camadas, métricas de fluxo, gates de PR, multi-cliente, integrações de ferramentas).

## 2. Decisão por elemento

Legenda: ✅ **Adotar** (como está) · 🔧 **Adaptar** (versão reduzida) · ❌ **Descartar**.

| Elemento do spec-driven | Decisão | Justificativa (contexto) |
|---|---|---|
| **Tiers de cerimônia** (Trivial/Pequeno/Arquitetural) | ✅ | Mecanismo perfeito p/ solo: escala a cerimônia ao risco, evita over-engineering |
| **`spec.md`** (AC em Given/When/Then) | ✅ | Vira o contrato testável de cada release; o business case já tem US com AC |
| **`tasks.md`** (decomposição + rastreio AC) | 🔧 | Mantido, sem a integração Jira/issues |
| **`STATE.md`** (memória volátil entre sessões) | ✅ | Continuidade com o Claude Code é alto valor num projeto intermitente |
| **ADR** (decisão durável, imutável) | ✅ | As decisões reais aqui (empacotador, updater, assinatura) são difíceis de reverter — ADR é o lar delas |
| **`roadmap.md`** (Now/Next/Later) | ✅ | Mapeia direto R1→R4 do business case |
| **DoR / DoD** | 🔧 | Mantém os gates; troca "cobertura ≥ X / SAST / review de PR" por "**testes passam + verificação manual do instalador**" (app desktop, solo) |
| **Verificação de conhecimento / "spec é a fonte da verdade"** | ✅ | Já alinhado ao `C:\fabrica\CLAUDE.md`; reforça não-inventar |
| **Linguagem ubíqua / `glossary.md`** | 🔧 | Glossário curto **inline** neste doc (§4); domínio raso não justifica arquivo separado |
| **`product.md` / `domain.md` / `design.md`** (5 artefatos por feature) | 🔧 | `product.md` = este business case; `domain.md` dispensado; `design.md` **só** no tier arquitetural (ex.: spike de empacotamento) |
| **Arquitetura em camadas DDD** (`interfaces→application→domain←infrastructure`) | ❌ | 2 scripts não pedem isso. **Gatilho de reavaliação:** se a tela de config + histórico crescerem, reabrir como ADR |
| **Pipeline Lean Inception completo** | 🔧 | Reduzido a **assessment brownfield** — discovery já está no business case |
| **`/integracoes` + trava de conta MCP** | ❌ | Sem ferramentas de time (Jira/Notion/Confluence) |
| **Geração multi-cliente** (Cursor/Codex/Copilot/Gemini/Windsurf) | ❌ | Só Claude Code |
| **`/metricas`** (Lead Time / Throughput) | ❌ | Solo; sem fluxo a medir. Métrica que importa = critérios de sucesso do business case |
| **`/revisar-pr`** (gate formal de PR) | ❌ | Solo; self-review no commit |
| **CI `esteira.yml`** (gate de spec no PR) | 🔧 | Trocado por um **workflow de build** que gera o instalador no release (valor real para distribuição) |
| **`/camada-agentica`** (gerar rules/subagents) | ❌ | `CLAUDE.md` do workspace já cobre as convenções do agente |

## 3. Tiers de cerimônia (adotado, com gatilho de escalonamento)

Pergunta que define o tier: *"isto introduz decisão difícil de reverter ou nova fronteira?"*

| Tier | Quando | Artefatos exigidos |
|---|---|---|
| **Trivial** | ≤ 3 arquivos, sem decisão (typo, ajuste de flag) | só o commit |
| **Pequeno** | feature/release isolada, < 10 tasks | `spec.md` (+ `tasks.md` se passar de ~5 passos) |
| **Arquitetural** | decisão difícil de reverter (empacotador, updater, assinatura, mudança de stack) | `design.md` **antes** de implementar **+ ADR** |

> **Escalonamento dinâmico:** mesmo no tier Pequeno, liste os passos atômicos antes de codar; se passar de ~5 passos ou surgir dependência complexa, **suba de tier**.
> Aplicação imediata: o **spike de empacotamento CUDA (US-1.1)** é **arquitetural** —
> exige `design.md` + ADR-0002 antes de fechar a rota.

## 4. Glossário mínimo (linguagem ubíqua)

Use **exatamente** estes termos em código, specs, commits e conversa:

- **Ditar** — nome do produto (o app instalável). O módulo de ditado ao vivo é o `ditar.py`.
- **Transcrever** — o modo em lote (arquivo/pasta → `.srt` + `.md`), `transcrever.py`.
- **Engine** — faster-whisper/CTranslate2 + modelo Whisper carregado em VRAM.
- **Daemon** — o processo residente na bandeja (tray) que escuta o hotkey.
- **Injeção** — colar o texto transcrito no app em foco (clipboard + Ctrl+V).
- **Release (RNN)** — incremento entregável (R1–R4 no roadmap). Não confundir com release do GitHub.
- **Bundle** — saída "congelada" do PyInstaller (Python + deps + DLLs CUDA).

## 5. O que NÃO muda

As convenções do `C:\fabrica\CLAUDE.md` (princípios de execução, simplicidade,
mudanças cirúrgicas) continuam valendo **acima** desta governança. Em conflito, o
princípio da simplicidade vence a cerimônia — tailoring existe justamente para isso.

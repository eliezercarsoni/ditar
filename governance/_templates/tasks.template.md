---
name: tasks
description: Decomposição e gates da release/feature. Puxe ao implementar.
alwaysApply: false
---

# Tasks — R<NN> <nome da release/feature>

> Cada task **mapeia para um ou mais `AC-N`** (rastreabilidade spec → task → commit) e
> tem um **gate**: o que prova que ela está pronta. `[P]` = pode rodar em paralelo.

## Plano
| #  | Task | Cobre AC | Depende de | Gate (como verificar) | Status |
|----|------|----------|------------|-----------------------|--------|
| 1  | <ex.: montar Ditar.spec do PyInstaller> | AC-1 | — | `pyinstaller Ditar.spec` builda sem erro | todo |
| 2  | <ex.: validar DLLs CUDA no bundle>      | AC-1 | 1 | `Ditar.exe` transcreve áudio de teste na GPU | todo |
| 3  | <ex.: instalador Inno Setup>           | AC-2 | 2 | instala em %LocalAppData% sem UAC | todo |

> Uma task só vira `done` quando o **gate passa**. Um commit por task.

## Plano de verificação
> Tailorizado: app desktop/instalador é validado por **smoke test + verificação manual**,
> não por cobertura de testes unitários.
- Automático: <ex.: `ditar --check` carrega o modelo e sai sem erro>
- Manual: <ex.: instalar do zero numa máquina/VM sem Python → tray sobe → ditado cola texto>

## Divergências (SPEC_DEVIATION)
> Se a implementação precisar fugir da spec, registre aqui antes de seguir.
- [ ] <task # · motivo · resolução: corrigir código OU atualizar spec/ADR>

## Definition of Done (tailorizado)
- [ ] Todos os AC verdes pelo gate (smoke test + verificação manual do instalador)
- [ ] Nenhum `SPEC_DEVIATION` pendente
- [ ] Decisões difíceis de reverter viraram ADR em `governance/adr/`
- [ ] Glossário (`tailoring.md` §4) atualizado se surgiu termo novo
- [ ] A spec reflete o que foi construído
- [ ] [`governance/STATE.md`](../STATE.md) atualizado (próximo passo / decisões)

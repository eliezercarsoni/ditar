---
name: adr-0005-code-signing-trusted-signing-gatilho
description: ADR-0005 — code signing (US-5.3) via Azure Trusted Signing; mantém adiado e fixa gatilho + pré-requisito de elegibilidade. Detalha o que o ADR-0002 deixou em uma linha.
alwaysApply: false
---

# ADR-0005: Code signing (US-5.3) — manter adiado, com gatilho e elegibilidade explícitos

- **Status:** aceito
- **Data:** 2026-06-29
- **Decisores:** Eliezer Carsoni (dono do produto / GP), Claude Code
- **Detalha:** a decisão #6 do [ADR-0002](0002-empacotamento-pyinstaller-inno-winsparkle.md)
  ("code signing adiado para a R4"), sem substituí-la.

## Contexto
O `Ditar-Setup-<ver>.exe` sai do pipeline (`pyinstaller → ISCC → gh release`) **sem assinatura
digital**. Em máquina de usuário novo, o **Defender SmartScreen** exibe *"editor desconhecido"*
e esconde o botão de instalar atrás de "Mais informações → Executar assim mesmo" — lê como
malware e derruba a conversão. É o risco de **probabilidade Alta / impacto Médio** já listado no
[business-case.md §8](../business-case.md), e a fricção #1 de adoção de um app desktop
distribuído fora da Microsoft Store.

Economia das rotas de assinatura (estado 2026):
- **Cert OV tradicional:** ~US$ 200–400/ano; mesmo assinado, o SmartScreen só silencia depois
  de **acumular reputação** (semanas de downloads).
- **Cert EV:** confiança imediata no SmartScreen, ~US$ 300–600/ano **e** exigia token USB (HSM)
  — incompatível com CI/automação.
- **Azure Trusted Signing:** **~US$ 9,99/mês** (tier Basic), chave em **HSM na nuvem**, assina
  via `signtool` + dlib do Azure — encaixa direto no fluxo de release. Por ser emissão gerenciada
  da própria Microsoft, o tratamento de reputação no SmartScreen é favorável. **Atrito de
  elegibilidade:** exige identidade verificada; para pessoa física a Microsoft pede ~3 anos de
  histórico verificável — o que pode empurrar para uma rota de pessoa jurídica/entidade.

## Decisão
**Manter a US-5.3 adiada** (não assinar agora). Quando ativar, usar **Azure Trusted Signing**
(não OV nem EV-com-token), pelo custo e pela compatibilidade com o pipeline automatizado.

- **Gatilho para ativar:** evidência de usuários reais travando no SmartScreen **ou** decisão de
  divulgar o Ditar em escala (post, HN, lista, etc.). Enquanto a base for pequena, o aviso é
  contornável e "aceitável para OSS no início" — o ROI da assinatura é baixo.
- **Pré-requisito a validar ANTES de comprar:** elegibilidade no Trusted Signing (pessoa física
  com 3 anos de histórico vs. usar entidade). Resolver isso é a primeira tarefa quando o gatilho
  disparar, não o pagamento.

**Alternativas descartadas:** cert OV (não silencia o SmartScreen sem reputação acumulada) e
cert EV com token USB (caro e quebra CI).

## Consequências
- **+** Custo trivial (~US$ 120/ano) quando ativar, para matar a barreira #1 de adoção.
- **+** Gatilho e pré-requisito ficam registrados — a ativação não depende de relembrar contexto.
- **−** Até o gatilho, todo usuário novo enfrenta a fricção do SmartScreen (dívida consciente).
- **−** Elegibilidade pode forçar rota de pessoa jurídica — risco a confirmar antes do commit.

## Rastreabilidade
- Backlog: US-5.3 (R4) em [business-case.md §7/§R4](../business-case.md) e [roadmap.md](../roadmap.md).
- Gatilho-irmão registrado em [STATE.md](../STATE.md) (seção de decisões adiadas).
- Origem: [ADR-0002 decisão #6](0002-empacotamento-pyinstaller-inno-winsparkle.md).

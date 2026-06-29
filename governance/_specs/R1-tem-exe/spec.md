---
name: spec-r1-tem-exe
description: Contrato da Release R1 "Tem .exe" — instalar e rodar o Ditar sem Python. Base enquanto a R1 está ativa.
alwaysApply: true
---

# Spec — R1 "Tem .exe"

> **Fonte da verdade.** Status: **aprovado** (pronto para `tasks.md` + spike)
> Os critérios de aceite são (a) o contrato, (b) o oráculo de verificação, (c) o prompt para implementar. Tier: **Pequeno**, exceto **AC-1/AC-2 (empacotamento CUDA) = Arquitetural**
> → exigem `design.md` antes de implementar (ver [ADR-0002](../../adr/0002-empacotamento-pyinstaller-inno-winsparkle.md)).

## Resumo
Um usuário sem Python instalado consegue **instalar o Ditar por um `.exe`** e usar o
ditado por voz (e a transcrição em lote) com aceleração por GPU — instalação per-user,
sem prompt de admin, com ícone e atalho próprios.

## Escopo (épicos/US cobertos)
É1 (executável + instalador): US-1.1, US-1.2, US-1.3, US-1.4 · É2: US-2.1.

## Critérios de aceite

### AC-1: Rodar sem Python, com GPU *(US-1.1 — Arquitetural)*
- **Dado** uma máquina Windows **sem Python instalado**, com GPU NVIDIA e o modelo já em cache
- **Quando** o usuário inicia `Ditar.exe`
- **Então** o daemon sobe na bandeja, o atalho `CTRL+ALT+ESPAÇO` grava e, ao parar, o texto
  é transcrito **na GPU** e colado no app em foco — sem nenhuma dependência de Python do sistema.

### AC-2: Fallback para CPU sem GPU NVIDIA *(US-1.1 — borda)*
- **Dado** uma máquina sem GPU NVIDIA (ou com erro de CUDA)
- **Quando** o usuário inicia `Ditar.exe`
- **Então** o app cai para CPU com modelo `medium` (lógica já em [`ditar.py:236`](../../../ditar.py))
  e o ditado continua funcionando, sem crash.

### AC-3: Instalador per-user sem UAC *(US-1.2)*
- **Dado** o instalador gerado pelo Inno Setup
- **Quando** o usuário o executa com uma conta padrão (sem privilégio de admin)
- **Então** o Ditar é instalado em `%LocalAppData%\Ditar` **sem prompt de UAC** e um atalho
  é criado no Menu Iniciar.

### AC-4: Iniciar com o Windows (opcional) *(US-1.3)*
- **Dado** a tela de opções do instalador
- **Quando** o usuário marca "iniciar com o Windows"
- **Então** é criada uma entrada de inicialização (chave Run) que sobe o Ditar **sem janela
  de console** no login; desmarcado, nenhuma entrada é criada.

### AC-5: Progresso do download do modelo na 1ª execução *(US-1.4)*
- **Dado** que o modelo Whisper ainda não está em cache (`%USERPROFILE%\.cache\huggingface`)
- **Quando** o Ditar é iniciado pela primeira vez
- **Então** uma indicação de progresso do download é exibida e o app **não aparenta estar
  travado**; ao concluir, o ditado fica disponível.

### AC-6: Identidade visual própria *(US-2.1)*
- **Dado** o Ditar instalado
- **Quando** o usuário o vê na bandeja, no Menu Iniciar, no instalador e na barra de tarefas
- **Então** o ícone próprio (`.ico`) do produto aparece em todos esses pontos (não o ícone genérico do Python).

### AC-7: CLI de transcrição em lote disponível
- **Dado** o Ditar instalado
- **Quando** o usuário executa `Transcrever.exe <arquivo|pasta>`
- **Então** os `.srt` + `.md` são gerados como hoje, a partir do mesmo bundle, sem Python do sistema.

### AC-8: Instalador enxuto
- **Dado** o instalador final
- **Quando** se mede seu tamanho
- **Então** ele tem **< 2 GB** (o modelo é baixado sob demanda, não embutido — ADR-0002).

## Casos de borda e erros
- Download do modelo **interrompido** (rede cai) → ao reabrir, retoma/refaz sem corromper o cache.
- App em foco rodando **como administrador** → injeção pode falhar (limitação do hook de teclado já documentada no `README.md`); comportamento esperado: avisar, não crashar.
- Bundle não acha as **DLLs CUDA** → cair no fallback CPU (AC-2), não travar.
- Segunda instalação por cima da primeira → atualiza no lugar, preserva o cache do modelo.

## Fora de escopo (vinculante — não implementar na R1)
- Tela de configurações (hotkey/modelo/idioma por UI) → **R2** (US-2.3).
- Histórico / SQLite → **R2** (É3).
- Auto-update / rollback → **R3** (É4).
- Code signing / assinatura → **R4** (US-5.3).
- Escada de fallback de injeção e push-to-talk → **R4** (US-5.1/5.2).
- Onboarding de privacidade (tela) → **R2** (US-2.2). *(Na R1, basta o texto no instalador.)*

## Rastreabilidade
- Business case: [`../../business-case.md`](../../business-case.md) (o "por quê")
- Decisão de rota: [`ADR-0002`](../../adr/0002-empacotamento-pyinstaller-inno-winsparkle.md)
- Design (US-1.1/AC-1, arquitetural): `./design.md` — **a produzir no spike**
- Decomposição: `./tasks.md` — **próximo artefato**

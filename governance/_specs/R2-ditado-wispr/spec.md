---
name: spec-r2-ditado-wispr
description: Contrato da R2 "Ditado estilo Wispr" — seleção de mic, som suave, HUD visual e modos hold+toggle. Base enquanto a R2 está ativa.
alwaysApply: true
---

# Spec — R2 "Ditado estilo Wispr"

> **Fonte da verdade.** Status: **em implementação** (fatia 1 feita; fatia 2 pendente).
> Origem: feedback do usuário (2026-06-28) — o ditado deve ser como o Wispr: **som suave** (não o bip agudo) e um **widget visual** mostrando quando está ouvindo. Tier: **Pequeno**
> (UI + config; sem decisão difícil de reverter), exceto o **HUD coexistir com pystray+CUDA**
> no mesmo processo, que é o ponto técnico de atenção (ver tasks.md).

## Resumo
O ditado por voz ganha cara de produto: o usuário escolhe o microfone, ouve um sinal
sonoro discreto, vê um HUD do estado e pode ativar por **toggle** ou **segurando** a tecla.

## Critérios de aceite

### AC-1: Seleção de microfone *(fatia 1 ✅)*
- **Dado** que o microfone certo não é o padrão do Windows
- **Quando** o usuário escolhe outro dispositivo em Configurações (ou `--mic N`)
- **Então** a gravação passa a usar esse microfone, a escolha **persiste** (`config.json`) e
  vale na próxima gravação **sem reiniciar** o app.

### AC-2: Som suave *(fatia 1 ✅)*
- **Dado** o ditado ativo
- **Quando** a gravação inicia/para
- **Então** toca um sinal **curto e suave** (seno com fade), nunca o bip agudo anterior; e há
  opção de **desligar o som** em Configurações.

### AC-3: Modos de ativação toggle + hold *(fatia 2)*
- **Dado** o modo configurado
- **Quando** em **toggle**: aperta para iniciar, aperta de novo para parar; em **hold**:
  segura o atalho enquanto fala e **solta** para transcrever
- **Então** o texto é transcrito e colado conforme o modo escolhido.

### AC-4: HUD visual *(fatia 2)*
- **Dado** uma gravação/transcrição em andamento
- **Quando** o estado muda
- **Então** uma **pílula flutuante** (perto do rodapé) mostra "Ouvindo…" / "Escrevendo…" e
  **some** ao voltar ao ocioso.

### AC-5: Configurações persistentes e acessíveis *(fatia 1 ✅ parcial)*
- **Dado** o app instalado
- **Quando** o usuário abre Configurações pela bandeja
- **Então** vê e edita microfone e som (na fatia 2: também modo e atalho), salvos em `config.json`.

## Casos de borda
- Nenhum microfone disponível → usar padrão / avisar, não crashar.
- Dispositivo salvo sumiu (desconectado) → cair no padrão do Windows.
- HUD em multimonitor → posicionar no monitor principal.
- Modo hold com evento de "soltar" perdido → failsafe por tempo máximo de gravação.

## Fora de escopo (R2)
- Auto-mute de música ao ditar (tip do Wispr) → backlog.
- Histórico / SQLite → R3.
- Onboarding com tela de privacidade → R3.

## Rastreabilidade
- Origem: feedback do usuário + prints do Wispr (sessão 2026-06-28).
- Código: [`config.py`](../../../config.py), [`settings.py`](../../../settings.py), [`ditar.py`](../../../ditar.py).
- Decomposição: [`tasks.md`](tasks.md).

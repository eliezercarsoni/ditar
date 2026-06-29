---
name: adr-0002-empacotamento
description: ADR-0002 — rota de empacotamento e distribuição do Ditar (PyInstaller onedir + Inno Setup + auto-update).
alwaysApply: false
---

# ADR-0002: Empacotamento e distribuição via PyInstaller (onedir) + Inno Setup + auto-update

- **Status:** aceito
- **Data:** 2026-06-28
- **Decisores:** Eliezer Carsoni (dono do produto / GP), Claude Code

## Contexto
O `ditar` precisa virar um software instalável no Windows sem exigir Python/venv/pip
(ver [business-case.md](../business-case.md)). As forças em jogo:

- O **engine** é Python 3.12 + faster-whisper/CTranslate2 + DLLs CUDA (cuBLAS/cuDNN/nvrtc)
  carregadas em runtime — hoje via injeção de PATH em [`transcrever.py:32`](../../transcrever.py).
- O **modelo** Whisper (`large-v3-turbo`, ~1,5 GB) fica em cache no HF
  (`%USERPROFILE%\.cache\huggingface`), baixado uma vez.
- Alvo: instalação **per-user, sem admin/UAC** (padrão observado no Wispr, que instala em
  `%LocalAppData%`), com atalho, ícone e auto-update — o "trio" que o FluidVoice usa para
  parecer software de verdade.
- Restrição-mãe: **simplicidade** (`C:\fabrica\CLAUDE.md`) — não reescrever o que funciona.

## Decisão
Vamos empacotar e distribuir o Ditar assim (**Opção C** do business case):

1. **PyInstaller em modo `onedir`** (uma pasta com `.exe` + dependências), gerando
   `Ditar.exe` (daemon/tray) e `Transcrever.exe` (CLI). **Não** usar `onefile`.
2. **DLLs CUDA incluídas no bundle**; adaptar a descoberta de PATH ao caminho "congelado"
   (`sys._MEIPASS` / `_internal`) — detalhado no `design.md` da US-1.1 (spike).
3. **Modelo Whisper NÃO embutido** — baixado do HF na 1ª execução com barra de progresso
   (mantém o instalador em ~1–2 GB em vez de ~3,5 GB).
4. **Inno Setup** como instalador, instalando em `%LocalAppData%\Ditar` (per-user, sem UAC),
   com atalho no Menu Iniciar, ícone próprio e checkbox opcional "iniciar com o Windows".
5. **Auto-update via GitHub Releases** com **WinSparkle** (appcast XML, plug-and-play) como
   escolha primária; **tufup** como alternativa se quisermos atualização segura por TUF.
   Implementação fica na **R3** (não bloqueia a R1).
6. **Code signing adiado** para a **R4** (Azure Trusted Signing, ~US$ 10/mês). Até lá, o
   SmartScreen exibirá "editor desconhecido" — aceitável para um projeto OSS no início.

**Alternativas descartadas:**
- *PyInstaller `onefile`:* re-extrai todo o bundle para `%TEMP%` a cada inicialização —
  lento com DLLs CUDA grandes e gatilho frequente de antivírus. O ganho (1 arquivo) não
  compensa o custo de boot.
- *Nuitka:* compila para C, bundle menor/mais rápido, mas configuração de CUDA/CTranslate2
  é mais frágil e o ganho não justifica o risco agora. Reconsiderar se o tamanho/boot virar problema.
- *Squirrel.Windows (o que o Wispr usa):* feito para .NET/Electron (empacota via NuGet);
  desconfortável para um app Python+CUDA. Replicamos o *comportamento* (per-user, update
  silencioso, rollback) com Inno Setup + WinSparkle, sem herdar o Squirrel.
- *MSIX:* sandbox/containerização atrapalha o acesso a GPU, microfone global e injeção de
  teclado em outros apps — incompatível com a natureza do ditado.
- *Reescrita nativa (C#/.NET ou Tauri + sidecar Python):* descarta o engine que já funciona;
  viola "simplicidade primeiro" (Opção B do business case).
- *Embutir o modelo de 1,5 GB no instalador:* instalador de ~3,5 GB assusta e duplica o que
  o cache do HF já resolve.

## Consequências
- **+** Reaproveita 100% do engine atual; esforço concentrado na "casca".
- **+** Instalação per-user sem UAC → atrito mínimo, igual ao Wispr.
- **+** Instalador enxuto (~1–2 GB) com modelo sob demanda.
- **+** Caminho claro e incremental para auto-update (R3) e assinatura (R4) sem retrabalho.
- **−** Bundle `onedir` é uma pasta (não um único arquivo) — o instalador resolve isso para o usuário final.
- **−** Empacotar CUDA no PyInstaller é o ponto de maior risco técnico → mitigado por um
  **spike arquitetural** (US-1.1) com `design.md` antes de fechar a rota.
- **−** Sem assinatura até a R4, há fricção de SmartScreen na primeira execução.

## Rastreabilidade
- Origem: [business-case.md §5](../business-case.md)
- Implementado em: [`_specs/R1-tem-exe/spec.md`](../_specs/R1-tem-exe/spec.md)
- Design detalhado do bundle CUDA: `_specs/R1-tem-exe/design.md` (a produzir no spike da US-1.1)

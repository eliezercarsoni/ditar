---
name: business-case
description: Business case do projeto Ditar — justificativa, benchmark (FluidVoice/Wispr), opções, recomendação, backlog ágil e métricas. Puxe ao discutir escopo, valor ou priorização.
alwaysApply: false
---

# Business Case — Ditar: de script a software instalável

> **Status:** aprovado para iniciar planejamento · **Data:** 2026-06-28 · **Autor:** Eliezer Carsoni (atuando como GP)
> **Patrocinador / dono do produto:** Eliezer Carsoni · **Time:** solo + Claude Code

## 1. Sumário executivo

O `audio/` (publicado como `eliezercarsoni/ditar`, MIT) já tem um **engine competitivo**:
transcrição em lote e ditado por voz ao vivo, 100% locais, acelerados por GPU, com
qualidade equivalente ao Whisper large-v3. O que falta **não é tecnologia de núcleo** —
é a **casca de produto**: hoje o uso exige Python, venv, `pip` e edição do `$PROFILE`,
o que torna o app **não-distribuível** e friccionado até para o próprio autor ao trocar
de máquina.

Este business case propõe transformar o `ditar` em um **aplicativo Windows instalável
em 1 clique** (`.exe` + instalador), preservando seu diferencial permanente sobre o
Wispr Flow: **local, gratuito, sem conta e sem áudio saindo da máquina**. A rota
recomendada — **PyInstaller (onedir) + Inno Setup + auto-update via GitHub Releases** —
entrega o executável em ~2 sprints, a custo **US$ 0**, sem reescrever o que já funciona.

## 2. Contexto e necessidade de negócio

| Dor atual | Evidência | Consequência |
|---|---|---|
| Instalação exige stack de dev | `README.md`: clonar → `winget` Python+ffmpeg → venv → `pip install` → editar `$PROFILE` | Inviável para leigos; fricção real para o autor |
| Não distribuível | Publicado como repo Python (MIT) | Alcance do projeto open-source travado |
| Concorrência paga e na nuvem | Wispr Flow: assinatura (~US$ 12–15/mês), processa áudio remoto | Existe demanda por alternativa local/grátis — falta só a embalagem |
| Sem identidade de "app" | Sem `.ico`, sem atalho, sem auto-update, sem histórico, sem tela de config | Percepção de "script", não de software |

**Oportunidade:** o engine já está pronto; o esforço marginal para virar produto é baixo
e o retorno (distribuição, portfólio open-source, possível open-core) é alto.

## 3. Benchmark — o que aprender de cada referência

### 3.1 FluidVoice (macOS, Swift, GPLv3, ~3,3k ⭐) — a referência de *maturidade de produto*

Mesma ideia do nosso `ditar`, com anos de polimento. **Validou nossa arquitetura**
(ditado por hotkey + injeção via clipboard com restauração — exatamente
[`ditar.py:115`](../ditar.py)). Padrões a copiar (conceito, **não** código — GPLv3 é viral):

- **Trio "instalador + zip portátil + auto-updater"** — é isto que vira "app".
- **Updater via GitHub Releases com verificação de assinatura + rollback** (guarda 3 versões).
- **Abstração de provider** (1 interface, N engines de transcrição).
- **Histórico** com texto bruto+processado, timestamp, app de origem, modelo — e **poda de áudio por orçamento de bytes**.
- **Download do modelo sob demanda com barra de progresso** (+ checksum/resume, que eles não têm).
- **Texto de permissão que tranquiliza** ("processado localmente, nunca enviado a servidores").

Descartado (macOS-only): overlay no notch, CoreML, notarização/DMG/Gatekeeper, AXUIElement.

### 3.2 Wispr Flow (Windows, Electron + Squirrel) — a referência de *empacotamento Windows*

Disecado em `C:\Users\eliez\AppData\Local\WisprFlow`. Arquitetura **oposta** à nossa
(nuvem/SaaS, conta, assinatura) → **não copiamos o miolo**, copiamos a **casca**:

| Evidência no disco | Lição |
|---|---|
| `app-1.5.x` (pastas por versão) + `Update.exe` + `Squirrel-*.log` | Auto-update silencioso **com rollback** é estado da arte |
| Instalado em `%LocalAppData%` | Instalação **per-user, sem UAC/admin** → zero fricção |
| `better_sqlite3.node` | Histórico local em **SQLite** desde o dia 1 |
| `app.ico` + atalhos (Start Menu) | Identidade visual + lançador |
| Electron (paks, `app.asar`, `ffmpeg.dll`), nuvem, conta, 60+ locales, Jabra | **Rejeitar** — peso morto / over-scope para nós |

> **Nota técnica:** Squirrel.Windows é feito para .NET/Electron (empacota via NuGet);
> para um app **Python+CUDA** é desconfortável. Replicamos o *comportamento* dele com
> **Inno Setup + WinSparkle/tufup**, não o Squirrel em si.

**Trunfo permanente sobre o Wispr:** 100% local, sem mensalidade, sem áudio na nuvem.
Esse é o coração da proposta de valor.

## 4. Opções analisadas

| # | Opção | Veredito |
|---|---|---|
| A | **Não fazer nada** (continuar script) | ❌ Mantém o projeto inerte e preso ao Python na máquina |
| B | **Reescrever em nativo** (C#/.NET ou Tauri + sidecar Python) | ❌ Custo alto; descarta engine que já funciona; viola "simplicidade primeiro" |
| C | **PyInstaller (onedir) + Inno Setup + auto-update** ⭐ | ✅ **Recomendada** — máximo de produto, mínimo de reescrita |

## 5. Recomendação (Opção C) — rota técnica

1. **PyInstaller modo `onedir`** (não `onefile`: este re-extrai a cada boot, lento com DLLs CUDA e dispara antivírus). Gera `Ditar.exe` (daemon/tray) e `Transcrever.exe` (CLI).
2. **Adaptar a injeção de DLLs CUDA** ([`transcrever.py:32`](../transcrever.py)) ao caminho "congelado" (`sys._MEIPASS`/`_internal`) — **ponto técnico de maior risco**.
3. **Não empacotar o modelo de 1,5 GB:** baixar do HF na 1ª execução (já é o comportamento) com **barra de progresso** → instalador ~1–2 GB em vez de ~3,5 GB.
4. **Inno Setup**, instalando em `%LocalAppData%\Ditar` (per-user, sem UAC, como o Wispr): atalho no Menu Iniciar, checkbox "iniciar com o Windows" (chave Run), embute `app.ico`.
5. **Auto-update:** **WinSparkle** (lê appcast XML, plug-and-play) ou **tufup** (TUF, mais seguro), com releases no GitHub.
6. **Code signing — adiar:** sem assinatura o SmartScreen marca "editor desconhecido". Caminho moderno barato quando valer: **Azure Trusted Signing (~US$ 10/mês)**.

## 6. Benefícios esperados

- **Distribuição real:** qualquer pessoa instala em < 2 min, sem Python.
- **Atrito zero para o autor** ao reinstalar/trocar de máquina.
- **Tração open-source** (portfólio) e base para **open-core** (engine grátis + extras pagos), espelhando o modelo OSS-shell do FluidVoice.
- **Mantém o diferencial:** local, gratuito, privado.

## 7. Custos e esforço

- **Esforço:** R1 ≈ 2 semanas (foco no empacotamento CUDA); R1–R3 ≈ 5 semanas calendário em ritmo de hobby.
- **Dinheiro:** **US$ 0** para R1–R3 (PyInstaller, Inno Setup, WinSparkle, GitHub Releases são grátis). Opcional ~US$ 10/mês de code signing (R4).

## 8. Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Empacotar CUDA/cuDNN no PyInstaller dá trabalho | Alta | Médio | Foco do Sprint 1 (spike); fallback CPU já existe no código |
| Instalador grande (1–2 GB) assusta | Média | Baixo | Modelo baixado sob demanda, não embutido |
| SmartScreen marca como "desconhecido" | Alta | Médio | Adiar p/ R4 (Azure Trusted Signing); aceitável em OSS no início |
| GPU diversa nos usuários | Média | Médio | Detecção + fallback CPU/`medium` (já em [`ditar.py:236`](../ditar.py)) |

## 9. Critérios de sucesso (métricas)

- Instalação em **< 2 min sem Python instalado** ✅/❌
- Tamanho do instalador **< 2 GB**
- Cold start do tray **< 10 s** (modelo já em cache)
- Auto-update aplicado **sem intervenção manual**

## 10. Backlog ágil — épicos e user stories

> Estimativas em story points. AC detalhados são escritos no `spec.md` de cada release
> (ver [`_templates/spec.template.md`](_templates/spec.template.md)).

**ÉPICO 1 — Executável + Instalador (MVP do `.exe`)** · *prioridade máxima*
- **US-1.1** Instalar `Ditar` por um `.exe` sem ter Python. *(PyInstaller onedir com CUDA funcionando no bundle)* — 5 pts
- **US-1.2** Instalador sem prompt de admin. *(Inno Setup per-user em %LocalAppData% + atalho no Menu Iniciar)* — 3 pts
- **US-1.3** Checkbox "iniciar com o Windows". *(chave Run opcional)* — 2 pts
- **US-1.4** Barra de progresso do download do modelo na 1ª execução — 3 pts

**ÉPICO 2 — Cara de produto** · *alta*
- **US-2.1** Ícone próprio (`.ico`) no tray, instalador e atalhos — 1 pt
- **US-2.2** Onboarding com a mensagem "100% local, seu áudio nunca sai da máquina" — 2 pts
- **US-2.3** Tela de configurações (hotkey, modelo, idioma, autostart) sem editar código — 5 pts

**ÉPICO 3 — Histórico** · *média*
- **US-3.1** Salvar cada ditado em **SQLite** (texto, timestamp, app de origem, modelo) — 3 pts
- **US-3.2** Janela de histórico pesquisável, com "copiar de novo" — 5 pts
- **US-3.3** Áudio opcional do ditado com **poda por orçamento de bytes** — 3 pts

**ÉPICO 4 — Auto-update** · *média*
- **US-4.1** App checa GitHub Releases e avisa de nova versão — 3 pts
- **US-4.2** Atualização baixada/aplicada em 1 clique, com rollback — 5 pts

**ÉPICO 5 — Robustez do ditado** (inspiração FluidVoice) · *baixa*
- **US-5.1** Escada de fallback de injeção (clipboard → SendInput Unicode → UI Automation) — 5 pts
- **US-5.2** Modos push-to-talk além do toggle — 3 pts ✅ *(entregue na R2-exec)*
- **US-5.3** Assinatura de código (Azure Trusted Signing) p/ matar o aviso do SmartScreen — 3 pts

**ÉPICO 6 — UX de ditado estilo Wispr** (emergiu do teste real, 2026-06-28) · *alta*
- **US-6.1** Seleção de microfone (não depende do padrão do Windows) — 3 pts ✅
- **US-6.2** Som suave no lugar do bip agudo (com opção de desligar) — 2 pts ✅
- **US-6.3** HUD visual flutuante ("Ouvindo…/Escrevendo…") — 5 pts ✅
- **US-6.4** Config aplicada ao vivo + instância única do daemon — 3 pts ✅

## 11. Releases

> **Reconciliação (2026-06-28):** a R2 original ("Parece app") foi **reprioritizada**. O teste
> real mostrou que o ditado precisava primeiro **funcionar e parecer Wispr** — isso virou a
> R2-executada (É6 + US-2.3 parcial + US-5.2). O conteúdo da R2 original (onboarding US-2.2 +
> histórico É3) **migrou para a R3**. Tabela abaixo reflete o **estado real**.

| Release | Conteúdo (real) | Épicos | Estado |
|---|---|---|---|
| **R1 — "Tem .exe"** | Instalador funcional, sem Python | É1 + US-2.1 | ✅ feito |
| **R2 — "Ditado estilo Wispr"** | Mic + som suave + HUD + modos hold/toggle + config | É6 + US-2.3 (parcial) + US-5.2 | ✅ feito |
| **R3 — "Parece app + se mantém"** | Histórico SQLite + onboarding + auto-update (delta) | US-2.2 + É3 + É4 | ✅ feito (1.3.6) |
| **R4 — "Polido / distribuição"** | ✅ full installer publicado (1.3.6) · ⬜ sincronizar fonte público, code signing, fallback de injeção, US-2.3/US-3.3, auto-mute | US-5.1 + US-5.3 + resto | 🟡 em andamento |

Ordem operacional e horizontes em [`roadmap.md`](roadmap.md).

## 12. Próximos passos

1. **Ratificar a rota técnica** (Opção C) como **ADR-0002** quando o planejamento começar "de fato".
2. **Spike do Sprint 1 (maior risco):** montar o `Ditar.spec` do PyInstaller e validar o empacotamento CUDA antes de investir no resto.
3. Abrir o `spec.md` da **R1** a partir do template.

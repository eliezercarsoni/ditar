---
name: adr-0003-auto-update
description: ADR-0003 — mecanismo de auto-update do Ditar (updater custom via GitHub Releases, não WinSparkle).
alwaysApply: false
---

# ADR-0003: Auto-update via updater custom (GitHub Releases)

- **Status:** aceito
- **Data:** 2026-06-28
- **Decisores:** Eliezer Carsoni (dono do produto / GP), Claude Code
- **Refina:** [ADR-0002](0002-empacotamento-pyinstaller-inno-winsparkle.md) (que deixava WinSparkle/tufup em aberto)

## Contexto
A R3 inclui auto-update (É4). Reavaliando na hora de implementar: o app é distribuído como um
instalador Inno (`Ditar-Setup-X.Y.Z.exe`, ~1 GB) no repo público `eliezercarsoni/ditar`, que
hoje **não tem releases**. `gh` está autenticado como `eliezercarsoni`. Precisamos de um
mecanismo que: detecte versão nova, avise o usuário e aplique a atualização — sem fricção e
sem peso de infraestrutura, para um projeto **solo/OSS**.

## Decisão
**Updater custom via GitHub Releases** (espelha o `SimpleUpdater` do FluidVoice):
1. **Versão única** em `version.py` (`VERSION`); o `installer.iss` mantém o `#define` em sincronia.
2. **Check:** GET `api.github.com/repos/eliezercarsoni/ditar/releases/latest`, compara `tag_name`
   (SemVer) com `VERSION`. Sem release / offline / 404 → "está atualizado" (degrada sem erro).
3. **Notificação + UI** num **processo separado** (`Ditar --check-update`, Tk, sem CUDA) — mesma
   estratégia da janela de Configurações, evita Tk no processo do daemon.
4. **Aplicação (fatia 2):** baixa o `.exe` da release, roda `/VERYSILENT` com
   `CloseApplications=yes RestartApplications=yes` no Inno → fecha o Ditar, atualiza no lugar e
   reabre. **Rollback:** reinstalar uma release anterior (o GitHub guarda todas).

**Alternativas descartadas:**
- *WinSparkle:* exige bundle da `win_sparkle.dll` + hospedar/assinar um `appcast.xml` (chaves
  EdDSA). Boa, mas adiciona infra para pouco ganho num projeto solo.
- *tufup:* atualização por TUF a nível de arquivo; seguro porém exige repositório TUF + gestão de
  chaves — complexidade desproporcional.

## Consequências
- **+** Autossuficiente: usa o instalador Inno + o repo que já temos; sem DLL/appcast/TUF.
- **+** UI própria e total controle; espelha um padrão comprovado (FluidVoice).
- **−** Nós mantemos o código de UI/download.
- **−** Sem verificação criptográfica da release até a R4 (Authenticode). Mitigação: download via
  HTTPS do próprio GitHub; assinatura fica para o épico de code signing.
- **−** Depende de **publicar releases** (passo externo, ~1 GB por release). O check degrada sem erro enquanto não houver.

## Rastreabilidade
- Spec/design: [`_specs/R3-auto-update/`](../_specs/R3-auto-update/spec.md)
- Código: `version.py`, `updater.py`, `ditar.py` (modo `--check-update`).

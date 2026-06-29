# Ditar — ditado por voz e transcrição 100% locais

Ditado por voz ao vivo (estilo Wispr Flow) e transcrição de áudios em lote, **100% locais**,
acelerados por GPU com [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Sem nuvem,
sem conta, sem mensalidade — o áudio **nunca sai da máquina**.

## Instalar (Windows)

Na [última release](https://github.com/eliezercarsoni/ditar/releases/latest), baixe o
**`Ditar-Setup-<versão>.exe`** (o instalador completo, ~1 GB) e execute. A instalação é
**por usuário, sem prompt de administrador**, em `%LocalAppData%\Ditar`, e cria atalhos no
Menu Iniciar e na Área de Trabalho.

> Os arquivos `delta-*.zip` da release são atualizações incrementais aplicadas pelo próprio
> app (ver *Atualizações automáticas*) — **não** servem para uma instalação nova.

> GPU NVIDIA é usada automaticamente (as libs CUDA vêm no pacote). Sem GPU, cai para CPU.
> Na 1ª execução, o modelo de voz (~1,5 GB) é baixado uma vez (com barra de progresso).

## Ditado por voz

Um ícone fica na **bandeja do sistema**. Atalho padrão: **`CTRL+ALT+D`** (configurável).

- **Modo Segurar** (padrão): segure `CTRL+ALT+D` enquanto fala, solte → o texto é digitado no app em foco.
- **Modo Toggle**: aperte para começar, aperte de novo para parar.
- Um **HUD** flutuante mostra "Ouvindo…" / "Escrevendo…"; um **som suave** marca início/fim.
- O texto é colado via clipboard (robusto para acentuação PT) e o clipboard anterior é restaurado;
  se o clipboard estiver ocupado por outro app, o Ditar digita o texto direto (SendInput) — sem perder o ditado.

**Configurações** (menu da bandeja → *Configurações*): microfone, **modelo de voz**, **idioma**,
som on/off, modo (segurar/toggle) e atalho. Mic, som e idioma valem na hora; modo e atalho aplicam
em segundos; **trocar o modelo exige reiniciar o Ditar** (e baixa o novo modelo na 1ª vez).

> Para digitar dentro de apps abertos **como administrador**, o Ditar também precisa rodar como
> admin (limitação do hook de teclado do Windows). Em apps normais, funciona sem elevação.

## Transcrição em lote (CLI)

`Transcrever.exe` (instalado junto, em `%LocalAppData%\Ditar`) transcreve arquivos e pastas:

```powershell
Transcrever .\reuniao.m4a               # um arquivo
Transcrever "C:\audios\caixa-de-entrada" # uma pasta inteira
Transcrever -r .\pasta-com-subpastas     # incluir subpastas
Transcrever --skip-existing .\lote        # pular o que já foi transcrito
```

Saída no mesmo diretório de cada áudio: `<nome>.srt` (legendas) e `<nome>.md` (parágrafos por turno).
Formatos: qualquer um que o ffmpeg leia (`.ogg`, `.mp3`, `.m4a`, `.wav`, `.opus`, `.flac`, …).

## Atualizações automáticas

O app checa a [página de releases](https://github.com/eliezercarsoni/ditar/releases) e avisa quando
há versão nova (menu da bandeja → *Verificar atualizações*). A atualização é **delta**: baixa só os
arquivos que mudaram (uns MB), não o pacote inteiro — fecha, atualiza e reabre o app sozinho.

## Performance

Na RTX 3050 6GB: **~16× mais rápido que tempo real** (1h de áudio em ~4 min). Modelo padrão
`large-v3-turbo` (CUDA, `int8_float16`, pt), qualidade equivalente ao Whisper large-v3.

## Troubleshooting

- **O ditado não escreve nada** → o microfone certo pode não ser o padrão do Windows. Em
  *Configurações → Microfone*, escolha o dispositivo correto e teste.
- **Acentuação errada no `.md`** → o arquivo está em UTF-8; abra no VS Code/Obsidian/Notepad com UTF-8.
- **Saída do CLI muda a cada execução / alucina no fim** → o default em CUDA é `int8_float16`
  (determinístico). Para forçar o antigo: `Transcrever --compute-type float16`.
- **VRAM cheia** → `Transcrever --model medium` ou feche outros apps que usem a GPU.

## Desenvolvimento / build

Stack: Python 3.12 + faster-whisper/CTranslate2 (CUDA via wheels `nvidia-*`), `sounddevice`,
`keyboard`, `pystray`, Tk. Empacotado com **PyInstaller** (`build/ditar.spec`) e **Inno Setup**
(`build/installer.iss`); auto-update por delta via `build/make_delta.py` (ver `governance/`).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt          # runtime
.venv\Scripts\python.exe -m pip install -r build\requirements-build.txt  # build (PyInstaller)
# rodar do código:
.venv\Scripts\python.exe ditar.py            # daemon de ditado
.venv\Scripts\python.exe transcrever.py <arquivo|pasta>
# empacotar:
.venv\Scripts\pyinstaller.exe build\ditar.spec --distpath build\dist --workpath build\work --noconfirm
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" build\installer.iss
```

A governança do projeto (business case, ADRs, specs, roadmap) está em [`governance/`](governance/).

## Licença

MIT.

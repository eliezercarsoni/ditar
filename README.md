# Transcrição local de áudio (Whisper)

Pipeline para transcrever áudios localmente usando [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — substitui ElevenLabs Scribe sem custo por minuto, sem limite, e com áudio nunca saindo da máquina.

## Como usar

Em qualquer pasta (pessoal ou trabalho):

```powershell
# um arquivo
transcrever .\reuniao.m4a
transcrever "C:\audios\entrevista-2026-05-08.ogg"

# uma pasta inteira — transcreve TODOS os áudios dela de uma vez
transcrever "C:\audios\caixa-de-entrada"

# vários arquivos e/ou pastas misturados
transcrever .\reuniao.m4a .\pasta-de-audios

# incluir subpastas
transcrever -r .\pasta-com-subpastas

# pular o que já foi transcrito (útil pra retomar um lote interrompido)
transcrever --skip-existing .\pasta-de-audios
```

Saída no mesmo diretório de cada áudio:
- `<nome>.srt` — legendas com timestamp (use no VLC sobre o áudio)
- `<nome>.md` — texto em parágrafos por turno (cole no Obsidian)

Ao processar uma pasta, o modelo é carregado **uma única vez** e reutilizado para todos os áudios. Se um arquivo falhar, o lote continua nos demais e um resumo (`X ok, Y com erro`) é exibido no final.

Formatos suportados: qualquer coisa que o ffmpeg leia — `.ogg`, `.mp3`, `.m4a`, `.wav`, `.opus`, `.flac`, etc. (arquivos `.srt`/`.md` já gerados são ignorados ao varrer pastas).

## Performance esperada

Na RTX 3050 6GB do notebook: **~16x mais rápido que tempo real** (1h de áudio em ~4 min). Modelo `large-v3-turbo`, qualidade equivalente ao Whisper large-v3.

## Ditado por voz ao vivo (`ditar`)

Estilo Wispr Flow, mas 100% local: um daemon fica na bandeja, você aperta um
atalho global, fala, aperta de novo e o texto é digitado no app que estiver em
foco (Word, navegador, Slack, terminal — onde o cursor estiver).

```powershell
ditar                       # inicia o daemon (atalho: CTRL+ALT+ESPAÇO)
ditar --hotkey ctrl+alt+d   # usar outro atalho
ditar --no-tray             # sem ícone na bandeja (só atalho + console)
ditar --check               # só valida deps + carrega o modelo e sai
```

Fluxo (modo **toggle**):
1. Aperte **CTRL+ALT+ESPAÇO** → bipe agudo, começa a gravar.
2. Fale à vontade.
3. Aperte **CTRL+ALT+ESPAÇO** de novo → bipe grave, ele transcreve o trecho e
   **cola o texto** no campo em foco.

Detalhes de implementação:
- Reusa o mesmo modelo do `transcrever` (`large-v3-turbo`, `cuda`,
  `int8_float16`, `pt`), carregado **uma vez** e residente na VRAM.
- Captura o microfone com `sounddevice` (16 kHz mono) direto pra memória — sem
  passar por arquivo nem ffmpeg.
- Injeta o texto via **clipboard + Ctrl+V** (robusto pra acentuação PT) e
  **restaura** o conteúdo anterior do clipboard depois.
- Ícone na bandeja muda de cor: azul (pronto) / vermelho (gravando) / laranja
  (transcrevendo). O menu do ícone também tem "Ligar/Desligar" e "Sair".

Sair: menu da bandeja → **Sair**, ou `Ctrl+C` no console.

**Por que "ao soltar" e não palavra-por-palavra:** o Whisper transcreve blocos,
não streaming nativo. Transcrever o trecho inteiro ao parar dá pontuação melhor
e zero tremulação — pra ditados de uma a poucas frases, o texto aparece ~1s
depois de você parar. (Streaming ao vivo é possível, mas treme e é bem mais pesado.)

**Iniciar junto com o Windows (opcional):** crie um atalho para `ditar.cmd` (ou,
para rodar sem janela de console, um `.vbs`/atalho chamando
`.venv\Scripts\pythonw.exe ditar.py`) e coloque na pasta
`shell:startup` (Win+R → `shell:startup`).

**Obs.:** para digitar dentro de apps abertos **como administrador**, o `ditar`
também precisaria rodar como admin (limitação do hook de teclado do Windows).
Para apps normais, funciona sem elevação.

## Comandos manuais (sem o atalho global)

```powershell
# direto pelo .cmd (a partir de qualquer pasta)
C:\caminho\para\ditar\transcrever.cmd .\audio.ogg

# ou ativando o venv
& C:\caminho\para\ditar\.venv\Scripts\python.exe `
  C:\caminho\para\ditar\transcrever.py .\audio.ogg
```

## Flags do script

```
transcrever <arquivo|pasta> [<mais> ...] [-r] [--skip-existing] [--model NOME] [--language pt] [--device cuda|cpu] [--compute-type ...]
```

- `-r` / `--recursive` — ao receber pasta, também varre subpastas.
- `--skip-existing` — pula áudios que já têm `.srt` **e** `.md` gerados.

Modelos disponíveis (do mais leve ao mais pesado):
| Modelo | VRAM | Qualidade | Quando usar |
|---|---|---|---|
| `tiny` | <1GB | baixa | só pra teste rápido |
| `small` | ~2GB | razoável | máquina sem GPU |
| `medium` | ~5GB | boa | fallback CPU ou GPU fraca |
| `large-v3-turbo` (default) | ~6GB | excelente | RTX 3050 ou superior |
| `large-v3` | ~10GB | top | só com GPU >= 8GB |

Idiomas: `--language pt` (default), `pt-BR`, `en`, `es`, etc. Use `--language auto` se misturado.

## Stack instalada

- **Python 3.12.10** (winget `Python.Python.3.12`) — paralelo ao 3.14 do sistema
- **ffmpeg 8.1.1** (winget `Gyan.FFmpeg`)
- **faster-whisper 1.2.1** + CTranslate2 4.7
- **CUDA libs via pip:** `nvidia-cublas-cu12`, `nvidia-cudnn-cu12`, `nvidia-cuda-nvrtc-cu12` — não precisa instalar CUDA toolkit do sistema
- venv isolado em `audio/.venv/`

Cache do modelo (~1.5GB) fica em `%USERPROFILE%\.cache\huggingface\hub\` — baixa uma vez só.

## Troubleshooting

**`Could not locate cublas64_*.dll`** — o script já injeta os paths automaticamente. Se ainda falhar, ele faz fallback pra CPU com modelo `medium`.

**Saída muda a cada execução / alucina no fim / aparece caractere chinês/coreano** — na GPU o caminho de ponto flutuante (`float16`/`float32`) das kernels cuBLAS/cuDNN é não-determinístico e às vezes empurra a busca em feixe do Whisper pra uma alucinação no fim do áudio. Por isso o default em CUDA é **`int8_float16`** (determinístico, mais rápido, menos VRAM, qualidade equivalente). Para forçar o antigo: `--compute-type float16`. O `cuDNN` está fixado em `9.10.2.21` no `requirements.txt` (versão de build do CTranslate2 4.7.1) — não atualize sem testar.

**VRAM cheia** — rode com `--model medium` ou feche outros apps que usem GPU.

**Acentuação errada no `.md`** — o terminal pode mostrar errado, mas o arquivo está em UTF-8 correto. Abra no VS Code, Obsidian ou Notepad com encoding UTF-8.

**Áudio muito longo (>2h)** — funciona, mas considere quebrar em pedaços de 1h pra evitar pico de memória.

## Instalação

Requer **Python 3.12**. O `transcrever` também precisa de **ffmpeg** (o `ditar`
não usa ffmpeg).

```powershell
git clone https://github.com/eliezercarsoni/ditar.git
cd ditar

# Windows (via winget):
winget install Python.Python.3.12 Gyan.FFmpeg

# ambiente isolado + dependências:
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

A GPU NVIDIA é usada automaticamente — as libs CUDA vêm via pip no
`requirements.txt`, **sem precisar** instalar o CUDA toolkit do sistema. Sem GPU
NVIDIA, rode com `--device cpu --model medium`.

**Comandos globais (opcional):** para chamar `transcrever`/`ditar` de qualquer
pasta, adicione funções ao seu perfil do PowerShell (`notepad $PROFILE`):

```powershell
function transcrever { & "C:\caminho\para\ditar\transcrever.cmd" @args }
function ditar       { & "C:\caminho\para\ditar\ditar.cmd"       @args }
```

"""
Transcreve arquivos de audio usando faster-whisper localmente.

Uso:
    python transcrever.py <arquivo_ou_pasta> [<mais> ...] [--model turbo] [--language pt] [--device cuda]

Aceita arquivos individuais E pastas (mistos). Quando recebe uma pasta,
transcreve todos os audios dela. Use -r/--recursive para incluir subpastas.

Saidas (no mesmo diretorio de cada arquivo de entrada):
    <nome>.srt  - legendas com timestamp
    <nome>.md   - texto em paragrafos por turno (pausa >= 1.5s)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path


# Extensoes que o ffmpeg/faster-whisper consegue ler. Arquivos com outra
# extensao (inclusive .srt/.md ja gerados) sao ignorados ao varrer pastas.
AUDIO_EXTENSIONS = {
    ".ogg", ".opus", ".mp3", ".m4a", ".m4b", ".wav", ".flac", ".aac",
    ".wma", ".aiff", ".aif", ".amr", ".3gp", ".mp4", ".mkv", ".webm", ".mov",
}


def _add_cuda_dlls_to_path() -> None:
    """Garante que as DLLs do cuBLAS/cuDNN/nvrtc instaladas via pip estejam visiveis."""
    try:
        import nvidia  # noqa: F401
    except ImportError:
        return
    base = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    if not base.exists():
        return
    candidates = [
        base / "cublas" / "bin",
        base / "cudnn" / "bin",
        base / "cuda_nvrtc" / "bin",
    ]
    extra = os.pathsep.join(str(p) for p in candidates if p.exists())
    if extra:
        os.environ["PATH"] = extra + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            for p in candidates:
                if p.exists():
                    try:
                        os.add_dll_directory(str(p))
                    except OSError:
                        pass


_add_cuda_dlls_to_path()

from faster_whisper import WhisperModel  # noqa: E402


def format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    h, millis = divmod(millis, 3_600_000)
    m, millis = divmod(millis, 60_000)
    s, millis = divmod(millis, 1_000)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"


def format_clock(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def write_srt(segments: list, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_timestamp(seg.start)} --> {format_srt_timestamp(seg.end)}\n")
            f.write(f"{seg.text.strip()}\n\n")


def write_md(segments: list, path: Path, source: Path, pause_threshold: float = 1.5) -> None:
    paragraphs: list[tuple[float, list[str]]] = []
    current_start: float | None = None
    current_texts: list[str] = []
    last_end: float | None = None

    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        if last_end is not None and (seg.start - last_end) >= pause_threshold:
            paragraphs.append((current_start, current_texts))
            current_start = seg.start
            current_texts = [text]
        else:
            if current_start is None:
                current_start = seg.start
            current_texts.append(text)
        last_end = seg.end

    if current_texts:
        paragraphs.append((current_start, current_texts))

    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Transcricao: {source.name}\n\n")
        for start, texts in paragraphs:
            stamp = format_clock(start or 0.0)
            f.write(f"**[{stamp}]** {' '.join(texts)}\n\n")


def gather_audio_files(paths: list[Path], recursive: bool) -> list[Path]:
    """Expande arquivos e pastas numa lista unica e ordenada de audios, sem duplicatas."""
    collected: list[Path] = []
    seen: set[str] = set()

    for raw in paths:
        path = raw.resolve()
        if path.is_dir():
            globber = path.rglob("*") if recursive else path.glob("*")
            items = sorted(
                (p for p in globber if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS),
                key=lambda p: str(p).lower(),
            )
        elif path.is_file():
            items = [path]
        else:
            print(f"[transcrever] aviso: ignorando caminho inexistente: {path}", file=sys.stderr)
            items = []

        for it in items:
            key = str(it).lower()
            if key not in seen:
                seen.add(key)
                collected.append(it)

    return collected


def load_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
    print(f"[transcrever] carregando modelo: {model_name} | device: {device} | compute_type: {compute_type}")
    t0 = time.time()
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    print(f"[transcrever] modelo carregado em {time.time() - t0:.1f}s")
    return model


def transcribe_one(model: WhisperModel, audio_path: Path, language: str | None) -> None:
    print(f"[transcrever] arquivo: {audio_path}")

    t1 = time.time()
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    print(f"[transcrever] idioma detectado: {info.language} (prob={info.language_probability:.2f})")
    print(f"[transcrever] duracao do audio: {format_clock(info.duration)} ({info.duration:.1f}s)")

    segments = []
    for seg in segments_iter:
        segments.append(seg)
        sys.stdout.write(f"\r[transcrever] processando... {format_clock(seg.end)} / {format_clock(info.duration)}")
        sys.stdout.flush()
    print()

    elapsed = time.time() - t1
    rtf = elapsed / info.duration if info.duration > 0 else 0
    print(f"[transcrever] transcricao concluida em {elapsed:.1f}s (RTF={rtf:.2f}x)")

    srt_path = audio_path.with_suffix(".srt")
    md_path = audio_path.with_suffix(".md")
    write_srt(segments, srt_path)
    write_md(segments, md_path, source=audio_path)
    print(f"[transcrever] gerado: {srt_path}")
    print(f"[transcrever] gerado: {md_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Transcreve audio com faster-whisper local.")
    p.add_argument(
        "paths",
        type=Path,
        nargs="+",
        help="arquivo(s) de audio e/ou pasta(s) com audios (.ogg, .mp3, .m4a, .wav, etc.)",
    )
    p.add_argument("-r", "--recursive", action="store_true", help="ao receber pasta, incluir subpastas")
    p.add_argument(
        "--skip-existing",
        action="store_true",
        help="pular audios que ja tem .srt e .md gerados",
    )
    p.add_argument("--model", default="large-v3-turbo", help="modelo (default: large-v3-turbo)")
    p.add_argument("--language", default="pt", help="codigo do idioma (default: pt; use 'auto' p/ detectar)")
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu", "auto"], help="device (default: cuda)")
    p.add_argument(
        "--compute-type",
        default=None,
        help="tipo numerico (default: int8_float16 em cuda, int8 em cpu)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    files = gather_audio_files(args.paths, recursive=args.recursive)
    if not files:
        sys.exit("erro: nenhum arquivo de audio encontrado nos caminhos informados.")

    if args.skip_existing:
        pending = [
            f for f in files
            if not (f.with_suffix(".srt").exists() and f.with_suffix(".md").exists())
        ]
        skipped = len(files) - len(pending)
        if skipped:
            print(f"[transcrever] {skipped} arquivo(s) ja transcrito(s) pulado(s) (--skip-existing)")
        files = pending
        if not files:
            print("[transcrever] nada a fazer.")
            return

    language = None if args.language.lower() == "auto" else args.language
    device = args.device
    model_name = args.model
    # int8_float16 (e nao float16) em CUDA de proposito: o caminho de ponto
    # flutuante das kernels cuBLAS/cuDNN e nao-deterministico (acumulacao com
    # atomics), o que faz a busca em feixe do Whisper variar entre execucoes e,
    # de vez em quando, alucinar no fim do audio (repeticao ou caracteres CJK).
    # O caminho int8 e deterministico, mais rapido e usa menos VRAM (ideal p/ a
    # RTX 3050 6GB), com qualidade equivalente. Use --compute-type float16 p/ voltar.
    compute_type = args.compute_type or ("int8_float16" if device == "cuda" else "int8")

    multiple = len(files) > 1
    total = len(files)
    if multiple:
        print(f"[transcrever] {total} arquivo(s) na fila:")
        for f in files:
            print(f"            - {f.name}")

    model: WhisperModel | None = None
    ok = 0
    fail = 0

    for idx, audio_path in enumerate(files, start=1):
        if multiple:
            print(f"\n[transcrever] === {idx}/{total}: {audio_path.name} ===")
        try:
            if model is None:
                model = load_model(model_name, device, compute_type)
            transcribe_one(model, audio_path, language=language)
            ok += 1
        except RuntimeError as e:
            msg = str(e).lower()
            cuda_err = "cuda" in msg or "cublas" in msg or "cudnn" in msg
            if device == "cuda" and cuda_err:
                print(f"\n[transcrever] erro CUDA: {e}", file=sys.stderr)
                print(
                    "[transcrever] fallback para CPU com modelo 'medium' "
                    "(vale para os proximos arquivos)...",
                    file=sys.stderr,
                )
                device, model_name, compute_type = "cpu", "medium", "int8"
                try:
                    model = load_model(model_name, device, compute_type)
                    transcribe_one(model, audio_path, language=language)
                    ok += 1
                except Exception as e2:
                    print(f"[transcrever] falhou tambem na CPU: {e2}", file=sys.stderr)
                    fail += 1
            else:
                print(f"[transcrever] erro ao processar {audio_path.name}: {e}", file=sys.stderr)
                fail += 1
        except Exception as e:
            print(f"[transcrever] erro ao processar {audio_path.name}: {e}", file=sys.stderr)
            fail += 1

    if multiple:
        print(f"\n[transcrever] concluido: {ok} ok, {fail} com erro, de {total} arquivo(s).")


if __name__ == "__main__":
    main()
    # faster-whisper/CTranslate2 crasham no teardown da GPU no Windows
    # (0xC0000409 / STATUS_STACK_BUFFER_OVERRUN, issue SYSTRAN/faster-whisper#1293):
    # o processo morre durante a limpeza do contexto CUDA, *depois* que os
    # arquivos .srt/.md ja foram gravados. Encerramos antes desse cleanup para
    # devolver exit code 0 limpo. As saidas usam context managers (ja fechadas);
    # so garantimos o flush do stdout/stderr. Caminhos de erro usam sys.exit()
    # (SystemExit propaga e preserva o codigo de saida, sem chegar aqui).
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)

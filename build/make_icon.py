"""
Gera audio/app.ico (icone do produto): microfone branco em circulo azul.
Mesma linguagem visual do icone da bandeja (ditar.py), em multiplas resolucoes.

Uso:
    .venv\\Scripts\\python.exe build\\make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "app.ico"

S = 256  # base; o ICO carrega tamanhos menores derivados desta
BLUE = (60, 110, 220, 255)
WHITE = (255, 255, 255, 255)

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Circulo de fundo (com leve margem).
m = int(S * 0.06)
d.ellipse((m, m, S - m, S - m), fill=BLUE)

# Microfone: corpo (capsula arredondada) + haste + base.
cx = S / 2
body_w = S * 0.26
body_top = S * 0.24
body_bot = S * 0.56
d.rounded_rectangle(
    (cx - body_w / 2, body_top, cx + body_w / 2, body_bot),
    radius=body_w / 2,
    fill=WHITE,
)
# Arco do suporte (semicirculo aberto embaixo da capsula).
arc_pad = S * 0.10
d.arc(
    (cx - body_w / 2 - arc_pad, body_top + S * 0.06, cx + body_w / 2 + arc_pad, body_bot + arc_pad),
    start=20,
    end=160,
    fill=WHITE,
    width=int(S * 0.035),
)
# Haste vertical + base.
stem_top = body_bot + arc_pad
stem_bot = S * 0.80
d.line((cx, stem_top, cx, stem_bot), fill=WHITE, width=int(S * 0.045))
base_w = S * 0.22
d.line((cx - base_w / 2, stem_bot, cx + base_w / 2, stem_bot), fill=WHITE, width=int(S * 0.045))

sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save(OUT, format="ICO", sizes=sizes)
print(f"gerado: {OUT}  ({OUT.stat().st_size} bytes, tamanhos: {[s[0] for s in sizes]})")

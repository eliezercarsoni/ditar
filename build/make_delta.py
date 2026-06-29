"""
Gera o manifesto e o delta (arquivos mudados vs versao anterior) p/ auto-update. ADR-0004.

Uso:
    python build/make_delta.py <versao>                  # baseline: so escreve o manifesto
    python build/make_delta.py <versao> <versao_anterior># gera delta-<versao>.zip + update.json

Le o bundle de build/dist/Ditar. Guarda manifestos em build/manifests/ (precisam persistir
entre releases p/ calcular o proximo delta). Saidas de publicacao em build/delta-output/.
"""

import hashlib
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))  # .../build
DIST = os.path.join(ROOT, "dist", "Ditar")
MANI_DIR = os.path.join(ROOT, "manifests")
OUT = os.path.join(ROOT, "delta-output")
SKIP = {"ditar.log", "config.json"}  # dados locais, fora do bundle


def fhash(p: str) -> str:
    m = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            m.update(c)
    return m.hexdigest()


def build_manifest(dist: str) -> dict:
    mani = {}
    for dp, _, fns in os.walk(dist):
        for fn in fns:
            if fn in SKIP:
                continue
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, dist)
            mani[rel] = {"sha256": fhash(full), "size": os.path.getsize(full)}
    return mani


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("uso: make_delta.py <versao> [versao_anterior]")
    version = sys.argv[1]
    from_version = sys.argv[2] if len(sys.argv) > 2 else None
    os.makedirs(MANI_DIR, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    mani = build_manifest(DIST)
    json.dump(mani, open(os.path.join(MANI_DIR, f"manifest-{version}.json"), "w"))
    print(f"manifest-{version}.json: {len(mani)} arquivos")

    if not from_version:
        print("(baseline — sem delta)")
        return

    prevp = os.path.join(MANI_DIR, f"manifest-{from_version}.json")
    if not os.path.exists(prevp):
        sys.exit(f"ERRO: manifesto anterior nao encontrado: {prevp}")
    prev = json.load(open(prevp))
    changed = [r for r, i in mani.items() if prev.get(r, {}).get("sha256") != i["sha256"]]

    zp = os.path.join(OUT, f"delta-{version}.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in changed:
            z.write(os.path.join(DIST, rel), rel)
    json.dump(
        {"version": version, "from_version": from_version, "delta": f"delta-{version}.zip"},
        open(os.path.join(OUT, "update.json"), "w"),
    )
    print(f"delta-{version}.zip: {len(changed)} arquivos, {os.path.getsize(zp)/1048576:.1f} MB (de {from_version})")
    for rel in changed[:10]:
        print("   +", rel)


if __name__ == "__main__":
    main()

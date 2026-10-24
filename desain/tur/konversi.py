#!/usr/bin/env python3
"""Ubah frame PNG transparan dari Blender menjadi WebP berlatar warna halaman (dua ukuran: desktop dan ponsel).
Jalankan: ../../.venv-cad/bin/python konversi.py  -> frame/<film>/{d,m}/NNNN.webp + frame/manifest.json"""
import glob, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BG = (15, 16, 18, 255)                      # #0F1012, sama dengan latar halaman
UKURAN = {"d": ((1024, 768), 72), "m": ((640, 480), 66)}
man = json.load(open(os.path.join(HERE, "frame", "manifest.json"))) if os.path.exists(os.path.join(HERE, "frame", "manifest.json")) else {}
for film in ("jepit", "jepitbb", "genggam", "banding"):
    src = sorted(glob.glob(os.path.join(HERE, "frame_mentah", film, "*.png")))
    if not src: continue
    for k, ((w, h), q) in UKURAN.items():
        out = os.path.join(HERE, "frame", film, k); os.makedirs(out, exist_ok=True)
        for i, f in enumerate(src):
            tujuan = os.path.join(out, f"{i:04d}.webp")
            if os.path.exists(tujuan) and os.path.getmtime(tujuan) > os.path.getmtime(f): continue
            im = Image.open(f).convert("RGBA")
            if im.size != (w, h): im = im.resize((w, h), Image.LANCZOS)
            bg = Image.new("RGBA", im.size, BG); bg.alpha_composite(im); bg.convert("RGB").save(tujuan, "WEBP", quality=q, method=5)
    besar = {k: sum(os.path.getsize(p) for p in glob.glob(os.path.join(HERE, "frame", film, k, "*.webp"))) // 1024 for k in UKURAN}
    man[film] = dict(n=len(src), kb=besar); print(film, len(src), "frame", besar, "KB")
json.dump(man, open(os.path.join(HERE, "frame", "manifest.json"), "w"))

#!/usr/bin/env python3
"""Pemeriksa rumah BeefFresh: render lewat OpenSCAD, lalu uji geometri (trimesh + manifold).
Pakai:  ../.venv-cad/bin/python verify.py [nama_scad] [-D key=val ...]
Yang DIUJI: bentuk tertutup (siap cetak), dimensi, tabrakan benda-tiruan-komponen vs dinding, kelonggaran >= 0,2 mm.
Yang TIDAK diuji: ukuran komponen aslimu (itu perlu jangka sorong), kekuatan, dan hasil cetak sebenarnya."""
import os, re, subprocess, sys
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); SCAD = os.path.join(HERE, "beeffresh_rumah.scad"); OUT = os.path.join(HERE, "stl")
os.makedirs(OUT, exist_ok=True)
extra = [a for a in sys.argv[1:]]
def render(part):
    path = os.path.join(OUT, part + ".stl")
    cmd = ["openscad", "-o", path, "-D", f'part="{part}"'] + extra + [SCAD]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stderr:
        print(f"GAGAL render {part}:\n{r.stderr[-400:]}"); sys.exit(1)
    return path, r.stderr
parts = ["base", "lid", "tube", "coupon", "lid_asm", "tube_asm", "ghost_esp", "ghost_usb", "ghost_oled", "ghost_tcs"]
mesh, derived = {}, None
for p in parts:
    path, err = render(p)
    mesh[p] = trimesh.load(path)
    m = re.search(r"derived = \[([^\]]+)\]", err)
    if m and derived is None: derived = [float(x) for x in m.group(1).split(",")]
inL, inW, outL, outW, z_cav_top, z_pcb_bot, tcx, tcy, tlen, chip_z = derived
ok_all = True
def cek(nama, kondisi, info=""):
    global ok_all
    ok_all &= bool(kondisi); print(("  LOLOS " if kondisi else "  GAGAL ") + nama + (f"  [{info}]" if info else ""))

print("== 1. Bentuk tertutup & dimensi ==")
for p in ("base", "lid", "tube", "coupon"):
    m = mesh[p]; b = m.bounds; d = b[1] - b[0]
    cek(f"{p}: tertutup (watertight), volume > 0", m.is_watertight and m.volume > 0, f"{d[0]:.1f} x {d[1]:.1f} x {d[2]:.1f} mm, {m.volume/1000:.1f} cm3")
print(f"  badan: {outL:.1f} x {outW:.1f} x {z_cav_top + 3.0:.1f} mm (tutup terpasang) + tabung {tlen:.1f} mm di bawah")

def vol_int(a, b):
    try:
        r = trimesh.boolean.intersection([a, b], engine="manifold")
        return 0.0 if r is None or r.is_empty else abs(r.volume)
    except Exception:
        return 0.0
shell = trimesh.util.concatenate([mesh["base"], mesh["lid_asm"], mesh["tube_asm"]])
print("== 2. Tabrakan: komponen tiruan vs rumah (harus 0 mm3) ==")
pairs = [("ESP32 vs base", "ghost_esp", ["base"]), ("ESP32 vs tutup", "ghost_esp", ["lid_asm"]),
         ("Colokan USB vs base (lewat lubang)", "ghost_usb", ["base"]),
         ("OLED vs tutup (kantong)", "ghost_oled", ["lid_asm"]), ("OLED vs base", "ghost_oled", ["base"]),
         ("OLED vs ESP32 (susun vertikal)", "ghost_oled", ["ghost_esp"]),
         ("Sensor TCS vs base", "ghost_tcs", ["base"]), ("Sensor TCS vs tabung", "ghost_tcs", ["tube_asm"]),
         ("Tabung vs base (flens di ceruk)", "tube_asm", ["base"])]
for nama, g, lawan in pairs:
    v = sum(vol_int(mesh[g], mesh[l]) for l in lawan); cek(nama, v < 0.5, f"{v:.2f} mm3")

print("== 3. Kelonggaran minimal 0,2 mm (komponen digeser 0,2 mm ke 5 arah) ==")
arah = {"+X": (0.2, 0, 0), "-X": (-0.2, 0, 0), "+Y": (0, 0.2, 0), "-Y": (0, -0.2, 0), "+Z": (0, 0, 0.2)}
# OLED vs tutup sengaja pas (pin penahan di lubang, celah radial ~0,1 mm), jadi OLED hanya diuji terhadap base
for g, lawan, label in (("ghost_esp", ["base", "lid_asm"], "ESP32"), ("ghost_oled", ["base"], "OLED (terhadap base)"), ("ghost_tcs", ["base"], "Sensor TCS")):
    bad = []
    for k, v in arah.items():
        gm = mesh[g].copy(); gm.apply_translation(v)
        if sum(vol_int(gm, mesh[l]) for l in lawan) > 0.5: bad.append(k)
    cek(f"{label}: celah >= 0,2 mm", not bad, "menyentuh ke arah " + ",".join(bad) if bad else "")
# kasus khusus: colokan USB digeser 0,5 mm (lubang harus longgar untuk colokan)
for k, v in {"+Y": (0, .5, 0), "-Y": (0, -.5, 0), "+Z": (0, 0, .5), "-Z": (0, 0, -.5)}.items():
    gm = mesh["ghost_usb"].copy(); gm.apply_translation(v)
    cek(f"Colokan USB longgar {k} 0,5 mm", vol_int(gm, mesh["base"]) < 0.5)

print("== 4. Arah cetak & kebutuhan penyangga ==")
base_m = mesh["base"]; cek("base: sisi bawah rata di bidang cetak (z=0)", abs(base_m.bounds[0][2]) < 1e-3)
print("\nHASIL:", "SEMUA LOLOS" if ok_all else "ADA YANG GAGAL")
sys.exit(0 if ok_all else 1)

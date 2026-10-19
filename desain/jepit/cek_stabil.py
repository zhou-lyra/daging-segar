"""Apakah alat terguling ke belakang saat kepala dibuka? Titik berat total harus di dalam alas baki (x 0..86)."""
import math, warnings; warnings.filterwarnings("ignore")
import numpy as np
from trimesh.transformations import rotation_matrix
import geometri as G
GRAM = {"esp_pcb": 9.0, "oled_pcb": 4.0, "sensor_pcb": 3.0, "engsel_bawah": 6.0, "engsel_atas": 3.0, "kait_bawah": 2.0, "kait_atas": 3.0}
RHO = {"busa": 0.03, "daging": 1.05, "plastik_hitam": 0.9, "beludru": 0.3}
def berat(rho_pvc, sudut):
    Rm = rotation_matrix(math.radians(sudut), [0, 1, 0], point=[G.SUMBU_ENGSEL[0], 0, G.SUMBU_ENGSEL[1]])
    mt, mx = 0.0, 0.0
    for k, b in G.B.items():
        if b["grup"] == "aksesori" or k.startswith(("kabel", "esp_", "oled_", "sensor_")) and k not in GRAM: continue
        m = b["mesh"].copy()
        if b["grup"] == "atas": m.apply_transform(Rm)
        g = GRAM.get(k) or m.volume / 1000 * (rho_pvc if b["bahan"] in ("pvc", "pvc_hitam") else RHO.get(b["bahan"], 1.0))
        mt += g; mx += g * m.center_mass[0] if m.is_volume else g * m.bounds.mean(0)[0]
    return mt, mx / mt
for rho in (0.55, 1.4):
    for sd in (0, 75, 90, 100):
        mt, x = berat(rho, sd); print(f"PVC {rho} g/cm3, buka {sd:3d} derajat: berat {mt:5.0f} g, titik berat x = {x:5.1f} mm  {'AMAN' if x < G.W - 5 else 'RAWAN TERGULING'}")

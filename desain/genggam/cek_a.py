"""Pemeriksaan desain A-PVC: garis pandang chip/LED ke lubang, dan titik berat terhadap pelat muka."""
import numpy as np, trimesh, warnings; warnings.filterwarnings("ignore")
import geometri_a as G
hal = trimesh.util.concatenate([b["mesh"] for k, b in G.B.items() if k not in ("sensor_chip", "sensor_led", "daging") and not k.startswith("kabel")])
ri = trimesh.ray.ray_triangle.RayMeshIntersector(hal)
rr, aa = np.meshgrid(np.linspace(0, G.AP_R - 0.01, 14), np.linspace(0, 2 * np.pi, 48, endpoint=False))
tgt = np.stack([rr.ravel() * np.cos(aa.ravel()), rr.ravel() * np.sin(aa.ravel()), np.zeros(rr.size)], 1)
for nama, src in (("chip", G.CHIP + G.Nn * 0.01), ("LED", G.LED_W + G.Nn * 0.5)):
    d = tgt - src; L = np.linalg.norm(d, axis=1); d /= L[:, None]
    loc, idx, _ = ri.intersects_location(np.repeat([src], len(d), 0), d, multiple_hits=True)
    hit = np.zeros(len(d), bool)
    for p, i in zip(loc, idx):
        if np.linalg.norm(p - src) < L[i] - 1e-3: hit[i] = True
    print(f"{nama}: {100*hit.mean():.1f} % titik lubang terhalang")
GRAM = {"esp_pcb": 9.0, "oled_pcb": 4.0, "sensor_pcb": 3.0}
mt = mx = 0.0
for k, b in G.B.items():
    if k == "daging": continue
    m = b["mesh"]; rho = {"pvc": 1.4, "pvc_hitam": 1.4, "busa": 0.03, "beludru": 0.3, "plastik_hitam": 0.9, "kabel": 1.2}.get(b["bahan"], 1.0)
    g = GRAM.get(k) or (m.volume / 1000 * rho if not k.startswith(("esp_", "oled_", "sensor_")) else 0.3)
    c = m.center_mass if m.is_volume else m.bounds.mean(0); mt += g; mx += g * c[0]
print(f"berat sekitar {mt:.0f} g (PVC padat), titik berat x = {mx/mt:.1f} mm; pelat muka x {G.X_PAD}..{G.X1}, tanda ibu jari x -16")

"""Periksa garis pandang: chip dan LED harus melihat seluruh lubang ukur tanpa terhalang bagian lain."""
import numpy as np, trimesh, warnings; warnings.filterwarnings("ignore")
import geometri as G
hal = trimesh.util.concatenate([b["mesh"] for k, b in G.B.items() if b["grup"] == "atas" and not k.startswith(("sensor_chip", "sensor_led", "kabel"))])
ri = trimesh.ray.ray_triangle.RayMeshIntersector(hal)
rr, aa = np.meshgrid(np.linspace(0, G.rl - 0.01, 14), np.linspace(0, 2 * np.pi, 48, endpoint=False))
tgt = np.stack([G.XC + rr.ravel() * np.cos(aa.ravel()), G.YC + rr.ravel() * np.sin(aa.ravel()), np.zeros(rr.size)], 1)
for nama, src in (("chip", G.CHIP + G.N * 0.01), ("LED", G.LED_W + G.N * 0.5)):
    d = tgt - src; L = np.linalg.norm(d, axis=1); d /= L[:, None]
    loc, idx, _ = ri.intersects_location(np.repeat([src], len(d), 0), d, multiple_hits=True)
    hit = np.zeros(len(d), bool)
    for p, i in zip(loc, idx):
        if np.linalg.norm(p - src) < L[i] - 1e-3: hit[i] = True
    print(f"{nama}: {100 * hit.mean():.1f} % titik lubang terhalang (terutama oleh tepi lubang setebal muka tutup)")
    if hit.any():
        h = tgt[hit]; print(f"   jarak titik terhalang dari pusat: {np.hypot(h[:,0]-G.XC, h[:,1]-G.YC).min():.2f} .. {np.hypot(h[:,0]-G.XC, h[:,1]-G.YC).max():.2f} mm")

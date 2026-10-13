#!/usr/bin/env python3
"""Perkiraan ketebalan dinding: dari titik acak di permukaan, tembakkan sinar ke dalam bahan dan ukur sampai keluar.
Ini PERKIRAAN (sampling), bukan analisis penuh. Pakai:  ../.venv-cad/bin/python tebal.py"""
import os, warnings
import numpy as np, trimesh
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); np.random.seed(0)
for nama in ("base", "lid", "tube"):
    m = trimesh.load(os.path.join(HERE, "stl", nama + ".stl")); n = 6000
    pts, fid = trimesh.sample.sample_surface(m, n)
    nrm = m.face_normals[fid]; org = pts - nrm * 0.02
    hits, ray, _ = m.ray.intersects_location(org, -nrm, multiple_hits=False)
    t = np.full(n, np.nan); t[ray] = np.linalg.norm(hits - org[ray], axis=1)
    v = t[~np.isnan(t)]
    print(f"{nama}: {len(v)} sampel | minimum {v.min():.2f} mm | persentil 1%: {np.percentile(v,1):.2f} | 5%: {np.percentile(v,5):.2f} | median {np.median(v):.2f}")
    tipis = pts[(~np.isnan(t)) & (t < 1.0)]
    if len(tipis):
        print(f"   {len(tipis)} titik < 1,0 mm; x {tipis[:,0].min():.1f}..{tipis[:,0].max():.1f}, y {tipis[:,1].min():.1f}..{tipis[:,1].max():.1f}, z {tipis[:,2].min():.1f}..{tipis[:,2].max():.1f}")

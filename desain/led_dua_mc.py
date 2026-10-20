#!/usr/bin/env python3
"""Uji Monte Carlo: akurasi klasifikasi dengan LED bawaan saja, LED2 saja, atau kedua LED berurutan (6 angka per ukur).
Memakai model spektral led_spektrum.py. Variasi daging antar-sampel (biologis) dibuat acak:
  bagian metmioglobin di sekitar pusat kelas, oksi/deoksi, kadar mioglobin, lemak/hamburan, kegelapan.
Pengklasifikasi: LDA (Linear Discriminant Analysis), validasi silang 5 lipatan, 600 sampel per kelas.
Jalankan: python3 desain/led_dua_mc.py
"""
import numpy as np
import led_spektrum as M

rng = np.random.default_rng(7)
PUSAT = {"segar": 0.10, "mulai_membusuk": 0.33, "busuk": 0.58}
GELAP = {"segar": 0.00, "mulai_membusuk": 0.05, "busuk": 0.12}
N = 600
CACAH = 60000.0          # cacah putih kanal tertinggi (setara rerata beberapa bacaan); derau R/G ~0,01

def pantulan(met, de, kadar, dasar, gelap):
    oks = max(0.0, 1 - met - de)
    KS = dasar + gelap + 0.27 * kadar * (oks * M.E["oksi"] + de * M.E["deoksi"] + met * M.E["met"])
    return 1 + KS - np.sqrt(KS**2 + 2 * KS)

def sampel():
    X, y = [], []
    for ci, (k, mu) in enumerate(PUSAT.items()):
        for _ in range(N):
            met = np.clip(rng.normal(mu, 0.075), 0, 0.95); de = rng.uniform(0.08, 0.35) * (1 - met)
            R = pantulan(met, de, rng.uniform(0.8, 1.25), rng.uniform(0.24, 0.40), max(0, GELAP[k] + rng.normal(0, 0.04)))
            X.append(R); y.append(ci)
    return np.array(X), np.array(y)

def fitur(Rs, S):
    w = M.baca(S, M.PUTIH); k = CACAH / w.max(); wc = w * k
    out = []
    for R in Rs:
        m = M.baca(S, R) * k; m = m + rng.normal(0, np.sqrt(2 * (m + 9)))
        out.append(m / wc * 255)
    return np.array(out)

def lda_cv(X, y, lipat=5):
    idx = rng.permutation(len(y)); benar = 0
    for f in range(lipat):
        te = idx[f::lipat]; tr = np.setdiff1d(idx, te)
        mus = [X[tr][y[tr] == c].mean(0) for c in range(3)]
        Sw = sum(np.cov(X[tr][y[tr] == c].T) for c in range(3)) / 3 + 1e-6 * np.eye(X.shape[1]); Si = np.linalg.inv(Sw)
        sk = np.stack([X[te] @ Si @ m - 0.5 * m @ Si @ m for m in mus], 1)
        benar += (sk.argmax(1) == y[te]).sum()
    return benar / len(y)

def transfer(Xa, Xb, y):
    """Latih dengan LED a, uji dengan LED b (sampel sama)."""
    mus = [Xa[y == c].mean(0) for c in range(3)]
    Si = np.linalg.inv(sum(np.cov(Xa[y == c].T) for c in range(3)) / 3)
    sk = np.stack([Xb @ Si @ m - 0.5 * m @ Si @ m for m in mus], 1); return (sk.argmax(1) == y).mean()

if __name__ == "__main__":
    Rs, y = sampel()
    nm = list(M.LEDS)
    F = {n: fitur(Rs, M.LEDS[n]) for n in nm}
    rg = lambda X: (X[:, :1] / X[:, 1:2])
    print(f"{len(y)} sampel tiruan, 3 kelas. Akurasi LDA (validasi silang 5 lipatan):")
    for n in nm: print(f"   {n:42s} R,G,B: {lda_cv(F[n], y) * 100:5.1f} %   hanya R/G: {lda_cv(rg(F[n]), y) * 100:5.1f} %")
    print(f"   {'LED bawaan + LED2 berurutan (6 angka)':42s}        {lda_cv(np.hstack([F[nm[0]], F[nm[1]]]), y) * 100:5.1f} %")
    print(f"   {'LED bawaan + LED 6500 K berurutan':42s}        {lda_cv(np.hstack([F[nm[0]], F[nm[2]]]), y) * 100:5.1f} %")
    print("\nModel dilatih dengan satu LED, lalu alat memakai LED lain tanpa melatih ulang (kalibrasi putih tetap dilakukan):")
    print(f"   latih LED bawaan, ukur LED2      : {transfer(F[nm[0]], F[nm[1]], y) * 100:5.1f} %")
    print(f"   latih LED2, ukur LED bawaan      : {transfer(F[nm[1]], F[nm[0]], y) * 100:5.1f} %")
    print(f"   latih LED bawaan, ukur LED bawaan: {transfer(F[nm[0]], F[nm[0]], y) * 100:5.1f} %  (pembanding)")

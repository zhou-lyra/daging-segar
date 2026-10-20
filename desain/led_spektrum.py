#!/usr/bin/env python3
"""LED kedua untuk BeefFresh: apakah LED putih lain lebih baik dari LED bawaan, dan bolehkah dua LED dipakai bergantian?

Model spektral sederhana (semua kurva adalah PENDEKATAN, bukan data ukur):
  * LED bawaan: Everlight 45-21/LK2C-B38452C4CB2/2T (forum Adafruit). Lembar data seri ini: putih hangat,
    bin CCT 3800-4500 K, Ra minimal 70. Dimodelkan: pompa biru 450 nm + satu fosfor lebar.
  * Calon LED2: putih netral 4000 K Ra >= 90 (pompa biru + fosfor hijau + fosfor merah), dan pembanding
    putih dingin 6500 K Ra 70 (LED 5 mm biasa).
  * Respons kanal TCS34725: Gaussian di sekitar puncak Figure 1 lembar data (B 465, G 525, R 615 nm).
  * Daging: pantulan Kubelka-Munk dari campuran oksimioglobin, deoksimioglobin, metmioglobin
    (puncak serapan dari pustaka mioglobin; tinggi dipilih supaya daging segar ~10 % di 540 nm, ~40 % di 650 nm).
    Kelas kesegaran dimodelkan sebagai naiknya bagian metmioglobin (perubahan warna merah ke coklat).
  * Bacaan dikalibrasi seperti firmware: (daging - hitam) / (putih - hitam) x 255, putih = kertas rata 90 %.
  * Derau: derau tembakan foton (akar cacah) + 3 cacah baca, dua kali (LED nyala dan LED mati dikurangkan).
Jalankan: python3 desain/led_spektrum.py
"""
import numpy as np

L = np.arange(380.0, 781.0, 1.0)
g = lambda mu, s: np.exp(-0.5 * ((L - mu) / s) ** 2)
def g2(mu, s1, s2): return np.where(L < mu, np.exp(-0.5 * ((L - mu) / s1) ** 2), np.exp(-0.5 * ((L - mu) / s2) ** 2))

# CIE 1931 (pendekatan Wyman, Sloan & Shirley 2013) untuk menghitung CCT model LED
xb = 1.056 * g2(599.8, 37.9, 31.0) + 0.362 * g2(442.0, 16.0, 26.7) - 0.065 * g2(501.1, 20.4, 26.2)
yb = 0.821 * g2(568.8, 46.9, 40.5) + 0.286 * g2(530.9, 16.3, 31.1)
zb = 1.217 * g2(437.0, 11.8, 36.0) + 0.681 * g2(459.0, 26.0, 13.8)
def cct(S):
    X, Y, Z = (S * xb).sum(), (S * yb).sum(), (S * zb).sum(); x, y = X / (X + Y + Z), Y / (X + Y + Z)
    n = (x - 0.3320) / (0.1858 - y); return 449 * n**3 + 3525 * n**2 + 6823.3 * n + 5520.33

def led(fosfor, target):
    """Cari porsi pompa biru supaya CCT model = target."""
    lo, hi = 0.0, 3.0
    for _ in range(60):
        m = (lo + hi) / 2; S = m * g(450, 10) + fosfor
        lo, hi = (m, hi) if cct(S) < target else (lo, m)
    S = m * g(450, 10) + fosfor; return S / (S * yb).sum()          # dinormalkan ke luminans sama

LEDS = {"LED bawaan (putih hangat ~4100 K, Ra 70)": led(g2(575, 45, 70), 4100),
        "LED2 putih netral 4000 K, Ra 90+": led(0.55 * g(530, 38) + 1.0 * g2(625, 35, 45), 4000),
        "LED 5 mm putih dingin 6500 K, Ra 70": led(g2(560, 42, 62), 6500)}

RESP = {"R": g2(615, 22, 30), "G": g2(525, 30, 34), "B": g2(465, 26, 30)}       # TCS34725, pendekatan Fig. 1

def eps(jenis):   # koefisien serapan relatif (mM^-1 cm^-1), pendekatan puncak pustaka
    if jenis == "oksi":  return 128 * g(418, 9) + 13.9 * g(543, 10) + 14.4 * g(581, 9) + 1.0 * g(500, 40)
    if jenis == "deoksi": return 115 * g(434, 10) + 12.9 * g(556, 22) + 1.0 * g(500, 40)
    if jenis == "met":   return 188 * g(409, 9) + 10.2 * g(503, 15) + 3.9 * g(630, 18) + 2.0 * g(560, 50)
E = {k: eps(k) for k in ("oksi", "deoksi", "met")}
def daging(met, gelap=0.0):
    oks = max(0.0, 0.78 - met); de = 1 - met - oks
    KS = 0.30 + gelap + 0.27 * (oks * E["oksi"] + de * E["deoksi"] + met * E["met"])
    return 1 + KS - np.sqrt(KS**2 + 2 * KS)

KELAS = {"segar": daging(0.08), "mulai_membusuk": daging(0.38, 0.05), "busuk": daging(0.65, 0.12)}
PUTIH = np.full_like(L, 0.90)
CACAH_PUTIH = 3000.0     # kanal tertinggi saat mengukur kertas putih (waktu integrasi diatur per LED)

def baca(S, R):
    return np.array([(S * R * RESP[c]).sum() for c in "RGB"])

def analisis(S):
    w = baca(S, PUTIH); k = CACAH_PUTIH / w.max()
    out = {}
    for n, R in KELAS.items():
        m = baca(S, R) * k; wc = w * k
        sd = np.sqrt(2 * (m + 9)) / wc * 255                      # nyala - mati, derau baca 3 cacah
        out[n] = (m / wc * 255, sd, m)
    return out

if __name__ == "__main__":
    print(f"Respons putih (kertas) per kanal R:G:B, dinormalkan ke kanal tertinggi; lalu daging terkalibrasi (0-255).\n")
    hasil = {}
    for nama, S in LEDS.items():
        w = baca(S, PUTIH); r = analisis(S); hasil[nama] = r
        print(f"{nama}: CCT model {cct(S):.0f} K, putih R:G:B = " + ":".join(f"{v / w.max():.2f}" for v in w))
        for n, (v, sd, m) in r.items():
            print(f"   {n:15s} R {v[0]:6.1f}  G {v[1]:5.1f}  B {v[2]:5.1f}   R/G {v[0] / v[1]:.2f}   sd {sd[0]:.2f}/{sd[1]:.2f}/{sd[2]:.2f}   cacah B {m[2]:.0f}")
        def jarak(a, b):
            (va, sa, _), (vb, sb, _) = r[a], r[b]; return float(np.sqrt((((va - vb) / np.sqrt(sa**2 + sb**2)) ** 2).sum()))
        def jarak_rg(a, b): return abs(r[a][0][0] / r[a][0][1] - r[b][0][0] / r[b][0][1])
        print(f"   pemisahan segar-mulai: {jarak('segar', 'mulai_membusuk'):.0f} x derau, selisih R/G {jarak_rg('segar', 'mulai_membusuk'):.2f};"
              f"  mulai-busuk: {jarak('mulai_membusuk', 'busuk'):.0f} x derau, selisih R/G {jarak_rg('mulai_membusuk', 'busuk'):.2f}\n")
    k1, k2 = list(LEDS)[0], list(LEDS)[1]
    print("Bila model klasifikasi dilatih dengan LED bawaan lalu alat pindah ke LED2 (keduanya sudah kalibrasi putih):")
    for n in KELAS:
        a, b = hasil[k1][n][0], hasil[k2][n][0]
        gap = abs(hasil[k1]["segar"][0][0] / hasil[k1]["segar"][0][1] - hasil[k1]["mulai_membusuk"][0][0] / hasil[k1]["mulai_membusuk"][0][1])
        print(f"   {n:15s} R/G {a[0] / a[1]:.2f} -> {b[0] / b[1]:.2f}  (geser {abs(a[0] / a[1] - b[0] / b[1]):.2f} = {abs(a[0] / a[1] - b[0] / b[1]) / gap * 100:.0f} % jarak segar-mulai)"
              f";  R {a[0]:.1f} -> {b[0]:.1f}, G {a[1]:.1f} -> {b[1]:.1f}, B {a[2]:.1f} -> {b[2]:.1f}")

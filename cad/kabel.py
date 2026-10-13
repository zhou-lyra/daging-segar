#!/usr/bin/env python3
"""Rute kabel skematis ESP32 -> OLED -> sensor (rangkai berantai), dicari otomatis agar tidak ada kabel yang bersentuhan.
Posisi pin ESP32 mengikuti DOIT DevKit V1 30 pin; header OLED dan sensor mengikuti urutan umum modulnya (BISA BERBEDA di papanmu).
Pakai:  from kabel import rute   -> daftar kabel dengan titik-titik polyline (mm)."""
import json, os, random
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, "kabel_rute.json")
R = 0.7; MIN_JARAK = 2 * R + 0.15   # jarak pusat-ke-pusat minimum antar kabel berbeda

def seg_dist(A, B):
    """jarak minimum antara dua himpunan segmen (N,2,3) dan (M,2,3) -> matriks (N,M)"""
    p1, q1 = A[:, 0][:, None, :], A[:, 1][:, None, :]; p2, q2 = B[:, 0][None, :, :], B[:, 1][None, :, :]
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = (d1 * d1).sum(-1), (d2 * d2).sum(-1), (d2 * r).sum(-1); c = (d1 * r).sum(-1); b = (d1 * d2).sum(-1)
    den = a * e - b * b; s = np.where(den > 1e-9, np.clip((b * f - c * e) / np.where(den > 1e-9, den, 1), 0, 1), 0.0)
    t = (b * s + f) / np.where(e > 1e-9, e, 1); t0 = np.clip(t, 0, 1)
    s = np.clip((b * t0 - c) / np.where(a > 1e-9, a, 1), 0, 1)
    return np.linalg.norm((p1 + d1 * s[..., None]) - (p2 + d2 * t0[..., None]), axis=-1)

# ---- geometri tetap (dari model OpenSCAD)
ESP_PIN = lambda k: 7.57 + 2.54 * k          # x pin ke-k dari ujung USB
Y_KIRI, Y_KANAN = 27.1, 1.7                   # baris pin ESP32 (kiri jika USB di bawah)
Z_PCB = 21.0
OLED_PIN_X = {"GND": 22.4, "VCC": 24.9, "SCL": 27.5, "SDA": 30.0}; OLED_PIN_Y = 25.3; OLED_PIN_Z = 26.4
SENSOR_X = 60.25; SENSOR_Z_PIN = 8.4
SENSOR_Y = {"VCC": 14.4 + (0 - 3) * 2.54, "GND": 14.4 + (2 - 3) * 2.54, "SDA": 14.4, "SCL": 14.4 + 1 * 2.54}   # VIN, GND, SDA, SCL (urutan Adafruit)
SUMBER = {"GND": (ESP_PIN(1), Y_KIRI, "GND"), "SCL": (ESP_PIN(5), Y_KIRI, "GPIO 27"), "SDA": (ESP_PIN(6), Y_KIRI, "GPIO 26"), "VCC": (ESP_PIN(0), Y_KANAN, "3V3")}
NAMA = ["GND", "SCL", "SDA", "VCC"]

def bangun(par):
    """par: {sinyal: dict(zl, zs, xd, yv)} -> {sinyal: list titik}"""
    out = {}
    for n in NAMA:
        xp, yr, _ = SUMBER[n]; p = par[n]; xo = OLED_PIN_X[n]; zl = p["zl"]; zs = p["zs"]; xd = p["xd"]; yl = p["yl"]; ys = SENSOR_Y[n]
        if n == "VCC":
            e = [(xp, yr, Z_PCB + 0.3), (xp, yr, zl), (xp, p["yv"], zl), (xo, p["yv"], zl), (xo, OLED_PIN_Y, zl), (xo, OLED_PIN_Y, OLED_PIN_Z)]
        else:
            e = [(xp, yr, Z_PCB + 0.3), (xp, yr, zl), (xo, yr, zl), (xo, OLED_PIN_Y, zl), (xo, OLED_PIN_Y, OLED_PIN_Z)]
        s = [(xo, OLED_PIN_Y, OLED_PIN_Z), (xo, OLED_PIN_Y, zs), (xo, yl, zs), (xd, yl, zs), (xd, ys, zs), (xd, ys, 9.6), (SENSOR_X, ys, 9.6), (SENSOR_X, ys, SENSOR_Z_PIN)]
        out[n] = [list(map(float, q)) for q in e + s[1:]]
    return out

def segs(pts): P = np.array(pts); return np.stack([P[:-1], P[1:]], axis=1)

# kotak terlarang (mm): modul WROOM, receptacle USB, PCB ESP32, papan sensor, header OLED + OLED
KOTAK = [((25.6, 5.4, 21.0), (51.1, 23.4, 24.2)), ((-1.1, 10.65, 21.0), (5.5, 18.15, 23.6)), ((0.3, 0.3, 19.4), (52.1, 28.5, 21.0)),
         ((58.7, 4.2, 3.4), (79.0, 24.6, 6.2)), ((12.6, 0.8, 26.5), (39.8, 28.0, 33.9))]
def dalam_kotak(rute, margin=R):
    pelanggaran = 0
    for n in NAMA:
        P = np.array(rute[n])
        for a, b in zip(P[:-1], P[1:]):
            L = np.linalg.norm(b - a); t = np.linspace(0, 1, max(2, int(L / 0.4)))[:, None]; pts = a + (b - a) * t
            for lo, hi in KOTAK:
                lo_, hi_ = np.array(lo) + margin * 0.6, np.array(hi) - margin * 0.6      # ujung kabel boleh menempel di permukaan
                m = np.all((pts > lo_) & (pts < hi_), axis=1)
                if m.sum() > 3: pelanggaran += int(m.sum())
    return pelanggaran

def tabrakan(rute):
    n_min = 1e9
    for i, a in enumerate(NAMA):
        for b in NAMA[i + 1:]:
            n_min = min(n_min, seg_dist(segs(rute[a]), segs(rute[b])).min())
    return n_min

def cari(seed=3, iterasi=40000):
    rnd = random.Random(seed); ZL = [22.0, 23.6, 25.2]; ZS = [21.9, 23.5, 25.1]; XD = [53.2, 54.8, 56.4, 58.0]
    YV = [8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]; YL = [2.0, 3.6, 24.3, 25.9, 27.5, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]
    terbaik = (-1, None)
    for _ in range(iterasi):
        par = {n: dict(zl=rnd.choice(ZL), zs=rnd.choice(ZS), xd=rnd.choice(XD), yv=rnd.choice(YV), yl=rnd.choice(YL)) for n in NAMA}
        r = bangun(par)
        if dalam_kotak(r): continue
        d = tabrakan(r)
        if d > terbaik[0]: terbaik = (d, par)
        if d >= MIN_JARAK: break
    return terbaik

def rute():
    if os.path.exists(CACHE):
        par = json.load(open(CACHE))
    else:
        d, par = cari(); json.dump(par, open(CACHE, "w"), indent=1); print(f"rute kabel dicari: jarak minimum {d:.2f} mm (syarat {MIN_JARAK:.2f})")
    r = bangun(par); return r, tabrakan(r), dalam_kotak(r)

if __name__ == "__main__":
    r, d, v = rute(); print("jarak minimum antar kabel:", round(d, 2), "mm | syarat >=", round(MIN_JARAK, 2), "| titik menembus komponen:", v)
    for n in NAMA: print(n, len(r[n]), "titik")

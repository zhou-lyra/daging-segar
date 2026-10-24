#!/usr/bin/env python3
"""Gambar tambahan: jalur kabel (skema + denah) dan ukuran setiap lembar PVC. Dipanggil oleh gambar.py."""
import math, os
import numpy as np
import geometri as G

BIRU, ABU, MERAH = "#1f5fa8", "#8a8f99", "#b3262e"
f1 = lambda v: (f"{v:.1f}".rstrip("0").rstrip(".")).replace(".", ",")
TX = lambda x, y, t, anc="middle", sz=14, w=600, col="#2a2226": (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{sz}" font-weight="{w}" fill="{col}" text-anchor="{anc}" '
                                                             f'paint-order="stroke" stroke="#fff" stroke-width="4" stroke-linejoin="round">{t}</text>')
DEFS = ('<defs><marker id="pa" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="' + BIRU + '"/></marker><marker id="pm" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="#b3262e"/></marker></defs>')
def svg(w, h, isi, judul): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" font-family="system-ui,Segoe UI,Roboto,sans-serif" role="img" aria-label="{judul}">{DEFS}{isi}</svg>'


# ============================================================================ peta titik solder (tidak berskala, papan berskala)
TITIK_ESP = ["3V3", "G25", "G26", "G27", "GND"]                 # E1..E5, urut dari atas gambar
TITIK_SENSOR = ["LED", "SDA", "SCL", "GND", "VIN"]              # S1..S5, urut tulisan di sisi depan papan sensor
TITIK_OLED = ["GND", "VCC", "SCL", "SDA"]                       # O1..O4, urut tulisan di OLED
URUT_SENSOR = ["LED", "INT", "SDA", "SCL", "3V3", "GND", "VIN"]    # sisi depan, kiri ke kanan (sama dengan gambar tim)


def potong_cm(mm):
    return math.ceil((mm + 20) / 5) * 5 / 10


def titik_dev(dev, pin):
    return f"S{TITIK_SENSOR.index(pin) + 1}" if dev == "Sensor" else f"O{TITIK_OLED.index(pin) + 1}"


def peta_solder(K, judul, catatan=""):
    """K: daftar dict(dari='Sensor VIN', ke='3V3', warna, panjang). Papan ESP32 digambar berskala dari geometri."""
    el = []; W_, S = 1180, 8.0
    E = G.ESP; ex0, ey0 = 70, 110; ew, eh = E["W"] * S, E["L"] * S
    el.append(TX(40, 34, judul, anc="start", sz=17, w=700))
    el.append(TX(40, 58, "Titik bernomor = tempat menyolder. Kabel disolder langsung ke pin, tanpa soket dupont. Warna kabel mengikuti kotak warna.", anc="start", sz=13, w=500, col="#555"))
    el.append(f'<rect x="{ex0}" y="{ey0}" width="{ew:.0f}" height="{eh:.0f}" rx="8" fill="#1d2024"/>')
    el.append(f'<rect x="{ex0 + ew / 2 - 30:.0f}" y="{ey0 + eh - 8:.0f}" width="60" height="30" rx="4" fill="#c0c4c9" stroke="#777"/>')
    el.append(TX(ex0 + ew / 2, ey0 + eh + 44, "USB", sz=12, w=600, col="#555"))
    el.append(f'<text x="{ex0 + ew / 2:.0f}" y="{ey0 + eh - 22:.0f}" font-size="11" font-weight="700" fill="#9aa0a6" text-anchor="middle">NodeMCU-32S</text>')
    el.append(TX(ex0 + ew / 2, ey0 - 30, "ESP32 terbalik, pin ke atas", sz=13, w=700))
    off = G.py0 - G.ESP["y0"]
    py = lambda i: ey0 + eh - (off + i * 2.54) * S
    xr = {0: ex0 + (E["W"] - E["pin_jarak_baris"]) / 2 * S, 1: ex0 + (E["W"] + E["pin_jarak_baris"]) / 2 * S}
    pos = {}
    for b, nama in ((0, G.B0), (1, G.B1)):
        for i, n in enumerate(nama):
            x, y = xr[b], py(i); dip = b == 1 and n in TITIK_ESP
            el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7 if dip else 4}" fill="{"#e3b85a" if dip else "#6f747c"}" stroke="{"#2a2226" if dip else "none"}" stroke-width="2"/>')
            el.append(f'<text x="{x + (9 if b == 0 else -11):.1f}" y="{y + 3.8:.1f}" font-size="{11 if dip else 9.5}" font-weight="{700 if dip else 400}" fill="{"#fff3c4" if dip else "#b9bec6"}" text-anchor="{"start" if b == 0 else "end"}">{n}</text>')
            pos[(n, b)] = (x, y)
    el.append(TX(xr[1], ey0 - 10, "baris 3V3", sz=11, w=700))
    # keterangan tiap titik ESP32
    bx, bh, gap = 330, 62, 10
    y_start = ey0 + 6
    for i, pn in enumerate(TITIK_ESP):
        x, y = pos[(pn, 1)]
        kab = sorted([kb for kb in K if kb["ke"] == pn], key=lambda kb: kb["dari"].startswith("OLED"))
        h = 30 + 22 * len(kab); by = y_start + sum(30 + 22 * len([kb for kb in K if kb["ke"] == q]) + gap for q in TITIK_ESP[:i])
        el.append(f'<path d="M{x + 8:.1f},{y:.1f} L{bx - 24:.1f},{y:.1f} L{bx - 8:.1f},{by + 16:.1f} L{bx:.1f},{by + 16:.1f}" fill="none" stroke="#2a2226" stroke-width="1.4"/>')
        el.append(f'<rect x="{bx}" y="{by}" width="300" height="{h}" rx="8" fill="#f3efe8" stroke="#d8cfc2"/>')
        el.append(f'<rect x="{bx + 8}" y="{by + 6}" width="32" height="20" rx="10" fill="#2a2226"/><text x="{bx + 24}" y="{by + 20}" font-size="12" font-weight="700" fill="#fff" text-anchor="middle">E{i + 1}</text>')
        el.append(TX(bx + 48, by + 21, f"pin {pn}" + ("  (2 kabel, 1 selongsong)" if len(kab) == 2 else ""), anc="start", sz=13, w=700))
        for j, kb in enumerate(kab):
            dev, pin = kb["dari"].split(); yy = by + 46 + j * 22
            el.append(f'<rect x="{bx + 12}" y="{yy - 11}" width="30" height="12" rx="3" fill="{kb["warna"]}"/>')
            el.append(TX(bx + 50, yy, f"ke {titik_dev(dev, pin)} {dev} {pin}, potong {f1(potong_cm(kb['panjang']))} cm", anc="start", sz=12.5, w=500))
    # perangkat
    def header(x0, y0, nama, judul_, warna, nomor, dev):
        w = (len(nama) - 1) * 50 + 60
        el.append(f'<rect x="{x0 - 30}" y="{y0 - 34}" width="{w}" height="62" rx="8" fill="{warna}"/>')
        el.append(TX(x0 - 30, y0 - 44, judul_, anc="start", sz=14, w=700))
        for i, n in enumerate(nama):
            x = x0 + i * 50; ada = n in nomor
            el.append(f'<text x="{x}" y="{y0 - 12}" font-size="12" font-weight="700" fill="#fff" text-anchor="middle">{n}</text>')
            el.append(f'<circle cx="{x}" cy="{y0 + 8}" r="7" fill="{"#e3b85a" if ada else "#8c8f95"}" stroke="#2a2226" stroke-width="{2 if ada else 0}"/>')
            if ada:
                kb = next(k for k in K if k["dari"] == f"{dev} {n}")
                el.append(f'<rect x="{x - 16}" y="{y0 + 36}" width="32" height="20" rx="10" fill="#2a2226"/><text x="{x}" y="{y0 + 50}" font-size="12" font-weight="700" fill="#fff" text-anchor="middle">{titik_dev(dev, n)}</text>')
                el.append(f'<rect x="{x - 15}" y="{y0 + 62}" width="30" height="10" rx="3" fill="{kb["warna"]}"/>')
                el.append(TX(x, y0 + 90, f"E{TITIK_ESP.index(kb['ke']) + 1}", sz=12, w=700)); el.append(TX(x, y0 + 106, kb["ke"], sz=11, w=500, col="#555"))
            else:
                el.append(TX(x, y0 + 52, "kosong", sz=11, w=600, col="#888"))
    header(720, 150, URUT_SENSOR, "Sensor TCS34725, dilihat dari depan (tulisan pin)", "#6a2c91", TITIK_SENSOR, "Sensor")
    header(720, 400, TITIK_OLED, "OLED SSD1306 (tulisan pin)", "#1d4f9c", TITIK_OLED, "OLED")
    el.append(TX(690, 560, "Baris bawah tiap pin: nomor titik pasangannya di ESP32.", anc="start", sz=12.5, w=500, col="#555"))
    el.append(TX(690, 580, "Header sensor: plastik di punggung papan, kabel disolder di ujung pin.", anc="start", sz=12.5, w=500, col="#555"))
    # tabel
    ty = max(ey0 + eh + 90, 640); cols = [40, 92, 180, 400, 640, 820]
    el.append(TX(40, ty - 14, "Daftar kabel: potong sepanjang kolom terakhir (jalur di model + 2 cm), kupas 4 mm kedua ujung.", anc="start", sz=14, w=700))
    for x, h in zip(cols, ["No", "Warna", "Titik awal di ESP32", "Titik akhir", "Jalur model", "Potong"]):
        el.append(TX(x, ty + 12, h, anc="start", sz=12.5, w=700, col="#555"))
    urut = sorted(K, key=lambda kb: (TITIK_ESP.index(kb["ke"]), kb["dari"].startswith("OLED")))
    for r, kb in enumerate(urut):
        y = ty + 36 + r * 24; dev, pin = kb["dari"].split()
        if r % 2 == 0: el.append(f'<rect x="32" y="{y - 16}" width="{W_ - 64}" height="24" fill="#f3efe8"/>')
        el.append(TX(cols[0], y, str(r + 1), anc="start", sz=12.5, w=600))
        el.append(f'<rect x="{cols[1]}" y="{y - 11}" width="30" height="12" rx="3" fill="{kb["warna"]}"/>')
        el.append(TX(cols[1] + 36, y, G.NAMA_WARNA[G.SINYAL[kb["ke"]]], anc="start", sz=12, w=500))
        el.append(TX(cols[2], y, f'E{TITIK_ESP.index(kb["ke"]) + 1}  pin {kb["ke"]}', anc="start", sz=12.5, w=700))
        el.append(TX(cols[3], y, f"{titik_dev(dev, pin)}  {dev} {pin}", anc="start", sz=12.5, w=700))
        el.append(TX(cols[4], y, f1(kb["panjang"]) + " mm", anc="start", sz=12.5, w=500))
        el.append(TX(cols[5], y, f1(potong_cm(kb["panjang"])) + " cm", anc="start", sz=13, w=700, col=MERAH))
    yb = ty + 36 + len(urut) * 24 + 6
    cat = ["Pin 3V3, GND, G26 dan G27 menerima DUA kabel (ke sensor dan ke OLED), disolder bersama di satu pin dan ditutup satu selongsong. G25 hanya satu kabel.",
           "VIN sensor ke 3V3 ESP32, BUKAN ke 5V. Pin 5V ESP32, pin 3V3 sensor, dan INT sensor tidak dipakai."] + ([catatan] if catatan else [])
    for i, t_ in enumerate(cat): el.append(TX(40, yb + i * 21, t_, anc="start", sz=12.5, w=500, col="#555"))
    return svg(W_, yb + len(cat) * 21 + 10, "".join(el), judul)


def skema():
    return peta_solder(list(G.KABEL.values()), "Model 2: peta titik solder dan daftar kabel")


# ============================================================================ denah jalur kabel (berskala, dari model)
def denah():
    S = 9.0; m = (60, 60, 60, 60); W = G.W
    X = lambda x: m[0] + x * S; Y = lambda y: m[1] + (W - y) * S
    el = [f'<rect x="{X(0)}" y="{Y(W)}" width="{W*S}" height="{W*S}" fill="#f4f0ea" stroke="#6c6469" stroke-width="1.6"/>',
          f'<rect x="{X(G.t)}" y="{Y(W-G.t)}" width="{(W-2*G.t)*S}" height="{(W-2*G.t)*S}" fill="none" stroke="#b5ada2" stroke-dasharray="5 4"/>']
    E = G.ESP; el.append(f'<rect x="{X(E["x0"])}" y="{Y(E["y0"]+E["L"])}" width="{E["W"]*S}" height="{E["L"]*S}" fill="#1f6f43" opacity=".18" stroke="#1f6f43"/>')
    O = G.OLED; el.append(f'<rect x="{X(O["cx"]-O["L"]/2)}" y="{Y(O["cy"]+O["H"]/2)}" width="{O["L"]*S}" height="{O["H"]*S}" fill="#1d4f9c" opacity=".08" stroke="#1d4f9c" stroke-dasharray="3 3"/>')
    J = G.JENDELA; el.append(f'<rect x="{X(J[0])}" y="{Y(J[3])}" width="{(J[1]-J[0])*S}" height="{(J[3]-J[2])*S}" fill="#fff" stroke="#2a2226" stroke-width="1.6"/>')
    for (n, b), _ in G.ESP_DIPAKAI.items():
        p = G.pin_esp(n, b); el.append(f'<circle cx="{X(p[0])}" cy="{Y(p[1])}" r="{G.R_SAMB*S}" fill="#202020"/>')
    urut = sorted(G.KABEL.items(), key=lambda kv: -kv[1]["titik"][:, 2].mean())
    for k, kb in urut:
        if k.startswith("kabel_y_"): continue
        P = kb["titik"]; d = "M" + " L".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in P)
        el.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>')
        el.append(f'<path d="{d}" fill="none" stroke="{kb["warna"]}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, pn in enumerate(TITIK_ESP):
        p = G.pin_esp(pn, 1); el.append(f'<circle cx="{X(p[0])}" cy="{Y(p[1])}" r="7" fill="#e3b85a" stroke="#2a2226" stroke-width="2"/>')
        el.append(TX(X(p[0]) - 12, Y(p[1]) + 4, f"E{i + 1} {pn}", anc="end", sz=11, w=700))
    el.append(TX(X(E["x0"] + E["W"] / 2), Y(E["y0"] + 4), "ESP32 NodeMCU-32S (dibalik)", sz=13, col="#145233"))
    el.append(TX(X(O["cx"] + 4), Y(O["cy"] + O["H"] / 2) - 8, "OLED di tutup atas", sz=13, col="#1d4f9c"))

    el.append(TX(X(W / 2), Y(W) - 12, "kanan", sz=13, col="#6c6469")); el.append(TX(X(W / 2), Y(0) + 24, "kiri (takik USB)", sz=13, col="#6c6469"))
    el.append(f'<text x="{X(0)-14}" y="{Y(W/2)}" font-size="13" font-weight="600" fill="#6c6469" text-anchor="middle" transform="rotate(-90 {X(0)-14} {Y(W/2)})">depan (kait)</text>')
    el.append(f'<text x="{X(W)+14}" y="{Y(W/2)}" font-size="13" font-weight="600" fill="#6c6469" text-anchor="middle" transform="rotate(90 {X(W)+14} {Y(W/2)})">belakang (engsel)</text>')
    for k, kb in G.KABEL.items():
        if k.startswith("kabel_y_"): continue
        p0 = kb["titik"][0]; lab = ("S " if k.startswith("kabel_s_") else "O ") + k.split("_")[-1]
        if k.startswith("kabel_o_"):
            xx, yy = X(p0[0]) + 4, Y(p0[1]) + 10
            el.append(f'<text x="{xx:.1f}" y="{yy:.1f}" font-size="11" font-weight="700" fill="{kb["warna"]}" text-anchor="end" transform="rotate(-90 {xx:.1f} {yy:.1f})" paint-order="stroke" stroke="#fff" stroke-width="3">{lab}</text>')
        else:
            el.append(TX(X(p0[0]) + 12, Y(p0[1]) + 4, lab, anc="start", sz=11, w=700, col=kb["warna"]))
    el.append(TX(X(G.W) - 6, Y(4), "S = ke sensor (lewat jendela kabel, kotak putih), O = ke OLED", anc="end", sz=12, w=600, col="#555"))
    return svg(W * S + m[0] + m[2] + 40, W * S + m[1] + m[3], "".join(el), "Denah jalur kabel")


# ============================================================================ ukuran setiap lembar PVC
class Lembar:
    """Satu lembar PVC: kerangka (w x h mm), lubang/takik, tanda (garis putus), ukuran berantai."""
    def __init__(s, judul, w, h, jumlah=1, tepi=None, catatan="", bentuk=None):
        s.judul, s.w, s.h, s.jumlah, s.tepi, s.catatan, s.bentuk = judul, w, h, jumlah, tepi or {}, catatan, bentuk
        s.lubang, s.tanda, s.ukH, s.ukV = [], [], [], []
    def kotak(s, u0, u1, v0, v1, label="", tanda=False, ukur=True):
        (s.tanda if tanda else s.lubang).append(("r", u0, u1, v0, v1, label))
        if ukur: s.ukH.append((u0, u1)); s.ukV.append((v0, v1))
        return s
    def bulat(s, cu, cv, r, label="", tanda=False, ukur=True):
        (s.tanda if tanda else s.lubang).append(("c", cu, cv, r, label))
        if ukur: s.ukH.append((cu, cu)); s.ukV.append((cv, cv))
        return s

    def gambar(s, ox, oy, S):
        el = []; X = lambda u: ox + u * S; Y = lambda v: oy + (s.h - v) * S
        if s.bentuk:
            el.append('<path d="M' + " L".join(f"{X(u):.1f},{Y(v):.1f}" for u, v in s.bentuk) + ' Z" fill="#ebe6dd" stroke="#2a2226" stroke-width="1.6"/>')
        else:
            el.append(f'<rect x="{X(0):.1f}" y="{Y(s.h):.1f}" width="{s.w*S:.1f}" height="{s.h*S:.1f}" fill="#ebe6dd" stroke="#2a2226" stroke-width="1.6"/>')
        for t_ in s.tanda:
            if t_[0] == "r": el.append(f'<rect x="{X(t_[1]):.1f}" y="{Y(t_[4]):.1f}" width="{(t_[2]-t_[1])*S:.1f}" height="{(t_[4]-t_[3])*S:.1f}" fill="none" stroke="#6c6469" stroke-width="1.1" stroke-dasharray="5 3"/>')
            else: el.append(f'<circle cx="{X(t_[1]):.1f}" cy="{Y(t_[2]):.1f}" r="{t_[3]*S:.1f}" fill="none" stroke="#6c6469" stroke-width="1.1" stroke-dasharray="6 4"/>')
            if t_[-1]: el.append(TX(X((t_[1] + t_[2]) / 2) if t_[0] == "r" else X(t_[1]), (Y(t_[4]) + 15) if t_[0] == "r" else Y(t_[2] + t_[3]) + 15, t_[-1] + (f" {f1(t_[2]-t_[1])}x{f1(t_[4]-t_[3])}" if t_[0] == "r" and (t_[2]-t_[1]) * S > 70 else ""), sz=11, w=600, col="#6c6469"))
        for l_ in s.lubang:
            if l_[0] == "r":
                el.append(f'<rect x="{X(l_[1]):.1f}" y="{Y(l_[4]):.1f}" width="{(l_[2]-l_[1])*S:.1f}" height="{(l_[4]-l_[3])*S:.1f}" fill="#fff" stroke="{MERAH}" stroke-width="1.6"/>')
                if l_[-1]: el.append(TX(X((l_[1] + l_[2]) / 2), Y((l_[3] + l_[4]) / 2) + 5, l_[-1] + (f" {f1(l_[2]-l_[1])}x{f1(l_[4]-l_[3])}" if (l_[2]-l_[1]) * S > 70 else ""), sz=11, w=700, col=MERAH))
            else:
                el.append(f'<circle cx="{X(l_[1]):.1f}" cy="{Y(l_[2]):.1f}" r="{max(l_[3]*S, 2.5):.1f}" fill="#fff" stroke="{MERAH}" stroke-width="1.6"/>')
        # ukuran potong (merah): lebar dan tinggi lembar
        yb = Y(0) + 30
        el += dimH(X(0), X(s.w), yb, f1(s.w) + " mm", warna=MERAH); el += dimV(X(0) - 30, Y(0), Y(s.h), f1(s.h) + " mm", warna=MERAH)
        # letak tanda/lubang (biru): berantai dari tepi kiri sampai tepi kanan, dan dari tepi bawah sampai tepi atas
        hs = sorted({round(v, 2) for a_, b_ in s.ukH for v in (a_, b_) if 0 < v < s.w})
        if hs:
            pts = [0] + hs + [s.w]
            for i in range(len(pts) - 1):
                el += dimH(X(pts[i]), X(pts[i + 1]), yb + 34, f1(pts[i + 1] - pts[i]), kecil=True)
            el.append(TX(X(0), yb + 52, "letak tanda, mulai dari tepi kiri", anc="start", sz=10.5, w=600, col=BIRU))
        vs = sorted({round(v, 2) for a_, b_ in s.ukV for v in (a_, b_) if 0 < v < s.h})
        if vs and s.h * S > 110:
            pts = [0] + vs + [s.h]
            for i in range(len(pts) - 1):
                el += dimV(X(s.w) + 26, Y(pts[i]), Y(pts[i + 1]), f1(pts[i + 1] - pts[i]), kanan=True, kecil=True)
            if s.h * S > 150: el.append(f'<text x="{X(s.w) + 60:.1f}" y="{Y(s.h / 2):.1f}" font-size="10.5" font-weight="600" fill="{BIRU}" text-anchor="middle" transform="rotate(90 {X(s.w) + 60:.1f} {Y(s.h / 2):.1f})">mulai dari tepi bawah</text>')
        for sisi, t_ in s.tepi.items():
            if sisi == "bawah": el.append(TX(X(0) + 4, Y(0) - 6, t_, anc="start", sz=11, w=600, col="#6c6469"))
            if sisi == "atas": el.append(TX(X(s.w / 2), Y(s.h) + 15, t_, sz=11, w=600, col="#6c6469"))
            if sisi == "kiri": el.append(f'<text x="{X(0)+14:.1f}" y="{Y(s.h/2):.1f}" font-size="11" font-weight="600" fill="#6c6469" text-anchor="middle" transform="rotate(-90 {X(0)+14:.1f} {Y(s.h/2):.1f})">{t_}</text>')
            if sisi == "kanan": el.append(f'<text x="{X(s.w)-10:.1f}" y="{Y(s.h/2):.1f}" font-size="11" font-weight="600" fill="#6c6469" text-anchor="middle" transform="rotate(90 {X(s.w)-10:.1f} {Y(s.h/2):.1f})">{t_}</text>')
        el.append(TX(X(0), Y(s.h) - 52, f"{s.judul}" + (f"  ×{s.jumlah}" if s.jumlah > 1 else ""), anc="start", sz=15, w=700))
        el.append(TX(X(0), Y(s.h) - 33, f"Potong {f1(s.w)} x {f1(s.h)} mm" + (f", {s.jumlah} lembar" if s.jumlah > 1 else ", 1 lembar"), anc="start", sz=13, w=700, col=MERAH))
        if s.catatan: el.append(TX(X(0), Y(s.h) - 14, s.catatan, anc="start", sz=12, w=400, col="#555"))
        return el

    def ukuran_px(s, S):
        teks = max(len(s.catatan) * 6.3, len(f"Potong {f1(s.w)} x {f1(s.h)} mm, 2 lembar") * 7.6, len(s.judul) * 8.6)
        return max(s.w * S + 30 + 110 + 50, teks + 70), s.h * S + 78 + 30 + 70


def dimH(a, b, y, t, kecil=False, warna=None):
    if abs(b - a) < 0.5: return []
    c = warna or BIRU; m = "pm" if warna else "pa"
    out = [f'<line x1="{a:.1f}" y1="{y:.1f}" x2="{b:.1f}" y2="{y:.1f}" stroke="{c}" stroke-width="{1.6 if warna else 1.2}" marker-start="url(#{m})" marker-end="url(#{m})"/>',
           f'<line x1="{a:.1f}" y1="{y-6:.1f}" x2="{a:.1f}" y2="{y+6:.1f}" stroke="{c}" stroke-width=".8"/><line x1="{b:.1f}" y1="{y-6:.1f}" x2="{b:.1f}" y2="{y+6:.1f}" stroke="{c}" stroke-width=".8"/>']
    out.append(TX((a + b) / 2, y - 5, t, sz=11 if kecil else 13.5, w=700, col=c)); return out


def dimV(x, a, b, t, kanan=False, kecil=False, warna=None):
    if abs(b - a) < 0.5: return []
    c = warna or BIRU; m = "pm" if warna else "pa"
    out = [f'<line x1="{x:.1f}" y1="{a:.1f}" x2="{x:.1f}" y2="{b:.1f}" stroke="{c}" stroke-width="{1.6 if warna else 1.2}" marker-start="url(#{m})" marker-end="url(#{m})"/>',
           f'<line x1="{x-6:.1f}" y1="{a:.1f}" x2="{x+6:.1f}" y2="{a:.1f}" stroke="{c}" stroke-width=".8"/><line x1="{x-6:.1f}" y1="{b:.1f}" x2="{x+6:.1f}" y2="{b:.1f}" stroke="{c}" stroke-width=".8"/>']
    out.append(TX(x + (8 if kanan else -8), (a + b) / 2 + 4, t, anc="start" if kanan else "end", sz=11 if kecil else 13.5, w=700, col=c)); return out


DAFTAR = []      # (gambar, judul, w, h, jumlah, catatan) setiap lembar yang pernah digambar


def legenda(lebar):
    if lebar < 900:
        return [f'<rect x="20" y="10" width="{lebar - 40}" height="76" rx="8" fill="#f3efe8" stroke="#ddd5c8"/>', TX(34, 30, "Semua angka dalam milimeter (mm).", anc="start", sz=12.5, w=700),
                TX(34, 52, "MERAH = ukuran potong, garis potong, lubang", anc="start", sz=11.5, w=600, col=MERAH), TX(34, 73, "BIRU = letak, berantai dari tepi kiri / bawah", anc="start", sz=11.5, w=600, col=BIRU)]
    el = [f'<rect x="20" y="14" width="{lebar - 40}" height="58" rx="8" fill="#f3efe8" stroke="#ddd5c8"/>',
          TX(36, 37, "Cara membaca: semua angka dalam milimeter (mm).", anc="start", sz=13, w=700),
          f'<line x1="36" y1="56" x2="70" y2="56" stroke="{MERAH}" stroke-width="2"/>', TX(76, 60, "MERAH = ukuran potong lembar, garis potong, lubang bor", anc="start", sz=12, w=600, col=MERAH),
          f'<line x1="470" y1="56" x2="504" y2="56" stroke="{BIRU}" stroke-width="1.6"/>', TX(510, 60, "BIRU = letak tanda/lubang, berantai dari tepi kiri dan tepi bawah (jumlahnya = ukuran lembar)", anc="start", sz=12, w=600, col=BIRU)]
    return el


def susun(lembar, judul, kolom=3, S=4.2, lebar=1180):
    el, x, y, tinggi_baris = legenda(lebar), 30, 92, 0
    for L_ in lembar:
        w, h = L_.ukuran_px(S)
        if x + w > lebar: x, y = 30, y + tinggi_baris + 10; tinggi_baris = 0
        el += L_.gambar(x + 84, y + 78, S); x += w + 40; tinggi_baris = max(tinggi_baris, h)
        DAFTAR.append((judul, L_.judul, L_.w, L_.h, L_.jumlah, L_.catatan))
    return svg(lebar, y + tinggi_baris + 20, "".join(el), judul)


def lembar_baki():
    W, t, hb = G.W, G.t, G.F + G.Hc; ax, az = G.SUMBU_ENGSEL; YC = G.YC
    L = [Lembar("Lantai baki", W, W, tepi={"bawah": "depan", "atas": "belakang"}, catatan="polos; empat dinding berdiri di atasnya"),
         Lembar("Dinding depan baki", W, hb, tepi={"bawah": "tepi bawah (ke lantai)"}, catatan="tampak luar; tepi atas = bibir tempat kepala menutup").kotak(YC - 9, YC + 9, G.Hc - 14 + G.F, G.Hc - 2 + G.F, "kait", tanda=True),
         Lembar("Dinding belakang baki", W, hb, tepi={"bawah": "tepi bawah"}, catatan="tampak luar; poros engsel di tepi atas, tandai lubang lewat daun engsel")
            .kotak(22 - 12.5, 22 + 12.5, az - 14 + G.F, az - 1 + G.F, "engsel", tanda=True).kotak(W - 22 - 12.5, W - 22 + 12.5, az - 14 + G.F, az - 1 + G.F, "engsel", tanda=True),
         Lembar("Dinding kiri / kanan baki", W - 2 * t, hb, jumlah=2, tepi={"bawah": "tepi bawah"}, catatan="dipasang di antara dinding depan dan belakang")]
    return susun(L, "Lembar PVC baki bawah")


def lembar_kepala():
    W, t, d = G.W, G.t, G.P["kepala_dalam"]; J = G.JENDELA; az = G.SUMBU_ENGSEL[1]; YC = G.YC; zk0 = G.Hc + t
    ex = G.ESP["x0"] + G.ESP["W"] / 2
    py = [sorted([G.papan(b0, 0, 0)[1], G.papan(b1, 0, 0)[1]]) for b0, b1 in G.PIPI_BX]
    lantai = Lembar("Lantai kepala (dilihat dari atas)", W, W, tepi={"kiri": "depan", "kanan": "belakang", "bawah": "kiri (sisi USB)"}, catatan="u = dari depan, v = dari kiri; garis putus ditandai di sisi BAWAH")
    # lantai: sumbu u = X (depan->belakang), v = Y (kiri->kanan)
    lantai.kotak(J[0], J[1], J[2], J[3], "jendela")
    lantai.bulat(G.XC, G.YC, G.R, "tutup cat Ø 65", tanda=True)
    lantai.catatan = "tepi kiri gambar = depan, tepi bawah = kiri; putus = tanda di sisi BAWAH lantai"
    for y0, y1 in py: lantai.kotak(G.PIPI_POLI[0][0], G.PIPI_POLI[1][0], y0, y1, "", tanda=True, ukur=False)
    L = [lantai,
         Lembar("Dinding depan kepala", W, d, tepi={"bawah": "tepi bawah (ke lantai kepala)"}, catatan="tampak luar; tuas kait 1 mm di bawah tepi ini").kotak(YC - 9, YC + 9, 0, G.Hc + 12 - zk0, "kait", tanda=True),
         Lembar("Dinding belakang kepala", W, d, tepi={"bawah": "tepi bawah"}, catatan="tampak luar; daun engsel turun 3 mm ke tepi lantai")
            .kotak(22 - 12.5, 22 + 12.5, 0, az + 14 - zk0, "engsel", tanda=True).kotak(W - 22 - 12.5, W - 22 + 12.5, 0, az + 14 - zk0, "engsel", tanda=True),
         Lembar("Dinding kiri kepala", W - 2 * t, d, tepi={"bawah": "tepi bawah", "kiri": "ujung depan"}, catatan="takik USB dipotong dari tepi bawah").kotak(ex - 6.5 - t, ex + 6.5 - t, 0, 10, "USB"),
         Lembar("Dinding kanan kepala", W - 2 * t, d, tepi={"bawah": "tepi bawah"}, catatan="polos")]
    return susun(L, "Lembar PVC kepala")


def lembar_kecil():
    W, t = G.W, G.t; O = G.OLED
    tutup = Lembar("Tutup atas (dilihat dari atas)", W, W, tepi={"kiri": "depan", "kanan": "belakang", "bawah": "kiri"}, catatan="4 lubang Ø 2,2 (23,3 x 23,3) sepusat jendela")
    tutup.kotak(O["cx"] - 12.5, O["cx"] + 12.5, O["cy"] - 7.5, O["cy"] + 7.5, "jendela")
    for sx in (-1, 1):
        for sy in (-1, 1): tutup.bulat(O["cx"] + sx * O["lubang"], O["cy"] + sy * O["lubang"], 1.1, ukur=False)
    tutup.kotak(t, W - t, t, W - t, "", tanda=True, ukur=False)
    pw, ph = G.PELAT["bx1"] - G.PELAT["bx0"], G.PELAT["by1"] - G.PELAT["by0"]
    pelat = Lembar("Pelat dudukan sensor", pw, ph, tepi={}, catatan="PVC hitam; tepi atas = sisi lubang")
    for hx, hy_ in G.TCS["lubang"]: pelat.bulat(hx - G.PELAT["bx0"], hy_ - G.PELAT["by0"], 1.4)
    pp = [(p[0] - G.PIPI_POLI[0][0], p[1] - G.PIPI_POLI[1][1]) for p in G.PIPI_POLI]
    pipi = Lembar("Pipi penyangga", G.PIPI_POLI[1][0] - G.PIPI_POLI[0][0], G.Hc - G.PIPI_POLI[1][1], jumlah=2, catatan="PVC hitam; sisi atas ke lantai kepala, sisi miring 40°", bentuk=pp)
    pipi.ukV.append((pp[0][1], pp[0][1]))
    L = [tutup, Lembar("Bibir panjang", 79.4, 6, jumlah=2, catatan="di sisi bawah tutup atas, 3 mm dari tepi kiri/kanan... lihat garis putus"),
         Lembar("Bibir pendek", 74, 6, jumlah=2, catatan="di antara bibir panjang"), pelat, pipi,
         Lembar("Lapisan balok kalibrasi", 60, 60, jumlah=6, catatan="3 lapis per balok; putih: kertas HVS, hitam: beludru")]
    L[1].catatan = "di sisi bawah tutup atas (garis putus)"
    return susun(L, "Lembar PVC kecil")


if __name__ == "__main__":
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gambar")
    for nama, isi in (("6_skema_kabel.svg", skema()), ("7_denah_kabel.svg", denah()), ("8_lembar_baki.svg", lembar_baki()), ("9_lembar_kepala.svg", lembar_kepala()), ("10_lembar_kecil.svg", lembar_kecil())):
        open(os.path.join(OUT, nama), "w").write(isi)
    print("ditulis 6..10")

#!/usr/bin/env python3
"""Gambar tambahan: jalur kabel (skema + denah) dan ukuran setiap lembar PVC. Dipanggil oleh gambar.py."""
import math, os
import numpy as np
import geometri as G

BIRU, ABU, MERAH = "#1f5fa8", "#8a8f99", "#b3262e"
f1 = lambda v: (f"{v:.1f}".rstrip("0").rstrip(".")).replace(".", ",")
TX = lambda x, y, t, anc="middle", sz=14, w=600, col="#2a2226": (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{sz}" font-weight="{w}" fill="{col}" text-anchor="{anc}" '
                                                             f'paint-order="stroke" stroke="#fff" stroke-width="4" stroke-linejoin="round">{t}</text>')
DEFS = ('<defs><marker id="pa" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="' + BIRU + '"/></marker></defs>')
def svg(w, h, isi, judul): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" font-family="system-ui,Segoe UI,Roboto,sans-serif" role="img" aria-label="{judul}">{DEFS}{isi}</svg>'


# ============================================================================ skema kabel (tidak berskala)
def skema():
    el = []; W_, H_ = 1180, 700
    ex0, ey0, ew, eh = 130, 60, 220, 500
    el.append(TX(ex0 + ew / 2, ey0 - 26, "ESP32 DOIT V1, dilihat dari atas (papan dibalik)", sz=15, w=700))
    el.append(f'<rect x="{ex0}" y="{ey0}" width="{ew}" height="{eh}" rx="10" fill="#1f6f43"/>')
    el.append(f'<rect x="{ex0 + ew/2 - 22}" y="{ey0 + eh - 6}" width="44" height="24" rx="4" fill="#c0c4c9" stroke="#777"/>')
    el.append(TX(ex0 + ew / 2 + 30, ey0 + eh + 14, "USB", anc="start", sz=13))
    pitch = (eh - 70) / 14; pin_y = lambda i: ey0 + eh - 35 - i * pitch
    xs = {0: ex0 + 22, 1: ex0 + ew - 22}; pos = {}
    for b, nama in ((0, G.B0), (1, G.B1)):
        for i, n in enumerate(nama):
            x, y = xs[b], pin_y(i); dip = (n, b) in G.ESP_DIPAKAI
            el.append(f'<circle cx="{x}" cy="{y}" r="{7 if dip else 4.5}" fill="{"#e3b85a" if dip else "#7aa58c"}" stroke="#0d3a22" stroke-width="1.2"/>')
            el.append(f'<text x="{x + (16 if b == 0 else -16)}" y="{y + 5}" font-size="{13 if dip else 12}" font-weight="{700 if dip else 400}" fill="{"#fff3c4" if dip else "#cfe6d8"}" text-anchor="{"start" if b == 0 else "end"}">{n}</text>')
            pos[(n, b)] = (x, y)
    el.append(f'<text x="{xs[0] - 6}" y="{ey0 + 20}" font-size="12" fill="#cfe6d8" text-anchor="start">baris VIN</text><text x="{xs[1] + 6}" y="{ey0 + 20}" font-size="12" fill="#cfe6d8" text-anchor="end">baris 3V3</text>')

    def header(x0, y0, nama, judul, warna):
        w = len(nama) * 34 + 20
        el.append(f'<rect x="{x0 - 27}" y="{y0 - 38}" width="{w}" height="54" rx="8" fill="{warna}"/>')
        el.append(TX(x0 - 27 + w / 2, y0 - 50, judul, sz=15, w=700)); p_ = {}
        for i, n in enumerate(nama):
            x = x0 + i * 34
            el.append(f'<text x="{x}" y="{y0 - 18}" font-size="12" font-weight="700" fill="#fff" text-anchor="middle">{n}</text>')
            el.append(f'<rect x="{x - 7}" y="{y0 - 7}" width="14" height="14" fill="#e3b85a" stroke="#333"/>'); p_[n] = (x, y0 + 7)
        return p_
    sp = header(700, 400, G.TCS["pin"], "TCS34725 (dari sisi punggung)", "#6a2c91")
    op = header(770, 140, ["GND", "VCC", "SCL", "SDA"], "OLED SSD1306", "#1d4f9c")
    paths = []
    def jalur(pts, col): paths.append((" ".join(("M" if i == 0 else "L") + f"{x:.0f},{y:.0f}" for i, (x, y) in enumerate(pts)), col))
    jx = xs[1] + 46
    WARNA = {"3V3": "#e0245e", "D21": "#e67e22", "D22": "#8e44ad"}
    for k, (pe, ps, po) in enumerate((("3V3", "VIN", "VCC"), ("D21", "SDA", "SDA"), ("D22", "SCL", "SCL"))):
        x1, y1 = pos[(pe, 1)]; col = WARNA[pe]
        jalur([(x1, y1), (jx, y1)], col)
        xs_, ys_ = sp[ps]; xv, ly = jx + 40 + k * 18, 470 + k * 16
        jalur([(jx, y1), (xv, y1), (xv, ly), (xs_, ly), (xs_, ys_)], col)
        xo, yo = op[po]; xv2, ly2 = jx + 150 + k * 18, 200 + k * 16
        jalur([(jx, y1), (xv2, y1), (xv2, ly2), (xo, ly2), (xo, yo)], col)
    x1, y1 = pos[("GND", 1)]; xo, yo = op["GND"]; xv2 = jx + 150 + 3 * 18; ly2 = 200 + 3 * 16
    jalur([(x1, y1), (xv2, y1), (xv2, ly2), (xo, ly2), (xo, yo)], "#2b2b2b")
    for k, (pin, ps, col) in enumerate(((("GND", 0), "GND", "#2b2b2b"), (("D26", 0), "LED", "#2e8b57"))):
        x1, y1 = pos[pin]; xs_, ys_ = sp[ps]; xl, ly = ex0 - 40 - k * 18, ey0 + eh + 50 + k * 18
        jalur([(x1, y1), (xl, y1), (xl, ly), (xs_, ly), (xs_, ys_)], col)
    for d, col in paths: el.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round"/>')
    for d, col in paths: el.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="4" stroke-linejoin="round"/>')
    for pe in ("3V3", "D21", "D22"):
        el.append(f'<circle cx="{jx}" cy="{pos[(pe, 1)][1]}" r="8" fill="#111" stroke="#fff" stroke-width="2.5"/>')
    lx, ly = 975, 300
    el.append(TX(lx, ly, "titik hitam = cabang Y", anc="start", sz=14, w=700))
    el.append(f'<circle cx="{lx - 14}" cy="{ly - 5}" r="7" fill="#111"/>')
    el.append(TX(lx, ly + 20, "1 soket di ESP32,", anc="start", sz=13, w=400)); el.append(TX(lx, ly + 38, "2 soket di ujung", anc="start", sz=13, w=400))
    for i, (col, t) in enumerate((("#e0245e", "3V3"), ("#2b2b2b", "GND (2 pin)"), ("#e67e22", "SDA, GPIO 21"), ("#8e44ad", "SCL, GPIO 22"), ("#2e8b57", "LED, GPIO 26"))):
        el.append(f'<line x1="{lx}" y1="{ly + 70 + i*24}" x2="{lx+28}" y2="{ly + 70 + i*24}" stroke="{col}" stroke-width="4"/>'); el.append(TX(lx + 36, ly + 75 + i * 24, t, anc="start", sz=13))
    el.append(TX(lx, ly + 200, "INT dan 3V3 sensor kosong", anc="start", sz=13, w=400, col="#6c6469"))
    return svg(W_, H_, "".join(el), "Skema kabel")


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
        p = G.pin_esp(n, b); el.append(f'<rect x="{X(p[0]-1.25)}" y="{Y(p[1]+1.25)}" width="{2.5*S}" height="{2.5*S}" fill="#202020"/>')
    urut = sorted(G.KABEL.items(), key=lambda kv: -kv[1]["titik"][:, 2].mean())
    for k, kb in urut:
        if k.startswith("kabel_y_"): continue
        P = kb["titik"]; d = "M" + " L".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in P)
        el.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>')
        el.append(f'<path d="{d}" fill="none" stroke="{kb["warna"]}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
    for pn in G.CABANG:
        p = G.pin_esp(pn, 1); el.append(f'<circle cx="{X(p[0])}" cy="{Y(p[1])}" r="7" fill="#111" stroke="#fff" stroke-width="2"/>')
    el.append(TX(X(E["x0"] + E["W"] / 2), Y(E["y0"] + 4), "ESP32 (dibalik)", sz=13, col="#145233"))
    el.append(TX(X(O["cx"] + 4), Y(O["cy"] + O["H"] / 2) - 8, "OLED di tutup atas", sz=13, col="#1d4f9c"))
    el.append(TX(X((J[0] + J[1]) / 2), Y(J[2]) + 20, "jendela kabel", sz=13))
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
    el.append(TX(X(G.W) - 6, Y(4), "S = ke sensor (lewat jendela), O = ke OLED", anc="end", sz=12, w=600, col="#555"))
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
            if t_[-1]: el.append(TX(X((t_[1] + t_[2]) / 2) if t_[0] == "r" else X(t_[1]), (Y(t_[4]) + 15) if t_[0] == "r" else Y(t_[2] + t_[3]) + 15, t_[-1], sz=11, w=600, col="#6c6469"))
        for l_ in s.lubang:
            if l_[0] == "r":
                el.append(f'<rect x="{X(l_[1]):.1f}" y="{Y(l_[4]):.1f}" width="{(l_[2]-l_[1])*S:.1f}" height="{(l_[4]-l_[3])*S:.1f}" fill="#fff" stroke="{MERAH}" stroke-width="1.6"/>')
                if l_[-1]: el.append(TX(X((l_[1] + l_[2]) / 2), Y((l_[3] + l_[4]) / 2) + 5, l_[-1], sz=11, w=700, col=MERAH))
            else:
                el.append(f'<circle cx="{X(l_[1]):.1f}" cy="{Y(l_[2]):.1f}" r="{max(l_[3]*S, 2.5):.1f}" fill="#fff" stroke="{MERAH}" stroke-width="1.6"/>')
        # ukuran keseluruhan
        yb = Y(0) + 26
        el += dimH(X(0), X(s.w), yb, f1(s.w)); el += dimV(X(0) - 26, Y(0), Y(s.h), f1(s.h))
        # ukuran berantai dari tepi kiri dan tepi bawah
        hs = sorted({round(v, 2) for a_, b_ in s.ukH for v in (a_, b_) if 0 < v < s.w})
        if hs:
            pts = [0] + hs
            for i in range(len(pts) - 1):
                el += dimH(X(pts[i]), X(pts[i + 1]), yb + 30, f1(pts[i + 1] - pts[i]), kecil=True)
        vs = sorted({round(v, 2) for a_, b_ in s.ukV for v in (a_, b_) if 0 < v < s.h})
        if vs:
            pts = [0] + vs
            for i in range(len(pts) - 1):
                el += dimV(X(s.w) + 26, Y(pts[i]), Y(pts[i + 1]), f1(pts[i + 1] - pts[i]), kanan=True, kecil=True)
        for sisi, t_ in s.tepi.items():
            if sisi == "bawah": el.append(TX(X(0), Y(0) + 13, t_, anc="start", sz=11, w=600, col="#6c6469"))
            if sisi == "atas": el.append(TX(X(s.w / 2), Y(s.h) + 15, t_, sz=11, w=600, col="#6c6469"))
            if sisi == "kiri": el.append(f'<text x="{X(0)+14:.1f}" y="{Y(s.h/2):.1f}" font-size="11" font-weight="600" fill="#6c6469" text-anchor="middle" transform="rotate(-90 {X(0)+14:.1f} {Y(s.h/2):.1f})">{t_}</text>')
            if sisi == "kanan": el.append(f'<text x="{X(s.w)-10:.1f}" y="{Y(s.h/2):.1f}" font-size="11" font-weight="600" fill="#6c6469" text-anchor="middle" transform="rotate(90 {X(s.w)-10:.1f} {Y(s.h/2):.1f})">{t_}</text>')
        el.append(TX(X(0), Y(s.h) - 34, f"{s.judul}" + (f"  ×{s.jumlah}" if s.jumlah > 1 else ""), anc="start", sz=15, w=700))
        if s.catatan: el.append(TX(X(0), Y(s.h) - 14, s.catatan, anc="start", sz=12, w=400, col="#555"))
        return el

    def ukuran_px(s, S):
        return s.w * S + 26 + 90, s.h * S + 60 + 26 + 60


def dimH(a, b, y, t, kecil=False):
    if abs(b - a) < 1: return []
    out = [f'<line x1="{a:.1f}" y1="{y:.1f}" x2="{b:.1f}" y2="{y:.1f}" stroke="{BIRU}" stroke-width="1.2" marker-start="url(#pa)" marker-end="url(#pa)"/>',
           f'<line x1="{a:.1f}" y1="{y-6:.1f}" x2="{a:.1f}" y2="{y+6:.1f}" stroke="{BIRU}" stroke-width=".8"/><line x1="{b:.1f}" y1="{y-6:.1f}" x2="{b:.1f}" y2="{y+6:.1f}" stroke="{BIRU}" stroke-width=".8"/>']
    out.append(TX((a + b) / 2, y - 5, t, sz=11 if kecil else 13, w=700, col=BIRU)); return out


def dimV(x, a, b, t, kanan=False, kecil=False):
    if abs(b - a) < 1: return []
    out = [f'<line x1="{x:.1f}" y1="{a:.1f}" x2="{x:.1f}" y2="{b:.1f}" stroke="{BIRU}" stroke-width="1.2" marker-start="url(#pa)" marker-end="url(#pa)"/>',
           f'<line x1="{x-6:.1f}" y1="{a:.1f}" x2="{x+6:.1f}" y2="{a:.1f}" stroke="{BIRU}" stroke-width=".8"/><line x1="{x-6:.1f}" y1="{b:.1f}" x2="{x+6:.1f}" y2="{b:.1f}" stroke="{BIRU}" stroke-width=".8"/>']
    out.append(TX(x + (8 if kanan else -8), (a + b) / 2 + 4, t, anc="start" if kanan else "end", sz=11 if kecil else 13, w=700, col=BIRU)); return out


def susun(lembar, judul, kolom=3, S=4.2, lebar=1180):
    el, x, y, tinggi_baris = [], 30, 70, 0
    for L_ in lembar:
        w, h = L_.ukuran_px(S)
        if x + w > lebar: x, y = 30, y + tinggi_baris + 10; tinggi_baris = 0
        el += L_.gambar(x + 30, y + 60, S); x += w + 40; tinggi_baris = max(tinggi_baris, h)
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
    lantai.catatan = "u dari depan, v dari kiri; garis putus = tanda di sisi BAWAH (tutup cat, 2 pipi)"
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

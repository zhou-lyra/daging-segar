#!/usr/bin/env python3
"""Gambar kerja BeefFresh Jepit dari geometri.py: potongan, detail ruang ukur, denah, tampak terbuka, pola 1:1.
Jalankan: ../../.venv-cad/bin/python gambar.py  -> gambar/*.svg"""
import math, os, warnings
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix
warnings.filterwarnings("ignore")
import geometri as G

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "gambar"); os.makedirs(OUT, exist_ok=True)
BIRU, MERAH, JINGGA, HIJAU, ABU = "#1f5fa8", "#b3262e", "#d97706", "#2e8b57", "#8a8f99"
f1 = lambda v: (f"{v:.1f}".rstrip("0").rstrip(".")).replace(".", ",")


class Kanvas:
    def __init__(s, xmin, xmax, zmin, zmax, S, m=(70, 70, 70, 70)):
        s.xmin, s.zmax, s.S, s.m = xmin, zmax, S, m
        s.w = (xmax - xmin) * S + m[0] + m[2]; s.h = (zmax - zmin) * S + m[1] + m[3]; s.el = []
        s.clip = (m[0], m[1], (xmax - xmin) * S, (zmax - zmin) * S)
    X = lambda s, x: (x - s.xmin) * s.S + s.m[0]
    Y = lambda s, z: (s.zmax - z) * s.S + s.m[1]

    def poly(s, loops, fill, stroke="#333", sw=1.0, op=1.0, dash=None):
        d = " ".join("M" + " L".join(f"{s.X(p[0]):.1f},{s.Y(p[1]):.1f}" for p in lp) + " Z" for lp in loops if len(lp) > 2)
        if d: s.el.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")

    def line(s, a, b, col=ABU, sw=1.2, dash=None, mk=False):
        s.el.append(f'<line x1="{s.X(a[0]):.1f}" y1="{s.Y(a[1]):.1f}" x2="{s.X(b[0]):.1f}" y2="{s.Y(b[1]):.1f}" stroke="{col}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + (' marker-end="url(#pn)"' if mk else "") + "/>")

    def text(s, x, y, t, anc="middle", col="#2a2226", sz=15, w=700, raw=False):
        px, py = (x, y) if raw else (s.X(x), s.Y(y))
        s.el.append(f'<text x="{px:.1f}" y="{py:.1f}" font-size="{sz}" font-weight="{w}" fill="{col}" text-anchor="{anc}" paint-order="stroke" stroke="#fff" stroke-width="4" stroke-linejoin="round">{t}</text>')

    def dimH(s, x1, x2, zref, ypix, t, col=BIRU):
        a, b = s.X(x1), s.X(x2)
        for xx in (a, b): s.el.append(f'<line x1="{xx:.1f}" y1="{s.Y(zref):.1f}" x2="{xx:.1f}" y2="{ypix + (6 if ypix > s.Y(zref) else -6):.1f}" stroke="#9aa3ad" stroke-width=".8" stroke-dasharray="3 2"/>')
        s.el.append(f'<line x1="{a:.1f}" y1="{ypix:.1f}" x2="{b:.1f}" y2="{ypix:.1f}" stroke="{col}" stroke-width="1.4" marker-start="url(#pa)" marker-end="url(#pa)"/>')
        s.text((a + b) / 2, ypix - 6, t, col=col, raw=True)

    def dimV(s, xref, z1, z2, xpix, t, col=BIRU, side="r"):
        a, b = s.Y(z1), s.Y(z2)
        for yy in (a, b): s.el.append(f'<line x1="{s.X(xref):.1f}" y1="{yy:.1f}" x2="{xpix + (6 if xpix > s.X(xref) else -6):.1f}" y2="{yy:.1f}" stroke="#9aa3ad" stroke-width=".8" stroke-dasharray="3 2"/>')
        s.el.append(f'<line x1="{xpix:.1f}" y1="{a:.1f}" x2="{xpix:.1f}" y2="{b:.1f}" stroke="{col}" stroke-width="1.4" marker-start="url(#pa)" marker-end="url(#pa)"/>')
        s.text(xpix + (8 if side == "r" else -8), (a + b) / 2 + 5, t, anc="start" if side == "r" else "end", col=col, raw=True)

    def tanda(s, n, x, z, col="#2a2226"):
        s.el.append(f'<circle cx="{s.X(x):.1f}" cy="{s.Y(z):.1f}" r="12" fill="#fff" stroke="{col}" stroke-width="1.6"/>')
        s.text(s.X(x), s.Y(z) + 5, str(n), sz=14, raw=True, col=col)

    def svg(s, judul=""):
        defs = ('<defs><marker id="pa" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="' + BIRU + '"/></marker>'
                '<marker id="pn" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="context-stroke"/></marker>'
                '<pattern id="htc" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="#d9d4cb"/><line x1="0" y1="0" x2="0" y2="6" stroke="#a49d92" stroke-width="1.2"/></pattern>'
                '<pattern id="hta" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="6" height="6" fill="#ebe6dd"/><line x1="0" y1="0" x2="0" y2="6" stroke="#b5ad a2" stroke-width="1"/></pattern></defs>').replace("#b5ad a2", "#b5ada2")
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w:.0f} {s.h:.0f}" font-family="system-ui,Segoe UI,Roboto,sans-serif" role="img" aria-label="{judul}">{defs}' + "".join(s.el) + "</svg>"


ISI = {"pvc": None, "pvc_hitam": "#2b2c30", "busa": "#4a4f57", "daging": "#b5483f", "plastik_hitam": "#1e1f22", "beludru": "#050505", "pcb_ungu": "#6a2c91",
       "chip": "#c9b37a", "led": "#fff1b8", "smd": "#3a3a3a", "emas": "#d4af37", "baja_hitam": "#111", "logam": "#9aa0a6", "pcb_hijau": "#1f6f43",
       "pcb_biru": "#1d4f9c", "kaca": "#0a0f1e", "kertas_putih": "#fbfbf7"}


def irisan(k, y0, M=None):
    m = (M or {}).get(k, G.B[k]["mesh"])
    y0 = y0 + 0.013                      # hindari bidang yang tepat melewati titik sudut
    sec = m.section(plane_origin=[0, y0, 0], plane_normal=[0, 1, 0])
    if sec is None: return []
    T = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, -y0], [0, 0, 0, 1]], float)
    try: pl, _ = sec.to_2D(to_2D=T)
    except Exception: pl, _ = sec.to_planar(to_2D=T)
    out = []
    for poly in pl.polygons_full:          # tiap poligon digambar sendiri: kulit luar + lubangnya
        out.append([np.array(poly.exterior.coords)] + [np.array(r.coords) for r in poly.interiors])
    return out


def gambar_irisan(K, y0, kecuali=(), M=None):
    cx, cy, cw, ch = K.clip
    K.el.append(f'<clipPath id="area"><rect x="{cx}" y="{cy}" width="{cw}" height="{ch}"/></clipPath><g clip-path="url(#area)">')
    for k, b in G.B.items():
        if b["grup"] == "aksesori" or k.startswith("kabel") or k in kecuali: continue
        lp = irisan(k, y0, M)
        if not lp: continue
        isi = ISI.get(b["bahan"]) or ("url(#htc)" if b["grup"] == "bawah" else "url(#hta)")
        for loops in lp: K.poly(loops, isi, "#3a3a3a" if b["bahan"] not in ("beludru",) else "#000", 0.9)
    K.el.append("</g>")


# ============================================================================ 1. potongan samping (tertutup)
def potongan():
    K = Kanvas(-10, 104, -42, 72, 8.0, (150, 80, 250, 120))
    gambar_irisan(K, G.YC)
    # pipi (di belakang bidang potong): garis putus
    K.poly([G.PIPI_POLI], "none", "#555", 1.3, dash="6 4")
    zk0, za = G.Hc + G.t, G.Z_ATAS
    # garis ukur
    xr = G.W + 7
    K.dimV(G.W, -G.F - G.t, G.Hc, K.X(xr) + 30, "baki " + f1(G.F + G.t + G.Hc))
    K.dimV(G.W, G.Hc, za + G.t, K.X(xr) + 30, "kepala " + f1(za + G.t - G.Hc))
    K.dimV(G.W, -G.F - G.t, za + G.t, K.X(xr) + 150, "tinggi " + f1(za + G.t + G.F + G.t))
    K.dimV(0, -G.F, 0, K.X(-2) - 26, f1(G.F), side="l")
    K.dimV(0, 0, G.Hc, K.X(-2) - 26, "tutup cat " + f1(G.Hc), side="l")
    K.dimV(0, zk0, za, K.X(-2) - 26, "dalam " + f1(G.P["kepala_dalam"]), side="l")
    K.dimV(0, -G.P["daging_tebal"], 0, K.X(-2) - 96, "daging " + f1(G.P["daging_tebal"]), side="l")
    K.dimH(0, G.W, za + G.t, K.Y(za + G.t) - 34, "86")
    K.dimH(G.XC - G.rl, G.XC + G.rl, -G.F - G.t, K.Y(-G.F - G.t) + 38, "lubang Ø 14")
    K.dimH(G.XC - G.R, G.XC + G.R, -G.F - G.t, K.Y(-G.F - G.t) + 76, "tutup cat Ø 65")
    K.dimH(0, G.XC, -G.F - G.t, K.Y(-G.F - G.t) + 112, "pusat lubang 43")
    nomor = [(1, 25, -5, "daging"), (2, 20, -26, "busa"), (3, G.XC - 26, 9, "tutup cat"), (4, 45.5, 13.5, "sensor"),
             (5, 68, 15, "pipi"), (6, 51, 30, "jendela"), (7, 20, 38, "ESP32"), (8, 60, za - 10, "OLED"), (9, G.W + 9, G.Hc + 16, "engsel"), (10, -9, G.Hc - 18, "kait"), (11, 76, -36.5, "lantai baki")]
    for n, x, z, _ in nomor: K.tanda(n, x, z)
    ax_, az_ = G.SUMBU_ENGSEL
    K.poly([[(G.W, az_ - 14), (G.W + 1, az_ - 14), (G.W + 1, az_ + 14), (G.W, az_ + 14)]], "none", "#555", 1.2, dash="5 3")
    K.el.append(f'<circle cx="{K.X(ax_):.1f}" cy="{K.Y(az_):.1f}" r="{2*K.S:.1f}" fill="none" stroke="#555" stroke-width="1.2" stroke-dasharray="5 3"/>')
    K.line((G.SUMBU_ENGSEL[0] - 3, G.SUMBU_ENGSEL[1]), (G.SUMBU_ENGSEL[0] + 3, G.SUMBU_ENGSEL[1]), MERAH, 1.4)
    K.line((G.SUMBU_ENGSEL[0], G.SUMBU_ENGSEL[1] - 3), (G.SUMBU_ENGSEL[0], G.SUMBU_ENGSEL[1] + 3), MERAH, 1.4)
    open(os.path.join(OUT, "1_potongan.svg"), "w").write(K.svg("Potongan samping alat tertutup"))
    return nomor


# ============================================================================ 2. detail ruang ukur dan jalan cahaya
def detail():
    K = Kanvas(G.XC - 34, G.XC + 36, -6, 26, 15.0, (115, 60, 440, 110))
    gambar_irisan(K, G.YC, kecuali=("esp_busa", "esp_modul", "esp_pcb", "esp_usb", "esp_header", "esp_pin", "esp_dupont"))
    K.poly([G.PIPI_POLI], "none", "#555", 1.3, dash="6 4")
    C, Lw = G.CHIP, G.LED_W; Pk = G.kilap()[1]
    xe = [G.XC - G.rl, G.XC + G.rl]
    for x in xe: K.line((Lw[0], Lw[2]), (x, 0), JINGGA, 1.6, "7 4")
    K.line((C[0], C[2]), (G.XC, 0), HIJAU, 2.0, mk=True)
    K.line((Lw[0], Lw[2]), (Pk[0], G.P["tutup_muka"]), MERAH, 1.6, "2 3")
    K.line((Pk[0], G.P["tutup_muka"]), (C[0], C[2]), MERAH, 1.6, "2 3")
    K.el.append(f'<circle cx="{K.X(Pk[0]):.1f}" cy="{K.Y(G.P["tutup_muka"]):.1f}" r="5" fill="{MERAH}"/>')
    # busur sudut 40
    r_ = 7.0; a0 = math.pi / 2
    pts = [(C[0] + r_ * math.cos(-a0 - t_ * math.radians(G.P["miring"])), C[2] + r_ * math.sin(-a0 - t_ * math.radians(G.P["miring"]))) for t_ in np.linspace(0, 1, 20)]
    K.el.append('<path d="M' + " L".join(f"{K.X(p[0]):.1f},{K.Y(p[1]):.1f}" for p in pts) + f'" fill="none" stroke="{BIRU}" stroke-width="1.4"/>')
    K.line((C[0], C[2]), (C[0], C[2] - 8), BIRU, 1.0, "3 3")
    K.text(C[0] - 2.2, C[2] - 9.3, "40°", col=BIRU, anc="end")
    K.text(Pk[0] + 1.2, 3.0, f"titik kilap: {f1(G.kilap()[0])} mm di luar lubang", col=MERAH, anc="start", sz=14)
    K.dimV(C[0], 0, C[2], K.X(G.XC + 36) + 14, "chip " + f1(C[2]))
    K.dimV(G.XC, 0, G.P["tutup_muka"], K.X(G.XC - 33) - 10, "muka 1,5", side="l")
    K.dimH(G.XC, C[0], 0, K.Y(-6) + 34, "geser " + f1(C[0] - G.XC))
    K.dimH(G.XC - G.rl, G.XC + G.rl, 0, K.Y(-6) + 76, "lubang 14")
    x0 = K.X(G.XC + 36) + 120; y = K.Y(25)
    for col, da, t1, t2 in [(HIJAU, "", "sumbu pandang chip", f"ke pusat lubang, {f1(G.P['h'])} mm"), (JINGGA, "7 4", "sinar LED bawaan", "ke tepi lubang"),
                            (MERAH, "2 3", "jalan kilap (pantulan cermin)", "jatuh di luar lubang, di muka hitam"), ("#555", "6 4", "pipi penyangga", "di belakang bidang potong")]:
        K.el.append(f'<line x1="{x0}" y1="{y-5}" x2="{x0+34}" y2="{y-5}" stroke="{col}" stroke-width="2.2"' + (f' stroke-dasharray="{da}"' if da else "") + "/>")
        K.text(x0 + 44, y, t1, anc="start", sz=14, raw=True); K.text(x0 + 44, y + 19, t2, anc="start", sz=14, w=400, raw=True, col="#555"); y += 54
    open(os.path.join(OUT, "2_ruang_ukur.svg"), "w").write(K.svg("Detail ruang ukur dan jalan cahaya"))


# ============================================================================ 3. denah lantai kepala (dari atas)
def denah():
    S = 9.0; m = (90, 70, 230, 110)
    K = Kanvas(-6, G.W + 4, -4, G.W + 4, S, m)                 # dipakai sebagai (x, y): Y(z) -> y dibalik
    def rect(x0, x1, y0, y1, fill, st, sw=1.2, dash=None, op=1.0):
        K.poly([[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], fill, st, sw, op, dash)
    def circ(cx, cy, r, st, sw=1.4, dash=None, fill="none"):
        K.el.append(f'<circle cx="{K.X(cx):.1f}" cy="{K.Y(cy):.1f}" r="{r*S:.1f}" fill="{fill}" stroke="{st}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
    rect(0, G.W, 0, G.W, "#ebe6dd", "#6c6469", 1.8)
    rect(G.t, G.W - G.t, G.t, G.W - G.t, "none", "#b5ada2", 1.0, "5 4")
    circ(G.XC, G.YC, G.R, "#1e1f22", 1.6, "8 5"); circ(G.XC, G.YC, G.Ri, "#1e1f22", 1.0, "3 4")
    circ(G.XC, G.YC, G.rl, MERAH, 1.8, "5 3")
    K.line((G.XC - 2.5, G.YC), (G.XC + 2.5, G.YC), MERAH, 1.4); K.line((G.XC, G.YC - 2.5), (G.XC, G.YC + 2.5), MERAH, 1.4)
    # papan sensor (proyeksi), pipi, jendela
    xy = G.B["sensor_pcb"]["mesh"].vertices[:, :2]
    from scipy.spatial import ConvexHull
    hh = ConvexHull(xy); K.poly([xy[hh.vertices]], "#6a2c91", "#4c2468", 1.2, 0.25, "5 3")
    for y0, y1 in [sorted([G.papan(b0, 0, 0)[1], G.papan(b1, 0, 0)[1]]) for b0, b1 in G.PIPI_BX]:
        rect(G.PIPI_POLI[0][0], G.PIPI_POLI[1][0], y0, y1, "#26272b", "#000", 1.0, "4 2", 0.55)
    J = G.JENDELA; rect(J[0], J[1], J[2], J[3], "#fff", "#2a2226", 2.0)
    # ESP32 dan USB, OLED
    E = G.ESP; rect(E["x0"], E["x0"] + E["W"], E["y0"], E["y0"] + E["L"], "#1f6f43", "#145233", 1.4, None, 0.30)
    ex = E["x0"] + E["W"] / 2; rect(ex - 6.5, ex + 6.5, 0, G.t, "#fff", "#2a2226", 1.6)
    O = G.OLED; rect(O["cx"] - O["L"] / 2, O["cx"] + O["L"] / 2, O["cy"] - O["H"] / 2, O["cy"] + O["H"] / 2, "none", "#1d4f9c", 1.4, "2 3")
    # label
    K.text(E["x0"] + E["W"] / 2, E["y0"] + E["L"] / 2 + 2, "ESP32", col="#145233")
    K.text(E["x0"] + E["W"] / 2, E["y0"] + E["L"] / 2 - 2.6, "dibalik, di atas busa", col="#145233", sz=13, w=600)
    K.text(ex, -3.2, "takik USB 13 x 10", sz=13)
    K.line(((J[0] + J[1]) / 2, J[3] - 3), (24, G.W - 5.5), "#2a2226", 1.0); K.text(6, G.W - 4.5, "jendela kabel (tembus)", anc="start", sz=13)
    K.text(G.XC, G.YC - G.rl - 2.6, "lubang ukur Ø 14", col=MERAH, sz=13)
    K.text(G.XC, G.YC + G.R + 1.2, "tutup cat Ø 65 (di bawah lantai)", sz=13)
    K.line((G.PIPI_POLI[1][0] - 2, 30.5), (72, 20), "#2a2226", 1.0); K.text(72.5, 18.5, "pipi (2), di bawah lantai", anc="start", sz=13)
    K.line((O["cx"] + 8, O["cy"] + O["H"] / 2), (76, G.W - 10), "#1d4f9c", 1.0); K.text(76, G.W - 9, "OLED (di tutup atas)", col="#1d4f9c", anc="start", sz=13)
    K.line((G.CHIP[0] + 9, G.YC - 6), (70, 12), "#4c2468", 1.0); K.text(70.5, 10.5, "papan sensor (miring 40°)", col="#4c2468", anc="start", sz=13)
    # ukuran
    K.dimH(0, G.W, 0, K.Y(0) + 40, "86")
    K.dimH(0, G.XC, 0, K.Y(0) + 76, "pusat lubang 43")
    K.dimH(J[0], J[1], G.W, K.Y(G.W) - 18, f"{f1(J[0])} sampai {f1(J[1])}")
    K.dimV(G.W, 0, G.W, K.X(G.W) + 30, "86")
    K.dimV(G.W, J[2], J[3], K.X(G.W) + 100, f"{f1(J[2])} sampai {f1(J[3])}")
    K.dimV(0, 0, G.YC, K.X(0) - 30, "43", side="l")
    K.text(K.X(-6), K.Y(G.W + 4) + 2, "depan (kait)", anc="start", sz=13, w=600, raw=True, col="#6c6469")
    K.text(K.X(G.W + 4), K.Y(G.W + 4) + 2, "belakang (engsel)", anc="end", sz=13, w=600, raw=True, col="#6c6469")
    open(os.path.join(OUT, "3_denah_lantai_kepala.svg"), "w").write(K.svg("Denah lantai kepala dari atas"))


# ============================================================================ 4. tampak terbuka (potongan, kepala diangkat 100 derajat)
def terbuka(sudut=100):
    Rm = rotation_matrix(math.radians(sudut), [0, 1, 0], point=[G.SUMBU_ENGSEL[0], 0, G.SUMBU_ENGSEL[1]])
    M = {}
    for k, b in G.B.items():
        m = b["mesh"].copy()
        if b["grup"] == "atas": m.apply_transform(Rm)
        M[k] = m
    K = Kanvas(-8, 170, -42, 96, 5.6, (60, 50, 60, 60))
    gambar_irisan(K, G.YC, M=M)
    K.text(43, -48, "daging di atas busa (dilapisi plastik wrap)", sz=14)
    K.text(140, 92, "kepala dibuka ke belakang", sz=14)
    open(os.path.join(OUT, "4_terbuka.svg"), "w").write(K.svg("Penjepit terbuka"))


# ============================================================================ 5. pola 1:1 (cetak 100 %)
def pola():
    el = []; mm = lambda v: f"{v:.2f}"
    def poly(pts, ox, oy, st="#000", sw=0.3, fill="none"):
        el.append(f'<path d="M' + " L".join(f"{mm(ox + p[0])},{mm(oy + p[1])}" for p in pts) + f' Z" fill="{fill}" stroke="{st}" stroke-width="{sw}"/>')
    def txt(x, y, t, sz=3.2, anc="start", w=600, col="#000"):
        el.append(f'<text x="{mm(x)}" y="{mm(y)}" font-size="{sz}" font-weight="{w}" text-anchor="{anc}" fill="{col}">{t}</text>')
    def silang(x, y, r=1.2):
        el.append(f'<path d="M{mm(x-r)},{mm(y)} H{mm(x+r)} M{mm(x)},{mm(y-r)} V{mm(y+r)}" stroke="#000" stroke-width="0.2"/>')
    # pipi: (x, z) -> gambar dengan z ke bawah dibalik; bidang atas (z = Hc) di atas
    pp = [(p[0] - G.PIPI_POLI[0][0], G.Hc - p[1]) for p in G.PIPI_POLI]
    for i, ox in enumerate((12, 42)):
        poly(pp, ox, 22); txt(ox, 18, f"Pipi {i+1}", 3.4)
    a_ = pp
    txt(12, 44, f"Sisi atas {f1(a_[2][0]-a_[3][0])} mm ditempel ke lantai kepala.", 2.8, w=400)
    txt(12, 48, f"Tinggi ujung pendek {f1(a_[0][1])}, ujung panjang {f1(a_[1][1])} mm. Sisi miring 40° ke datar.", 2.8, w=400)
    # pelat dudukan
    pw, ph = G.PELAT["bx1"] - G.PELAT["bx0"], G.PELAT["by1"] - G.PELAT["by0"]
    ox, oy = 80, 18
    poly([(0, 0), (pw, 0), (pw, ph), (0, ph)], ox, oy); txt(ox, oy - 4, f"Pelat dudukan {f1(pw)} x {f1(ph)} mm", 3.4)
    for hx, hy in G.TCS["lubang"]:
        cx, cy = ox + hx - G.PELAT["bx0"], oy + ph - (hy - G.PELAT["by0"])
        el.append(f'<circle cx="{mm(cx)}" cy="{mm(cy)}" r="1.4" fill="none" stroke="#000" stroke-width="0.25"/>'); silang(cx, cy)
    txt(ox, oy + ph + 5, "2 lubang Ø 2,8 untuk baut M2,5. Jarak 15,24 mm.", 2.8, w=400)
    txt(ox, oy + ph + 9, "Sisi lubang = tepi bawah (ujung panjang pipi).", 2.8, w=400)
    # muka tutup cat: lingkaran 65, lubang 14
    cx, cy = 45, 100
    el.append(f'<circle cx="{cx}" cy="{cy}" r="{G.R}" fill="none" stroke="#000" stroke-width="0.3"/>')
    el.append(f'<circle cx="{cx}" cy="{cy}" r="{G.rl}" fill="none" stroke="#000" stroke-width="0.35"/>'); silang(cx, cy, 3)
    txt(cx, cy - G.R - 3, "Muka tutup cat Ø 65: lubang ukur Ø 14 di pusat", 3.2, "middle")
    # jendela kabel dan jarak dari tepi
    J = G.JENDELA; jx, jy = 110, 82
    poly([(0, 0), (J[1] - J[0], 0), (J[1] - J[0], J[3] - J[2]), (0, J[3] - J[2])], jx, jy)
    txt(jx, jy - 4, f"Jendela kabel {f1(J[1]-J[0])} x {f1(J[3]-J[2])} mm", 3.2)
    txt(jx, jy + J[3] - J[2] + 5, f"Tepi depan {f1(J[0])} mm dari sisi depan lantai,", 2.8, w=400)
    txt(jx, jy + J[3] - J[2] + 9, f"tepi kiri {f1(J[2])} mm dari sisi kiri.", 2.8, w=400)
    # skala uji
    el.append('<path d="M12,170 H62" stroke="#000" stroke-width="0.4"/>' + "".join(f'<path d="M{12+i*10},168 V172" stroke="#000" stroke-width="0.3"/>' for i in range(6)))
    txt(12, 177, "Garis uji 50 mm: ukur dengan penggaris setelah dicetak. Harus tepat 50 mm.", 3.0, w=600)
    txt(12, 8, "BeefFresh Jepit: pola 1:1. Cetak di A4, skala 100 % (matikan 'fit to page').", 3.6, w=700)
    W_, H_ = 190, 182
    open(os.path.join(OUT, "5_pola_1banding1.svg"), "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}mm" height="{H_}mm" viewBox="0 0 {W_} {H_}" font-family="system-ui,Segoe UI,Roboto,sans-serif">' + "".join(el) + "</svg>")


if __name__ == "__main__":
    potongan(); detail(); denah(); terbuka(); pola()
    print("ditulis:", ", ".join(sorted(os.listdir(OUT))))

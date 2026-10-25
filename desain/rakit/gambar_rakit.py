#!/usr/bin/env python3
"""Gambar kerja tur rakit BeefFresh. Semua ukuran diambil dari geometri_a.py (Model 1 Genggam) dan geometri.py (Model 2 Jepit).
Keluaran: desain/rakit/gambar/*.svg (gambar layar) dan pola_*.svg (1:1 dalam mm, untuk dicetak A4 skala 100 %).
Jalankan: ../../.venv-cad/bin/python gambar_rakit.py
"""
import math, os, sys, warnings
import numpy as np
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jepit")); sys.path.insert(0, os.path.join(HERE, "..", "genggam"))
import geometri as GE
import geometri_a as GA
from gambar_kabel_lembar import Lembar, TX, dimH, dimV, svg, susun, BIRU, MERAH, f1
import gambar_kabel_lembar as GKL

OUT = os.path.join(HERE, "gambar"); os.makedirs(OUT, exist_ok=True)
TINTA, ABU = "#2a2226", "#6c6469"


class LembarX(Lembar):
    """Lembar + tanda elips dan tanda bebas (poligon)."""
    def __init__(s, *a, **k):
        super().__init__(*a, **k); s.ekstra = []
    def elips(s, cu, cv, a, b, label=""):
        s.ekstra.append(("e", cu, cv, a, b, label)); return s
    def gambar(s, ox, oy, S):
        el = super().gambar(ox, oy, S); X = lambda u: ox + u * S; Y = lambda v: oy + (s.h - v) * S
        for e in s.ekstra:
            _, cu, cv, a, b, lab = e
            el.insert(1, f'<ellipse cx="{X(cu):.1f}" cy="{Y(cv):.1f}" rx="{a*S:.1f}" ry="{b*S:.1f}" fill="none" stroke="{ABU}" stroke-width="1.2" stroke-dasharray="6 4"/>')
            if lab: el.append(TX(X(cu), Y(cv - b) - 6, lab, sz=11, w=600, col=ABU))
        return el


def lingkaran(cx, cy, r, n=72): return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ============================================================================ MODEL 1 (GENGGAM)
X0, X1, XP, YW, t = GA.X0, GA.X1, GA.X_PAD, GA.YW, GA.t
L_TOT, W_TOT = X1 - X0, 2 * YW
H_DIND = GA.Z_TOP - t                     # dinding samping bagian depan (z 3..49)
OX, OH = GA.OX, GA.OH
TUBE_RO, TUBE_RI, SA, CA = GA.TUBE_RO, GA.TUBE_RI, GA.SA, GA.CA
S_END = GA.S_END
EL_X = t * SA / CA                        # pusat elips tepi luar pipa di atas pelat, maju dari pusat lubang
EL_A = TUBE_RO / CA                       # setengah sumbu panjang elips


def s_potong(r, th):                      # posisi sepanjang sumbu tempat permukaan pipa (jari-jari r, sudut th) memotong bidang z = t
    return (t + r * math.cos(th) * SA) / CA


PIPA_PANJANG = S_END - s_potong(TUBE_RO, math.pi)     # sisi terpanjang
PIPA_PENDEK = S_END - s_potong(TUBE_RO, 0.0)          # sisi terpendek
KELILING = 2 * math.pi * TUBE_RO


def m1_lembar_badan():
    pel = LembarX("Pelat muka (PVC hitam)", X1 - XP, W_TOT, tepi={"kiri": "belakang", "kanan": "depan"}, catatan="dari atas (sisi dalam); putus kecil = Ø 16 kikir miring")
    pel.bulat(-XP, YW, GA.AP_R, "Ø 12")
    pel.bulat(-XP, YW, 8.0, "", tanda=True, ukur=False)
    pel.elips(-XP + EL_X, YW, EL_A, TUBE_RO, "tepi luar pipa (lem di sini)")
    lantai = Lembar("Lantai belakang", XP - X0, W_TOT, tepi={"kiri": "belakang", "kanan": "ke pelat muka"}, catatan="polos")
    prof = [(0, 2), (XP - X0, 2), (XP - X0, 0), (L_TOT, 0), (L_TOT, H_DIND), (0, H_DIND)]
    samping = Lembar("Dinding samping", L_TOT, H_DIND, jumlah=2, tepi={"kiri": "belakang", "kanan": "depan"},
                     catatan="tepi bawah bertangga 2 mm: bagian depan di atas pelat muka, bagian belakang di atas lantai", bentuk=prof)
    samping.ukH.append((XP - X0, XP - X0)); samping.ukV.append((2, 2))
    depan = Lembar("Dinding depan", 2 * GA.YI, H_DIND, catatan="polos, di antara dua dinding samping")
    hb = GA.Z_TOP - 5
    bel = Lembar("Dinding belakang", 2 * GA.YI, hb, catatan="takik USB dari tepi bawah (ke lantai)")
    bel.kotak(GA.YI - 6.5, GA.YI + 6.5, 0, GA.usb_z1 + 4 - 5, "USB")
    return susun([pel, lantai, samping, depan, bel], "Model 1: lembar PVC badan", S=3.6)


def m1_lembar_tutup():
    tut = Lembar("Tutup atas (dilihat dari atas)", L_TOT, W_TOT, tepi={"kiri": "belakang", "kanan": "depan"}, catatan="jendela 15 x 25; 4 lubang Ø 2,2 berjarak 23,3 x 23,3 sepusat jendela; putus = bibir")
    tut.kotak(OX - 7.5 - X0, OX + 7.5 - X0, YW - 12.5, YW + 12.5, "jendela")
    for sx in (-1, 1):
        for sy in (-1, 1): tut.bulat(OX + sx * 11.65 - X0, YW + sy * 11.65, 1.1, ukur=sx > 0 and sy > 0)
    tut.bulat(-16 - X0, YW, 6.0, "ibu jari (cat merah)", tanda=True)
    for xa, xb in ((X0 + t, OX - OH / 2 - 1), (OX + OH / 2 + 1, X1 - t)):
        for ys in (-GA.YI + 0.3, GA.YI - 3.3): tut.kotak(xa - X0, xb - X0, ys + YW, ys + 3 + YW, "", tanda=True, ukur=False)
    bp = Lembar("Bibir panjang", (OX - OH / 2 - 1) - (X0 + t), 6, jumlah=2, catatan="lem di garis putus, sisi bawah tutup")
    bk = Lembar("Bibir pendek", (X1 - t) - (OX + OH / 2 + 1), 6, jumlah=2, catatan="di depan OLED")
    R = TUBE_RI - 0.15; cx, cy = GE.TCS["chip"]
    ck = Lembar("Cakram dudukan (PVC hitam)", 2 * R, 2 * R, catatan="dari sisi papan; celah header 18,3 x 3; 2 lubang Ø 2,8", bentuk=lingkaran(R, R, R))
    xs = [GE.TCS["header_x0"] + i * GE.TCS["pitch"] for i in range(7)]; hy = GE.TCS["header_y"]
    ck.kotak(min(xs) - 1.52 - cx + R, max(xs) + 1.52 - cx + R, hy - 1.52 - cy + R, hy + 1.52 - cy + R, "")
    for hx, hy_ in GE.TCS["lubang"]: ck.bulat(hx - cx + R, hy_ - cy + R, 1.4, "")
    ck.bulat(R, R, 0.6, "", tanda=True, ukur=True)
    return susun([tut, bp, bk], "Model 1: tutup dan bibir", S=3.6), susun([ck], "Model 1: cakram dudukan", S=10.0, lebar=560)


def m1_pipa():
    """Pandangan samping pipa yang sudah dipotong + ukuran."""
    S = 6.0; W_, H_ = 980, 470; el = []
    ox, oy = 250, 400                          # titik ujung bawah sisi panjang
    # gambar dalam bidang (sumbu s ke atas di kanan-miring?): tampilkan pipa tegak, potongan miring di bawah
    def P(s, side):                            # side +1 sisi pendek (kanan), -1 sisi panjang (kiri)
        return ox + (side + 1) * TUBE_RO * S, oy - (s - s_potong(TUBE_RO, math.pi)) * S
    sL0, sR0 = s_potong(TUBE_RO, math.pi), s_potong(TUBE_RO, 0)
    xl, yb_l = P(sL0, -1); xr, yb_r = P(sR0, 1); _, yt = P(S_END, -1)
    el.append(f'<path d="M{xl:.1f},{yt:.1f} L{xr:.1f},{yt:.1f} L{xr:.1f},{yb_r:.1f} L{xl:.1f},{yb_l:.1f} Z" fill="#e4ded4" stroke="{TINTA}" stroke-width="1.6"/>')
    di = (TUBE_RO - TUBE_RI) * S
    el.append(f'<path d="M{xl+di:.1f},{yt:.1f} L{xr-di:.1f},{yt:.1f}" stroke="{ABU}" stroke-dasharray="5 3"/>')
    el.append(f'<path d="M{xl+di:.1f},{yt:.1f} L{xl+di:.1f},{yb_l - (s_potong(TUBE_RI, math.pi) - sL0) * S:.1f} M{xr-di:.1f},{yt:.1f} L{xr-di:.1f},{yb_r - (s_potong(TUBE_RI, 0) - sR0) * S:.1f}" stroke="{ABU}" stroke-width="1" stroke-dasharray="5 3"/>')
    el += dimV(xl - 30, yb_l, yt, f1(PIPA_PANJANG) + " (sisi panjang)")
    el += dimV(xr + 30, yb_r, yt, f1(PIPA_PENDEK) + " (sisi pendek)", kanan=True)
    el += dimH(xl, xr, yt - 26, "Ø luar " + f1(2 * TUBE_RO))
    # sudut potong terhadap sumbu: 90 - 40 = 50 derajat dari sumbu, atau 40 dari bidang tegak lurus sumbu
    ang = math.degrees(math.atan2(yb_l - yb_r, xr - xl))
    el.append(f'<path d="M{xl:.1f},{yb_l:.1f} L{xr + 60:.1f},{yb_l:.1f}" stroke="{BIRU}" stroke-width="1" stroke-dasharray="4 3"/>')
    r_ = 70; a2 = math.radians(ang)
    el.append(f'<path d="M{xl + r_:.1f},{yb_l:.1f} A{r_},{r_} 0 0 0 {xl + r_ * math.cos(a2):.1f},{yb_l - r_ * math.sin(a2):.1f}" fill="none" stroke="{BIRU}" stroke-width="1.4"/>')
    el.append(TX(xl + r_ + 34, yb_l - 14, f"{ang:.0f}°", sz=15, w=700, col=BIRU))
    el.append(TX((xl + xr) / 2, yt + 22, "ujung tegak lurus", sz=12, col=ABU))
    el.append(TX((xl + xr) / 2, yt - 52, "Pipa PVC 1 inci, dilihat dari samping", sz=15, w=700))
    # keterangan kanan
    tx0 = 600
    for i, s_ in enumerate([f"1. Potong pipa lurus {f1(PIPA_PANJANG + 4)} mm dulu, ratakan ujungnya.",
                            "2. Bungkus pola potong (cetak 1:1) di ujung pipa,",
                            "    tepi lurus pola rata dengan ujung tegak lurus.",
                            "3. Gores garis lengkung pola dengan spidol halus.",
                            "4. Gergaji sedikit di luar garis, lalu amplas di",
                            "    kertas amplas yang ditaruh di meja datar sampai",
                            "    garis tepat hilang. Muka potong harus rata.",
                            f"5. Periksa: sisi panjang {f1(PIPA_PANJANG)}, sisi pendek {f1(PIPA_PENDEK)} mm,",
                            "    sudut muka potong 40° terhadap ujung tegak lurus."]):
        el.append(TX(tx0, 90 + i * 30, s_, anc="start", sz=14, w=500))
    return svg(W_, H_, "".join(el), "Pipa dipotong miring")


def m1_pipa_pola():
    """Pola bungkus 1:1 (mm) untuk menandai potongan miring pada pipa Ø 32."""
    m = 12.0; W_ = KELILING + 2 * m; tinggi = PIPA_PANJANG + 2 * m + 30
    el = [f'<rect x="{m}" y="{m}" width="{KELILING:.2f}" height="{PIPA_PANJANG + 6:.2f}" fill="none" stroke="#000" stroke-width="0.25"/>']
    pts = []
    for i in range(0, 361):
        th = math.radians(i); u = KELILING * i / 360; h = S_END - s_potong(TUBE_RO, th)
        pts.append(f"{m + u:.2f},{m + h:.2f}")
    el.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#c00" stroke-width="0.4"/>')
    for i in range(0, 361, 45):
        u = KELILING * i / 360
        el.append(f'<line x1="{m + u:.2f}" y1="{m}" x2="{m + u:.2f}" y2="{m + 4}" stroke="#000" stroke-width="0.25"/>')
    el.append(f'<text x="{m + 2}" y="{m + PIPA_PANJANG + 13:.1f}" font-size="3.2" fill="#000">Pola potong pipa 1 inci (Ø luar 32): tepi ATAS = ujung tegak lurus. Garis merah = garis potong 40°. Keliling {f1(KELILING)} mm;</text>')
    el.append(f'<text x="{m + 2}" y="{m + PIPA_PANJANG + 18:.1f}" font-size="3.2" fill="#000">bila pola tidak pas melingkar, pipamu bukan Ø 32: ukur ulang sebelum memotong. Titik terendah = sisi panjang ({f1(PIPA_PANJANG)} mm), tandai untuk arah header sensor.</text>')
    el.append(f'<line x1="{m}" y1="{m + PIPA_PANJANG + 25:.1f}" x2="{m + 50}" y2="{m + PIPA_PANJANG + 25:.1f}" stroke="#000" stroke-width="0.4"/>'
              f'<text x="{m + 54}" y="{m + PIPA_PANJANG + 26.2:.1f}" font-size="3.2" fill="#000">garis uji 50 mm</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_:.1f}mm" height="{tinggi:.1f}mm" viewBox="0 0 {W_:.1f} {tinggi:.1f}" font-family="system-ui,sans-serif">'
            + "".join(el) + "</svg>")


def m1_lubang():
    """Potongan pelat muka di lubang ukur + letak pipa."""
    S = 12.0; W_, H_ = 980, 420; el = []; ox, oy = 470, 300
    X = lambda x: ox + x * S; Y = lambda z: oy - z * S
    # pelat: x -26..32 tampak sebagian (-20..26)
    x_a, x_b = -22, 26
    # profil lubang: lurus Ø12 dari z 0..1, lalu 45 derajat ke Ø16 di z 3
    for sgn in (-1, 1):
        xs = [x_a, -sgn * 0 if False else None]
    kiri = [(x_a, 0), (-6, 0), (-6, 1), (-8, 3), (x_a, 3)]
    kanan = [(6, 0), (x_b, 0), (x_b, 3), (8, 3), (6, 1)]
    for poly in (kiri, kanan):
        el.append('<path d="M' + " L".join(f"{X(x):.1f},{Y(z):.1f}" for x, z in poly) + ' Z" fill="#3a3b40" stroke="#111" stroke-width="1.4"/>')
    # daging
    el.append(f'<rect x="{X(x_a):.1f}" y="{Y(0):.1f}" width="{(x_b - x_a) * S:.1f}" height="40" fill="#b5483f" opacity=".55"/>')
    el.append(f'<text x="{X(x_a) + 20:.1f}" y="{Y(0) + 26:.1f}" font-size="13" font-weight="700" fill="#fff">daging</text>')
    # pipa: dinding kiri (sisi panjang) dan kanan, miring 40 derajat dari vertikal
    for r in (TUBE_RO, TUBE_RI):
        for sgn in (-1, 1):
            # garis permukaan pipa di bidang y = 0: titik pada sumbu s, offset sgn*r ke arah V (cos40,0,-sin40)
            s1 = (3 + sgn * r * SA) / CA; s2 = s1 + 9.0
            xa_, za_ = s1 * SA + sgn * r * CA, 3.0
            xb_, zb_ = s2 * SA + sgn * r * CA, s2 * CA - sgn * r * SA
            if xb_ > x_b + 4: k = (x_b + 4 - xa_) / (xb_ - xa_); xb_, zb_ = xa_ + k * (xb_ - xa_), za_ + k * (zb_ - za_)
            el.append(f'<line x1="{X(xa_):.1f}" y1="{Y(za_):.1f}" x2="{X(xb_):.1f}" y2="{Y(zb_):.1f}" stroke="{TINTA}" stroke-width="{1.6 if r == TUBE_RO else 1}" {"" if r == TUBE_RO else "stroke-dasharray=\"5 3\""}/>')
    # sumbu pandang
    el.append(f'<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(9 * SA):.1f}" y2="{Y(9 * CA):.1f}" stroke="{BIRU}" stroke-width="1.2" stroke-dasharray="8 4"/>')
    el.append(TX(X(9 * SA) + 10, Y(9 * CA) + 4, "sumbu pandang sensor (40°)", anc="start", sz=12, col=BIRU))
    el += dimH(X(-6), X(6), Y(0) + 62, "Ø 12 (lurus 1 mm)")
    el += dimH(X(-8), X(8), Y(3) - 26, "Ø 16 di sisi atas")
    el += dimV(X(x_b) + 24, Y(0), Y(3), "3", kanan=True, kecil=True)
    el.append(f'<path d="M{X(-7.2):.1f},{Y(2):.1f} L{X(-12):.1f},{Y(3) + 60:.1f}" stroke="{MERAH}" fill="none"/>'); el.append(TX(X(-12), Y(3) + 78, "kikir 45° dari Ø 12 ke Ø 16", sz=13, w=700, col=MERAH))
    el.append(TX(140, 36, "Lubang ukur di pelat muka, dipotong di tengah", anc="start", sz=15, w=700))
    el.append(TX(140, 58, f"Pusat lubang {f1(-XP)} mm dari tepi belakang pelat, {f1(YW)} mm dari tepi samping. Tepi luar pipa", anc="start", sz=13, w=500, col=ABU))
    el.append(TX(140, 76, f"menempel di pelat sebagai elips {f1(2 * EL_A)} x {f1(2 * TUBE_RO)} mm yang pusatnya {f1(EL_X)} mm di depan pusat lubang.", anc="start", sz=13, w=500, col=ABU))
    return svg(W_, H_, "".join(el), "Lubang ukur")


def m1_modul_sensor():
    """Susunan modul sensor dalam pipa (potongan sepanjang sumbu, digambar tegak)."""
    S = 17.0; W_, H_ = 980, 520; el = []; cx, top = 300, 110
    s_top = S_END; s_bawah = 11.0
    Y = lambda s: top + (s_top - s) * S; X = lambda r: cx + r * S
    pc, ck = GE.TCS["pcb"], 3.0
    s_komp = GA.H_CHIP + GE.TCS["chip_tebal"]           # sisi komponen papan
    for sgn in (-1, 1):
        el.append(f'<rect x="{min(X(sgn * TUBE_RI), X(sgn * TUBE_RO)):.1f}" y="{Y(s_top):.1f}" width="{(TUBE_RO - TUBE_RI) * S:.1f}" height="{(s_top - s_bawah) * S:.1f}" fill="#e4ded4" stroke="{TINTA}" stroke-width="1.2"/>')
        el.append(f'<rect x="{min(X(sgn * TUBE_RI), X(sgn * (TUBE_RI - 0.6))):.1f}" y="{Y(17.5):.1f}" width="{0.6 * S:.1f}" height="{(17.5 - s_bawah) * S:.1f}" fill="#0b0b0d"/>')
    R = TUBE_RI - 0.15
    el.append(f'<rect x="{X(-R):.1f}" y="{Y(s_komp + pc + ck):.1f}" width="{2 * R * S:.1f}" height="{ck * S:.1f}" fill="#3a3b40" stroke="#111"/>')
    hw = GE.TCS["L"] / 2
    el.append(f'<rect x="{X(-hw):.1f}" y="{Y(s_komp + pc):.1f}" width="{2 * hw * S:.1f}" height="{pc * S:.1f}" fill="#6a2c91" stroke="#3b1552"/>')
    el.append(f'<rect x="{X(-1):.1f}" y="{Y(s_komp):.1f}" width="{2 * S:.1f}" height="{0.65 * S:.1f}" fill="#c9b37a"/>')
    lx = GE.TCS["led"][0] - GE.TCS["chip"][0]
    el.append(f'<rect x="{X(lx - 0.7):.1f}" y="{Y(s_komp):.1f}" width="{1.4 * S:.1f}" height="{1.1 * S:.1f}" fill="#fff4c2" stroke="#b9a46a"/>')
    for hx in (GE.TCS["lubang"][0][0] - GE.TCS["chip"][0], GE.TCS["lubang"][1][0] - GE.TCS["chip"][0]):
        el.append(f'<rect x="{X(hx - 1.2):.1f}" y="{Y(s_komp + pc + ck + 2.6):.1f}" width="{2.4 * S:.1f}" height="{(pc + ck + 2.6 + 1.7) * S:.1f}" fill="#666"/>')
        el.append(f'<rect x="{X(hx - 2.25):.1f}" y="{Y(s_komp):.1f}" width="{4.5 * S:.1f}" height="{1.7 * S:.1f}" fill="#1c1c1c"/>')
        el.append(f'<rect x="{X(hx - 2.5):.1f}" y="{Y(s_komp + pc + ck + 2.0):.1f}" width="{5 * S:.1f}" height="{2.0 * S:.1f}" fill="#1c1c1c"/>')
    el.append(f'<line x1="{X(0):.1f}" y1="{Y(s_top) - 30:.1f}" x2="{X(0):.1f}" y2="{Y(s_bawah) + 30:.1f}" stroke="{BIRU}" stroke-dasharray="8 4"/>')
    el.append(TX(X(0), Y(s_bawah) + 50, f"sumbu: ke pusat lubang ukur {f1(GA.H_CHIP)} mm dari muka chip", sz=13, w=700, col=BIRU))
    el += dimV(X(-TUBE_RO) - 34, Y(s_komp + pc + ck), Y(s_top), "rata", kecil=True)
    el += dimV(X(-TUBE_RO) - 34, Y(GA.H_CHIP), Y(s_komp + pc + ck), f1(s_top - GA.H_CHIP), kecil=True)
    el += dimH(X(-R), X(R), Y(s_top) - 34, "cakram Ø " + f1(2 * R))
    hk = GE.TCS["lubang"][1][0] - GE.TCS["chip"][0]
    lab = [("mur M2,5", s_komp + pc + ck + 1.0, -24, hk + 2.5), ("cakram PVC hitam 3 mm", s_komp + pc + ck / 2, 0, R - 0.5), ("papan sensor 1,6 mm", s_komp + pc / 2, 24, hw - 0.5),
           ("kepala baut M2,5", s_komp - 0.85, 48, hk + 2.25), ("chip (tengah) dan LED", s_komp - 0.3, 72, 0.9), ("beludru hitam", 13.0, 96, TUBE_RI - 0.3)]
    for tx, s_, dy, r0 in lab:
        y_ = Y(s_); yl = Y(s_top) + 40 + dy
        el.append(f'<circle cx="{X(r0):.1f}" cy="{y_:.1f}" r="3" fill="{ABU}"/><path d="M{X(r0):.1f},{y_:.1f} L{X(TUBE_RO) + 60:.1f},{yl:.1f} L{X(TUBE_RO) + 80:.1f},{yl:.1f}" fill="none" stroke="{ABU}"/>')
        el.append(TX(X(TUBE_RO) + 86, yl + 5, tx, anc="start", sz=13, w=600))
    for i, s_ in enumerate(["1. Baut papan ke cakram: 2 baut M2,5 x 10 hitam dari sisi komponen, mur di punggung cakram. Header menembus celah cakram.",
                            "2. Dorong modul ke dalam pipa dari ujung tegak lurus sampai punggung cakram RATA dengan ujung pipa (tempelkan penggaris).",
                            "3. Putar modul: header ke arah sisi panjang pipa (tanda panah dari pola). Chip dan LED menghadap ke lubang ukur.",
                            "4. Kunci dengan silikon hitam di tepi cakram dan celah header, supaya cahaya dari dalam kotak tidak masuk ke tabung."]):
        el.append(TX(40, 410 + i * 26, s_, anc="start", sz=13, w=500))
    el.append(TX(40, 36, "Modul sensor di dalam pipa (potongan sepanjang sumbu)", anc="start", sz=15, w=700))
    return svg(W_, H_, "".join(el), "Modul sensor")


def susunan_oled(ganjal, tebal_tutup, judul, catatan):
    """Potongan satu baut OLED: kepala, tutup, ganjal, PCB, mur."""
    S = 14.0; W_, H_ = 980, 330; el = []; cx, z0 = 300, 60
    Y = lambda z: z0 + z * S
    lap = [("kepala baut M2", 1.2, "#1c1c1c", 3.6), (f"tutup PVC {f1(tebal_tutup)}", tebal_tutup, "#e4ded4", 14), (f"ganjal {f1(ganjal)}", ganjal, "#444", 4.0),
           ("PCB OLED 1,2", 1.2, "#1d4f9c", 14), ("mur pengunci M2 1,6", 1.6, "#1c1c1c", 4.0)]
    z = 0.0
    for nama, h, c, w in lap:
        el.append(f'<rect x="{cx - w / 2 * S:.1f}" y="{Y(z):.1f}" width="{w * S:.1f}" height="{h * S:.1f}" fill="{c}" stroke="#111" stroke-width="1"/>')
        el.append(f'<line x1="{cx + w / 2 * S + 4:.1f}" y1="{Y(z + h / 2):.1f}" x2="{cx + 230:.1f}" y2="{Y(z + h / 2):.1f}" stroke="{ABU}"/>')
        el.append(TX(cx + 236, Y(z + h / 2) + 5, nama, anc="start", sz=13, w=600)); z += h
    el.append(f'<rect x="{cx - 0.95 * S:.1f}" y="{Y(1.2):.1f}" width="{1.9 * S:.1f}" height="{(z - 1.2 + 1.2) * S:.1f}" fill="#777" opacity=".55"/>')
    el += dimV(cx - 120, Y(0), Y(z), f1(z) + " (baut minimal M2 x " + str(int(math.ceil((z - 1.2 + 0.5) / 2) * 2)) + ")")
    el.append(TX(40, 30, judul, anc="start", sz=15, w=700))
    el.append(TX(560, 120, catatan, anc="start", sz=13, w=500, col=ABU))
    return svg(W_, H_, "".join(el), judul)


def sambungan(judul, L, W, t, penuh, nama, lantai, catatan):
    """Denah sambungan dilihat dari atas: penuh='y' -> dinding depan/belakang sepanjang W penuh, samping di antaranya; 'x' sebaliknya.
    nama: dict depan, belakang, kiri, kanan -> teks."""
    S = min(560 / L, 300 / W); W_, H_ = 980, 560; ox, oy = 160, 150; el = []
    X = lambda x: ox + x * S; Y = lambda y: oy + (W - y) * S
    el.append(f'<rect x="{X(0):.1f}" y="{Y(W):.1f}" width="{L * S:.1f}" height="{W * S:.1f}" fill="#f1ece4" stroke="#bbb" stroke-dasharray="4 3"/>')
    el.append(TX(X(L / 2), Y(W / 2) - 10, lantai, sz=12, w=600, col=ABU))
    def papan(x0, x1, y0, y1, c, teks, vert=False):
        el.append(f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{(x1 - x0) * S:.1f}" height="{(y1 - y0) * S:.1f}" fill="{c}" stroke="{TINTA}" stroke-width="1.2"/>')
    if penuh == "y":     # belakang di x = 0 (kiri gambar), depan di x = L
        papan(0, t, 0, W, "#c9b9a3", ""); papan(L - t, L, 0, W, "#c9b9a3", "")
        papan(t, L - t, 0, t, "#e6dccd", ""); papan(t, L - t, W - t, W, "#e6dccd", "")
        el += dimH(X(t), X(L - t), Y(W / 2) + 40, f1(L - 2 * t) + f" mm = {f1(L)} - 2 x {f1(t)}", kecil=False)
        el += dimV(X(L) + 40, Y(0), Y(W), f1(W) + " mm", kanan=True, warna=MERAH)
    else:                # samping penuh sepanjang L, depan/belakang di antaranya
        papan(0, L, 0, t, "#c9b9a3", ""); papan(0, L, W - t, W, "#c9b9a3", "")
        papan(0, t, t, W - t, "#e6dccd", ""); papan(L - t, L, t, W - t, "#e6dccd", "")
        el += dimV(X(L) + 40, Y(t), Y(W - t), f1(W - 2 * t) + f" mm = {f1(W)} - 2 x {f1(t)}", kanan=True)
        el += dimH(X(0), X(L), Y(0) + 70, f1(L) + " mm", warna=MERAH)
    el += dimH(X(0), X(L), Y(W) - 26, f1(L) + " mm (luar)", warna=MERAH)
    el.append(TX(X(0) - 12, Y(W / 2) + 4, nama["belakang"], anc="end", sz=12.5, w=700))
    el.append(TX(X(L) + 12 + (90 if penuh == "x" else 70), Y(W / 2) - 40, nama["depan"], anc="start", sz=12.5, w=700))
    el.append(TX(X(L / 2), Y(W) - 48, nama["atas"], sz=12.5, w=700)); el.append(TX(X(L / 2), Y(0) + 34, nama["bawah"], sz=12.5, w=700))
    el.append(f'<rect x="{X(0):.1f}" y="{Y(W) - 96:.1f}" width="14" height="14" fill="#c9b9a3" stroke="{TINTA}"/>'); el.append(TX(X(0) + 20, Y(W) - 84, "lembar sepanjang ukuran luar penuh", anc="start", sz=12))
    el.append(f'<rect x="{X(0) + 300:.1f}" y="{Y(W) - 96:.1f}" width="14" height="14" fill="#e6dccd" stroke="{TINTA}"/>'); el.append(TX(X(0) + 320, Y(W) - 84, "lembar yang masuk DI ANTARA keduanya", anc="start", sz=12))
    for i, c_ in enumerate(catatan): el.append(TX(40, H_ - 46 + i * 20, c_, anc="start", sz=12.5, w=500))
    el.append(TX(40, 26, judul, anc="start", sz=15, w=700))
    return svg(W_, H_, "".join(el), judul)


# ============================================================================ UMUM
def header_solder():
    S = 9.0; W_, H_ = 980, 330; el = []; cx, cy = 300, 170
    # papan tampak samping
    el.append(f'<rect x="{cx - 10.16 * S:.1f}" y="{cy:.1f}" width="{20.32 * S:.1f}" height="{1.6 * S:.1f}" fill="#6a2c91"/>')
    el.append(TX(cx, cy - 46, "sisi komponen (chip, LED) menghadap daging", sz=13, w=600))
    el.append(f'<rect x="{cx - 1 * S:.1f}" y="{cy - 0.65 * S:.1f}" width="{2 * S:.1f}" height="{0.65 * S:.1f}" fill="#c9b37a"/>')
    hx = cx + (GE.TCS["header_y"] - 10.16) * S
    el.append(f'<rect x="{hx - 1.27 * S:.1f}" y="{cy + 1.6 * S:.1f}" width="{2.54 * S:.1f}" height="{2.5 * S:.1f}" fill="#151515"/>')
    el.append(f'<rect x="{hx - 0.32 * S:.1f}" y="{cy - 1.5 * S:.1f}" width="{0.64 * S:.1f}" height="{(1.5 + 1.6 + 8.5) * S:.1f}" fill="#d4af37"/>')
    el.append(f'<path d="M{hx - 1.1 * S:.1f},{cy:.1f} Q{hx:.1f},{cy - 1.6 * S:.1f} {hx + 1.1 * S:.1f},{cy:.1f} Z" fill="#c0c4c9" stroke="#888"/>')
    el.append(f'<line x1="{hx + 14:.1f}" y1="{cy - 10:.1f}" x2="{hx + 140:.1f}" y2="{cy - 70:.1f}" stroke="{MERAH}"/>')
    el.append(TX(hx + 144, cy - 72, "solder di sisi komponen", anc="start", sz=13, w=700, col=MERAH))
    el.append(f'<line x1="{hx - 16:.1f}" y1="{cy + 1.6 * S + 12:.1f}" x2="{hx - 120:.1f}" y2="{cy + 70:.1f}" stroke="{ABU}"/>')
    el.append(TX(hx - 124, cy + 84, "plastik header", anc="end", sz=13, w=600)); el.append(TX(hx - 124, cy + 102, "di punggung", anc="end", sz=13, w=600))
    el.append(TX(hx, cy + (1.6 + 8.5) * S + 22, "pin panjang ke belakang", sz=13, w=600))
    tx0 = 560
    for i, s_ in enumerate(["Header 7 pin TCS34725:", "1. Tancapkan header ke breadboard, pin panjang ke bawah.", "2. Letakkan papan dengan sisi komponen DI ATAS,",
                            "    jadi plastik header berada di punggung papan.", "3. Solder 330-350 °C, 2 detik per pin. Mulai pin ujung,", "    periksa lurus, lalu pin lainnya.",
                            "4. Sambungan baik: kerucut mengilap, tidak bulat.", "OLED dan ESP32 biasanya sudah tersolder."]):
        el.append(TX(tx0, 60 + i * 30, s_, anc="start", sz=14, w=700 if i in (0, 7) else 500))
    el.append(TX(40, 30, "Menyolder header sensor (tampak samping)", anc="start", sz=15, w=700))
    return svg(W_, H_, "".join(el), "Header")


def solder_pin():
    """Cara menyolder kabel langsung ke pin header (ESP32, sensor, OLED), tampak samping, berskala 16 px/mm."""
    W_, H_ = 980, 640; el = []; S = 16.0; yp = 330
    def dasar(cx, judul):
        el.append(f'<rect x="{cx - 60}" y="{yp + 40}" width="120" height="26" fill="#1d2024"/>')
        el.append(f'<rect x="{cx - 20}" y="{yp}" width="40" height="40" fill="#151515"/>')
        el.append(f'<rect x="{cx - 5}" y="{yp - 6 * S}" width="10" height="{6 * S + 66}" fill="#d4af37"/>')
        el.append(TX(cx, yp + 88, "pin header", sz=11, w=600, col=ABU))
        el.append(TX(cx, 40, judul, sz=14, w=700))
    def kabel(x, y0, y1, c, kupas):
        el.append(f'<rect x="{x - 5}" y="{y0}" width="10" height="{y1 - y0}" rx="3" fill="{c}" stroke="#333" stroke-width=".6"/>')
        el.append(f'<rect x="{x - 3}" y="{y1}" width="6" height="{kupas}" fill="#c87533"/>')
    def selongsong(x, y0, y1, w, susut):
        el.append(f'<rect x="{x - w / 2}" y="{y0}" width="{w}" height="{y1 - y0}" rx="4" fill="{"#2a2226" if susut else "#9a958e"}" opacity="{.55 if susut else .35}" stroke="#2a2226" stroke-dasharray="{"0" if susut else "4 3"}"/>')
    c1, c2, c3 = 160, 480, 800
    dasar(c1, "1. Siapkan"); dasar(c2, "2. Solder"); dasar(c3, "3. Tutup selongsong")
    # 1: dua kabel kuning dikupas 4 mm, selongsong sudah masuk
    for dx in (34, 48): kabel(c1 + dx, 70, yp - 6 * S - 10, "#e8b00c", 4 * S)
    selongsong(c1 + 41, 80, 80 + 15 * S * 0.55, 34, False)
    el.append(TX(c1 + 70, 140, "selongsong", anc="start", sz=11, w=600)); el.append(TX(c1 + 70, 154, "masuk dulu", anc="start", sz=11, w=600))
    el += dimV(c1 + 78, yp - 6 * S - 10, yp - 6 * S - 10 + 4 * S, "kupas 4", kanan=True, kecil=True)
    # 2: kabel menempel sejajar pin, ujung 1 mm di atas plastik, timah
    for dx in (11, 22): kabel(c2 + dx, 70, yp - 16 - 4 * S, "#e8b00c", 4 * S)
    el.append(f'<ellipse cx="{c2 + 9}" cy="{yp - 16 - 2 * S}" rx="24" ry="{2.4 * S}" fill="#b8bcc2" stroke="#7d828a"/>')
    el.append(TX(c2 + 40, yp - 60, "timah meresap,", anc="start", sz=11, w=600)); el.append(TX(c2 + 40, yp - 46, "kerucut mengilap", anc="start", sz=11, w=600))
    el += dimV(c2 - 40, yp - 16, yp, "1", kecil=True)
    # 3: selongsong menutup pin sampai plastik
    for dx in (11, 22): kabel(c3 + dx, 70, yp - 16 - 4 * S, "#e8b00c", 4 * S)
    selongsong(c3 + 9, yp - 15 * S, yp, 40, True)
    el += dimV(c3 + 56, yp - 15 * S, yp, "15", kanan=True)
    el += dimV(c3 - 34, yp - 6 * S, yp, "pin 6", kecil=True)
    el.append(TX(c3 - 24, yp - 15 * S + 20, "selongsong Ø 2 mm,", anc="end", sz=11, w=600)); el.append(TX(c3 - 24, yp - 15 * S + 34, "dipanaskan", anc="end", sz=11, w=600))
    langkah_ = ["1. Potong kabel sepanjang kolom \u201cPotong\u201d di daftar kabel. Kupas 4 mm di kedua ujung, pilin serabutnya, lapisi timah tipis.",
                "2. Masukkan selongsong panas Ø 2 x 15 mm SEBELUM menyolder. Pin yang menerima dua kabel: kedua kabel masuk ke SATU selongsong.",
                "3. Tempel ujung kabel sejajar pin, 1 mm di atas plastik header. Solder 330-350 °C selama 2-3 detik sampai timah meresap.",
                "4. Tunggu dingin, tarik pelan: kabel tidak boleh lepas. Geser selongsong sampai menyentuh plastik, panaskan sampai menciut.",
                "5. Pin G27, G26, G25 bersebelahan (2,54 mm). Selesaikan satu pin sampai selongsongnya menciut, baru pin berikutnya.",
                "6. Uji multimeter mode bunyi: kedua ujung tiap kabel berbunyi; dua pin yang bersebelahan TIDAK boleh berbunyi."]
    for i, t_ in enumerate(langkah_): el.append(TX(40, 470 + i * 26, t_, anc="start", sz=13, w=500))
    el.append(TX(40, 448, "Sama untuk pin ESP32, header sensor, dan header OLED. Gambar berskala 16 px per mm.", anc="start", sz=13, w=700))
    return svg(W_, H_, "".join(el), "Menyolder kabel ke pin")


def skema(model, judul):
    """Peta titik solder dan daftar kabel model (papan berskala, jalur tidak berskala)."""
    K = list((GA if model == "genggam" else GE).KABEL.values())
    return GKL.peta_solder(K, judul)


def tutup_cat():
    """Tutup cat semprot Model 2: tampak samping (potong 22 mm) dan tampak muka (lubang Ø 14), berskala 5 px/mm."""
    P = GE.P; D, Di, Hc, dl, mk = P["tutup_D"], P["tutup_Di"], P["Hc"], P["lubang_D"], P["tutup_muka"]
    H0 = 50.0                                                  # tinggi tutup utuh (ukuran Zhou: Ø 65 x 50)
    S = 5.0; W_, H_ = 980, 640; el = []
    el.append(TX(40, 32, "Tutup cat semprot: dipotong dan dibor (semua angka dalam mm)", anc="start", sz=16, w=700))
    cx, yb = 250, 400
    X = lambda x: cx + x * S; Y = lambda z: yb - z * S
    box = lambda x0, x1, z0, z1, f, st="#111": el.append(f'<rect x="{X(x0):.1f}" y="{Y(z1):.1f}" width="{(x1 - x0) * S:.1f}" height="{(z1 - z0) * S:.1f}" fill="{f}" stroke="{st}" stroke-width="1"/>')
    # bagian yang dibuang (garis putus)
    el.append(f'<rect x="{X(-D / 2):.1f}" y="{Y(H0):.1f}" width="{D * S:.1f}" height="{(H0 - Hc) * S:.1f}" fill="#e4dfd7" stroke="#9a958e" stroke-dasharray="5 4"/>')
    el.append(TX(cx, Y((H0 + Hc) / 2) + 5, "sisa, dibuang", sz=13, w=600, col=ABU))
    # bagian yang dipakai: dua dinding + muka berlubang (potongan tengah)
    t_d = (D - Di) / 2
    box(-D / 2, -D / 2 + t_d, 0, Hc, "#2b2c30"); box(D / 2 - t_d, D / 2, 0, Hc, "#2b2c30")
    box(-D / 2, -dl / 2, 0, mk, "#2b2c30"); box(dl / 2, D / 2, 0, mk, "#2b2c30")
    el.append(TX(cx, Y(Hc / 2) + 5, "bagian yang dipakai", sz=13, w=600, col="#555"))
    # garis potong
    el.append(f'<line x1="{X(-D / 2) - 20:.1f}" y1="{Y(Hc):.1f}" x2="{X(D / 2) + 20:.1f}" y2="{Y(Hc):.1f}" stroke="{MERAH}" stroke-width="2.4"/>')
    el.append(TX(X(D / 2) + 24, Y(Hc) - 8, "garis potong", anc="start", sz=13, w=700, col=MERAH))
    el.append(TX(X(D / 2) + 24, Y(Hc) + 10, "(lilitkan selotip)", anc="start", sz=12, w=500, col=MERAH))
    # lubang
    for sx in (-1, 1):
        el.append(f'<line x1="{X(sx * dl / 2):.1f}" y1="{Y(-4):.1f}" x2="{X(sx * dl / 2):.1f}" y2="{Y(mk + 5):.1f}" stroke="{MERAH}" stroke-dasharray="4 3"/>')
    # ukuran
    el += dimV(X(-D / 2) - 34, Y(0), Y(Hc), f1(Hc) + " mm", warna=MERAH)
    el += dimV(X(D / 2) + 46, Y(Hc), Y(H0), f"+ {f1(H0 - Hc)} = {f1(H0)} utuh", kanan=True, kecil=True)
    el += dimH(X(-D / 2), X(D / 2), Y(0) + 36, f"Ø {f1(D)} mm (lebar luar)")
    el += dimH(X(-dl / 2), X(dl / 2), Y(0) + 72, f"Ø {f1(dl)} lubang", warna=MERAH)
    el.append(TX(cx, Y(0) + 100, "muka tutup (sisi tertutup) ada di bawah, menyentuh daging", sz=12, w=600, col=ABU))
    el.append(TX(cx, 76, "Tampak samping (dipotong di tengah)", sz=14, w=700))
    # tampak muka
    c2x, c2y, r2 = 760, 250, D / 2 * 4.2
    el.append(TX(c2x, 76, "Tampak muka (dari bawah)", sz=14, w=700))
    el.append(f'<circle cx="{c2x}" cy="{c2y}" r="{r2:.1f}" fill="#2b2c30" stroke="#111" stroke-width="1.2"/>')
    rl = dl / 2 * 4.2
    el.append(f'<circle cx="{c2x}" cy="{c2y}" r="{rl:.1f}" fill="#fff" stroke="{MERAH}" stroke-width="2.4"/>')
    el.append(f'<path d="M{c2x - 10},{c2y} h20 M{c2x},{c2y - 10} v20" stroke="{MERAH}" stroke-width="1"/>')
    el.append(f'<line x1="{c2x - r2:.1f}" y1="{c2y}" x2="{c2x + r2:.1f}" y2="{c2y}" stroke="#777" stroke-dasharray="3 3"/><line x1="{c2x}" y1="{c2y - r2:.1f}" x2="{c2x}" y2="{c2y + r2:.1f}" stroke="#777" stroke-dasharray="3 3"/>')
    el.append(f'<text x="{c2x}" y="{c2y + rl + 24:.1f}" font-size="13" font-weight="700" fill="#fff" text-anchor="middle">lubang Ø {f1(dl)} tepat di pusat</text>')
    el += dimH(c2x - r2, c2x + r2, c2y + r2 + 30, f"Ø {f1(D)}")
    el.append(TX(c2x, c2y + r2 + 58, "garis putus = 2 garis tengah untuk mencari pusat", sz=12, w=500, col=ABU))
    for i, t_ in enumerate([f"1. Tandai {f1(Hc)} mm dari muka di 4 sisi, lilitkan selotip lurus di tanda itu, gergaji di sepanjang tepi selotip.",
                            "2. Cari pusat muka: tarik 2 garis tengah bersilangan. Bor bertahap Ø 4, 8, 12 mm, lalu kikir bulat sampai Ø 14.",
                            f"3. Cek dengan jangka sorong: tinggi {f1(Hc)} ± 0,5 mm di keempat sisi, lubang {f1(dl)} ± 0,3 mm. Lubang terlalu besar = cahaya luar bocor."]):
        el.append(TX(40, 562 + i * 24, t_, anc="start", sz=13, w=500))
    return svg(W_, H_, "".join(el), "Tutup cat semprot")


def cara_baca():
    W_, H_ = 980, 150; el = []
    items = [("#b3262e", "garis merah", "potong atau bor"), ("#6c6469", "garis putus", "tanda untuk menempel"), ("#1f5fa8", "garis biru", "ukuran (mm)")]
    for i, (c, a, b) in enumerate(items):
        x = 40 + i * 310
        el.append(f'<line x1="{x}" y1="60" x2="{x + 70}" y2="60" stroke="{c}" stroke-width="2.5" {"stroke-dasharray=\"6 4\"" if i == 1 else ""}/>')
        el.append(TX(x + 84, 56, a, anc="start", sz=14, w=700)); el.append(TX(x + 84, 76, b, anc="start", sz=13, w=500, col=ABU))
    el.append(TX(40, 120, "Semua ukuran dalam milimeter. Ukuran berantai diukur dari tepi kiri dan tepi bawah setiap lembar.", anc="start", sz=13, w=500))
    el.append(TX(40, 144, "Ø (huruf O dicoret, bukan nol) = diameter, garis tengah lingkaran. Ø 14 = lubang bulat selebar 14 mm.", anc="start", sz=13, w=700))
    return svg(W_, H_ + 14, "".join(el), "Cara membaca gambar")


def pola_m1_a4():
    """Semua lembar PVC Model 1 skala 1:1 (mm) untuk A4."""
    el = []; m = 10.0; y = m
    def rect(x, y, w, h, lab, lubang=()):
        el.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="none" stroke="#000" stroke-width="0.3"/>')
        el.append(f'<text x="{x + 1.5:.2f}" y="{y + 4.5:.2f}" font-size="3.2" fill="#000">{lab}</text>')
        for kind, *a in lubang:
            if kind == "c": el.append(f'<circle cx="{x + a[0]:.2f}" cy="{y + h - a[1]:.2f}" r="{a[2]:.2f}" fill="none" stroke="#c00" stroke-width="0.3"/>'
                                     f'<path d="M{x + a[0] - 1:.2f},{y + h - a[1]:.2f} h2 M{x + a[0]:.2f},{y + h - a[1] - 1:.2f} v2" stroke="#c00" stroke-width="0.2"/>')
            if kind == "r": el.append(f'<rect x="{x + a[0]:.2f}" y="{y + h - a[3]:.2f}" width="{a[1] - a[0]:.2f}" height="{a[3] - a[2]:.2f}" fill="none" stroke="#c00" stroke-width="0.3"/>')
            if kind == "t": el.append(f'<circle cx="{x + a[0]:.2f}" cy="{y + h - a[1]:.2f}" r="{a[2]:.2f}" fill="none" stroke="#666" stroke-width="0.25" stroke-dasharray="1.5 1"/>')
            if kind == "e": el.append(f'<ellipse cx="{x + a[0]:.2f}" cy="{y + h - a[1]:.2f}" rx="{a[2]:.2f}" ry="{a[3]:.2f}" fill="none" stroke="#666" stroke-width="0.25" stroke-dasharray="1.5 1"/>')
    def poly(x, y, pts, h, lab):
        el.append('<path d="M' + " L".join(f"{x + u:.2f},{y + h - v:.2f}" for u, v in pts) + ' Z" fill="none" stroke="#000" stroke-width="0.3"/>')
        el.append(f'<text x="{x + 1.5:.2f}" y="{y + 4.5:.2f}" font-size="3.2" fill="#000">{lab}</text>')
    prof = [(0, 2), (XP - X0, 2), (XP - X0, 0), (L_TOT, 0), (L_TOT, H_DIND), (0, H_DIND)]
    poly(m, y, prof, H_DIND, "Dinding samping kiri (belakang di kiri)"); y += H_DIND + 4
    poly(m, y, prof, H_DIND, "Dinding samping kanan"); y += H_DIND + 4
    tl = [("r", OX - 7.5 - X0, OX + 7.5 - X0, YW - 12.5, YW + 12.5), ("t", -16 - X0, YW, 6.0)] + [("c", OX + sx * 11.65 - X0, YW + sy * 11.65, 1.1) for sx in (-1, 1) for sy in (-1, 1)]
    rect(m, y, L_TOT, W_TOT, "Tutup atas (belakang di kiri)", tl); y += W_TOT + 4
    rect(m, y, X1 - XP, W_TOT, "Pelat muka HITAM", [("c", -XP, YW, GA.AP_R), ("t", -XP, YW, 8.0), ("e", -XP + EL_X, YW, EL_A, TUBE_RO)])
    rect(m + (X1 - XP) + 4, y, XP - X0, W_TOT, "Lantai belakang"); y += W_TOT + 4
    rect(m, y, 2 * GA.YI, H_DIND, "Dinding depan")
    rect(m + 2 * GA.YI + 4, y, 2 * GA.YI, GA.Z_TOP - 5, "Dinding belakang", [("r", GA.YI - 6.5, GA.YI + 6.5, 0, GA.usb_z1 + 4 - 5)])
    xb = m + 4 * GA.YI + 8; lb = (OX - OH / 2 - 1) - (X0 + t); lk = (X1 - t) - (OX + OH / 2 + 1)
    for i in range(2): rect(xb, y + i * 8, lb, 6, "")
    for i in range(2): rect(xb, y + 16 + i * 8, lk, 6, "")
    el.append(f'<text x="{xb:.2f}" y="{y + 36:.2f}" font-size="3" fill="#000">bibir: 2 panjang, 2 pendek (6 mm)</text>')
    R = TUBE_RI - 0.15; cx_, cy_ = GE.TCS["chip"]; ckx, cky = xb + lb - R - 1, y + 40 + R
    el.append(f'<circle cx="{ckx:.2f}" cy="{cky:.2f}" r="{R:.2f}" fill="none" stroke="#000" stroke-width="0.3"/>')
    xs = [GE.TCS["header_x0"] + i * GE.TCS["pitch"] for i in range(7)]; hy = GE.TCS["header_y"]
    el.append(f'<rect x="{ckx + min(xs) - 1.52 - cx_:.2f}" y="{cky - (hy + 1.52 - cy_):.2f}" width="{max(xs) - min(xs) + 3.04:.2f}" height="3.04" fill="none" stroke="#c00" stroke-width="0.3"/>')
    for hx, hy_ in GE.TCS["lubang"]: el.append(f'<circle cx="{ckx + hx - cx_:.2f}" cy="{cky - (hy_ - cy_):.2f}" r="1.4" fill="none" stroke="#c00" stroke-width="0.3"/>')
    el.append(f'<text x="{ckx - R:.2f}" y="{cky + R + 4:.2f}" font-size="3" fill="#000">cakram HITAM Ø {f1(2 * R)}</text>')
    y += H_DIND + 4
    y = max(y, cky + R + 8)
    el.append(f'<line x1="{m}" y1="{y:.2f}" x2="{m + 50}" y2="{y:.2f}" stroke="#000" stroke-width="0.4"/><text x="{m + 53}" y="{y + 1.2:.2f}" font-size="3.2">garis uji 50 mm: ukur setelah dicetak (skala 100 %)</text>')
    H = y + 8
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="190mm" height="{H:.1f}mm" viewBox="0 0 190 {H:.1f}" font-family="system-ui,sans-serif">' + "".join(el) + "</svg>")


if __name__ == "__main__":
    tulis = {"cara_baca.svg": cara_baca(), "header_sensor.svg": header_solder(), "solder_pin.svg": solder_pin(), "tutup_cat.svg": tutup_cat(),
             "m1_lembar_badan.svg": m1_lembar_badan(), "m1_lembar_tutup.svg": m1_lembar_tutup()[0], "m1_cakram.svg": m1_lembar_tutup()[1], "m1_pipa.svg": m1_pipa(),
             "m1_lubang.svg": m1_lubang(), "m1_modul_sensor.svg": m1_modul_sensor(),
             "m1_oled.svg": susunan_oled(GA.GANJAL, t, "Model 1: satu baut OLED (potongan)", "mur M2 di antara tutup dan PCB = ganjal 1,6 mm"),
             "m2_oled.svg": susunan_oled(GE.GANJAL_OLED, t, "Model 2: satu baut OLED (potongan)", "mur M2 di antara tutup dan PCB = ganjal 1,6 mm"),
             "m1_sambungan.svg": sambungan("Model 1: cara menyambung dinding (dilihat dari atas, tutup dilepas)", L_TOT, W_TOT, t, "x",
                                    dict(depan="DEPAN (kepala ukur)", belakang="BELAKANG (USB)", atas="dinding samping", bawah="dinding samping"), "pelat muka + lantai belakang di bawah semua dinding",
                                    ["Dinding samping sepanjang 107,5 (luar penuh). Dinding depan dan belakang 33 mm masuk DI ANTARA dinding samping: 39 - 3 - 3 = 33.",
                                     "Semua dinding BERDIRI DI ATAS pelat muka dan lantai belakang, jadi tinggi alat = 3 (pelat) + 46 (dinding) + 3 (tutup) = 52 mm."]),
            "m2_sambungan.svg": sambungan("Model 2: cara menyambung dinding baki dan kepala (dilihat dari atas)", GE.W, GE.W, t, "y",
                                    dict(depan="DEPAN (kait)", belakang="BELAKANG (engsel)", atas="dinding kiri (kepala: takik USB)", bawah="dinding kanan"), "lantai 86 x 86 di bawah semua dinding",
                                    ["Dinding depan dan belakang 86 (luar penuh). Dinding kiri dan kanan 80 mm masuk DI ANTARA keduanya: 86 - 3 - 3 = 80.",
                                     "Sama untuk baki dan kepala. Semua dinding BERDIRI DI ATAS lantainya; lantai tidak dijepit di antara dinding."]),
            "m1_skema.svg": skema("genggam", "Model 1: peta titik solder dan daftar kabel"), "m2_skema.svg": skema("jepit", "Model 2: peta titik solder dan daftar kabel"),
             "pola_m1_badan_1banding1.svg": pola_m1_a4(), "pola_m1_pipa_1banding1.svg": m1_pipa_pola()}
    for n, s_ in tulis.items(): open(os.path.join(OUT, n), "w").write(s_)
    print("ditulis", len(tulis), "gambar;", f"pipa: panjang {PIPA_PANJANG:.2f}, pendek {PIPA_PENDEK:.2f}, keliling {KELILING:.2f}; elips {2*EL_A:.2f} x {2*TUBE_RO:.0f} pusat +{EL_X:.2f}")

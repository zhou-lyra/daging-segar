#!/usr/bin/env python3
"""BeefFresh Jepit (desain E): penjepit berengsel dari PVC, kepala ukur tutup cat, LED bawaan TCS34725.

Satu sumber ukuran untuk gambar kerja (gambar.py), penampil web (bangun_halaman.py), dan Blender (blender_jepit.py).
Jalankan: ../../.venv-cad/bin/python geometri.py   -> model/jepit.glb, model/bagian.json, laporan pemeriksaan

Koordinat (alat tertutup): X depan(0) -> belakang (engsel), Y kiri(0) -> kanan, Z ke atas.
z = 0 adalah muka tutup cat = permukaan daging. Satuan mm.
Asal ukuran: data = berkas resmi (Adafruit, lembar data); masukan = dari Zhou; anggapan = belum diukur; dihitung.
"""
import json, math, os, sys
import numpy as np
import trimesh
from shapely.geometry import Polygon, box as sbox, Point
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "model"); os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------- ukuran
P = dict(
    t=3.0,            # tebal lembaran PVC (anggapan, umum 3 mm)
    W=86.0,           # sisi luar penjepit, X dan Y (dihitung: tutup cat 65 + celah 7,5 x 2 + dinding)
    F=35.0,           # lantai baki (sisi atas) di bawah permukaan daging
    tutup_D=65.0,     # tutup cat semprot, diameter luar (masukan)
    tutup_Di=62.0,    # diameter dalam (anggapan: dinding 1,5)
    tutup_muka=1.5,   # tebal muka tutup (anggapan)
    Hc=22.0,          # tinggi tutup cat setelah dipotong (dihitung dari tinggi papan miring)
    lubang_D=14.0,    # lubang ukur di muka tutup
    miring=40.0,      # kemiringan papan sensor dari datar (dihitung, optik_jepit.py)
    h=15.5,           # muka chip ke pusat lubang, sepanjang sumbu pandang
    kepala_dalam=40.0,  # tinggi dalam kotak kepala
    busa_lapis=3, busa_tebal=10.0, daging_tebal=10.0, daging_sisi=50.0,
)
t, W, F, Hc = P["t"], P["W"], P["F"], P["Hc"]
XC = YC = W / 2                                   # pusat lubang ukur
Z_LANTAI_KEPALA = Hc                              # sisi bawah lantai kepala = bibir baki
Z_ATAS = Hc + t + P["kepala_dalam"]               # sisi bawah tutup atas
SUMBU_ENGSEL = (W + 2.0, Hc)                      # (x, z) poros engsel, di luar dinding belakang

# papan TCS34725 (berkas desain resmi Adafruit, mm, sudut kiri bawah papan = 0,0; sisi komponen = bz 0)
TCS = dict(L=20.32, chamfer=2.54, pcb=1.6, chip=(10.46, 10.00), chip_wh=(2.0, 2.4), chip_tebal=0.65,
           led=(7.241, 10.262), lubang=[(2.54, 17.78), (17.78, 17.78)], lubang_d=2.5,
           header_y=1.524, header_x0=2.54, pitch=2.54,
           # urutan pin header dari skema Adafruit: JP1-1 VIN ... JP1-7 LED (pin 1 di x = 17,78)
           pin=["VIN", "GND", "3V3", "SCL", "SDA", "INT", "LED"])
SMD = [("C1", 13.242, 7.05, 0, "0805"), ("R1", 14.13, 10.253, 90, "0805"), ("R2", 7.486, 13.757, 0, "0805"),
       ("Q1", 7.359, 5.468, 180, "SOT23"), ("Q2", 11.784, 13.9, 0, "SOT23"), ("R3", 10.302, 5.931, 270, "0805"),
       ("R4", 13.627, 4.873, 0, "0805"), ("U2", 17.293, 8.341, 90, "SOT23"), ("C3", 17.801, 4.991, 180, "0805"),
       ("R5", 4.415, 11.015, 270, "0805"), ("C2", 17.433, 11.177, 0, "0805"), ("Q3", 3.041, 6.842, 90, "SOT23"),
       ("R6", 1.905, 11.049, 90, "0805")]
PELAT = dict(bx0=-3.5, bx1=23.82, by0=4.5, by1=21.3, tebal=3.0)     # pelat dudukan di punggung papan
PIPI_BX = [(-3.5, -0.5), (20.82, 23.82)]           # di luar mur M2,5                             # dua pipi penyangga (tebal 3)

ESP = dict(L=51.8, W=28.2, pcb=1.6, x0=6.0, y0=6.0, busa=3.0, modul=(18.0, 25.5, 3.1),
           pin_jarak_baris=25.4, plastik=2.5, pin_panjang=8.5)
OLED = dict(L=27.3, H=27.8, pcb=1.2, kaca=(26.7, 19.3, 1.4), lubang=11.65, cx=60.0, cy=YC)

# ----------------------------------------------------------------------------- arah papan sensor
a = math.radians(P["miring"])
N = np.array([-math.sin(a), 0.0, -math.cos(a)])        # normal sisi komponen (menghadap lubang)
U = np.array([0.0, 1.0, 0.0])                          # sumbu x papan
V = np.array([math.cos(a), 0.0, -math.sin(a)])         # sumbu y papan (ke luar dan turun)
CHIP = np.array([XC + P["h"] * math.sin(a), YC, P["h"] * math.cos(a)])
T0 = CHIP - (TCS["chip"][0] * U + TCS["chip"][1] * V + TCS["chip_tebal"] * N)
M_PAPAN = np.eye(4); M_PAPAN[:3, 0], M_PAPAN[:3, 1], M_PAPAN[:3, 2], M_PAPAN[:3, 3] = U, V, N, T0


def papan(bx, by, bz):
    return T0 + bx * U + by * V + bz * N


LED_W = papan(TCS["led"][0], TCS["led"][1], TCS["chip_tebal"])


# ----------------------------------------------------------------------------- pembuat bentuk
def kotak(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0]); m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]); return m


def silinder(cx, cy, z0, z1, r, n=72):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n); m.apply_translation([cx, cy, (z0 + z1) / 2]); return m


def kurang(a_, *b):
    return trimesh.boolean.difference([a_, *b], engine="manifold")


def gabung(ms):
    return trimesh.boolean.union(ms, engine="manifold")


def ekstrusi(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0); m.apply_translation([0, 0, z0]); return m


def lokal(m):                                           # dari koordinat papan ke dunia
    m = m.copy(); m.apply_transform(M_PAPAN); return m


def pipa(titik, r=0.7, n=10):
    """Tabung kabel lewat titik-titik (Catmull-Rom)."""
    p = np.array(titik, float); pts = []
    q = np.vstack([p[0], p, p[-1]])
    for i in range(1, len(q) - 2):
        for s in np.linspace(0, 1, 12, endpoint=False):
            p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    pts.append(p[-1]); pts = np.array(pts)
    lingk = trimesh.path.polygons.Polygon([(r * math.cos(k), r * math.sin(k)) for k in np.linspace(0, 2 * math.pi, n, endpoint=False)])
    return trimesh.creation.sweep_polygon(lingk, pts)


# ----------------------------------------------------------------------------- bagian
B = {}          # nama -> dict(mesh, grup, warna, nama_tampil, bahan)


def tambah(k, mesh, grup, warna, nama, bahan="pvc", alpha=1.0):
    B[k] = dict(mesh=mesh, grup=grup, warna=warna, nama=nama, bahan=bahan, alpha=alpha)


PVC_BAWAH, PVC_ATAS = "#d9d4cb", "#e8e3da"
# ---- baki bawah
zb0, zb1 = -F - t, -F
tambah("baki_lantai", kotak(0, W, 0, W, zb0, zb1), "bawah", PVC_BAWAH, "Lantai baki")
tambah("baki_depan", kotak(0, t, 0, W, zb1, Hc), "bawah", PVC_BAWAH, "Dinding depan baki")
tambah("baki_belakang", kotak(W - t, W, 0, W, zb1, Hc), "bawah", PVC_BAWAH, "Dinding belakang baki")
tambah("baki_kiri", kotak(t, W - t, 0, t, zb1, Hc), "bawah", PVC_BAWAH, "Dinding kiri baki")
tambah("baki_kanan", kotak(t, W - t, W - t, W, zb1, Hc), "bawah", PVC_BAWAH, "Dinding kanan baki")
# busa (tertekan dari 30 ke 25 mm oleh daging 10 mm)
z_busa_atas = -P["daging_tebal"]; tebal_tekan = (z_busa_atas - zb1) / P["busa_lapis"]
for i in range(P["busa_lapis"]):
    tambah(f"busa_{i+1}", kotak(t + 0.5, W - t - 0.5, t + 0.5, W - t - 0.5, zb1 + i * tebal_tekan, zb1 + (i + 1) * tebal_tekan - 0.02),
           "bawah", "#3b3f46", f"Busa lapis {i+1}", "busa")
s = P["daging_sisi"] / 2
daging = kotak(XC - s, XC + s, YC - s * 0.9, YC + s * 0.9, -P["daging_tebal"], 0.0)
tambah("daging", daging, "bawah", "#b5483f", "Irisan daging 10 mm", "daging")

# ---- kepala: tutup cat + ruang ukur
R, Ri, rl = P["tutup_D"] / 2, P["tutup_Di"] / 2, P["lubang_D"] / 2
tc = kurang(silinder(XC, YC, 0, Hc, R), silinder(XC, YC, P["tutup_muka"], Hc + 1, Ri), silinder(XC, YC, -1, P["tutup_muka"] + 1, rl, 48))
tambah("tutup_cat", tc, "atas", "#1e1f22", "Tutup cat semprot (dipotong 22 mm)", "plastik_hitam")
lap = 0.8
pel = kurang(silinder(XC, YC, P["tutup_muka"], P["tutup_muka"] + lap, Ri - 0.01), silinder(XC, YC, 0, 5, rl + 1.0, 48))
pel_d = kurang(silinder(XC, YC, P["tutup_muka"] + lap, Hc - 0.01, Ri - 0.01), silinder(XC, YC, 0, Hc + 1, Ri - lap, 72))
tambah("beludru", gabung([pel, pel_d]), "atas", "#0b0b0d", "Pelapis beludru hitam", "beludru")

# ---- papan sensor (koordinat papan, lalu dipindah)
L, c_ = TCS["L"], TCS["chamfer"]
oct_ = Polygon([(c_, 0), (L - c_, 0), (L, c_), (L, L - c_), (L - c_, L), (c_, L), (0, L - c_), (0, c_)])
for hx, hy in TCS["lubang"]: oct_ = oct_.difference(Point(hx, hy).buffer(TCS["lubang_d"] / 2, 24))
tambah("sensor_pcb", lokal(ekstrusi(oct_, -TCS["pcb"], 0)), "atas", "#6a2c91", "Papan sensor TCS34725", "pcb_ungu")
cx_, cy_ = TCS["chip"]
tambah("sensor_chip", lokal(kotak(cx_ - 1.0, cx_ + 1.0, cy_ - 1.2, cy_ + 1.2, 0, TCS["chip_tebal"])), "atas", "#c9b37a", "Chip TCS34725", "chip")
lx, ly = TCS["led"]
tambah("sensor_led", lokal(kotak(lx - 0.7, lx + 0.7, ly - 1.1, ly + 1.1, 0, 1.1)), "atas", "#fff4c2", "LED bawaan (putih)", "led")
smd = []
for _, x, y, rot, pk in SMD:
    w, h_, z = (2.0, 1.25, 0.5) if pk == "0805" else (2.9, 1.3, 1.0)
    if rot in (90, 270): w, h_ = h_, w
    smd.append(kotak(x - w / 2, x + w / 2, y - h_ / 2, y + h_ / 2, 0, z))
tambah("sensor_smd", lokal(trimesh.util.concatenate(smd)), "atas", "#3a3a3a", "Komponen kecil di papan", "smd")
xs_pin = [TCS["header_x0"] + i * TCS["pitch"] for i in range(7)][::-1]       # pin 1 (VIN) di x = 17,78
hy = TCS["header_y"]
tambah("sensor_header", lokal(kotak(xs_pin[-1] - 1.27, xs_pin[0] + 1.27, hy - 1.27, hy + 1.27, -TCS["pcb"] - 2.5, -TCS["pcb"])),
       "atas", "#151515", "Header 7 pin (plastik)", "plastik_hitam")
pins = [kotak(x - 0.32, x + 0.32, hy - 0.32, hy + 0.32, -TCS["pcb"] - 2.5 - 6.0, 1.5) for x in xs_pin]
tambah("sensor_pin", lokal(trimesh.util.concatenate(pins)), "atas", "#d4af37", "Pin header", "emas")
DIPAKAI = {"VIN": "#e0245e", "GND": "#2b2b2b", "SCL": "#8e44ad", "SDA": "#e67e22", "LED": "#2e8b57"}
dup = [kotak(x - 1.25, x + 1.25, hy - 1.25, hy + 1.25, -TCS["pcb"] - 2.5 - 14.0, -TCS["pcb"] - 2.5) for x, n in zip(xs_pin, TCS["pin"]) if n in DIPAKAI]
tambah("sensor_dupont", lokal(trimesh.util.concatenate(dup)), "atas", "#202020", "Soket dupont (5)", "plastik_hitam")
# baut M2,5 x 10 + mur, kepala di sisi komponen
baut = []
for hx, hy_ in TCS["lubang"]:
    baut += [silinder(hx, hy_, 0, 1.7, 2.25, 24), silinder(hx, hy_, -TCS["pcb"] - PELAT["tebal"] - 2.6, 0, 1.2, 16),
             silinder(hx, hy_, -TCS["pcb"] - PELAT["tebal"] - 2.0, -TCS["pcb"] - PELAT["tebal"], 2.85, 6)]
tambah("sensor_baut", lokal(gabung(baut)), "atas", "#1c1c1c", "Baut M2,5 x 10 hitam + mur", "baja_hitam")
# pelat dudukan dan pipi
pl = kurang(kotak(PELAT["bx0"], PELAT["bx1"], PELAT["by0"], PELAT["by1"], -TCS["pcb"] - PELAT["tebal"], -TCS["pcb"]),
            *[silinder(hx, hy_, -10, 5, 1.4, 24) for hx, hy_ in TCS["lubang"]])
tambah("dudukan_pelat", lokal(pl), "atas", "#26272b", "Pelat dudukan sensor", "pvc_hitam")
bz_pg = -TCS["pcb"] - PELAT["tebal"]
pa, pb = papan(0, PELAT["by0"], bz_pg), papan(0, PELAT["by1"], bz_pg)
PIPI_POLI = [(pa[0], pa[2]), (pb[0], pb[2]), (pb[0], Hc), (pa[0], Hc)]       # (x, z)
pipi = []
for bx0, bx1 in PIPI_BX:
    y0, y1 = papan(bx0, 0, 0)[1], papan(bx1, 0, 0)[1]
    m = ekstrusi(Polygon(PIPI_POLI), y0, y1)                          # ekstrusi di z, lalu putar: (x, y, z) -> (x, z, y)
    m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    m.invert() if m.volume < 0 else None
    pipi.append(m)
tambah("dudukan_pipi", trimesh.util.concatenate(pipi), "atas", "#26272b", "Pipi penyangga (2)", "pvc_hitam")

# ---- jendela kabel di lantai kepala: jejak header + soket yang menembus lantai, ditambah 1,5 mm
lempeng = kotak(-1, W + 1, -1, W + 1, Hc - 0.3, Hc + t + 0.3)
jejak = [trimesh.boolean.intersection([B[k]["mesh"], lempeng], engine="manifold") for k in ("sensor_dupont", "sensor_pin", "sensor_header")]
jejak = [m for m in jejak if len(m.vertices)]
bb = np.vstack([m.bounds for m in jejak]); JENDELA = [bb[:, 0].min() - 1.0, bb[:, 0].max() + 1.0, bb[:, 1].min() - 1.0, bb[:, 1].max() + 1.0]
JENDELA = [math.floor(JENDELA[0] * 2) / 2, math.ceil(JENDELA[1] * 2) / 2, math.floor(JENDELA[2] * 2) / 2, math.ceil(JENDELA[3] * 2) / 2]

# ---- kotak kepala
tambah("kepala_lantai", kurang(kotak(0, W, 0, W, Hc, Hc + t), kotak(JENDELA[0], JENDELA[1], JENDELA[2], JENDELA[3], Hc - 1, Hc + t + 1)),
       "atas", PVC_ATAS, "Lantai kepala (berjendela kabel)")
zk0, zk1 = Hc + t, Z_ATAS
# colokan micro-USB ESP32 (dibalik): pusat colokan
usb_z = zk0 + ESP["busa"] + 1.4
usb_y = ESP["y0"]
tambah("kepala_depan", kotak(0, t, 0, W, zk0, zk1), "atas", PVC_ATAS, "Dinding depan kepala")
tambah("kepala_belakang", kotak(W - t, W, 0, W, zk0, zk1), "atas", PVC_ATAS, "Dinding belakang kepala")
ex = ESP["x0"] + ESP["W"] / 2
tambah("kepala_kiri", kurang(kotak(t, W - t, 0, t, zk0, zk1), kotak(ex - 6.5, ex + 6.5, -1, t + 1, zk0 - 1, zk0 + 10)),
       "atas", PVC_ATAS, "Dinding kiri kepala (takik USB)")
tambah("kepala_kanan", kotak(t, W - t, W - t, W, zk0, zk1), "atas", PVC_ATAS, "Dinding kanan kepala")
ow = (OLED["cx"] - 12.5, OLED["cx"] + 12.5, OLED["cy"] - 7.5, OLED["cy"] + 7.5)   # jendela tampil 25 x 15
tp = kurang(kotak(0, W, 0, W, Z_ATAS, Z_ATAS + t), kotak(ow[0], ow[1], ow[2], ow[3], Z_ATAS - 1, Z_ATAS + t + 1),
            *[silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], Z_ATAS - 1, Z_ATAS + t + 1, 1.1, 16) for sx in (-1, 1) for sy in (-1, 1)])
tambah("kepala_tutup", tp, "atas", PVC_ATAS, "Tutup atas (jendela OLED)", alpha=0.45)
bib = [kotak(t, 2 * t, t + 0.3, W - t - 0.3, Z_ATAS - 6, Z_ATAS), kotak(W - 2 * t, W - t, t + 0.3, W - t - 0.3, Z_ATAS - 6, Z_ATAS),
       kotak(2 * t, W - 2 * t, t + 0.3, 2 * t + 0.3, Z_ATAS - 6, Z_ATAS), kotak(2 * t, W - 2 * t, W - 2 * t - 0.3, W - t - 0.3, Z_ATAS - 6, Z_ATAS)]
tambah("kepala_bibir", trimesh.util.concatenate(bib), "atas", PVC_ATAS, "Bibir tutup atas", alpha=0.45)

# ---- ESP32 DOIT V1, dibalik (modul ke bawah, pin ke atas) di atas busa
e0x, e0y, ez = ESP["x0"], ESP["y0"], zk0 + ESP["busa"]
tambah("esp_busa", kotak(e0x + 4, e0x + ESP["W"] - 4, e0y + 14, e0y + ESP["L"] - 2, zk0, ez), "atas", "#7b7f86", "Busa dobel tape 3 mm", "busa")
z_pcb0 = ez + ESP["modul"][2]
mod = kotak(e0x + (ESP["W"] - ESP["modul"][1]) / 2, e0x + (ESP["W"] + ESP["modul"][1]) / 2, e0y + ESP["L"] - ESP["modul"][0] - 0.5, e0y + ESP["L"] - 0.5, ez, z_pcb0)
tambah("esp_modul", mod, "atas", "#a7adb4", "Modul WROOM-32 (logam)", "logam")
tambah("esp_pcb", kotak(e0x, e0x + ESP["W"], e0y, e0y + ESP["L"], z_pcb0, z_pcb0 + ESP["pcb"]), "atas", "#1f6f43", "ESP32 DOIT DevKit V1", "pcb_hijau")
tambah("esp_usb", kotak(ex - 3.75, ex + 3.75, e0y - 1.0, e0y + 4.6, z_pcb0 - 2.7, z_pcb0), "atas", "#c0c4c9", "Colokan micro-USB", "logam")
zp = z_pcb0 + ESP["pcb"]
nn = 15; py0 = e0y + (ESP["L"] - (nn - 1) * 2.54) / 2 - 1.0
baris = [e0x + (ESP["W"] - ESP["pin_jarak_baris"]) / 2, e0x + (ESP["W"] + ESP["pin_jarak_baris"]) / 2]
tambah("esp_header", trimesh.util.concatenate([kotak(bx - 1.27, bx + 1.27, py0 - 1.27, py0 + (nn - 1) * 2.54 + 1.27, zp, zp + ESP["plastik"]) for bx in baris]),
       "atas", "#151515", "Header ESP32 (2 x 15)", "plastik_hitam")
tambah("esp_pin", trimesh.util.concatenate([kotak(bx - 0.32, bx + 0.32, py0 + i * 2.54 - 0.32, py0 + i * 2.54 + 0.32, zp - 1, zp + ESP["pin_panjang"]) for bx in baris for i in range(nn)]),
       "atas", "#d4af37", "Pin ESP32", "emas")
# nama pin DOIT 30 pin. Baris dengan 3V3 berurutan dari ujung USB: 3V3 GND D15 D2 D4 RX2 TX2 D5 D18 D19 D21 RX0 TX0 D22 D23
# baris seberang dari ujung USB: VIN GND D13 D12 D14 D27 D26 D25 D33 D32 D35 D34 VN VP EN.
# Papan dibalik, jadi baris 3V3 jatuh di sisi x besar (baris[1]) bila dilihat dari atas. [UKUR: cocokkan tulisan di papan]
B1 = ["3V3", "GND", "D15", "D2", "D4", "RX2", "TX2", "D5", "D18", "D19", "D21", "RX0", "TX0", "D22", "D23"]
B0 = ["VIN", "GND", "D13", "D12", "D14", "D27", "D26", "D25", "D33", "D32", "D35", "D34", "VN", "VP", "EN"]
def pin_esp(nama, baris_ke):
    i = (B1 if baris_ke == 1 else B0).index(nama); return np.array([baris[baris_ke], py0 + i * 2.54, zp + ESP["plastik"]])
ESP_DIPAKAI = {("3V3", 1): "#e0245e", ("GND", 1): "#2b2b2b", ("D21", 1): "#e67e22", ("D22", 1): "#8e44ad", ("D26", 0): "#2e8b57"}
tambah("esp_dupont", trimesh.util.concatenate([kotak(*(pin_esp(n, b)[:1] + [-1.25, 1.25]), *(pin_esp(n, b)[1:2] + [-1.25, 1.25]), zp + ESP["plastik"], zp + ESP["plastik"] + 14) for (n, b) in ESP_DIPAKAI]),
       "atas", "#202020", "Soket dupont ESP32 (5)", "plastik_hitam")

# ---- OLED di sisi bawah tutup atas, layar menghadap jendela
oz1 = Z_ATAS; oz0 = oz1 - OLED["kaca"][2]
tambah("oled_kaca", kotak(OLED["cx"] - OLED["kaca"][0] / 2, OLED["cx"] + OLED["kaca"][0] / 2, OLED["cy"] - OLED["kaca"][1] / 2, OLED["cy"] + OLED["kaca"][1] / 2, oz0, oz1),
       "atas", "#0a0f1e", "Layar OLED 0,96 inci", "kaca")
op = kurang(kotak(OLED["cx"] - OLED["L"] / 2, OLED["cx"] + OLED["L"] / 2, OLED["cy"] - OLED["H"] / 2, OLED["cy"] + OLED["H"] / 2, oz0 - OLED["pcb"], oz0),
            *[silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], oz0 - 5, oz0 + 1, 1.0, 16) for sx in (-1, 1) for sy in (-1, 1)])
tambah("oled_pcb", op, "atas", "#1d4f9c", "Papan OLED SSD1306", "pcb_biru")
oy_pin = OLED["cy"] - OLED["H"] / 2 + 1.6
OLED_PIN = {"GND": OLED["cx"] - 3.81, "VCC": OLED["cx"] - 1.27, "SCL": OLED["cx"] + 1.27, "SDA": OLED["cx"] + 3.81}
zo = oz0 - OLED["pcb"]
tambah("oled_header", kotak(OLED["cx"] - 5.08, OLED["cx"] + 5.08, oy_pin - 1.27, oy_pin + 1.27, zo - 2.5, zo), "atas", "#151515", "Header OLED (4)", "plastik_hitam")
tambah("oled_dupont", trimesh.util.concatenate([kotak(x - 1.25, x + 1.25, oy_pin - 1.25, oy_pin + 1.25, zo - 2.5 - 14, zo - 2.5) for x in OLED_PIN.values()]),
       "atas", "#202020", "Soket dupont OLED (4)", "plastik_hitam")
tambah("oled_baut", gabung([silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], zo - 6.5, Z_ATAS + t + 1.2, 0.95, 12) for sx in (-1, 1) for sy in (-1, 1)]
                                         + [silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], Z_ATAS + t, Z_ATAS + t + 1.2, 1.8, 16) for sx in (-1, 1) for sy in (-1, 1)]
                                         + [silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], oz0 - OLED["pcb"] - 4.0, oz0 - OLED["pcb"], 0.95 + 1.1, 16) for sx in (-1, 1) for sy in (-1, 1)]),
       "atas", "#1c1c1c", "Baut M2 x 12 + ganjal 4 mm", "baja_hitam")

# ---- engsel (2 buah, 25 mm) dan kait depan
ax, az = SUMBU_ENGSEL
eng_b, eng_a = [], []
for yc in (22.0, W - 22.0):
    eng_b.append(kotak(W, W + 1.0, yc - 12.5, yc + 12.5, az - 14, az - 1.0))
    eng_a.append(kotak(W, W + 1.0, yc - 12.5, yc + 12.5, az + 1.0, az + 14))
    knuckle = trimesh.creation.cylinder(radius=2.0, height=25, sections=24); knuckle.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0])); knuckle.apply_translation([ax, yc, az])
    eng_b.append(knuckle)
tambah("engsel_bawah", gabung(eng_b), "bawah", "#9a9ea5", "Engsel 25 mm (daun bawah + poros)", "logam")
tambah("engsel_atas", trimesh.util.concatenate(eng_a), "atas", "#9a9ea5", "Engsel 25 mm (daun atas)", "logam")
tambah("kait_bawah", gabung([kotak(-1.2, 0, YC - 9, YC + 9, Hc - 14, Hc - 2), kotak(-4.2, -1.2, YC - 5, YC + 5, Hc - 9, Hc - 6)]), "bawah", "#9a9ea5", "Kait kotak (pengait)", "logam")
tambah("kait_atas", gabung([kotak(-1.2, 0, YC - 9, YC + 9, Hc + 2, Hc + 12), kotak(-5.5, -1.2, YC - 6, YC + 6, Hc + 6, Hc + 8),
                                               kotak(-5.5, -1.5, YC - 6, YC + 6, Hc - 11.5, Hc - 9.2), kotak(-5.5, -4.4, YC - 6, YC + 6, Hc - 11.5, Hc + 6)]), "atas", "#9a9ea5", "Kait kotak (tuas)", "logam")

# ---- kabel (skematis): sensor -> ESP32, OLED -> ESP32
ujung_sensor = {n: papan(x, hy, -TCS["pcb"] - 2.5 - 14.0) for x, n in zip(xs_pin, TCS["pin"])}
KE_ESP = {"VIN": ("3V3", 1), "GND": ("GND", 1), "SDA": ("D21", 1), "SCL": ("D22", 1), "LED": ("D26", 0)}
kabel = {}
for i, (n, (pn, b)) in enumerate(KE_ESP.items()):
    s0 = ujung_sensor[n]; e = pin_esp(pn, b) + [0, 0, 14]
    kabel[f"kabel_s_{n}"] = [s0, s0 + 3 * (-N), [s0[0] + 3, s0[1], zk0 + 14 + i * 1.6], [e[0] + 8, e[1], zk0 + 26 + i * 1.6], e + [0, 0, 4], e]
OLED_KE = {"VCC": ("3V3", 1), "GND": ("GND", 1), "SDA": ("D21", 1), "SCL": ("D22", 1)}
for i, (n, (pn, b)) in enumerate(OLED_KE.items()):
    s0 = np.array([OLED_PIN[n], oy_pin, zo - 16.5]); e = pin_esp(pn, b) + [0, 0, 14]
    kabel[f"kabel_o_{n}"] = [s0, s0 - [0, 0, 3], [s0[0] - 4, s0[1] - 6, zk0 + 30 - i * 1.6], [e[0] + 6, e[1] + 3, zk0 + 30 - i * 1.6], e + [0, 0, 5], e]
WARNA_KABEL = {"VIN": "#e0245e", "VCC": "#e0245e", "GND": "#2b2b2b", "SDA": "#e67e22", "SCL": "#8e44ad", "LED": "#2e8b57"}
for k, tt in kabel.items():
    tambah(k, pipa(tt), "atas", WARNA_KABEL[k.split("_")[-1]], "Kabel " + k.split("_")[-1], "kabel")

# ---- tatakan kalibrasi (disimpan di samping alat)
tambah("kal_putih", trimesh.util.concatenate([kotak(W + 20, W + 80, 0, 60, zb0, zb0 + 9), kotak(W + 20, W + 80, 0, 60, zb0 + 9, zb0 + 10)]), "aksesori", "#f7f7f2", "Balok kalibrasi putih", "kertas_putih")
tambah("kal_hitam", trimesh.util.concatenate([kotak(W + 20, W + 80, 70, 130, zb0, zb0 + 9), kotak(W + 20, W + 80, 70, 130, zb0 + 9, zb0 + 10)]), "aksesori", "#111111", "Balok kalibrasi hitam", "beludru")


# ----------------------------------------------------------------------------- pemeriksaan
def potong_vol(m1, m2):
    if not np.all(m1.bounds[0] < m2.bounds[1] - 1e-6) or not np.all(m2.bounds[0] < m1.bounds[1] - 1e-6): return 0.0
    try: return float(trimesh.boolean.intersection([m1, m2], engine="manifold").volume)
    except Exception: return -1.0


def periksa(sudut=0.0, keluaran=True):
    M = {}
    Rm = rotation_matrix(math.radians(sudut), [0, 1, 0], point=[ax, 0, az])
    for k, b in B.items():
        if b["grup"] == "aksesori": continue
        m = b["mesh"].copy()
        if b["grup"] == "atas" and sudut: m.apply_transform(Rm)
        M[k] = m
    boleh = {frozenset(p) for p in [("sensor_pin", "sensor_header"), ("sensor_pin", "sensor_pcb"), ("sensor_pin", "sensor_dupont"), ("esp_pin", "esp_header"),
             ("esp_pin", "esp_pcb"), ("esp_pin", "esp_dupont"), ("sensor_baut", "sensor_pcb"), ("sensor_baut", "dudukan_pelat"), ("oled_baut", "oled_pcb"),
             ("oled_baut", "kepala_tutup"), ("engsel_bawah", "engsel_atas"), ("tutup_cat", "beludru"), ("esp_usb", "esp_pcb")]}
    masalah = []
    ks = list(M)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a_, b_ = ks[i], ks[j]
            if frozenset((a_, b_)) in boleh: continue
            if a_.startswith("kabel") and (b_.startswith("kabel") or "dupont" in b_ or "pin" in b_): continue
            if b_.startswith("kabel") and (a_.startswith("kabel") or "dupont" in a_ or "pin" in a_): continue
            v = potong_vol(M[a_], M[b_])
            if v > 0.05 or v == -1.0: masalah.append((a_, b_, round(v, 2)))
    if keluaran:
        print(f"  sudut buka {sudut:5.1f} derajat: {'tidak ada tabrakan' if not masalah else masalah}")
    return masalah


def kilap():
    Lc = LED_W * np.array([1, 1, -1]); tt_ = CHIP[2] / (CHIP[2] + LED_W[2]); Pk = CHIP + tt_ * (Lc - CHIP)
    return float(math.hypot(Pk[0] - XC, Pk[1] - YC) - rl), Pk


if __name__ == "__main__":
    sisa, Pk = kilap()
    print(f"chip di ({CHIP[0]:.2f}, {CHIP[1]:.2f}, {CHIP[2]:.2f}), LED ({LED_W[0]:.2f}, {LED_W[1]:.2f}, {LED_W[2]:.2f})")
    print(f"titik kilap ({Pk[0]:.2f}, {Pk[1]:.2f}) -> {sisa:+.2f} mm di luar tepi lubang")
    print(f"jendela kabel lantai kepala: x {JENDELA[0]}..{JENDELA[1]}, y {JENDELA[2]}..{JENDELA[3]} ({JENDELA[1]-JENDELA[0]} x {JENDELA[3]-JENDELA[2]} mm)")
    zmax_papan = max(B[k]["mesh"].bounds[1][2] for k in ("sensor_pcb", "dudukan_pelat"))
    zmin_ruang = min(B[k]["mesh"].bounds[0][2] for k in ("sensor_pcb", "dudukan_pelat", "sensor_baut", "sensor_led", "sensor_chip"))
    print(f"papan + pelat: z {zmin_ruang:.2f} .. {zmax_papan:.2f} (lantai kepala di z {Hc}); pipi x {PIPI_POLI[0][0]:.2f}..{PIPI_POLI[1][0]:.2f}, tinggi {Hc-PIPI_POLI[0][1]:.2f} dan {Hc-PIPI_POLI[1][1]:.2f}")
    # pipi tidak boleh menutupi jendela
    for bx0, bx1 in PIPI_BX:
        y0, y1 = sorted([papan(bx0, 0, 0)[1], papan(bx1, 0, 0)[1]])
        tumpang = sbox(PIPI_POLI[0][0], y0, PIPI_POLI[1][0], y1).intersection(sbox(JENDELA[0], JENDELA[2], JENDELA[1], JENDELA[3])).area
        print(f"  pipi y {y0:.2f}..{y1:.2f}: tumpang dengan jendela {tumpang:.2f} mm2")
    # semua bagian ruang ukur harus di dalam tutup cat
    for k in ("sensor_pcb", "dudukan_pelat", "dudukan_pipi", "sensor_baut"):
        v = B[k]["mesh"].vertices; r_ = np.hypot(v[:, 0] - XC, v[:, 1] - YC).max()
        print(f"  {k}: jari-jari terjauh {r_:.2f} (dinding dalam {Ri - lap:.2f})")
    print("tabrakan:")
    for sd in (0, 5, 10, 15, 20, 30, 45, 60, 90, 105): periksa(sd)
    berat = {}
    for k, b in B.items():
        if b["grup"] == "aksesori": continue
        if b["bahan"] == "pvc": berat.setdefault("PVC", 0); berat["PVC"] += b["mesh"].volume
    print(f"volume PVC {berat['PVC']/1000:.1f} cm3 -> {berat['PVC']/1000*0.55:.0f} g (PVC busa 0,55) atau {berat['PVC']/1000*1.4:.0f} g (PVC padat 1,4)")
    bb_ = np.vstack([B[k]["mesh"].bounds for k in B if B[k]["grup"] != "aksesori"])
    print(f"ukuran tertutup: {bb_[:,0].max()-bb_[:,0].min():.1f} x {bb_[:,1].max()-bb_[:,1].min():.1f} x {bb_[:,2].max()-bb_[:,2].min():.1f} mm")

    # ---- ekspor: GLB (meter, Y ke atas) dan data bagian
    sc = trimesh.Scene()
    for k, b in B.items():
        m = b["mesh"].copy(); m.visual.face_colors = [int(b["warna"][i:i + 2], 16) for i in (1, 3, 5)] + [255]
        sc.add_geometry(m, node_name=k, geom_name=k)
    g = sc.copy(); g.apply_transform(rotation_matrix(-math.pi / 2, [1, 0, 0])); g.apply_scale(0.001)
    g.export(os.path.join(OUT, "jepit.glb"))
    info = dict(P=P, sumbu_engsel=SUMBU_ENGSEL, jendela=JENDELA, chip=CHIP.tolist(), led=LED_W.tolist(), kilap_sisa=sisa,
                pipi=PIPI_POLI, pipi_y=[sorted([papan(b0, 0, 0)[1], papan(b1, 0, 0)[1]]) for b0, b1 in PIPI_BX],
                bagian={k: dict(grup=b["grup"], warna=b["warna"], nama=b["nama"], bahan=b["bahan"], alpha=b["alpha"],
                                bounds=np.round(b["mesh"].bounds, 2).tolist()) for k, b in B.items()})
    json.dump(info, open(os.path.join(OUT, "bagian.json"), "w"), indent=1, ensure_ascii=False)

    # ---- katalog komponen: tiap kelompok diletakkan mendatar di kisi, untuk render "setiap komponen"
    KAT = [("Baki bawah", ["baki_lantai", "baki_depan", "baki_belakang", "baki_kiri", "baki_kanan"], None),
           ("Busa 3 lapis", ["busa_1", "busa_2", "busa_3"], None),
           ("Tutup cat + beludru", ["tutup_cat", "beludru"], None),
           ("Dudukan sensor", ["dudukan_pelat", "dudukan_pipi"], "balik"),
           ("Sensor TCS34725", ["sensor_pcb", "sensor_chip", "sensor_led", "sensor_smd", "sensor_header", "sensor_pin", "sensor_baut"], "papan"),
           ("Lantai kepala", ["kepala_lantai"], None),
           ("Dinding kepala", ["kepala_depan", "kepala_belakang", "kepala_kiri", "kepala_kanan"], None),
           ("Tutup atas", ["kepala_tutup", "kepala_bibir"], "balik"),
           ("ESP32 DevKit V1", ["esp_modul", "esp_pcb", "esp_usb", "esp_header", "esp_pin"], None),
           ("OLED 0,96 inci", ["oled_kaca", "oled_pcb", "oled_header"], "balik"),
           ("Engsel dan kait", ["engsel_bawah", "engsel_atas", "kait_bawah", "kait_atas"], None),
           ("Balok kalibrasi", ["kal_putih", "kal_hitam"], None)]
    inv = np.linalg.inv(M_PAPAN); kolom, sel, baris_ = 4, 125.0, 165.0
    kat = trimesh.Scene(); kinfo = []
    for i, (judul, ks, orient) in enumerate(KAT):
        ms = {k: B[k]["mesh"].copy() for k in ks}
        for m in ms.values():
            if orient == "papan": m.apply_transform(inv)                       # papan mendatar, sisi komponen ke atas
            if orient == "balik": m.apply_transform(rotation_matrix(math.pi, [1, 0, 0]))
        if "kal_hitam" in ms: ms["kal_hitam"].apply_translation([-65.0, -70.0, 0])          # dua balok berdampingan
        for kk_ in ("kait_bawah", "kait_atas"):
            if kk_ in ms: ms[kk_].apply_translation([72.0, 0, 0])                          # kait di samping engsel
        bb = np.vstack([m.bounds for m in ms.values()]); lo, hi = bb.min(0), bb.max(0)
        cx_, cy_ = (i % kolom) * sel, -(i // kolom) * baris_
        geser = np.array([cx_ - (lo[0] + hi[0]) / 2, cy_ - (lo[1] + hi[1]) / 2, -lo[2]])
        for k, m in ms.items():
            m.apply_translation(geser); m.visual.face_colors = [int(B[k]["warna"][j:j + 2], 16) for j in (1, 3, 5)] + [255]
            kat.add_geometry(m, node_name=f"k{i+1:02d}__{k}", geom_name=f"k{i+1:02d}__{k}")
        kinfo.append(dict(no=i + 1, judul=judul, bagian=ks, pusat=[cx_, cy_], ukuran=np.round(hi - lo, 1).tolist(), tinggi=float(hi[2] - lo[2])))
    g = kat.copy(); g.apply_transform(rotation_matrix(-math.pi / 2, [1, 0, 0])); g.apply_scale(0.001); g.export(os.path.join(OUT, "katalog.glb"))
    json.dump(kinfo, open(os.path.join(OUT, "katalog.json"), "w"), indent=1, ensure_ascii=False)
    print(f"ditulis model/katalog.glb: {len(KAT)} kelompok komponen")
    print(f"ditulis model/jepit.glb ({os.path.getsize(os.path.join(OUT, 'jepit.glb'))//1024} KB), {len(B)} bagian")

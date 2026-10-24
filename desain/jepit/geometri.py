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
VARIAN = os.environ.get("JEPIT_VARIAN", "solder")    # "solder" = Model 2, "breadboard" = Model 2B
# breadboard 400 lubang 85 x 55 mm; kedua rel daya dilepas (tidak dipakai) -> 85 x 36 x 8,5. [UKUR bagian tengahnya]
BB = dict(L=85.0, H=36.0, T=8.5, baris=30)
if VARIAN == "breadboard":
    P.update(W=94.0, kepala_dalam=50.0)              # breadboard 85 mm berdiri di dinding belakang kepala
    OUT = os.path.join(HERE, "model_bb"); os.makedirs(OUT, exist_ok=True)
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

# ESP32 NodeMCU-32S 38 pin (Ai-Thinker): baris pin berjarak 0,9 inci. [UKUR: panjang dan lebar papanmu]
ESP = dict(L=51.5, W=25.4, pcb=1.6, x0=6.0, y0=6.0, busa=3.0, modul=(18.0, 25.5, 3.1),
           pin_jarak_baris=22.86, plastik=2.5, pin_panjang=8.5, n=19)
# urutan pin dari ujung USB, seperti tulisan di papan. Baris 3V3 memuat semua pin yang dipakai.
B1 = ["5V", "CMD", "SD3", "SD2", "G13", "GND", "G12", "G14", "G27", "G26", "G25", "G33", "G32", "G35", "G34", "SN", "SP", "EN", "3V3"]
B0 = ["CLK", "SD0", "SD1", "G15", "G2", "G0", "G4", "G16", "G17", "G5", "G18", "G19", "GND", "G21", "RXD", "TXD", "G22", "G23", "GND"]
# rangkaian tim (Oktober 2026): semua kabel di baris 3V3. Sensor VIN ke 3V3 agar SDA/SCL tetap 3,3 V.
KE_SENSOR = {"VIN": "3V3", "GND": "GND", "SDA": "G26", "SCL": "G27", "LED": "G25"}
KE_OLED = {"VCC": "3V3", "GND": "GND", "SDA": "G26", "SCL": "G27"}
SINYAL = {"3V3": "3V3", "GND": "GND", "G26": "SDA", "G27": "SCL", "G25": "LED"}
WARNA_SINYAL = {"3V3": "#d62828", "GND": "#2b2b2b", "SDA": "#e8b00c", "SCL": "#1f6fd1", "LED": "#2e8b57"}
NAMA_WARNA = {"3V3": "merah", "GND": "hitam", "SDA": "kuning", "SCL": "biru", "LED": "hijau"}
SAMB = 14.0          # sambungan solder + selongsong panas Ø 2 x 15 mm, diukur dari plastik header
R_SAMB = 1.1
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
DIPAKAI = {n: WARNA_SINYAL[SINYAL[pe]] for n, pe in KE_SENSOR.items()}
if VARIAN == "solder":
    dup = [silinder(x, hy, -TCS["pcb"] - 2.5 - SAMB, -TCS["pcb"] - 2.5, R_SAMB, 16) for x, n in zip(xs_pin, TCS["pin"]) if n in DIPAKAI]
    tambah("sensor_dupont", lokal(trimesh.util.concatenate(dup)), "atas", "#202020", "Titik solder sensor + selongsong (5)", "plastik_hitam")
else:
    dup = [kotak(x - 1.25, x + 1.25, hy - 1.25, hy + 1.25, -TCS["pcb"] - 2.5 - SAMB, -TCS["pcb"] - 2.5) for x, n in zip(xs_pin, TCS["pin"]) if n in DIPAKAI]
    tambah("sensor_dupont", lokal(trimesh.util.concatenate(dup)), "atas", "#202020", "Soket dupont betina di sensor (5)", "plastik_hitam")
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
if VARIAN == "solder":
    TAKIK = dict(dinding="kiri", x=ex, z0=zk0, z1=zk0 + 10)
    tambah("kepala_kiri", kurang(kotak(t, W - t, 0, t, zk0, zk1), kotak(ex - 6.5, ex + 6.5, -1, t + 1, zk0 - 1, zk0 + 10)),
           "atas", PVC_ATAS, "Dinding kiri kepala (takik USB)")
    tambah("kepala_kanan", kotak(t, W - t, W - t, W, zk0, zk1), "atas", PVC_ATAS, "Dinding kanan kepala")
else:
    # ESP32 tegak di breadboard, colokan USB ke dinding kanan: lubang 13 x 10 di tengah dinding
    _bx0 = W - t - BB["T"]; _ux = _bx0 - 2.5 - 1.6 - 1.4; _zc = zk0 + BB["H"] / 2; _uz = _zc - 2.54
    TAKIK = dict(dinding="kanan", x=_ux, z0=_uz - 5.0, z1=_uz + 5.0)
    tambah("kepala_kiri", kotak(t, W - t, 0, t, zk0, zk1), "atas", PVC_ATAS, "Dinding kiri kepala")
    tambah("kepala_kanan", kurang(kotak(t, W - t, W - t, W, zk0, zk1), kotak(_ux - 6.5, _ux + 6.5, W - t - 1, W + 1, TAKIK["z0"], TAKIK["z1"])),
           "atas", PVC_ATAS, "Dinding kanan kepala (lubang USB)")
ow = (OLED["cx"] - 12.5, OLED["cx"] + 12.5, OLED["cy"] - 7.5, OLED["cy"] + 7.5)   # jendela tampil 25 x 15
tp = kurang(kotak(0, W, 0, W, Z_ATAS, Z_ATAS + t), kotak(ow[0], ow[1], ow[2], ow[3], Z_ATAS - 1, Z_ATAS + t + 1),
            *[silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], Z_ATAS - 1, Z_ATAS + t + 1, 1.1, 16) for sx in (-1, 1) for sy in (-1, 1)])
tambah("kepala_tutup", tp, "atas", PVC_ATAS, "Tutup atas (jendela OLED)", alpha=0.45)
bib = [kotak(t, 2 * t, t + 0.3, W - t - 0.3, Z_ATAS - 6, Z_ATAS), kotak(W - 2 * t, W - t, t + 0.3, W - t - 0.3, Z_ATAS - 6, Z_ATAS),
       kotak(2 * t, W - 2 * t, t + 0.3, 2 * t + 0.3, Z_ATAS - 6, Z_ATAS), kotak(2 * t, W - 2 * t, W - 2 * t - 0.3, W - t - 0.3, Z_ATAS - 6, Z_ATAS)]
tambah("kepala_bibir", trimesh.util.concatenate(bib), "atas", PVC_ATAS, "Bibir tutup atas", alpha=0.45)

if VARIAN == "solder":
    # ---- ESP32 NodeMCU-32S, dibalik (modul ke bawah, pin ke atas) di atas busa
    e0x, e0y, ez = ESP["x0"], ESP["y0"], zk0 + ESP["busa"]
    tambah("esp_busa", kotak(e0x + 4, e0x + ESP["W"] - 4, e0y + 14, e0y + ESP["L"] - 2, zk0, ez), "atas", "#7b7f86", "Busa dobel tape 3 mm", "busa")
    z_pcb0 = ez + ESP["modul"][2]
    mod = kotak(e0x + (ESP["W"] - ESP["modul"][0]) / 2, e0x + (ESP["W"] + ESP["modul"][0]) / 2, e0y + ESP["L"] - ESP["modul"][1] - 0.5, e0y + ESP["L"] - 0.5, ez, z_pcb0)
    tambah("esp_modul", mod, "atas", "#a7adb4", "Modul ESP-32S (logam)", "logam")
    tambah("esp_pcb", kotak(e0x, e0x + ESP["W"], e0y, e0y + ESP["L"], z_pcb0, z_pcb0 + ESP["pcb"]), "atas", "#1d2024", "ESP32 NodeMCU-32S (38 pin)", "pcb_hitam")
    tambah("esp_usb", kotak(ex - 3.75, ex + 3.75, e0y - 1.0, e0y + 4.6, z_pcb0 - 2.7, z_pcb0), "atas", "#c0c4c9", "Colokan micro-USB", "logam")
    zp = z_pcb0 + ESP["pcb"]
    nn = ESP["n"]; py0 = e0y + (ESP["L"] - (nn - 1) * 2.54) / 2 - 1.0
    baris = [e0x + (ESP["W"] - ESP["pin_jarak_baris"]) / 2, e0x + (ESP["W"] + ESP["pin_jarak_baris"]) / 2]
    tambah("esp_header", trimesh.util.concatenate([kotak(bx - 1.27, bx + 1.27, py0 - 1.27, py0 + (nn - 1) * 2.54 + 1.27, zp, zp + ESP["plastik"]) for bx in baris]),
           "atas", "#151515", "Header ESP32 (2 x 19)", "plastik_hitam")
    tambah("esp_pin", trimesh.util.concatenate([kotak(bx - 0.32, bx + 0.32, py0 + i * 2.54 - 0.32, py0 + i * 2.54 + 0.32, zp - 1, zp + ESP["pin_panjang"]) for bx in baris for i in range(nn)]),
           "atas", "#d4af37", "Pin ESP32", "emas")
    # Papan dibalik, jadi baris 3V3 (B1) jatuh di sisi x besar (baris[1]) bila dilihat dari atas. [UKUR: cocokkan tulisan di papan]
    def pin_esp(nama, baris_ke):
        i = (B1 if baris_ke == 1 else B0).index(nama); return np.array([baris[baris_ke], py0 + i * 2.54, zp + ESP["plastik"]])
    ESP_DIPAKAI = {(pe, 1): WARNA_SINYAL[SINYAL[pe]] for pe in dict.fromkeys(list(KE_SENSOR.values()) + list(KE_OLED.values()))}
    tambah("esp_dupont", trimesh.util.concatenate([silinder(*pin_esp(n, b)[:2], zp + ESP["plastik"], zp + ESP["plastik"] + SAMB, R_SAMB, 16) for (n, b) in ESP_DIPAKAI]),
           "atas", "#202020", f"Titik solder ESP32 + selongsong ({len(ESP_DIPAKAI)})", "plastik_hitam")

else:
    # ---- breadboard di dinding belakang kepala, ESP32 dicolok tegak (sisi komponen menghadap ke depan)
    bx1 = W - t; bx0 = bx1 - BB["T"]; by0 = W - t - 0.5 - BB["L"]; bz0, bz1 = zk0, zk0 + BB["H"]
    tambah("bb_papan", kotak(bx0, bx1, by0, by0 + BB["L"], bz0, bz1), "atas", "#efebe4", "Breadboard 400 lubang (rel daya dilepas)", "plastik_putih")
    BARIS_BB = lambda r: by0 + (BB["L"] - (BB["baris"] - 1) * 2.54) / 2 + (r - 1) * 2.54
    zc_bb = (bz0 + bz1) / 2
    KOLOM_BB = {c: zc_bb + 3.81 + 2.54 * k for k, c in enumerate("edcba")}
    KOLOM_BB.update({c: zc_bb - 3.81 - 2.54 * m for m, c in enumerate("fghij")})
    KOL_ESP = {1: "c", 0: "j"}                       # baris 3V3 di kolom c: kolom b dan a bebas untuk kabel
    nn = ESP["n"]; R_ESP0 = BB["baris"]               # pin ke-0 (5V, ujung USB) di baris 30, dekat dinding kanan
    def baris_pin(i): return R_ESP0 - i
    def pin_esp(nama, baris_ke):
        i = (B1 if baris_ke == 1 else B0).index(nama); return np.array([bx0 - 2.5, BARIS_BB(baris_pin(i)), KOLOM_BB[KOL_ESP[baris_ke]]])
    ph = bx0 - 2.5; pp0, pp1 = ph - ESP["pcb"], ph                       # plastik header di muka breadboard, lalu PCB
    yU = BARIS_BB(baris_pin(0)) + (G_PY0 := (ESP["L"] - (nn - 1) * 2.54) / 2 - 1.0)   # tepi papan di ujung USB
    yA = yU - ESP["L"]
    zB0, zB1 = KOLOM_BB["j"], KOLOM_BB["c"]; zpm = (zB0 + zB1) / 2
    tambah("esp_pcb", kotak(pp0, pp1, yA, yU, zpm - ESP["W"] / 2, zpm + ESP["W"] / 2), "atas", "#1d2024", "ESP32 NodeMCU-32S (38 pin)", "pcb_hitam")
    tambah("esp_modul", kotak(pp0 - ESP["modul"][2], pp0, yA + 0.5, yA + 0.5 + ESP["modul"][1], zpm - ESP["modul"][0] / 2, zpm + ESP["modul"][0] / 2), "atas", "#a7adb4", "Modul ESP-32S (logam)", "logam")
    tambah("esp_usb", kotak(pp0 - 2.7, pp0, yU - 4.6, yU + 1.0, zpm - 3.75, zpm + 3.75), "atas", "#c0c4c9", "Colokan micro-USB", "logam")
    tambah("esp_header", trimesh.util.concatenate([kotak(ph, bx0, BARIS_BB(baris_pin(nn - 1)) - 1.27, BARIS_BB(baris_pin(0)) + 1.27, z_ - 1.27, z_ + 1.27) for z_ in (zB0, zB1)]),
           "atas", "#151515", "Header ESP32 (2 x 19)", "plastik_hitam")
    tambah("esp_pin", trimesh.util.concatenate([kotak(pp0 - 1.0, bx0 + 6.0, BARIS_BB(baris_pin(i)) - 0.32, BARIS_BB(baris_pin(i)) + 0.32, z_ - 0.32, z_ + 0.32) for z_ in (zB0, zB1) for i in range(nn)]),
           "atas", "#d4af37", "Pin ESP32 (masuk breadboard)", "emas")
    ESP_DIPAKAI = {(pe, 1): WARNA_SINYAL[SINYAL[pe]] for pe in dict.fromkeys(list(KE_SENSOR.values()) + list(KE_OLED.values()))}
    # lubang kabel: sensor di kolom b, OLED di kolom a, sebaris dengan pin ESP32-nya
    def lubang(pe, dev): return (baris_pin(B1.index(pe)), "b" if dev == "Sensor" else "a")
    DUP_L = 14.0
    def ujung_bb(pe, dev):
        r, c = lubang(pe, dev); return np.array([bx0 - DUP_L, BARIS_BB(r), KOLOM_BB[c]])
    _dup = [(pe, "Sensor") for pe in KE_SENSOR.values()] + [(pe, "OLED") for pe in KE_OLED.values()]
    tambah("esp_dupont", trimesh.util.concatenate([kotak(bx0 - DUP_L, bx0, ujung_bb(pe, d)[1] - 1.2, ujung_bb(pe, d)[1] + 1.2, ujung_bb(pe, d)[2] - 1.2, ujung_bb(pe, d)[2] + 1.2) for pe, d in _dup]),
           "atas", "#202020", f"Kabel dupont jantan di breadboard ({len(_dup)})", "plastik_hitam")
    zp = ph

# ---- OLED di sisi bawah tutup atas, layar menghadap jendela
GANJAL_OLED = 1.6                                   # mur M2 sebagai ganjal antara tutup dan PCB OLED
oz0 = Z_ATAS - GANJAL_OLED; oz1 = oz0 + OLED["kaca"][2]
tambah("oled_kaca", kotak(OLED["cx"] - OLED["kaca"][0] / 2, OLED["cx"] + OLED["kaca"][0] / 2, OLED["cy"] - OLED["kaca"][1] / 2, OLED["cy"] + OLED["kaca"][1] / 2, oz0, oz1),
       "atas", "#0a0f1e", "Layar OLED 0,96 inci", "kaca")
op = kurang(kotak(OLED["cx"] - OLED["L"] / 2, OLED["cx"] + OLED["L"] / 2, OLED["cy"] - OLED["H"] / 2, OLED["cy"] + OLED["H"] / 2, oz0 - OLED["pcb"], oz0),
            *[silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], oz0 - 5, oz0 + 1, 1.0, 16) for sx in (-1, 1) for sy in (-1, 1)])
tambah("oled_pcb", op, "atas", "#1d4f9c", "Papan OLED SSD1306", "pcb_biru")
oy_pin = OLED["cy"] - OLED["H"] / 2 + 1.6
OLED_PIN = {"GND": OLED["cx"] - 3.81, "VCC": OLED["cx"] - 1.27, "SCL": OLED["cx"] + 1.27, "SDA": OLED["cx"] + 3.81}
zo = oz0 - OLED["pcb"]
tambah("oled_header", kotak(OLED["cx"] - 5.08, OLED["cx"] + 5.08, oy_pin - 1.27, oy_pin + 1.27, zo - 2.5, zo), "atas", "#151515", "Header OLED (4)", "plastik_hitam")
if VARIAN == "solder":
    tambah("oled_dupont", trimesh.util.concatenate([silinder(x, oy_pin, zo - 2.5 - SAMB, zo - 2.5, R_SAMB, 16) for x in OLED_PIN.values()]),
           "atas", "#202020", "Titik solder OLED + selongsong (4)", "plastik_hitam")
else:
    tambah("oled_dupont", trimesh.util.concatenate([kotak(x - 1.25, x + 1.25, oy_pin - 1.25, oy_pin + 1.25, zo - 2.5 - SAMB, zo - 2.5) for x in OLED_PIN.values()]),
           "atas", "#202020", "Soket dupont betina di OLED (4)", "plastik_hitam")
tambah("oled_baut", gabung([silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], zo - 3.0, Z_ATAS + t + 1.2, 0.95, 12) for sx in (-1, 1) for sy in (-1, 1)]
                                         + [silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], Z_ATAS + t, Z_ATAS + t + 1.2, 1.8, 16) for sx in (-1, 1) for sy in (-1, 1)]
                                         + [silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], oz0, Z_ATAS, 2.0, 6) for sx in (-1, 1) for sy in (-1, 1)]
                                         + [silinder(OLED["cx"] + sx * OLED["lubang"], OLED["cy"] + sy * OLED["lubang"], zo - 1.6, zo, 2.0, 6) for sx in (-1, 1) for sy in (-1, 1)]),
       "atas", "#1c1c1c", "Baut M2 x 10 + mur ganjal + mur pengunci", "baja_hitam")

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

# ---- kabel: disolder langsung. Pin ESP32 yang dipakai dua perangkat (3V3, GND, G26, G27) menerima DUA kabel di satu pin.
# Jalur Manhattan: tiap kabel punya ketinggian mendatar (lapis) dan lajur x sendiri, jadi tidak ada kabel yang saling memotong.
ujung_sensor = {n: papan(x, hy, -TCS["pcb"] - 2.5 - SAMB) for x, n in zip(xs_pin, TCS["pin"])}
if VARIAN == "solder":
    Z_SOKET_ESP = zp + ESP["plastik"] + SAMB                # ujung selongsong di pin ESP32
    Z_J = Z_SOKET_ESP + 0.8
    # sensor: (lapis z, lajur x); OLED: (lapis z, lajur x). Urutan lapis OLED: SDA paling bawah, GND paling atas.
    SENSOR_KE = {n: ((pe, 1), L_, x_) for (n, pe), L_, x_ in zip(KE_SENSOR.items(), (57.8, 56.1, 54.4, 52.7, 51.0), (46.8, 45.1, 43.4, 41.7, 40.0))}
    OLED_KE = {n: ((pe, 1), L_, x_) for (n, pe), L_, x_ in zip(KE_OLED.items(), (41.3, 43.0, 37.9, 39.6), (38.1, 36.4, 33.0, 34.7))}
else:
    Z_SOKET_ESP = Z_J = None
    # sensor: (lapis z, lajur x); OLED: (lapis z, lajur x). Lapis OLED naik SDA < SCL < VCC < GND.
    SENSOR_KE = {n: ((pe, 1), L_, x_) for (n, pe), L_, x_ in zip(KE_SENSOR.items(), (37.0, 38.7, 40.4, 42.1, 43.8), (53.0, 54.7, 56.4, 58.1, 59.8))}
    OLED_KE = {n: ((pe, 1), L_, x_) for (n, pe), L_, x_ in zip(KE_OLED.items(), (49.4, 51.1, 46.0, 47.7), (47.7, 46.0, 51.1, 49.4))}
CABANG = {pe: (next(n for n, q in KE_SENSOR.items() if q == pe), next(n for n, q in KE_OLED.items() if q == pe))
          for pe in KE_OLED.values() if pe in KE_SENSOR.values()}     # pin ESP32 -> (pin sensor, pin OLED)


def fillet(P_, r=2.0, n=6):
    P_ = [np.array(p, float) for p in P_]; out = [P_[0]]
    for i in range(1, len(P_) - 1):
        a_, b_, c__ = P_[i - 1], P_[i], P_[i + 1]
        d1, d2 = b_ - a_, c__ - b_; l1, l2 = np.linalg.norm(d1), np.linalg.norm(d2)
        if l1 < 1e-6 or l2 < 1e-6: continue
        rr = min(r, l1 / 2, l2 / 2); p0, p1 = b_ - d1 / l1 * rr, b_ + d2 / l2 * rr
        for t_ in np.linspace(0, 1, n): out.append((1 - t_) ** 2 * p0 + 2 * (1 - t_) * t_ * b_ + t_ ** 2 * p1)
    out.append(P_[-1]); return np.array(out)


def pipa(titik, r=0.7, n=10):
    pts = np.array(titik, float)
    keep = [0] + [i for i in range(1, len(pts)) if np.linalg.norm(pts[i] - pts[i - 1]) > 1e-4]; pts = pts[keep]
    lingk = Polygon([(r * math.cos(k), r * math.sin(k)) for k in np.linspace(0, 2 * math.pi, n, endpoint=False)])
    return trimesh.creation.sweep_polygon(lingk, pts)


def nama_pin(pn, b=1):
    return pn


KABEL = {}   # nama -> dict(titik, warna, dari, ke (pin ESP32), b, panjang)
SINYAL_PIN = {"VIN": "3V3", "VCC": "3V3", "GND": "GND", "SDA": "SDA", "SCL": "SCL", "LED": "LED"}
if VARIAN == "solder":
    for n, ((pn, b), L_, xc) in SENSOR_KE.items():
        E = ujung_sensor[n]; A = E + 4.0 * (-N); T = pin_esp(pn, b)
        KABEL[f"kabel_s_{n}"] = dict(titik=fillet([E, A, [A[0], A[1], L_], [xc, A[1], L_], [xc, T[1], L_], [xc, T[1], Z_J], [T[0], T[1], Z_J], [T[0], T[1], Z_SOKET_ESP]]),
                                    warna=WARNA_SINYAL[SINYAL[pn]], dari=f"Sensor {n}", ke=pn, b=b)
    for n, ((pn, b), L_, xc) in OLED_KE.items():
        E = np.array([OLED_PIN[n], oy_pin, zo - 2.5 - SAMB]); T = pin_esp(pn, b)
        KABEL[f"kabel_o_{n}"] = dict(titik=fillet([E, [E[0], E[1], L_], [E[0], T[1], L_], [xc, T[1], L_], [xc, T[1], Z_J], [T[0], T[1], Z_J], [T[0], T[1], Z_SOKET_ESP]]),
                                    warna=WARNA_SINYAL[SINYAL[pn]], dari=f"OLED {n}", ke=pn, b=b)
else:
    for n, ((pn, b), L_, xc) in SENSOR_KE.items():
        E = ujung_sensor[n]; A = E + 4.0 * (-N); T = ujung_bb(pn, "Sensor")
        KABEL[f"kabel_s_{n}"] = dict(titik=fillet([E, A, [A[0], A[1], L_], [xc, A[1], L_], [xc, T[1], L_], [xc, T[1], T[2]], T]),
                                    warna=WARNA_SINYAL[SINYAL[pn]], dari=f"Sensor {n}", ke=pn, b=b, lubang=lubang(pn, "Sensor"))
    for n, ((pn, b), L_, xc) in OLED_KE.items():
        E = np.array([OLED_PIN[n], oy_pin, zo - 2.5 - SAMB]); T = ujung_bb(pn, "OLED")
        KABEL[f"kabel_o_{n}"] = dict(titik=fillet([T, [xc, T[1], T[2]], [xc, T[1], L_], [xc, E[1], L_], [E[0], E[1], L_], E])[::-1].copy(),
                                    warna=WARNA_SINYAL[SINYAL[pn]], dari=f"OLED {n}", ke=pn, b=b, lubang=lubang(pn, "OLED"))
for k, kb in KABEL.items():
    kb["panjang"] = float(np.sum(np.linalg.norm(np.diff(kb["titik"], axis=0), axis=1)))
    tambah(k, pipa(kb["titik"]), "atas", kb["warna"], "Kabel " + kb["dari"] + " ke ESP32 " + kb["ke"], "kabel")


def jarak_kabel():
    """Jarak terdekat antar sumbu kabel yang berbeda sinyal (harus >= 1,6 mm untuk kabel Ø 1,4)."""
    from scipy.spatial import cKDTree
    hasil = []
    ks = list(KABEL)
    def padat(P_):
        out = [P_[0]]
        for a_, b_ in zip(P_[:-1], P_[1:]):
            m_ = max(1, int(np.linalg.norm(b_ - a_) / 0.3)); out += [a_ + (b_ - a_) * t_ for t_ in np.linspace(0, 1, m_ + 1)[1:]]
        return np.array(out)
    D = {k: padat(KABEL[k]["titik"]) for k in ks}
    sig = lambda k: SINYAL_PIN.get(k.split("_")[-1], k)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a_, b_ = ks[i], ks[j]
            if sig(a_) == sig(b_): continue          # dua kabel satu sinyal bertemu di pin ESP32 yang sama
            d, _ = cKDTree(D[b_]).query(D[a_]); hasil.append((float(d.min()), a_, b_))
    return sorted(hasil)[:5]


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
             ("oled_baut", "kepala_tutup"), ("engsel_bawah", "engsel_atas"), ("tutup_cat", "beludru"), ("esp_usb", "esp_pcb"),
             ("esp_pin", "bb_papan"), ("esp_dupont", "bb_papan"), ("esp_pin", "esp_modul")]}
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
    print("kabel: jarak terdekat antar kabel beda sinyal", [(round(d, 2), a_, b_) for d, a_, b_ in jarak_kabel()[:3]])
    for k, kb in KABEL.items(): print(f"  {k:16s} {kb['dari']:>12s} -> ESP32 {kb['ke']:<5s} {kb['panjang']:6.1f} mm")
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
           ("ESP32 NodeMCU-32S", ["esp_modul", "esp_pcb", "esp_usb", "esp_header", "esp_pin"], None),
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
    print(f"ditulis {os.path.basename(OUT)}/katalog.glb: {len(KAT)} kelompok komponen")
    print(f"ditulis {os.path.basename(OUT)}/jepit.glb ({os.path.getsize(os.path.join(OUT, 'jepit.glb'))//1024} KB), {len(B)} bagian")

#!/usr/bin/env python3
"""BeefFresh Genggam (desain A versi PVC): kotak ramping dari PVC 3 mm, kepala ukur tabung miring 40 derajat.

Koordinat: X ujung belakang (USB, -) ke ujung depan (kepala ukur, +), Y kiri-kanan, Z ke atas.
Pusat lubang ukur di (0, 0, 0); z = 0 = permukaan daging. Satuan mm.
Jalankan: ../../.venv-cad/bin/python geometri_a.py  -> model/genggam.glb, model/bagian.json + pemeriksaan
"""
import json, math, os, sys, warnings
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point
from trimesh.transformations import rotation_matrix
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "jepit"))
import geometri as GE                                       # alat bantu dan data papan yang sama dengan desain E
from geometri import kotak, silinder, kurang, gabung, ekstrusi, fillet, pipa, TCS, SMD

OUT = os.path.join(HERE, "model"); os.makedirs(OUT, exist_ok=True)
t = 3.0
A = math.radians(40.0); SA, CA = math.sin(A), math.cos(A)
u = np.array([SA, 0.0, CA])                                 # sumbu tabung, dari lubang ke atas
H_CHIP = 17.0; TUBE_RO, TUBE_RI, S_END = 16.0, 14.0, 24.0; AP_R = 6.0
X0, X1 = -75.5, 32.0                                        # luar kotak
YW = 19.5; YI = YW - t                                      # setengah lebar luar / dalam
X_PAD = -26.0                                               # pelat muka hitam: x X_PAD..X1, z 0..3; lantai belakang naik 2 mm
Z_TOP = 49.0                                                # sisi bawah tutup atas
P = dict(t=t, miring=40, h=H_CHIP, pipa_luar=2 * TUBE_RO, pipa_dalam=2 * TUBE_RI, lubang=2 * AP_R, panjang=X1 - X0, lebar=2 * YW, tinggi=Z_TOP + t)

B = {}
def tambah(k, mesh, warna, nama, bahan="pvc", alpha=1.0):
    B[k] = dict(mesh=mesh, warna=warna, nama=nama, bahan=bahan, alpha=alpha, grup="atas")

def sumbu(m):                                               # benda yang dibuat sepanjang z dipindah ke sumbu tabung
    m = m.copy(); m.apply_transform(rotation_matrix(A, [0, 1, 0])); return m

PVC = "#e4ded4"
# ---------------------------------------------------------------- badan PVC
kerucut = trimesh.creation.cone(radius=14.0, height=14.0, sections=64); kerucut.apply_transform(rotation_matrix(math.pi, [1, 0, 0])); kerucut.apply_translation([0, 0, 9.0])
# lubang Ø 12 di muka, melebar 45 derajat di sisi dalam (Ø 16 di atas) supaya tepi lubang tidak menghalangi pandangan miring
tambah("pelat_muka", kurang(kotak(X_PAD, X1, -YW, YW, 0, t), silinder(0, 0, -1, t + 1, AP_R, 48), kerucut), "#26272b", "Pelat muka hitam (lubang Ø 12, dalam Ø 16)", "pvc_hitam")
tambah("lantai_belakang", kotak(X0, X_PAD, -YW, YW, 2, 5), PVC, "Lantai belakang (naik 2 mm)")
prof = Polygon([(X0, 5), (X_PAD, 5), (X_PAD, t), (X1, t), (X1, Z_TOP), (X0, Z_TOP)])
def dinding_samping(y0, y1):
    m = ekstrusi(prof, y0, y1); m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    if m.volume < 0: m.invert()
    return m
tambah("dinding_kiri", dinding_samping(-YW, -YI), PVC, "Dinding kiri")
tambah("dinding_kanan", dinding_samping(YI, YW), PVC, "Dinding kanan")
tambah("dinding_depan", kotak(X1 - t, X1, -YI, YI, t, Z_TOP), PVC, "Dinding depan")

# ---------------------------------------------------------------- ESP32 dibalik di atas busa (USB ke dinding belakang)
EL, EW = 51.8, 28.2; e0x, e1x = X0 + t + 0.5, X0 + t + 0.5 + EL
z_busa = 5.0; z_mod0 = z_busa + 3.0; z_pcb0 = z_mod0 + 3.1; z_pcb1 = z_pcb0 + 1.6; z_pl = z_pcb1 + 2.5; z_sok = z_pl + 14.0
usb_z0, usb_z1 = z_pcb0 - 2.7, z_pcb0
tambah("dinding_belakang", kurang(kotak(X0, X0 + t, -YI, YI, 5, Z_TOP), kotak(X0 - 1, X0 + t + 1, -6.5, 6.5, 4, usb_z1 + 4)), PVC, "Dinding belakang (takik USB)")
tambah("esp_busa", kotak(e0x + 14, X_PAD - 1, -10, 10, z_busa, z_mod0), "#7b7f86", "Busa dobel tape 3 mm", "busa")
tambah("esp_modul", kotak(e1x - 26.0, e1x - 0.5, -9.0, 9.0, z_mod0, z_pcb0), "#a7adb4", "Modul WROOM-32 (logam)", "logam")
tambah("esp_pcb", kotak(e0x, e1x, -EW / 2, EW / 2, z_pcb0, z_pcb1), "#1f6f43", "ESP32 DOIT DevKit V1", "pcb_hijau")
tambah("esp_usb", kotak(e0x - 1.0, e0x + 4.6, -3.75, 3.75, usb_z0, usb_z1), "#c0c4c9", "Colokan micro-USB", "logam")
px0 = e0x + (EL - 14 * 2.54) / 2 - 1.0
ROW = {1: 12.7, 0: -12.7}                                   # baris 3V3 di kanan (+y), baris VIN di kiri: cocokkan dengan papanmu
def pin_esp(nama, b):
    i = (GE.B1 if b == 1 else GE.B0).index(nama); return np.array([px0 + i * 2.54, ROW[b], z_sok])
tambah("esp_header", trimesh.util.concatenate([kotak(px0 - 1.27, px0 + 14 * 2.54 + 1.27, y - 1.27, y + 1.27, z_pcb1, z_pl) for y in ROW.values()]), "#151515", "Header ESP32 (2 x 15)", "plastik_hitam")
tambah("esp_pin", trimesh.util.concatenate([kotak(px0 + i * 2.54 - .32, px0 + i * 2.54 + .32, y - .32, y + .32, z_pcb0, z_pcb1 + 8.5) for y in ROW.values() for i in range(15)]), "#d4af37", "Pin ESP32", "emas")
ESP_DIPAKAI = [("3V3", 1), ("GND", 1), ("D21", 1), ("D22", 1), ("GND", 0), ("D26", 0)]
tambah("esp_dupont", trimesh.util.concatenate([kotak(p[0] - 1.25, p[0] + 1.25, p[1] - 1.25, p[1] + 1.25, z_pl, z_sok) for p in (pin_esp(n, b) for n, b in ESP_DIPAKAI)]), "#202020", "Soket dupont ESP32 (6)", "plastik_hitam")

# ---------------------------------------------------------------- kepala ukur: pipa 1 inci dipotong miring + papan tegak lurus sumbu
s0 = -30.0
pipa_ = kurang(silinder(0, 0, s0, S_END, TUBE_RO, 72), silinder(0, 0, s0 - 1, S_END + 1, TUBE_RI, 72))
tambah("tabung", kurang(sumbu(pipa_), kotak(-200, 200, -200, 200, -200, t)), "#cfc8bc", "Tabung pipa PVC 1 inci, ujung dipotong 40°", "pvc")
lap = kurang(silinder(0, 0, s0, H_CHIP + 0.5, TUBE_RI - 0.02, 72), silinder(0, 0, s0 - 1, H_CHIP + 1.5, TUBE_RI - 0.6, 72))
tambah("beludru", kurang(sumbu(lap), kotak(-200, 200, -200, 200, -200, t + 0.02)), "#0b0b0d", "Pelapis beludru hitam", "beludru")

Nn = -u; U = np.array([0.0, 1.0, 0.0]); V = np.array([CA, 0.0, -SA])
CHIP = H_CHIP * u
T0 = CHIP - (TCS["chip"][0] * U + TCS["chip"][1] * V + TCS["chip_tebal"] * Nn)
M_PAPAN = np.eye(4); M_PAPAN[:3, 0], M_PAPAN[:3, 1], M_PAPAN[:3, 2], M_PAPAN[:3, 3] = U, V, Nn, T0
def lokal(m): m = m.copy(); m.apply_transform(M_PAPAN); return m
def papan(bx, by, bz): return T0 + bx * U + by * V + bz * Nn
LED_W = papan(TCS["led"][0], TCS["led"][1], TCS["chip_tebal"])
L_, c_ = TCS["L"], TCS["chamfer"]
oct_ = Polygon([(c_, 0), (L_ - c_, 0), (L_, c_), (L_, L_ - c_), (L_ - c_, L_), (c_, L_), (0, L_ - c_), (0, c_)])
for hx, hy in TCS["lubang"]: oct_ = oct_.difference(Point(hx, hy).buffer(TCS["lubang_d"] / 2, 24))
tambah("sensor_pcb", lokal(ekstrusi(oct_, -TCS["pcb"], 0)), "#6a2c91", "Papan sensor TCS34725", "pcb_ungu")
cx_, cy_ = TCS["chip"]
tambah("sensor_chip", lokal(kotak(cx_ - 1, cx_ + 1, cy_ - 1.2, cy_ + 1.2, 0, TCS["chip_tebal"])), "#c9b37a", "Chip TCS34725", "chip")
lx, ly = TCS["led"]
tambah("sensor_led", lokal(kotak(lx - .7, lx + .7, ly - 1.1, ly + 1.1, 0, 1.1)), "#fff4c2", "LED bawaan (putih)", "led")
smd = []
for _, x, y, rot, pk in SMD:
    w, h_, z = (2.0, 1.25, 0.5) if pk == "0805" else (2.9, 1.3, 1.0)
    if rot in (90, 270): w, h_ = h_, w
    smd.append(kotak(x - w / 2, x + w / 2, y - h_ / 2, y + h_ / 2, 0, z))
tambah("sensor_smd", lokal(trimesh.util.concatenate(smd)), "#3a3a3a", "Komponen kecil di papan", "smd")
xs_pin = [TCS["header_x0"] + i * TCS["pitch"] for i in range(7)][::-1]; hy0 = TCS["header_y"]
tambah("sensor_header", lokal(kotak(xs_pin[-1] - 1.27, xs_pin[0] + 1.27, hy0 - 1.27, hy0 + 1.27, -TCS["pcb"] - 2.5, -TCS["pcb"])), "#151515", "Header 7 pin", "plastik_hitam")
tambah("sensor_pin", lokal(trimesh.util.concatenate([kotak(x - .32, x + .32, hy0 - .32, hy0 + .32, -TCS["pcb"] - 8.5, 1.5) for x in xs_pin])), "#d4af37", "Pin header", "emas")
DIPAKAI_S = ["VIN", "GND", "SCL", "SDA", "LED"]
tambah("sensor_dupont", lokal(trimesh.util.concatenate([kotak(x - 1.25, x + 1.25, hy0 - 1.25, hy0 + 1.25, -TCS["pcb"] - 16.5, -TCS["pcb"] - 2.5) for x, n in zip(xs_pin, TCS["pin"]) if n in DIPAKAI_S])), "#202020", "Soket dupont sensor (5)", "plastik_hitam")
# cakram dudukan di punggung papan (lubang header + 2 baut)
ck = silinder(cx_, cy_, -TCS["pcb"] - 3.0, -TCS["pcb"], TUBE_RI - 0.15, 72)          # sepusat sumbu tabung (chip di sumbu)
ck = kurang(ck, kotak(xs_pin[-1] - 1.8, xs_pin[0] + 1.8, hy0 - 1.75, hy0 + 1.75, -10, 5), *[silinder(hx, hy, -10, 5, 1.4, 24) for hx, hy in TCS["lubang"]])
tambah("dudukan_cakram", lokal(ck), "#26272b", "Cakram dudukan Ø 27,7 (PVC hitam)", "pvc_hitam")
baut = []
for hx, hy in TCS["lubang"]:
    baut += [silinder(hx, hy, 0, 1.7, 2.25, 24), silinder(hx, hy, -TCS["pcb"] - 3 - 2.6, 0, 1.2, 16), silinder(hx, hy, -TCS["pcb"] - 3 - 2.0, -TCS["pcb"] - 3, 2.85, 6)]
tambah("sensor_baut", lokal(gabung(baut)), "#1c1c1c", "Baut M2,5 x 10 hitam + mur", "baja_hitam")

# ---------------------------------------------------------------- OLED diputar 90 derajat di sisi bawah tutup atas
OX = 6.0; OH, OL = 27.8, 27.3
oz1 = Z_TOP; oz0 = oz1 - 1.4; zo = oz0 - 1.2
tambah("oled_kaca", kotak(OX - 9.65, OX + 9.65, -13.35, 13.35, oz0, oz1), "#0a0f1e", "Layar OLED 0,96 inci", "kaca")
tambah("oled_pcb", kurang(kotak(OX - OH / 2, OX + OH / 2, -OL / 2, OL / 2, zo, oz0), *[silinder(OX + sx * 11.65, sy * 11.65, zo - 2, oz0 + 1, 1.0, 16) for sx in (-1, 1) for sy in (-1, 1)]), "#1d4f9c", "Papan OLED SSD1306", "pcb_biru")
ox_pin = OX - OH / 2 + 1.6
OLED_PIN = {"GND": -3.81, "VCC": -1.27, "SCL": 1.27, "SDA": 3.81}
tambah("oled_header", kotak(ox_pin - 1.27, ox_pin + 1.27, -5.08, 5.08, zo - 2.5, zo), "#151515", "Header OLED (4)", "plastik_hitam")
tambah("oled_dupont", trimesh.util.concatenate([kotak(ox_pin - 1.25, ox_pin + 1.25, y - 1.25, y + 1.25, zo - 16.5, zo - 2.5) for y in OLED_PIN.values()]), "#202020", "Soket dupont OLED (4)", "plastik_hitam")
tambah("oled_baut", gabung([silinder(OX + sx * 11.65, sy * 11.65, zo - 3.0, Z_TOP + t + 1.2, 0.95, 12) for sx in (-1, 1) for sy in (-1, 1)]
                         + [silinder(OX + sx * 11.65, sy * 11.65, Z_TOP + t, Z_TOP + t + 1.2, 1.8, 16) for sx in (-1, 1) for sy in (-1, 1)]
                         + [silinder(OX + sx * 11.65, sy * 11.65, oz0, Z_TOP, 1.9, 16) for sx in (-1, 1) for sy in (-1, 1)]), "#1c1c1c", "Baut M2 + ring ganjal 1,4", "baja_hitam")
tutup = kurang(kotak(X0, X1, -YW, YW, Z_TOP, Z_TOP + t), kotak(OX - 7.5, OX + 7.5, -12.5, 12.5, Z_TOP - 1, Z_TOP + t + 1),
               *[silinder(OX + sx * 11.65, sy * 11.65, Z_TOP - 1, Z_TOP + t + 1, 1.1, 16) for sx in (-1, 1) for sy in (-1, 1)])
tambah("tutup_atas", tutup, PVC, "Tutup atas (jendela OLED)", "pvc", 0.45)
tambah("tanda_tekan", kurang(silinder(-16, 0, Z_TOP + t, Z_TOP + t + 0.4, 6, 48), silinder(-16, 0, Z_TOP, Z_TOP + t + 1, 4.5, 48)), "#b3262e", "Tanda tempat ibu jari", "cat_merah")
tambah("bibir", trimesh.util.concatenate([kotak(xa, xb, ys, ys + 3.0, Z_TOP - 6, Z_TOP) for xa, xb in ((X0 + t, OX - OH / 2 - 1), (OX + OH / 2 + 1, X1 - t)) for ys in (-YI + 0.3, YI - 3.3)]), PVC, "Bibir tutup (4)", "pvc", 0.45)

# ---------------------------------------------------------------- kabel: lajur mendatar di ketinggian berbeda
ujung_s = {n: papan(x, hy0, -TCS["pcb"] - 16.5) for x, n in zip(xs_pin, TCS["pin"])}
S_KE = {"VIN": ("3V3", 1), "GND": ("GND", 1), "SCL": ("D22", 1), "SDA": ("D21", 1), "LED": ("D26", 0)}
S_LAJUR = {"VIN": (37.8, 7.0), "GND": (39.5, 8.6), "SCL": (41.2, 10.2), "SDA": (42.9, 5.6), "LED": (44.6, -7.5)}   # (z lajur, y lajur)
O_KE = {"VCC": ("3V3", 1), "GND": ("GND", 0), "SDA": ("D21", 1), "SCL": ("D22", 1)}
O_LAJUR = {"GND": (22.5, 31.0), "VCC": (24.2, 32.7), "SCL": (25.9, 34.4), "SDA": (27.6, 36.1)}               # (z bawah, z atas)
WARNA = {"VIN": "#e0245e", "VCC": "#e0245e", "GND": "#2b2b2b", "SDA": "#e67e22", "SCL": "#8e44ad", "LED": "#2e8b57"}
KABEL = {}
for n, (pn, b) in S_KE.items():
    E = ujung_s[n]; Ae = E + 3.0 * u; T = pin_esp(pn, b); zl, yl = S_LAJUR[n]
    KABEL["kabel_s_" + n] = dict(titik=fillet([E, Ae, [Ae[0], Ae[1], zl], [Ae[0], yl, zl], [T[0], yl, zl], [T[0], T[1], zl], [T[0], T[1], z_sok + 0.8]]), warna=WARNA[n], dari="Sensor " + n, ke=pn, b=b)
for n, (pn, b) in O_KE.items():
    E = np.array([ox_pin, OLED_PIN[n], zo - 16.5]); T = pin_esp(pn, b); zb, za = O_LAJUR[n]
    KABEL["kabel_o_" + n] = dict(titik=fillet([E, [E[0], E[1], zb], [T[0], E[1], zb], [T[0], E[1], za], [T[0], T[1], za], [T[0], T[1], z_sok + 0.8]]), warna=WARNA[n], dari="OLED " + n, ke=pn, b=b)
for k, kb in KABEL.items():
    kb["panjang"] = float(np.sum(np.linalg.norm(np.diff(kb["titik"], axis=0), axis=1)))
    tambah(k, pipa(kb["titik"]), kb["warna"], "Kabel " + kb["dari"], "kabel")
tambah("kabel_cabang", trimesh.util.concatenate([silinder(*pin_esp(pn, 1)[:2], z_sok + 0.1, z_sok + 2.2, 1.35, 16) for pn in ("3V3", "D21", "D22")]), "#111111", "Selongsong cabang Y (3)", "plastik_hitam")

# ---------------------------------------------------------------- daging (contoh) dan tutup kalibrasi
tambah("daging", kotak(-42, 46, -32, 32, -14, 0), "#b5483f", "Daging (contoh 88 x 64 x 14)", "daging")
for k in B: B[k]["grup"] = "daging" if k == "daging" else "alat"


def nama_pin(pn, b):
    if pn == "GND": return "GND (baris " + ("3V3" if b == 1 else "VIN") + ")"
    return pn.replace("D", "GPIO ") if pn.startswith("D") else pn


def kilap():
    Lc = LED_W * np.array([1, 1, -1]); tt = CHIP[2] / (CHIP[2] + LED_W[2]); Pk = CHIP + tt * (Lc - CHIP)
    return float(math.hypot(Pk[0], Pk[1]) - AP_R), Pk


def jarak_kabel():
    from scipy.spatial import cKDTree
    def padat(P_):
        out = [P_[0]]
        for a_, b_ in zip(P_[:-1], P_[1:]):
            m_ = max(1, int(np.linalg.norm(b_ - a_) / 0.3)); out += [a_ + (b_ - a_) * s for s in np.linspace(0, 1, m_ + 1)[1:]]
        return np.array(out)
    D = {k: padat(v["titik"]) for k, v in KABEL.items()}; ks = list(D); hasil = []
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a_, b_ = ks[i], ks[j]
            if KABEL[a_]["ke"] == KABEL[b_]["ke"] and KABEL[a_]["b"] == KABEL[b_]["b"]: continue      # cabang Y yang sama
            d, _ = cKDTree(D[b_]).query(D[a_]); hasil.append((round(float(d.min()), 2), a_, b_))
    return sorted(hasil)


def tabrakan():
    boleh = {frozenset(p) for p in [("sensor_pin", "sensor_header"), ("sensor_pin", "sensor_pcb"), ("sensor_pin", "sensor_dupont"), ("esp_pin", "esp_header"), ("esp_pin", "esp_pcb"),
             ("esp_pin", "esp_dupont"), ("sensor_baut", "sensor_pcb"), ("sensor_baut", "dudukan_cakram"), ("sensor_pin", "dudukan_cakram"), ("oled_baut", "oled_pcb"), ("oled_baut", "tutup_atas"),
             ("esp_usb", "esp_pcb"), ("tabung", "beludru"), ("oled_baut", "oled_kaca")]}
    out = []; ks = [k for k in B if k != "daging"]
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a_, b_ = ks[i], ks[j]
            if frozenset((a_, b_)) in boleh: continue
            if a_.startswith("kabel") and (b_.startswith("kabel") or "dupont" in b_ or "pin" in b_ or "cabang" in b_): continue
            if b_.startswith("kabel") and (a_.startswith("kabel") or "dupont" in a_ or "pin" in a_ or "cabang" in a_): continue
            m1, m2 = B[a_]["mesh"], B[b_]["mesh"]
            if not (np.all(m1.bounds[0] < m2.bounds[1] - 1e-6) and np.all(m2.bounds[0] < m1.bounds[1] - 1e-6)): continue
            try: v = float(trimesh.boolean.intersection([m1, m2], engine="manifold").volume)
            except Exception: v = -1
            if v > 0.05 or v == -1: out.append((a_, b_, round(v, 2)))
    return out


if __name__ == "__main__":
    sisa, Pk = kilap()
    print(f"chip {np.round(CHIP, 2)}, LED {np.round(LED_W, 2)}; kilap di ({Pk[0]:.2f}, {Pk[1]:.2f}) -> {sisa:+.2f} mm di luar tepi lubang")
    v = B["sensor_pcb"]["mesh"].vertices; print(f"papan sensor: z terendah {v[:, 2].min():.2f} (pelat muka atas {t}), jari-jari dari sumbu maks {np.linalg.norm(np.cross(v, u), axis=1).max():.2f} (dalam pipa {TUBE_RI})")
    print("tabrakan:", tabrakan() or "tidak ada")
    jk = jarak_kabel(); print("kabel: jarak terdekat beda tujuan", jk[:3])
    for k, kb in KABEL.items(): print(f"  {k:14s} {kb['dari']:>11s} -> ESP32 {nama_pin(kb['ke'], kb['b']):<15s} {kb['panjang']:6.1f} mm")
    bb = np.vstack([B[k]["mesh"].bounds for k in B if k != "daging"]); print("ukuran:", np.round(bb[1::2].max(0) - bb[0::2].min(0), 1))
    pv = sum(B[k]["mesh"].volume for k in B if B[k]["bahan"] in ("pvc", "pvc_hitam")) / 1000
    print(f"volume PVC {pv:.1f} cm3 -> {pv*0.55:.0f} g (PVC busa) / {pv*1.4:.0f} g (PVC padat); + komponen sekitar 25 g")
    sc = trimesh.Scene()
    for k, b in B.items():
        m = b["mesh"].copy(); m.visual.face_colors = [int(b["warna"][i:i + 2], 16) for i in (1, 3, 5)] + [255]; sc.add_geometry(m, node_name=k, geom_name=k)
    g = sc.copy(); g.apply_transform(rotation_matrix(-math.pi / 2, [1, 0, 0])); g.apply_scale(0.001); g.export(os.path.join(OUT, "genggam.glb"))
    json.dump(dict(P=P, chip=CHIP.tolist(), kilap_sisa=sisa, bagian={k: dict(grup=b["grup"], warna=b["warna"], nama=b["nama"], bahan=b["bahan"], alpha=b["alpha"],
              bounds=np.round(b["mesh"].bounds, 2).tolist()) for k, b in B.items()}), open(os.path.join(OUT, "bagian.json"), "w"), indent=1, ensure_ascii=False)
    print(f"ditulis model/genggam.glb, {len(B)} bagian")

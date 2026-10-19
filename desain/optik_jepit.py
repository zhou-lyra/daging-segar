"""Perbandingan geometri kepala ukur dengan LED bawaan TCS34725 (satu pantulan, Lambert).

Tujuan: memilih letak papan sensor di dalam tutup cat supaya
  (1) kilap (pantulan cermin) daging basah tidak sampai ke chip, dan
  (2) sinyal daging tetap besar dibanding pantulan dinding hitam di dalam ruang ukur.

Data papan dari berkas desain resmi Adafruit (Adafruit TCS34725.brd):
  chip U1 (10,46; 10,00), LED1 (7,24; 10,26) -> LED 3,22 mm dari chip, sejajar tepi lubang sekrup.
Respons sudut chip: Figure 3 lembar data TCS3472, hampir kosinus (0,87 pada 30 derajat).
LED dianggap Lambert (kosinus) terhadap normal papan. Hanya pantulan tunggal; pantulan ganda diabaikan.

Koordinat: muka tutup cat (bidang daging) z = 0, pusat lubang ukur di (0, 0). Satuan mm.
Jalankan: python3 desain/optik_jepit.py
"""
import math
import numpy as np

D_LED = 3.22          # chip ke LED, data Adafruit
T_MUKA = 1.5          # tebal muka tutup cat (anggapan)
R_DALAM = 31.0        # jari-jari dalam tutup cat (62 mm, anggapan dari luar 65 mm)
RHO_KILAP = 0.02      # pantulan cermin permukaan basah pada sudut kecil (air, Fresnel)
RHO_DAGING_G = 0.06   # pantulan daging sapi segar di kanal hijau, kira-kira 5-8 %
RHO_HITAM = {"cat hitam doff": 0.04, "beludru hitam": 0.01}


def geometri(jenis, h, sudut=0.0, geser=0.0):
    """Kembalikan posisi chip C, LED L, normal n (menghadap daging)."""
    if jenis == "miring":                         # sumbu chip mengarah ke pusat lubang
        a = math.radians(sudut)
        C = np.array([0.0, h * math.sin(a), h * math.cos(a)])
        n = -C / np.linalg.norm(C)
    else:                                         # papan datar, chip digeser sejauh `geser`
        C = np.array([0.0, geser, h])
        n = np.array([0.0, 0.0, -1.0])
    u = np.array([1.0, 0.0, 0.0])                 # arah chip -> LED (sejajar tepi lubang sekrup)
    return C, C + D_LED * u, n


def titik_kilap(C, L):
    Lc = np.array([L[0], L[1], -L[2]])            # bayangan cermin LED terhadap bidang daging
    t = C[2] / (C[2] + L[2])
    return C + t * (Lc - C)


def kontribusi(C, L, n, pts, normal, dA):
    """Sinyal relatif dari elemen permukaan Lambert dengan pantulan 1."""
    vL = L - pts; rL = np.linalg.norm(vL, axis=1); vL /= rL[:, None]
    vC = C - pts; rC = np.linalg.norm(vC, axis=1); vC /= rC[:, None]
    cos_emit = np.clip(-(vL @ n), 0, None)        # sudut terhadap normal LED (= normal papan)
    cos_in = np.clip(np.sum(vL * normal, axis=1), 0, None)
    cos_out = np.clip(np.sum(vC * normal, axis=1), 0, None)
    cos_det = np.clip(-(vC @ n), 0, None)
    E = cos_emit * cos_in / rL**2
    return float(np.sum(E / math.pi * cos_out * cos_det / rC**2 * dA))


def kisi_cakram(r0, r1, z, langkah=0.25):
    xs = np.arange(-r1, r1 + langkah, langkah)
    X, Y = np.meshgrid(xs, xs); R = np.hypot(X, Y)
    m = (R >= r0) & (R < r1)
    pts = np.stack([X[m], Y[m], np.full(m.sum(), z)], axis=1)
    return pts, np.tile([0, 0, 1.0], (len(pts), 1)), langkah**2


def kisi_dinding(r, z0, z1, langkah=0.3):
    k = int(2 * math.pi * r / langkah); zs = np.arange(z0, z1, langkah)
    a = np.linspace(0, 2 * math.pi, k, endpoint=False)
    A, Z = np.meshgrid(a, zs)
    pts = np.stack([r * np.cos(A).ravel(), r * np.sin(A).ravel(), Z.ravel()], axis=1)
    nor = np.stack([-np.cos(A).ravel(), -np.sin(A).ravel(), np.zeros(A.size)], axis=1)
    return pts, nor, (2 * math.pi * r / k) * langkah


def nilai(jenis, h, r_lubang, sudut=0.0, geser=0.0, z_atap=17.8):
    C, L, n = geometri(jenis, h, sudut, geser)
    P = titik_kilap(C, L)
    jarak_kilap = math.hypot(P[0], P[1])
    daging = kontribusi(C, L, n, *kisi_cakram(0, r_lubang, 0.0))
    hitam = kontribusi(C, L, n, *kisi_cakram(r_lubang, R_DALAM, T_MUKA))
    hitam += kontribusi(C, L, n, *kisi_dinding(R_DALAM, T_MUKA, z_atap))
    pa, na, da = kisi_cakram(0, R_DALAM, z_atap); na = -na
    hitam += kontribusi(C, L, n, pa, na, da)
    # kilap: bayangan cermin LED sebagai sumber titik dengan pantulan RHO_KILAP (permukaan basah, kira-kira air)
    Lc = np.array([L[0], L[1], -L[2]]); v = C - Lc; d = np.linalg.norm(v); v /= d
    vin = P - L; vin /= np.linalg.norm(vin)
    kilap = RHO_KILAP * max(vin @ n, 0) * max(-(v @ n), 0) / d**2 if jarak_kilap < r_lubang else 0.0
    return dict(kilap_per_daging=kilap / (daging * RHO_DAGING_G), kilap_dari_pusat=jarak_kilap, sisa_tepi=jarak_kilap - r_lubang,
                sinyal_daging=daging, hitam_per_daging=hitam / daging, sudut_pandang=math.degrees(math.acos(-n @ (-C / np.linalg.norm(C)))) if jenis != "miring" else 0.0)


if __name__ == "__main__":
    calon = [
        ("D: datar di tengah, h 15,5", "datar", 15.5, 7, 0, 0),
        ("miring 15, lubang 14", "miring", 15.5, 7, 15, 0),
        ("miring 30, lubang 14", "miring", 15.5, 7, 30, 0),
        ("miring 35, lubang 14", "miring", 15.5, 7, 35, 0),
        ("miring 40, lubang 14", "miring", 15.5, 7, 40, 0),
        ("miring 30, lubang 12", "miring", 15.5, 6, 30, 0),
        ("miring 35, lubang 12", "miring", 15.5, 6, 35, 0),
        ("miring 35, lubang 12, h 13", "miring", 13, 6, 35, 0),
        ("miring 35, lubang 10", "miring", 15.5, 5, 35, 0),
        ("datar, geser 12, h 12, lubang 14", "datar", 12, 7, 0, 12),
    ]
    acuan = None
    print(f"{'calon':36s} {'kilap dari tepi lubang':>22s} {'kilap/daging G':>15s} {'sinyal daging':>14s} " + " ".join(f"{'hitam/daging G ('+k+')':>30s}" for k in RHO_HITAM))
    for nama, jenis, h, rl, sd, gs in calon:
        v = nilai(jenis, h, rl, sd, gs)
        acuan = acuan or v["sinyal_daging"]
        rasio = " ".join(f"{v['hitam_per_daging'] * rho / RHO_DAGING_G:30.2f}" for rho in RHO_HITAM.values())
        print(f"{nama:36s} {v['sisa_tepi']:+20.1f} mm {v['kilap_per_daging']:15.2f} {v['sinyal_daging'] / acuan:14.2f} {rasio}")
    print("\nsisa tepi negatif = kilap jatuh DI DALAM lubang (daging basah memantulkan LED langsung ke chip).")
    print("hitam/daging G = sinyal dari dinding hitam dibagi sinyal daging di kanal hijau. Bagian ini tetap,")
    print("jadi dibuang oleh kalibrasi hitam; makin kecil makin sedikit derau. Kilap tidak bisa dikalibrasi.")

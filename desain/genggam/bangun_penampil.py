#!/usr/bin/env python3
"""Penampil 3D desain A-PVC (genggam). Memakai template penampil yang sama dengan desain E.
Jalankan: ../../.venv-cad/bin/python bangun_penampil.py  -> penampil_3d.html"""
import base64, json, os, warnings
import numpy as np
warnings.filterwarnings("ignore")
import geometri_a as G

HERE = os.path.dirname(os.path.abspath(__file__))
f1 = lambda v: (f"{v:.1f}".rstrip("0").rstrip(".")).replace(".", ",")
def stl_b64(m):
    tri = m.triangles.astype("<f4"); rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = m.face_normals.astype("<f4"), tri
    return base64.b64encode(bytes(80) + np.uint32(len(tri)).tobytes() + rec.tobytes()).decode()

def urai(k):
    if k == "daging": return -20
    if k in ("tutup_atas", "bibir", "tanda_tekan"): return 75
    if k.startswith("oled_"): return 62
    if k.startswith("esp_"): return 32
    if k.startswith(("sensor_", "dudukan_")): return 22
    if k in ("tabung", "beludru"): return 12
    if k.startswith("dinding"): return 0
    return 0
B = G.B
PARTS = {k: dict(nama=b["nama"], warna=b["warna"], grup=b["grup"], bahan=b["bahan"], alpha=b["alpha"], urai=urai(k)) for k, b in B.items()}
DATA = {k: stl_b64(b["mesh"]) for k, b in B.items()}
pref = lambda p: [k for k in B if k.startswith(p)]
def uk(ks):
    bb = np.vstack([B[k]["mesh"].bounds for k in ks]); return np.round(bb.max(0) - bb.min(0), 1).tolist()
def atas(ks):
    bb = np.vstack([B[k]["mesh"].bounds for k in ks]); lo, hi = bb.min(0), bb.max(0); return [float((lo[0] + hi[0]) / 2), float((lo[1] + hi[1]) / 2), float(hi[2])]
sisa = G.kilap()[0]
GROUPS = [
 dict(nama="Daging", warna="#b5483f", bagian=["daging"], ringkas="Daging utuh, tidak perlu diiris.", jangkar=[-30, -24, 0.0],
      teks="Alat ditempelkan ke permukaan daging yang rata, lalu ditekan ringan dengan ibu jari di tanda merah. Pelat muka hitam (58 x 39 mm) yang menyentuh daging; bagian belakang alat terangkat 2 mm sehingga tidak ikut menumpu."),
 dict(nama="Pelat muka", warna="#26272b", bagian=["pelat_muka"], ringkas="Lubang ukur Ø 12, satu-satunya bagian yang menempel.", jangkar=[26, -16, 3.0],
      teks="PVC hitam 3 mm. Lubang Ø 12 dibor di bawah sumbu tabung, lalu sisi dalamnya dikikir miring 45° sampai Ø 16 supaya tepi lubang tidak menghalangi pandangan sensor yang miring."),
 dict(nama="Tabung miring", warna="#9a9387", bagian=["tabung", "beludru"], ringkas="Pipa PVC 1 inci, ujung dipotong 40°.", jangkar=None,
      teks="Ujung pipa dipotong miring 40° dan dilem ke pelat muka. Karena tabungnya yang miring, papan sensor cukup dipasang tegak lurus di dalamnya, tanpa dudukan miring. Bagian dalam tabung dilapisi beludru hitam."),
 dict(nama="Sensor TCS34725", warna="#6a2c91", bagian=pref("sensor_") + ["dudukan_cakram"], ringkas="LED bawaan, melihat daging dari sudut 40°.", jangkar=None,
      teks=f"Papan dibaut ke cakram PVC hitam Ø 27,7 yang dilem di dalam tabung, chip berjarak {f1(G.H_CHIP)} mm dari pusat lubang. Kilap dari daging basah jatuh {f1(sisa)} mm di luar tepi lubang, di pelat hitam. Cakram juga menutup tabung dari cahaya di dalam kotak (lubang header ditutup silikon hitam)."),
 dict(nama="ESP32 DevKit V1", warna="#1f6f43", bagian=pref("esp_"), ringkas="Dibalik di atas busa, USB keluar di belakang.", jangkar=None,
      teks="ESP32 yang sudah ada, dibalik sehingga pin menghadap ke atas untuk soket dupont. Colokan USB keluar lewat takik di dinding belakang; kabel USB sekaligus daya dan jalur data ke laptop. Lampu merah dayanya ditutup selotip hitam."),
 dict(nama="OLED", warna="#1d4f9c", bagian=pref("oled_"), ringkas="Di bawah jendela tutup atas.", jangkar=None,
      teks="Layar dipasang diputar 90° di sisi bawah tutup atas dengan 4 baut M2 dan ring ganjal 1,4 mm, menghadap jendela 15 x 25 mm."),
 dict(nama="Kotak PVC", warna="#c9c2b6", bagian=pref("dinding_") + ["lantai_belakang", "tutup_atas", "bibir", "tanda_tekan"], ringkas=f"{f1(G.P['panjang'])} x {f1(G.P['lebar'])} x {f1(G.P['tinggi'])} mm.", jangkar=[-60, 18, G.Z_TOP + 3],
      teks="Semua bagian dari lembaran PVC 3 mm yang dipotong lurus: 2 dinding samping berbentuk L (bagian belakang naik 2 mm), dinding depan, dinding belakang bertakik USB, lantai belakang, dan tutup atas yang ditahan bibir. Lingkaran merah di tutup adalah tempat ibu jari menekan."),
 dict(nama="Kabel dupont", warna="#e67e22", bagian=pref("kabel_"), ringkas="9 kabel, 3 bercabang Y.", jangkar=None,
      teks="Sama dengan desain E: sensor VIN ke 3V3, GND, SDA ke GPIO 21, SCL ke GPIO 22, LED ke GPIO 26; OLED VCC ke 3V3, GND, SDA, SCL. Setiap kabel berjalan di ketinggian sendiri, jarak antarkabel paling dekat 1,7 mm."),
]
for g in GROUPS:
    g["ukuran"] = uk(g["bagian"]); g["jangkar_bagian"] = g["bagian"][0]
    if g["jangkar"] is None: g["jangkar"] = atas(g["bagian"])
GROUPS[3]["jangkar"] = [float(v) for v in G.CHIP]
INTRO = ('<h3>BeefFresh Genggam (A versi PVC)</h3><p class="lead">Ditempel ke daging dan ditekan ringan, seperti stempel kecil.</p><p class="body">Pilih <b>Potong: tengah (Y)</b> untuk melihat tabung miring dan sensor di dalamnya, '
         'dan geser <b>Urai</b> untuk memisahkan bagian. Klik nama bagian untuk penjelasannya.</p>')
T = open(os.path.join(HERE, "..", "jepit", "penampil_template.html")).read()
T = T.replace("<title>BeefFresh Jepit 3D</title>", "<title>BeefFresh Genggam 3D</title>")
T = T.replace("__PARTS__", json.dumps(PARTS)).replace("__GROUPS__", json.dumps(GROUPS, ensure_ascii=False)).replace("__DATA__", json.dumps(DATA)).replace("__HINGE__", "null").replace("__INTRO__", json.dumps(INTRO, ensure_ascii=False))
T = T.replace("dist=fit(2.0);select(null)", "dist=fit(1.25);select(null)").replace("dist=fit(2.0);draw()", "dist=fit(1.25);draw()")
T = T.replace(' <label><input type="checkbox"> tatakan kalibrasi</label>', '')
open(os.path.join(HERE, "penampil_3d.html"), "w").write(T)
print(f"penampil_3d.html {len(T)//1024} KB, {len(GROUPS)} kelompok")

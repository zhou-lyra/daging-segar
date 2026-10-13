#!/usr/bin/env python3
"""Penampil 3D berlabel: apa isi kotak dan di mana daging diletakkan. Satu berkas HTML mandiri.
Pakai: ../.venv-cad/bin/python bangun_web.py  -> gambar/beeffresh_3d.html"""
import base64, json, os, subprocess, sys
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); SCAD = os.path.join(HERE, "beeffresh_rumah.scad")
os.makedirs(os.path.join(HERE, "stl"), exist_ok=True)

def muat(part):
    path = os.path.join(HERE, "stl", part + ".stl")
    r = subprocess.run(["openscad", "-o", path, "-D", f'part="{part}"', SCAD], capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stderr: sys.exit(f"gagal render {part}: {r.stderr[-300:]}")
    return trimesh.load(path)

def stl_b64(m):
    tri = m.triangles.astype("<f4"); rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = m.face_normals.astype("<f4"), tri
    return base64.b64encode(bytes(80) + np.uint32(len(tri)).tobytes() + rec.tobytes()).decode()

M = {k: muat(p) for k, p in dict(base="base", tabung="tube_asm", esp="ghost_esp", oled="ghost_oled", tcs="ghost_tcs", tutup="lid_asm").items()}
tube = M["tabung"].bounds; tcs = M["tcs"].bounds; base = M["base"].bounds
tcx, tcy = (tube[0][0] + tube[1][0]) / 2, (tube[0][1] + tube[1][1]) / 2
ztip = tube[0][2]; tube_od = tube[1][0] - tube[0][0]
jarak = round(float(tcs[0][2] - ztip), 1)   # dasar papan sensor -> ujung tabung (perkiraan; chip sedikit di bawahnya)

# daging: lempengan di bawah ujung tabung, ujung tabung menyentuh permukaan atasnya
dx, dy = 70.0, 56.0; tebal = 14.0
daging = trimesh.creation.box(extents=[dx, dy, tebal]); daging.apply_translation([tcx, tcy, ztip - tebal / 2])
titik = trimesh.creation.cylinder(radius=tube_od / 2 + 0.2, height=0.3, sections=48); titik.apply_translation([tcx, tcy, ztip + 0.05])
M["daging"], M["titik"] = daging, titik

# ---- jalur kabel (contoh skematis: 4 kabel dari ESP32 ke OLED dan ke sensor)
def kabel(titik_, r=0.7):
    bagian = []
    for a, b in zip(titik_[:-1], titik_[1:]):
        bagian.append(trimesh.creation.cylinder(radius=r, segment=[a, b], sections=12))
    for q in titik_:
        bola = trimesh.creation.icosphere(radius=r, subdivisions=1); bola.apply_translation(q); bagian.append(bola)
    return trimesh.util.concatenate(bagian)
import kabel as KB
rute, jarak_min, tembus = KB.rute()
ob, tb = M["oled"].bounds, M["tcs"].bounds
ocx = (ob[0][0] + ob[1][0]) / 2
WARNA = {"VCC": "#e0245e", "GND": "#2b2b2b", "SCL": "#8e44ad", "SDA": "#e67e22"}
KUNCI = {"VCC": "w_vcc", "GND": "w_gnd", "SCL": "w_scl", "SDA": "w_sda"}
SINYAL = {"VCC": "Daya 3,3 V", "GND": "Tanah (GND)", "SCL": "Clock I2C (SCL)", "SDA": "Data I2C (SDA)"}
SENS_PIN = {"VCC": "VIN", "GND": "GND", "SCL": "SCL", "SDA": "SDA"}
def bola(q, r=1.05):
    m = trimesh.creation.icosphere(radius=r, subdivisions=2); m.apply_translation(q); return m
for n in KB.NAMA:
    pts = rute[n]; idx_tip = [i for i, q in enumerate(pts) if abs(q[2] - KB.OLED_PIN_Z) < 1e-6][0]
    M[KUNCI[n]] = trimesh.util.concatenate([kabel(pts)] + [bola(pts[i]) for i in (0, idx_tip, len(pts) - 1)])
# kaki header ESP32 (ujung pin di sisi atas PCB, 2 baris x 15) dan header 7 pin sensor
tips = []
for yy in (KB.Y_KIRI, KB.Y_KANAN):
    for k in range(15):
        bx = trimesh.creation.box(extents=[0.7, 0.7, 0.9]); bx.apply_translation([KB.ESP_PIN(k), yy, KB.Z_PCB + 0.45]); tips.append(bx)
M["w_pin"] = trimesh.util.concatenate(tips)
hs = trimesh.creation.box(extents=[2.54, 7 * 2.54, 2.5]); hs.apply_translation([KB.SENSOR_X, 14.4, 6.2 + 1.25]); M["w_hdr"] = hs
allw = trimesh.util.concatenate([M[KUNCI[n]] for n in KB.NAMA]); wb = allw.bounds
WC = ((wb[0] + wb[1]) / 2).tolist()
ESP_LABEL = {n: KB.SUMBER[n][2] for n in KB.NAMA}
TABEL = [dict(sinyal=SINYAL[n], warna=WARNA[n], esp=ESP_LABEL[n], oled=n, sensor=SENS_PIN[n]) for n in ("VCC", "GND", "SCL", "SDA")]
TAGS = []
for n in KB.NAMA:
    xp, yr, lab = KB.SUMBER[n]; TAGS.append(dict(p=[xp, yr, KB.Z_PCB + 0.3], t=lab.replace("GPIO ", "G"), c=WARNA[n], g="ESP32"))
    TAGS.append(dict(p=[KB.OLED_PIN_X[n], KB.OLED_PIN_Y, KB.OLED_PIN_Z], t=n, c=WARNA[n], g="OLED"))
for i, nm in enumerate(["VIN", "3V3", "GND", "SDA", "SCL", "INT", "LED"]):
    yy = 14.4 + (i - 3) * 2.54; pakai = {"VIN": "VCC", "GND": "GND", "SDA": "SDA", "SCL": "SCL"}.get(nm)
    TAGS.append(dict(p=[KB.SENSOR_X, yy, 8.7], t=nm, c=WARNA[pakai] if pakai else "#8a8a8a", g="Sensor"))
zesp = KB.Z_PCB + 3.2

def pusat(k): b = M[k].bounds; return ((b[0] + b[1]) / 2).tolist()
def atas(k): b = M[k].bounds; return [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2, b[1][2]]
def ukuran(k): b = M[k].bounds; return [round(float(v), 1) for v in (b[1] - b[0])]

INFO = [
 dict(k="kabel", nama="Kabel", warna="#e0245e", alpha=1.0, jangkar=[ocx, 5.2, zesp + 1.2], urai=0, tampil=True, virtual=True,
      judul="Jalur kabel (contoh)", ringkas="4 kabel: daya, tanah, dan dua jalur data.",
      teks="Empat kabel disolder langsung ke pin, tanpa PCB. Tiap kabel berjalan dari pin ESP32 ke pin OLED (titik bulat = sambungan solder), lalu diteruskan dari pin OLED yang sama ke pin sensor. Pin LED dan INT di sensor dibiarkan kosong. Jalur dihitung otomatis supaya tidak ada kabel yang bersentuhan atau menembus komponen. Posisi pin mengikuti ESP32 DOIT V1 30 pin dan urutan umum modul OLED dan sensor Adafruit: cocokkan dengan tulisan di papanmu sebelum menyolder. Kabel hanya terlihat saat 'Urai' = 0."),
 dict(k="daging", nama="Daging", warna="#c0392b", alpha=1.0, jangkar=[tcx+dx*0.2, tcy-dy*0.38, ztip], urai=-0.55, tampil=True,
      judul="Daging yang diperiksa", ringkas="Diletakkan di bawah alat, bukan di dalam kotak.",
      teks=f"Taruh daging di permukaan yang rata, misalnya talenan atau piring. Lingkaran merah muda adalah titik yang disentuh ujung tabung ({tube_od:.0f} mm). Pilih bagian yang datar, tidak berlemak tebal, tanpa genangan darah, dan selalu bagian yang sama setiap kali. Balok merah di gambar hanya contoh, bukan bentuk daging sebenarnya."),
 dict(k="titik", nama="Titik sentuh", warna="#f2b8b5", alpha=1.0, jangkar=None, urai=-0.55, tampil=True, judul="", ringkas="", teks=""),
 dict(k="tabung", nama="Tabung gelap", warna="#2f3138", alpha=1.0, jangkar=pusat("tabung"), urai=-0.22, tampil=True,
      judul="Tabung gelap", ringkas="Menghalangi cahaya ruangan dan menjaga jarak tetap.",
      teks=f"Ujung tabung ditempelkan ke daging. Jaraknya dari papan sensor ke ujung tabung ±{jarak:.0f} mm, selalu sama di setiap pengukuran. Bagian dalamnya harus hitam doff agar tidak memantulkan cahaya. Ada tiga ukuran (D5, D8, D11) untuk mencari jarak terbaik."),
 dict(k="tcs", nama="Sensor warna", warna="#d4a017", alpha=1.0, jangkar=pusat("tcs"), urai=-0.10, tampil=True,
      judul="Sensor warna TCS34725", ringkas="Mata alat: membaca warna daging.",
      teks="Dipasang terbalik di lantai kotak. LED putihnya menyinari daging, lalu chip membaca warna yang kembali (merah, hijau, biru, dan terang) lewat jendela kecil di dalam tabung."),
 dict(k="esp", nama="ESP32", warna="#2e8b57", alpha=1.0, jangkar=pusat("esp"), urai=0.22, tampil=True,
      judul="Papan ESP32", ringkas="Otak alat: membaca sensor dan menghitung hasil.",
      teks="Berbaring di atas satu rusuk tengah, colokan USB menghadap lubang di ujung kotak. Kabel USB yang sama menjadi sumber daya dan jalur data ke komputer."),
 dict(k="oled", nama="Layar OLED", warna="#2f6fd0", alpha=1.0, jangkar=pusat("oled"), urai=0.32, tampil=True,
      judul="Layar OLED", ringkas="Menampilkan hasil langsung di alat.",
      teks="Menempel di tutup, menghadap ke atas, ditahan 4 pin. Hasil bisa dibaca tanpa membuka komputer."),
 dict(k="tutup", nama="Tutup", warna="#8aa4c8", alpha=0.38, jangkar=atas("tutup"), urai=0.55, tampil=True,
      judul="Tutup kotak", ringkas="Menutup kotak dan memegang layar.",
      teks="Dikunci 2 sekrup M2.5 ditambah lip keliling. Di gambar dibuat transparan supaya isinya terlihat."),
 dict(k="base", nama="Badan bawah", warna="#5b6272", alpha=1.0, jangkar=atas("base"), urai=0.0, tampil=True,
      judul="Badan bawah (dicetak 3D)", ringkas="Rumah untuk semua komponen elektronik.",
      teks="Ukuran 87,6 × 33,6 mm. Lantainya punya jendela kecil tempat sensor mengintip, ceruk di bawahnya untuk tabung, dan lubang USB di ujungnya."),
]
LANGKAH = ["Letakkan daging di permukaan rata.", "Tempelkan ujung tabung ke daging, ringan dan tegak lurus, tanpa menekan sampai cekung.",
           "Alat membaca warna, hasilnya muncul di layar OLED dan di komputer.", "Ulangi di titik yang sama setiap kali agar hasilnya bisa dibandingkan."]

for n in ("VCC", "GND", "SCL", "SDA"):
    INFO.append(dict(k=KUNCI[n], nama=SINYAL[n], warna=WARNA[n], alpha=1.0, jangkar=None, urai=0, tampil=True, judul="", ringkas="", teks=""))
INFO.append(dict(k="w_pin", nama="Pin ESP32", warna="#c9a227", alpha=1.0, jangkar=None, urai=0, tampil=True, judul="", ringkas="", teks=""))
INFO.append(dict(k="w_hdr", nama="Header sensor", warna="#262626", alpha=1.0, jangkar=None, urai=0, tampil=True, judul="", ringkas="", teks=""))
data = {i["k"]: stl_b64(M[i["k"]]) for i in INFO if not i.get("virtual")}
for i in INFO: i["ukuran"] = ukuran(i["k"]) if not i.get("virtual") else [round(float(v), 1) for v in (wb[1] - wb[0])]

HTML = open(os.path.join(HERE, "web_template.html")).read()
HTML = HTML.replace("__INFO__", json.dumps(INFO)).replace("__DATA__", json.dumps(data)).replace("__LANGKAH__", json.dumps(LANGKAH, ensure_ascii=False)).replace("__TABEL__", json.dumps(TABEL, ensure_ascii=False)).replace("__TAGS__", json.dumps(TAGS)).replace("__WC__", json.dumps(WC))
out = os.path.join(HERE, "gambar", "beeffresh_3d.html"); open(out, "w").write(HTML)
print(f"kabel: jarak minimum {jarak_min:.2f} mm, tembus komponen {tembus}"); print(f"ditulis {out} ({len(HTML)//1024} KB) | jarak papan sensor->ujung tabung {jarak} mm | tabung ({tcx:.1f},{tcy:.1f}) ujung z={ztip:.1f}")

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

def pusat(k): b = M[k].bounds; return ((b[0] + b[1]) / 2).tolist()
def atas(k): b = M[k].bounds; return [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2, b[1][2]]
def ukuran(k): b = M[k].bounds; return [round(float(v), 1) for v in (b[1] - b[0])]

INFO = [
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

data = {i["k"]: stl_b64(M[i["k"]]) for i in INFO}
for i in INFO: i["ukuran"] = ukuran(i["k"])

HTML = open(os.path.join(HERE, "web_template.html")).read()
HTML = HTML.replace("__INFO__", json.dumps(INFO)).replace("__DATA__", json.dumps(data)).replace("__LANGKAH__", json.dumps(LANGKAH, ensure_ascii=False))
out = os.path.join(HERE, "gambar", "beeffresh_3d.html"); open(out, "w").write(HTML)
print(f"ditulis {out} ({len(HTML)//1024} KB) | jarak papan sensor->ujung tabung {jarak} mm | tabung ({tcx:.1f},{tcy:.1f}) ujung z={ztip:.1f}")

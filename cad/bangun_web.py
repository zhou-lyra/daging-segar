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
 dict(k="daging", nama="Daging yang diperiksa", warna="#b3414a", alpha=1.0, jangkar=[tcx+dx*0.2, tcy-dy*0.38, ztip], urai=-0.55, tampil=True,
      judul="Daging (contoh, bukan model asli)",
      teks=f"Letakkan daging di PERMUKAAN YANG RATA, mis. talenan atau piring. Daging ada DI BAWAH alat, bukan di dalam kotak. Lingkaran merah muda di permukaannya adalah titik yang disentuh ujung tabung ({tube_od:.0f} mm). Pilih bagian yang datar, tidak berlemak tebal, tanpa genangan darah, dan selalu bagian yang sama setiap pengukuran."),
 dict(k="titik", nama="Titik sentuh", warna="#e8a3a8", alpha=1.0, jangkar=None, urai=-0.55, tampil=True, judul="", teks=""),
 dict(k="tabung", nama="Tabung gelap", warna="#4a4a58", alpha=1.0, jangkar=pusat("tabung"), urai=-0.22, tampil=True,
      judul="Tabung gelap (cetak hitam doff)",
      teks=f"Ditekan ke ceruk di bawah badan. Ujungnya ditempelkan ke daging, jadi cahaya ruangan terhalang dan jarak sensor ke daging selalu sama (±{jarak:.0f} mm dari papan sensor ke ujung tabung). Bagian dalamnya harus hitam doff supaya tidak memantulkan cahaya. Ada tiga ukuran (D5, D8, D11) untuk mencari jarak terbaik."),
 dict(k="tcs", nama="Sensor warna TCS34725", warna="#c9974a", alpha=1.0, jangkar=pusat("tcs"), urai=-0.10, tampil=True,
      judul="Sensor warna TCS34725",
      teks="Dipasang TERBALIK di lantai badan: chip dan LED putihnya menghadap ke bawah, mengintip lewat jendela ke dalam tabung. LED menyinari daging, chip membaca warna yang kembali (merah, hijau, biru, dan terang). Inilah 'mata' alat."),
 dict(k="esp", nama="ESP32", warna="#2e9e4f", alpha=1.0, jangkar=pusat("esp"), urai=0.22, tampil=True,
      judul="Papan ESP32 (otak)",
      teks="Berbaring di atas satu rusuk tengah, colokan USB menghadap lubang di ujung badan. Membaca sensor lewat dua kabel (I2C), menghitung hasilnya, menampilkannya di OLED, dan mengirimnya ke komputer lewat kabel USB yang sama dengan sumber dayanya."),
 dict(k="oled", nama="Layar OLED", warna="#4a7bd0", alpha=1.0, jangkar=pusat("oled"), urai=0.32, tampil=True,
      judul="Layar OLED",
      teks="Menempel di tutup, menghadap ke atas, ditahan 4 pin di lubang pemasangannya. Menunjukkan hasil pembacaan langsung di alat, jadi tidak harus membuka komputer."),
 dict(k="tutup", nama="Tutup", warna="#b8bdd6", alpha=0.42, jangkar=atas("tutup"), urai=0.55, tampil=True,
      judul="Tutup",
      teks="Menutup badan dan memegang OLED lewat jendela di atasnya. Dikunci 2 sekrup M2.5 ditambah lip keliling. Di gambar dibuat transparan supaya isinya terlihat."),
 dict(k="base", nama="Badan bawah", warna="#8a8fa8", alpha=1.0, jangkar=atas("base"), urai=0.0, tampil=True,
      judul="Badan bawah (cetak 3D)",
      teks=f"Rumah untuk ESP32, sensor, dan kabel. Ukuran badan 87,6 × 33,6 mm. Lantainya punya jendela kecil tempat sensor mengintip, dan ceruk di bawahnya untuk tabung. Ada lubang USB di ujungnya."),
]
LANGKAH = ["Letakkan daging di permukaan rata.", "Tempelkan ujung tabung ke daging, ringan dan tegak lurus, tanpa menekan sampai daging cekung.",
           "Alat membaca warna, lalu hasilnya muncul di OLED dan di komputer.", "Ulangi di titik yang sama setiap kali, supaya hasilnya bisa dibandingkan."]

data = {i["k"]: stl_b64(M[i["k"]]) for i in INFO}
for i in INFO: i["ukuran"] = ukuran(i["k"])

HTML = open(os.path.join(HERE, "web_template.html")).read()
HTML = HTML.replace("__INFO__", json.dumps(INFO)).replace("__DATA__", json.dumps(data)).replace("__LANGKAH__", json.dumps(LANGKAH, ensure_ascii=False))
out = os.path.join(HERE, "gambar", "beeffresh_3d.html"); open(out, "w").write(HTML)
print(f"ditulis {out} ({len(HTML)//1024} KB) | jarak papan sensor->ujung tabung {jarak} mm | tabung ({tcx:.1f},{tcy:.1f}) ujung z={ztip:.1f}")

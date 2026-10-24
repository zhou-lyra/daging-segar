#!/usr/bin/env python3
"""Bangun halaman desain E (BeefFresh Jepit): penampil 3D + gambar kerja + daftar potongan + langkah rakit.
Jalankan: ../../.venv-cad/bin/python bangun_halaman.py   (setelah geometri.py dan gambar.py)
Keluaran: jepit/penampil_3d.html dan ../penjepit.html"""
import base64, json, os, re, warnings
from collections import Counter
import numpy as np
warnings.filterwarnings("ignore")
import geometri as G

HERE = os.path.dirname(os.path.abspath(__file__)); DESAIN = os.path.dirname(HERE)
f1 = lambda v: (f"{v:.1f}".rstrip("0").rstrip(".")).replace(".", ",")


def stl_b64(m):
    tri = m.triangles.astype("<f4"); rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = m.face_normals.astype("<f4"), tri
    return base64.b64encode(bytes(80) + np.uint32(len(tri)).tobytes() + rec.tobytes()).decode()


URAI = {"busa_1": 6, "busa_2": 14, "busa_3": 22, "daging": 45, "tutup_cat": 75, "beludru": 75, "dudukan_pelat": 100, "dudukan_pipi": 100,
        "kepala_lantai": 120, "kepala_depan": 135, "kepala_belakang": 135, "kepala_kiri": 135, "kepala_kanan": 135, "engsel_atas": 135, "kait_atas": 135,
        "kepala_tutup": 200, "kepala_bibir": 200}
def urai(k):
    if k in URAI: return URAI[k]
    if k.startswith("sensor_"): return 92
    if k.startswith("esp_"): return 145
    if k.startswith("oled_"): return 180
    return 0


B = G.B
PARTS = {k: dict(nama=b["nama"], warna=b["warna"], grup=b["grup"], bahan=b["bahan"], alpha=b["alpha"], urai=urai(k)) for k, b in B.items()}
DATA = {k: stl_b64(b["mesh"]) for k, b in B.items()}


def ukuran(ks):
    bb = np.vstack([B[k]["mesh"].bounds for k in ks]); return np.round(bb.max(0) - bb.min(0), 1).tolist()


def pusat_atas(ks, dz=0.0):
    bb = np.vstack([B[k]["mesh"].bounds for k in ks]); lo, hi = bb.min(0), bb.max(0)
    return [float((lo[0] + hi[0]) / 2), float((lo[1] + hi[1]) / 2), float(hi[2] + dz)]


pref = lambda p: [k for k in B if k.startswith(p)]
J = G.JENDELA
GROUPS = [
    dict(nama="Daging", warna="#b5483f", bagian=["daging"], ringkas="Irisan setebal 10 mm, di atas busa.",
         teks="Daging dipotong rata setebal 10 mm dan diletakkan di tengah busa yang dilapisi plastik wrap. Saat kepala ditutup, busa mendorong daging ke atas sampai rata dengan muka tutup cat. Lebar minimal 30 x 30 mm supaya lubang ukur tertutup rapat."),
    dict(nama="Busa 3 lapis", warna="#4a4f57", bagian=pref("busa_"), ringkas="Mendorong daging ke muka tutup cat.",
         teks="Tiga lembar busa hitam 78 x 78 x 10 mm (busa ati atau EVA lunak). Tebal awal 30 mm, tertekan menjadi 25 mm oleh daging 10 mm. Untuk daging 20 mm, ambil satu lapis. Lapisi dengan plastik wrap baru setiap sampel."),
    dict(nama="Baki bawah", warna="#a49d92", bagian=pref("baki_"), ringkas="Rahang bawah, tempat busa dan daging.",
         teks=f"Kotak terbuka dari PVC 3 mm, luar 86 x 86 x {f1(G.F + G.t + G.Hc)} mm. Bibir atasnya menjadi penahan: kepala tertutup bertumpu di sini, jadi celah dan tekanan busa selalu sama."),
    dict(nama="Tutup cat + beludru", warna="#1e1f22", bagian=["tutup_cat", "beludru"], ringkas="Ruang ukur gelap dengan lubang Ø 14.",
         teks=f"Tutup cat semprot Ø 65 dipotong setinggi {f1(G.Hc)} mm dan direkatkan terbalik di bawah lantai kepala. Muka tutupnya menjadi bidang acuan: daging selalu menempel di sini. Bagian dalamnya dilapisi kertas beludru hitam supaya hampir tidak memantulkan cahaya."),
    dict(nama="Sensor TCS34725", warna="#6a2c91", bagian=pref("sensor_"), ringkas="Miring 40 derajat, LED bawaan menyala.",
         teks=f"Papan sensor dimiringkan 40 derajat supaya kilap dari permukaan daging yang basah jatuh di muka hitam, {f1(G.kilap()[0])} mm di luar lubang, dan tidak masuk ke chip. Chip berjarak {f1(G.P['h'])} mm ke pusat lubang sepanjang sumbu pandangnya. Hanya LED bawaan papan yang dipakai."),
    dict(nama="Dudukan miring", warna="#26272b", bagian=pref("dudukan_"), ringkas="Pelat + 2 pipi yang menentukan sudut 40°.",
         teks="Pelat PVC hitam 27,3 x 16,8 mm tempat papan sensor dibaut, ditopang dua pipi berbentuk trapesium yang direkatkan di bawah lantai kepala. Sudutnya ditentukan oleh bentuk pipi, jadi cukup dipotong mengikuti pola 1:1."),
    dict(nama="Lantai kepala", warna="#c9c2b6", bagian=["kepala_lantai"], ringkas=f"Berjendela kabel {f1(J[1]-J[0])} x {f1(J[3]-J[2])} mm.",
         teks=f"Lembar PVC 86 x 86 mm. Tutup cat menempel di sisi bawahnya. Jendela kabel ({f1(J[1]-J[0])} x {f1(J[3]-J[2])} mm, {f1(J[0])} mm dari depan dan {f1(J[2])} mm dari kiri) dilewati 5 kabel sensor, lalu ditutup selotip hitam dari atas supaya cahaya dari dalam kotak tidak masuk ke ruang ukur."),
    dict(nama="ESP32 NodeMCU-32S", warna="#1d2024", bagian=pref("esp_"), ringkas="Dibalik di atas busa, USB ke takik kiri.",
         teks="Papan ESP32 diletakkan terbalik (modul logam di bawah) di atas busa dobel tape 3 mm, sehingga pin menghadap ke atas dan kabel bisa disolder di ujung pin. Lampu merah dayanya ditutup selotip hitam."),
    dict(nama="OLED 0,96 inci", warna="#1d4f9c", bagian=pref("oled_"), ringkas="Di sisi bawah tutup atas, tampil lewat jendela.",
         teks="Layar dibaut ke tutup atas dengan 4 baut M2 x 10 (1 mur ganjal 1,6 mm + 1 mur pengunci), menghadap jendela 25 x 15 mm. Hasil ukur bisa dibaca tanpa membuka alat."),
    dict(nama="Kotak kepala", warna="#e8e3da", bagian=["kepala_depan", "kepala_belakang", "kepala_kiri", "kepala_kanan", "kepala_tutup", "kepala_bibir"],
         ringkas="Rahang atas berisi elektronik.", teks=f"Empat dinding PVC setinggi {f1(G.P['kepala_dalam'])} mm dan tutup atas yang bisa dilepas (ditahan bibir di sisi bawahnya). Dinding kiri punya takik USB 13 x 10 mm."),
    dict(nama="Engsel", warna="#9a9ea5", bagian=pref("engsel_"), ringkas="2 engsel 25 mm di sisi belakang.",
         teks="Dua engsel kupu-kupu 25 mm dipasang di sisi belakang dengan baut M3 dan mur, porosnya tepat di garis sambungan baki dan kepala. Pasang tali pembatas supaya kepala tidak terbuka lebih dari sekitar 100 derajat."),
    dict(nama="Kait", warna="#7d838b", bagian=pref("kait_"), ringkas="Mengunci kepala supaya tekanan busa sama.",
         teks="Kait kotak kecil di sisi depan. Busa mendorong kepala ke atas, jadi kepala harus dikunci supaya daging selalu tertekan sama rata ke muka tutup cat."),
    dict(nama="Kabel", warna="#e8b00c", bagian=pref("kabel_"), ringkas="9 kabel disolder, 5 titik di ESP32.",
         teks="Kabel disolder langsung ke pin, tanpa soket. Sensor: VIN ke 3V3, GND ke GND, SDA ke G26, SCL ke G27, LED ke G25. OLED: VCC ke 3V3, GND ke GND, SDA ke G26, SCL ke G27. Semua titik ESP32 di baris 3V3; pin 3V3, GND, G26 dan G27 menerima dua kabel. Tiap kabel berjalan di ketinggiannya sendiri dan tidak menyentuh kabel lain."),
    dict(nama="Tatakan kalibrasi", warna="#f0efe8", bagian=["kal_putih", "kal_hitam"], ringkas="Balok putih dan hitam 60 x 60 x 10 mm.",
         teks="Dipakai sekali per sesi: balok putih (kertas HVS doff) untuk titik putih, balok hitam (beludru) untuk titik gelap. Tebalnya sama dengan daging (10 mm), jadi ditekan busa ke muka tutup cat dengan cara yang sama."),
]
for g in GROUPS:
    g["ukuran"] = ukuran(g["bagian"]); g["jangkar_bagian"] = g["bagian"][0]
    g["jangkar"] = pusat_atas(g["bagian"])
GROUPS[4]["jangkar"] = [float(v) for v in G.CHIP]; GROUPS[3]["jangkar"] = [G.XC - G.R + 2, G.YC - 18, 6.0]; GROUPS[5]["jangkar"] = [G.PIPI_POLI[1][0], G.YC + 12, 12.0]
GROUPS[0]["jangkar"] = [G.XC - 20, G.YC - 18, -2.0]; GROUPS[1]["jangkar"] = [12, 12, -14.0]; GROUPS[2]["jangkar"] = [2, 12, -30.0]
GROUPS[6]["jangkar"] = [70, 70, G.Hc + G.t]; GROUPS[9]["jangkar"] = [3, 70, G.Z_ATAS - 6]
HINGE = dict(x=G.SUMBU_ENGSEL[0], z=G.SUMBU_ENGSEL[1], yc=G.YC)

T = open(os.path.join(HERE, "penampil_template.html")).read()
T = T.replace("__PARTS__", json.dumps(PARTS)).replace("__GROUPS__", json.dumps(GROUPS, ensure_ascii=False)).replace("__DATA__", json.dumps(DATA)).replace("__HINGE__", json.dumps(HINGE)).replace("__INTRO__", json.dumps('<h3>BeefFresh Jepit</h3><p class="lead">Penjepit berengsel: daging dijepit antara busa dan tutup cat.</p><p class="body">Geser <b>Buka engsel</b> untuk melihat cara memasukkan daging, <b>Urai</b> untuk memisahkan bagian, dan <b>Potong: tengah (Y)</b> untuk melihat sensor miring di dalam tutup cat. Klik nama bagian untuk penjelasannya.</p>', ensure_ascii=False))
open(os.path.join(HERE, "penampil_3d.html"), "w").write(T)

# ----------------------------------------------------------------------------- daftar potongan PVC (dari model)
potong = Counter()
for k, b in B.items():
    if b["bahan"] not in ("pvc", "pvc_hitam") or b["grup"] == "aksesori": continue
    tubuh = b["mesh"].split(only_watertight=False) if k in ("kepala_bibir", "dudukan_pipi") else [b["mesh"]]
    for m in tubuh:
        e = sorted(np.round(m.extents, 1), reverse=True)
        if k == "dudukan_pelat":
            nama, uk = b["nama"], f"{f1(G.PELAT['bx1'] - G.PELAT['bx0'])} x {f1(G.PELAT['by1'] - G.PELAT['by0'])}"
        elif k == "dudukan_pipi":
            nama, uk = "Pipi penyangga (trapesium, lihat pola)", f"{f1(G.PIPI_POLI[1][0]-G.PIPI_POLI[0][0])} x {f1(G.Hc-G.PIPI_POLI[1][1])}"
        else:
            nama = re.sub(r" \(.*\)", "", b["nama"]); uk = f"{f1(e[0])} x {f1(e[1])}"
        catatan = {"kepala_lantai": f"jendela {f1(J[1]-J[0])} x {f1(J[3]-J[2])}", "kepala_kiri": "takik USB 13 x 10", "kepala_tutup": "jendela 25 x 15, 4 lubang Ø 2,2",
                   "dudukan_pelat": "2 lubang Ø 2,8", "dudukan_pipi": "sisi miring 40°"}.get(k, "")
        warna_ = "hitam" if b["bahan"] == "pvc_hitam" else "putih"
        potong[(nama, uk, catatan, warna_)] += 1
POTONG = sorted(potong.items(), key=lambda x: -float(x[0][1].split(" x ")[0].replace(",", ".")))
luas = sum(float(n[1].split(" x ")[0].replace(",", ".")) * float(n[1].split(" x ")[1].replace(",", ".")) * c for n, c in POTONG) / 100
rows_potong = "".join(f"<tr><td>{n}{' <span class=mut>(PVC hitam atau dicat hitam doff)</span>' if w=='hitam' else ''}</td><td class=n>{u}</td><td class=n>{c}</td><td class=mut>{cat}</td></tr>" for (n, u, cat, w), c in POTONG)

import gambar_kabel_lembar as GKL
rows_kabel = "".join(f'<tr><td><i style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{kb["warna"]};margin-right:6px"></i>'
                     f'{GKL.titik_dev(*kb["dari"].split())} {kb["dari"]}</td><td>E{GKL.TITIK_ESP.index(kb["ke"]) + 1} {kb["ke"]}</td>'
                     f'<td class=n>{f1(kb["panjang"] / 10)} cm</td><td class=n>{f1(GKL.potong_cm(kb["panjang"]))} cm</td></tr>'
                     for kb in sorted(G.KABEL.values(), key=lambda kb: (GKL.TITIK_ESP.index(kb["ke"]), kb["dari"].startswith("OLED"))))
svg = {f: open(os.path.join(HERE, "gambar", f)).read() for f in os.listdir(os.path.join(HERE, "gambar")) if f.endswith(".svg")}
pola_w = re.search(r'width="([\d.]+)mm"', svg["5_pola_1banding1.svg"]).group(1)
sisa = G.kilap()[0]
render_ada = [f for f in sorted(os.listdir(os.path.join(HERE, "render"))) if f.endswith(".jpg")] if os.path.isdir(os.path.join(HERE, "render")) else []
JUDUL_RENDER = {"1_tertutup.jpg": "Tertutup, siap mengukur", "2_terbuka.jpg": "Terbuka 90°: daging diletakkan di atas busa", "3_potongan.jpg": "Potongan tengah: sensor miring di dalam tutup cat",
                "4_ruang_ukur.jpg": "Ruang ukur dari dekat", "5_urai.jpg": "Urai: semua bagian dipisah", "6_katalog_komponen.jpg": "Katalog: setiap komponen"}
html_render = "".join(f'<figure><img src="jepit/render/{f}" alt="{JUDUL_RENDER.get(f, f)}" loading="lazy"><figcaption>{JUDUL_RENDER.get(f, f)}</figcaption></figure>' for f in render_ada)

HAL = open(os.path.join(HERE, "halaman_template.html")).read()
for k, v in {"__SVG1__": svg["1_potongan.svg"], "__SVG2__": svg["2_ruang_ukur.svg"], "__SVG3__": svg["3_denah_lantai_kepala.svg"], "__SVG4__": svg["4_terbuka.svg"],
             "__SVG6__": svg["6_skema_kabel.svg"], "__SVG7__": svg["7_denah_kabel.svg"], "__SVG8__": svg["8_lembar_baki.svg"], "__SVG9__": svg["9_lembar_kepala.svg"], "__SVG10__": svg["10_lembar_kecil.svg"], "__KABEL__": rows_kabel, "__JARAK__": f1(G.jarak_kabel()[0][0]),
             "__SVG5__": svg["5_pola_1banding1.svg"].replace(f'width="{pola_w}mm"', 'width="100%"').replace('height="182mm"', ''),
             "__POTONG__": rows_potong, "__LUAS__": f1(luas), "__SISA__": f1(sisa), "__RENDER__": html_render or "<p class=mut>Render belum dibuat.</p>",
             "__JX0__": f1(J[0]), "__JX1__": f1(J[1]), "__JY0__": f1(J[2]), "__JY1__": f1(J[3]), "__JW__": f1(J[1] - J[0]), "__JH__": f1(J[3] - J[2]),
             "__PX0__": f1(G.PIPI_POLI[0][0]), "__PX1__": f1(G.PIPI_POLI[1][0]), "__PY__": " dan ".join(f"{f1(a)} sampai {f1(b)}" for a, b in [sorted([G.papan(b0, 0, 0)[1], G.papan(b1, 0, 0)[1]]) for b0, b1 in G.PIPI_BX]),
             "__CHX__": f1(G.CHIP[0] - G.XC), "__CHZ__": f1(G.CHIP[2]), "__TINGGI__": f1(G.Z_ATAS + G.t + G.F + G.t)}.items():
    HAL = HAL.replace(k, v)
assert "__" not in re.sub(r"<svg.*?</svg>", "", HAL, flags=re.S).replace("__siap", ""), re.findall(r"__\w+__", HAL)
open(os.path.join(DESAIN, "penjepit.html"), "w").write(HAL)
print(f"penampil_3d.html {len(T)//1024} KB, penjepit.html {len(HAL)//1024} KB, {len(POTONG)} jenis potongan, luas PVC {luas:.0f} cm2, render {len(render_ada)}")

#!/usr/bin/env python3
"""Bangun halaman tur rakit: desain/rakit_model1.html (Genggam) dan desain/rakit_model2.html (Jepit).
Setiap langkah: teks berangka, gambar kerja berukuran, dan keadaan penampil 3D (bagian tampil/baru, kamera, potongan, engsel).
Jalankan (setelah geometri_a.py, geometri.py, gambar_rakit.py): ../../.venv-cad/bin/python bangun_rakit.py
"""
import base64, html, json, math, os, sys, warnings
import numpy as np
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); DES = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(DES, "jepit")); sys.path.insert(0, os.path.join(DES, "genggam"))
import geometri as GE
import geometri_a as GA
import gambar_rakit as GR
f1 = GR.f1


def stl_b64(m):
    tri = m.triangles.astype("<f4"); rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = m.face_normals.astype("<f4"), tri
    return base64.b64encode(bytes(80) + np.uint32(len(tri)).tobytes() + rec.tobytes()).decode()


def ukuran(m):
    d = sorted(np.round(m.bounds[1] - m.bounds[0], 1), reverse=True)
    return " x ".join(f1(v) for v in d) + " mm"


def penampil(B, urai, hinge, judul, nama_file, grup_aks=()):
    PARTS = {}
    for k, b in B.items():
        p = dict(nama=b["nama"], warna=b["warna"], grup=("aksesori" if k in grup_aks else b["grup"]), bahan=b["bahan"], alpha=b["alpha"], urai=urai(k))
        if b["bahan"] in ("pvc", "pvc_hitam", "busa", "beludru"): p["ukuran"] = ukuran(b["mesh"])
        PARTS[k] = p
    DATA = {k: stl_b64(b["mesh"]) for k, b in B.items()}
    T = open(os.path.join(HERE, "penampil_langkah_template.html")).read()
    T = T.replace("__JUDUL__", judul).replace("__PARTS__", json.dumps(PARTS, ensure_ascii=False)).replace("__DATA__", json.dumps(DATA)).replace("__HINGE__", json.dumps(hinge))
    open(os.path.join(HERE, nama_file), "w").write(T)
    return len(T) // 1024


def pilih(B, *pola):
    """Kunci bagian dari pola: 'nama' persis atau 'awalan*'."""
    out = []
    for p in pola:
        for k in B:
            if (p.endswith("*") and k.startswith(p[:-1])) or k == p:
                if k not in out: out.append(k)
    return out


def daftar_kabel(KABEL):
    """Baris tabel kabel dari daftar kabel model, urut titik ESP32 (sama dengan peta titik solder)."""
    T = GKL.TITIK_ESP; out = []
    for kb in sorted(KABEL.values(), key=lambda kb: (T.index(kb["ke"]), kb["dari"].startswith("OLED"))):
        dev, pin = kb["dari"].split()
        dua = sum(1 for k2 in KABEL.values() if k2["ke"] == kb["ke"]) == 2
        out.append((kb["warna"], f"{GKL.titik_dev(dev, pin)} {dev} {pin}", f"E{T.index(kb['ke']) + 1} {kb['ke']}", kb["panjang"],
                    GE.NAMA_WARNA[GE.SINYAL[kb["ke"]]] + ("; 2 kabel di pin ini" if dua else "")))
    return out


def kabel_tabel(daftar):
    """daftar: (warna, dari, ke, panjang_model_mm, catatan)."""
    r = []
    for i, (w, dari, ke, L, cat) in enumerate(daftar, 1):
        jadi = GKL.potong_cm(L)
        r.append(f'<tr><td><i class="kw" style="background:{w}"></i>{i}</td><td>{ke}</td><td>{dari}</td><td>{f1(L)}</td><td><b>{f1(jadi)} cm</b></td><td>{cat}</td></tr>')
    total = sum(GKL.potong_cm(d[3]) for d in daftar)
    return ('<div class="tw"><table class="kt"><tr><th>No</th><th>Titik ESP32</th><th>Titik akhir</th><th>Jalur di model (mm)</th><th>Potong</th><th>Catatan</th></tr>' + "".join(r) + "</table></div>"
            f'<p class="mut">Potong = jalur di model + 2 cm cadangan, dari titik solder ke titik solder (sudah termasuk kupasan 4 mm di kedua ujung). Total {f1(total)} cm kabel. '
            'Nomor titik sama dengan peta titik solder: E = ESP32, S = sensor, O = OLED.</p>')


def bom(baris):
    return '<div class="tw"><table class="kt"><tr><th>Bahan</th><th>Jumlah</th><th>Catatan</th></tr>' + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in baris) + "</table></div>"


import gambar_kabel_lembar as GKL


def daftar_potong(fungsi, mod=None, hitam=()):
    """Tabel semua lembar PVC dari fungsi gambar lembar (ukuran sama persis dengan gambar)."""
    mod = mod or GKL
    mod.DAFTAR.clear()
    for f in fungsi: f()
    r = []; n = 0
    for gb, judul, w, h, jml, cat in mod.DAFTAR:
        if "kalibrasi" in judul.lower(): continue
        n += jml; hit = any(k in (judul + cat).lower() for k in ("hitam",) + hitam)
        r.append(f'<tr><td>{judul}</td><td><b>{f1(w)} x {f1(h)}</b></td><td>{jml}</td><td>{"HITAM" if hit else "biasa"}</td><td>{cat}</td></tr>')
    return ('<div class="tw"><table class="kt"><tr><th>Lembar</th><th>Potong (mm)</th><th>Jumlah</th><th>PVC</th><th>Catatan</th></tr>' + "".join(r) + "</table></div>"
            f'<p class="mut">{n} potongan. Ukuran = lebar x tinggi seperti di gambar, dalam milimeter. Lembar tidak persegi (dinding samping bertangga, cakram, pipi) dipotong dari persegi panjang sebesar ukuran ini lalu dibentuk sesuai gambar.</p>')


CARA_UKUR = ("<p><b>Cara membaca ukuran:</b> semua angka dalam <b>milimeter</b>. Angka <b style='color:#e06a62'>merah</b> di kiri dan bawah setiap lembar = ukuran potong (lebar x tinggi). "
             "Angka <b style='color:#7fa7e0'>biru</b> berantai = letak tanda atau lubang: mulai dari tepi kiri ke kanan (baris bawah) dan dari tepi bawah ke atas (kolom kanan); "
             "kalau dijumlahkan hasilnya sama dengan ukuran lembar. Contoh 34 + 18 + 34 = 86: tanda kait mulai 34 mm dari tepi kiri, lebarnya 18 mm.</p>"
             "<ol><li>Gores ukuran potong dulu, periksa siku, baru potong.</li><li>Ukur dan tandai letak tanda/lubang dari tepi yang disebut (kiri atau bawah), dengan pensil.</li>"
             "<li>Tulis nama di setiap lembar setelah dipotong (misal \"samping kiri\") supaya tidak tertukar.</li></ol>")


ALAT = ("Cutter besar + penggaris besi 30 cm, penggaris siku, jangka sorong (sangat membantu), spidol halus, selotip kertas, gergaji besi kecil, bor tangan "
        "dengan mata bor 2, 2,5, 3, 4, 8 dan 12 mm (atau mata bor bertingkat), kikir bulat dan setengah bulat, amplas 240, solder 30-60 W + timah 0,8 mm, "
        "pemanas atau korek untuk selongsong, tang kupas kabel, penjepit buaya (tangan ketiga), multimeter, lem PVC atau lem tembak, silikon hitam.")


# ============================================================================ MODEL 1: GENGGAM
def model1():
    B = GA.B
    def urai(k):
        if k == "daging": return -20
        if k in ("tutup_atas", "bibir", "tanda_tekan"): return 75
        if k.startswith("oled_"): return 62
        if k.startswith("esp_"): return 32
        if k.startswith(("sensor_", "dudukan_")): return 22
        if k in ("tabung", "beludru"): return 12
        return 0
    kb = penampil(B, urai, None, "BeefFresh Model 1: langkah rakit", "penampil_model1.html")
    PVC = pilih(B, "pelat_muka", "lantai_belakang", "dinding_*", "tutup_atas", "bibir", "dudukan_cakram")
    SENS = pilih(B, "sensor_*") ; SENS_ND = [k for k in SENS if k != "sensor_dupont"]
    KEPALA = pilih(B, "pelat_muka", "tabung", "beludru")
    BADAN = pilih(B, "lantai_belakang", "dinding_*")
    ESP = pilih(B, "esp_*"); ESP_ND = [k for k in ESP if k != "esp_dupont"]
    OLED = pilih(B, "oled_*"); OLED_ND = [k for k in OLED if k != "oled_dupont"]
    TUTUP = pilih(B, "tutup_atas", "bibir", "tanda_tekan")
    KABEL = pilih(B, "kabel_*")
    SEMUA = [k for k in B if k != "daging"]
    sisi = 2 * GA.YI
    R = GA.TUBE_RI - 0.15
    luas_putih = (2 * GR.L_TOT * GR.H_DIND + (GA.X_PAD - GA.X0) * GR.W_TOT + sisi * GR.H_DIND + sisi * (GA.Z_TOP - 5) + GR.L_TOT * GR.W_TOT) / 100
    luas_hitam = ((GA.X1 - GA.X_PAD) * GR.W_TOT + (2 * R) ** 2) / 100
    K = GA.KABEL
    def ln(k): return K[k]["panjang"]
    nama = lambda pn, b: GA.nama_pin(pn, b)
    kabel = daftar_kabel(K)
    L = []
    def langkah(judul, waktu, isi, gambar=(), periksa="", awas="", **v3):
        L.append(dict(judul=judul, waktu=waktu, isi=isi, gambar=list(gambar), periksa=periksa, awas=awas, v3=v3))
    langkah("Siapkan bahan dan alat", "15 menit", [
        bom([("PVC board 3 mm putih/abu", f"± {math.ceil(luas_putih)} cm²", "dinding, lantai, tutup, bibir; sisa potongan tutup cat tidak dipakai"),
             ("PVC board 3 mm HITAM", f"± {math.ceil(luas_hitam)} cm²", "pelat muka dan cakram; boleh PVC putih yang dicat hitam doff 2 lapis"),
             ("Pipa PVC 1 inci (Ø luar 32)", "4 cm", "potongan sisa sudah cukup"),
             ("ESP32 NodeMCU-32S 38 pin, TCS34725, OLED 0,96 inci I2C", "1 set", "sudah ada"),
             ("Baut M2,5 x 10 hitam + mur", "2", "papan sensor ke cakram"), ("Baut M2 x 10 + mur", "4 + 8", "OLED: 1 mur ganjal dan 1 mur pengunci per baut"),
             ("Kabel serabut 24-26 AWG: merah, hitam, kuning, biru, hijau", f"± {f1(sum(GKL.potong_cm(d[3]) for d in kabel) + 10)} cm total", "boleh kabel dupont yang dipotong soketnya; panjang tiap kabel di tabel kabel"), ("Selongsong panas Ø 2 mm", "14 x 15 mm", "1 per titik solder"),
             ("Busa dobel tape 3 mm", "31 x 20 mm", "alas ESP32"), ("Kertas beludru hitam (flok)", "88 x 26 mm", "pelapis dalam pipa; pengganti: kain flanel hitam"),
             ("Silikon hitam, selotip hitam, cat merah", "sedikit", "penutup celah, lampu ESP32, tanda ibu jari")]),
        f"<p><b>Alat:</b> {ALAT}</p>"], gambar=[("rakit/gambar/cara_baca.svg", "Cara membaca semua gambar kerja")],
        tampil=SEMUA, baru=[], pandang=[0.75, 0.45, 1.5])
    langkah("Cetak pola 1:1", "10 menit", [
        "<ol><li>Buka pola badan dan pola pipa (tautan di bawah), cetak di kertas A4 dengan skala <b>100 %</b> (matikan \"sesuaikan dengan halaman\").</li>"
        "<li>Ukur <b>garis uji 50 mm</b> dengan penggaris. Bila meleset lebih dari 0,5 mm, cetak ulang.</li>"
        "<li>Gunting pola dengan sisa 3 mm, tempel di PVC dengan selotip kertas. Pelat muka dan cakram di PVC hitam.</li></ol>",
        '<p class="dl"><a href="rakit/gambar/pola_m1_badan_1banding1.svg" target="_blank">Pola badan 1:1 (A4)</a> <a href="rakit/gambar/pola_m1_pipa_1banding1.svg" target="_blank">Pola potong pipa 1:1</a></p>'],
        tampil=PVC, baru=PVC, urai=1.0, pandang=[0.75, 0.5, 1.4], label=[])
    langkah("Potong lembar PVC", "45 menit", [
        "<ol><li>Gores PVC 3-5 kali di sepanjang penggaris besi, lalu patahkan di tepi meja. PVC padat: gergaji besi.</li>"
        f"<li>Potong: 2 dinding samping {f1(GR.L_TOT)} x {f1(GR.H_DIND)} (tangga 2 mm di {f1(GA.X_PAD - GA.X0)} mm dari belakang), dinding depan {f1(sisi)} x {f1(GR.H_DIND)}, "
        f"dinding belakang {f1(sisi)} x {f1(GA.Z_TOP - 5)}, lantai belakang {f1(GA.X_PAD - GA.X0)} x {f1(GR.W_TOT)}, tutup {f1(GR.L_TOT)} x {f1(GR.W_TOT)}, pelat muka hitam {f1(GA.X1 - GA.X_PAD)} x {f1(GR.W_TOT)}.</li>"
        "<li>Bibir: 2 strip 63,6 x 6 dan 2 strip 8,1 x 6.</li>"
        "<li>Jendela OLED 15 x 25: bor Ø 3 di keempat sudut, lalu potong di antara lubang dan kikir lurus. 4 lubang OLED Ø 2,2 (mata bor 2 lalu putar sedikit).</li>"
        "<li>Takik USB 13 x 10,1 di tepi bawah dinding belakang.</li>"
        "<li>Amplas semua tepi sampai lurus dan siku. Tepi yang miring membuat celah cahaya.</li></ol>", CARA_UKUR,
        daftar_potong([GR.m1_lembar_badan, GR.m1_lembar_tutup])],
        gambar=[("rakit/gambar/m1_lembar_badan.svg", "Lembar badan"), ("rakit/gambar/m1_lembar_tutup.svg", "Tutup dan bibir"), ("rakit/gambar/m1_cakram.svg", "Cakram dudukan")],
        periksa="Ukur setiap lembar dengan jangka sorong: selisih paling banyak 0,3 mm. Dinding kiri dan kanan ditumpuk harus sama persis.",
        tampil=PVC, baru=pilih(B, "dinding_*", "lantai_belakang", "tutup_atas", "bibir"), urai=1.0, pandang=[0.75, 0.5, 1.3])
    langkah("Lubang ukur di pelat muka", "20 menit", [
        f"<ol><li>Tandai pusat lubang: {f1(-GA.X_PAD)} mm dari tepi belakang pelat dan {f1(GA.YW)} mm dari tepi samping.</li>"
        "<li>Bor bertahap Ø 4, 8, lalu 12 mm dengan tekanan ringan supaya PVC tidak pecah.</li>"
        "<li>Dari sisi atas (dalam), kikir tepi lubang miring 45° sampai diameternya Ø 16 di permukaan. Sisakan 1 mm bagian lurus Ø 12 di sisi bawah.</li>"
        "<li>Haluskan sisi bawah (yang menyentuh daging) dengan amplas: tidak boleh ada serpih.</li></ol>"],
        gambar=[("rakit/gambar/m1_lubang.svg", "Potongan lubang ukur")],
        periksa="Sisi bawah pelat rata dan hitam doff. Tepi lubang di sisi bawah tajam dan bulat, tidak gompal.",
        tampil=["pelat_muka"], baru=["pelat_muka"], potong=[1, 0.0, 1], pandang=[0.15, 0.55, 1.1])
    langkah("Potong pipa miring 40°", "30 menit", [
        f"<ol><li>Potong pipa 1 inci lurus sepanjang {f1(GR.PIPA_PANJANG + 4)} mm, ratakan kedua ujungnya.</li>"
        "<li>Bungkus pola pipa di ujung pipa, tepi lurus pola rata dengan ujung tegak lurus. Ujung pola harus bertemu tepat; bila tidak, pipamu bukan Ø 32.</li>"
        "<li>Gores garis merah pola dengan spidol halus. Beri tanda panah di titik terendah garis: itu <b>sisi panjang</b>.</li>"
        "<li>Gergaji sedikit di luar garis, lalu gosok muka potong di amplas yang ditaruh di meja datar sampai garis tepat hilang.</li></ol>"],
        gambar=[("rakit/gambar/m1_pipa.svg", "Pipa setelah dipotong"), ("rakit/gambar/pola_m1_pipa_1banding1.svg", "Pola bungkus 1:1 (cetak)")],
        periksa=f"Sisi panjang {f1(GR.PIPA_PANJANG)} mm, sisi pendek {f1(GR.PIPA_PENDEK)} mm. Diletakkan di meja dengan muka miring di bawah, pipa tidak bergoyang.",
        tampil=["tabung"], baru=["tabung"], pandang=[0.0, 0.1, 1.4])
    langkah("Lapisi bagian dalam pipa", "15 menit", [
        "<ol><li>Potong beludru hitam 88 x 26 mm.</li>"
        "<li>Gulung, masukkan dari ujung miring, tepi lurusnya 6,5 mm di bawah ujung tegak lurus (ruang untuk modul sensor).</li>"
        "<li>Rekatkan (beludru berperekat atau lem tipis), lalu potong sisa yang keluar dari muka miring dengan cutter.</li></ol>"],
        awas="Jangan sampai lem merembes ke permukaan beludru: bagian mengilap memantulkan cahaya LED ke chip.",
        tampil=["tabung", "beludru"], baru=["beludru"], potong=[1, 0.0, 1], pandang=[0.0, 0.25, 1.4])
    langkah("Lem pipa ke pelat muka", "15 menit + kering", [
        f"<ol><li>Tandai elips tepi luar pipa di sisi atas pelat (ada di pola): {f1(2 * GR.EL_A)} x 32 mm, pusatnya {f1(GR.EL_X)} mm di depan pusat lubang.</li>"
        "<li>Sisi panjang pipa menghadap ke BELAKANG (ke arah USB), sisi pendek ke depan.</li>"
        "<li>Oles lem PVC di muka miring, tekan di atas elips 1 menit. Tutup sambungan luar dengan silikon hitam setelah kering.</li></ol>"],
        periksa="Intip dari bawah lewat lubang Ø 12: dinding dalam pipa terlihat hitam semua dan lubang berada di tengah pipa.",
        tampil=KEPALA, baru=["tabung", "beludru"], potong=[1, 0.0, 1], pandang=[0.2, 0.3, 1.3])
    langkah("Solder header sensor", "15 menit", [
        "<p>Bila header TCS34725 belum tersolder: plastik header di punggung papan, pin pendek menembus ke sisi komponen, solder di sisi komponen. Solder hanya 7 pin, jangan mengenai komponen kecil di dekatnya.</p>"],
        gambar=[("rakit/gambar/header_sensor.svg", "Arah header sensor")],
        periksa="Ukur dengan multimeter (mode bunyi): tidak ada dua pin bersebelahan yang tersambung.",
        tampil=SENS_ND, baru=pilih(B, "sensor_header", "sensor_pin"), pandang=[0.6, 0.6, 2.2], label=pilih(B, "sensor_header", "sensor_pin", "sensor_chip", "sensor_led"))
    langkah("Cakram dudukan dan baut sensor", "20 menit", [
        f"<ol><li>Potong cakram Ø {f1(2 * R)} dari PVC hitam (pola). Bor 2 lubang Ø 2,8 (mata bor 3) dan buat celah header 18,3 x 3 mm.</li>"
        "<li>Amplas tepi cakram sampai masuk ke pipa dengan pas, tidak longgar.</li>"
        "<li>Baut papan sensor ke cakram: 2 baut M2,5 x 10 hitam dari sisi komponen, mur di punggung cakram. Header menembus celah.</li></ol>"],
        gambar=[("rakit/gambar/m1_cakram.svg", "Cakram dudukan (skala besar)")],
        awas="Sudut celah header sangat dekat ke tepi cakram dan bisa tembus sedikit. Tidak apa-apa: celah itu ditutup silikon di langkah berikut.",
        tampil=SENS_ND + ["dudukan_cakram"], baru=["dudukan_cakram", "sensor_baut"], pandang=[0.6, -0.5, 2.2])
    langkah("Pasang modul sensor ke pipa", "15 menit", [
        "<ol><li>Dorong modul (papan + cakram) ke pipa dari ujung tegak lurus, sisi komponen lebih dulu.</li>"
        "<li>Tekan sampai punggung cakram <b>rata</b> dengan ujung pipa. Tempelkan penggaris melintang: tidak boleh ada celah.</li>"
        "<li>Putar modul: header ke arah sisi panjang pipa (belakang, tanda panah dari langkah 5). Chip dan LED menghadap ke lubang ukur.</li>"
        "<li>Kunci dengan silikon hitam di sekeliling tepi cakram dan di celah header.</li></ol>"],
        gambar=[("rakit/gambar/m1_modul_sensor.svg", "Modul sensor di dalam pipa")],
        periksa=f"Chip berjarak {f1(GA.H_CHIP)} mm dari pusat lubang. Dengan cakram rata di ujung pipa, jarak ini otomatis benar.",
        tampil=KEPALA + SENS_ND + ["dudukan_cakram"], baru=SENS_ND + ["dudukan_cakram"], potong=[1, 0.0, 1], pandang=[0.1, 0.25, 1.6],
        label=["dudukan_cakram", "sensor_pcb", "sensor_chip", "sensor_header"])
    langkah("Rakit kotak", "40 menit + kering", [
        "<ol><li>Lem lantai belakang di belakang pelat muka, sejajar. Lantai 2 mm lebih tinggi dari pelat: gunakan 2 lembar PVC sisa (1 mm + 1 mm, atau kertas karton) sebagai ganjal saat mengelem.</li>"
        "<li>Lem dinding samping kiri dan kanan di atas tepi pelat dan lantai; tangga 2 mm tepat di sambungan pelat-lantai.</li>"
        "<li>Lem dinding depan dan dinding belakang (takik USB di bawah) di antara dinding samping.</li>"
        "<li>Periksa siku dengan penggaris siku sebelum lem kering.</li></ol>"],
        gambar=[("rakit/gambar/m1_sambungan.svg", "Cara menyambung dinding")],
        periksa="Letakkan alat di meja kaca/keramik: hanya pelat muka yang menyentuh, bagian belakang terangkat 2 mm.",
        tampil=KEPALA + SENS_ND + ["dudukan_cakram"] + BADAN, baru=BADAN, pandang=[0.75, 0.45, 1.5])
    langkah("Pasang ESP32", "10 menit", [
        "<ol><li>Tempel busa dobel tape 31 x 20 mm di lantai belakang, 14,5 mm dari dinding belakang.</li>"
        "<li>Letakkan ESP32 terbalik (pin menghadap ke atas) di atas busa, colokan USB masuk ke takik dinding belakang.</li>"
        "<li>Tutup lampu merah daya ESP32 dengan selotip hitam supaya tidak menyinari bagian dalam.</li></ol>"],
        periksa="Kabel USB bisa dicolok dari luar tanpa menggeser ESP32.",
        tampil=KEPALA + SENS_ND + ["dudukan_cakram"] + BADAN + ESP_ND, baru=ESP_ND, samar=pilih(B, "dinding_kiri", "dinding_belakang"), pandang=[-0.9, 1.0, 1.4], fokus=BADAN, label=["esp_pcb", "esp_busa", "esp_usb"])
    langkah("OLED ke tutup atas", "20 menit", [
        "<ol><li>Masukkan 4 baut M2 x 10 dari atas tutup, pasang 1 mur sebagai ganjal di setiap baut (tebal 1,6 mm).</li>"
        "<li>Pasang OLED (layar menghadap jendela, diputar 90°), kunci dengan mur kedua.</li>"
        "<li>Lem 4 bibir di sisi bawah tutup pada garis putus (3,3 mm dari tepi samping).</li>"
        "<li>Cat lingkaran merah Ø 12 tempat ibu jari.</li></ol>"],
        gambar=[("rakit/gambar/m1_oled.svg", "Satu baut OLED")],
        tampil=TUTUP + OLED_ND, baru=OLED_ND + ["bibir"], urai=0.0, pandang=[0.75, -0.6, 1.6])
    langkah("Solder kabel", "60 menit", [
        "<ol><li>Potong 9 kabel sesuai tabel (kolom Potong), kupas 4 mm kedua ujung, lapisi timah. Warna mengikuti tabel.</li>"
        "<li>Sensor dulu (titik S1-S5 di ujung header, di atas cakram): solder satu kabel per pin, tutup selongsong. Pin 3V3 dan INT sensor kosong.</li>"
        "<li>OLED (titik O1-O4): balik tutup atas di meja, solder di ujung pin header OLED.</li>"
        "<li>ESP32 (titik E1-E5, semuanya di baris 3V3): urutan G25, G26, G27, GND, 3V3. Pin dengan dua kabel: kedua kabel masuk ke satu selongsong lalu disolder bersama.</li>"
        "<li>Rapikan jalur seperti model 3D: kabel sensor naik dari ujung pipa lalu ke belakang, kabel OLED turun dari tutup. Kabel tidak boleh menekan modul sensor.</li></ol>",
        kabel_tabel(kabel)],
        gambar=[("rakit/gambar/m1_skema.svg", "Peta titik solder Model 1"), ("rakit/gambar/solder_pin.svg", "Cara menyolder kabel ke pin")],
        periksa="Sebelum menyalakan: multimeter mode bunyi antara E1 (3V3) dan E5 (GND) TIDAK boleh berbunyi; tiap kabel berbunyi dari titik awal ke titik akhirnya.",
        awas="VIN sensor ke 3V3, BUKAN ke 5V. Pin 5V ESP32 berisi 5 V dari USB dan tidak dipakai.",
        tampil=KEPALA + SENS + ["dudukan_cakram"] + BADAN + ESP + OLED + KABEL + ["tutup_atas"], baru=KABEL + ["sensor_dupont", "esp_dupont", "oled_dupont"], samar=["tutup_atas"],
        pandang=[0.75, 0.75, 1.3], label=[])
    langkah("Tutup, unggah firmware, uji", "30 menit", [
        "<ol><li>Pasang tutup (bibir masuk di dalam dinding). Jangan dilem: tutup harus bisa dibuka.</li>"
        "<li>Unggah firmware Data_Latih_Uji.ino (pin SDA G26, SCL G27, LED G25) lewat USB.</li>"
        "<li>Layar menyala dan perintah RAW di Serial Monitor menampilkan angka sensor: rangkaian benar.</li>"
        "<li>Kalibrasi: tempel alat di kertas HVS putih doff, kalibrasi putih; lalu di beludru hitam, kalibrasi hitam.</li>"
        "<li>Uji ulangan: ukur kertas warna yang sama 10 kali sambil mengangkat dan menempel ulang alat. Simpangan R/G harus 0,03 atau kurang.</li></ol>"],
        periksa="Saat ditempel di daging, bacaan LED-mati (Rgelap/Ggelap/Bgelap di RAW) hampir nol. Bila besar, ada cahaya bocor: periksa tepi pelat muka dan silikon.",
        tampil=SEMUA, baru=TUTUP, pandang=[0.75, 0.45, 1.5], label=["tutup_atas", "tanda_tekan"])
    return L, kb, dict(judul="Model 1: Genggam", ringkas=f"{f1(GR.L_TOT)} x {f1(GR.W_TOT)} x {f1(GA.Z_TOP + GA.t)} mm, ditempel ke daging", file="penampil_model1.html")


# ============================================================================ MODEL 2: JEPIT
def model2(GEm=None, GKLm=None, GD="gambar", NM="2", berkas="penampil_model2.html", judul_m="Model 2: Jepit"):
    GEm = GEm or GE; GKLm = GKLm or GKL
    B = GEm.B
    URAI = {"busa_1": 6, "busa_2": 14, "busa_3": 22, "daging": 45, "tutup_cat": 75, "beludru": 75, "dudukan_pelat": 100, "dudukan_pipi": 100,
            "kepala_lantai": 120, "kepala_depan": 135, "kepala_belakang": 135, "kepala_kiri": 135, "kepala_kanan": 135, "engsel_atas": 135, "kait_atas": 135,
            "kepala_tutup": 200, "kepala_bibir": 200}
    def urai(k):
        if k in URAI: return URAI[k]
        if k.startswith("sensor_"): return 92
        if k.startswith("esp_") or k == "bb_papan": return 145
        if k.startswith("oled_"): return 180
        return 0
    hinge = dict(x=GEm.SUMBU_ENGSEL[0], z=GEm.SUMBU_ENGSEL[1], yc=GEm.YC)
    kb = penampil(B, urai, hinge, f"BeefFresh Model {NM}: langkah rakit", berkas, grup_aks=("kal_putih", "kal_hitam"))
    BAKI = pilih(B, "baki_*"); BUSA = pilih(B, "busa_*")
    KEP = pilih(B, "kepala_lantai", "kepala_depan", "kepala_belakang", "kepala_kiri", "kepala_kanan")
    PVC = BAKI + KEP + pilih(B, "kepala_tutup", "kepala_bibir", "dudukan_*")
    SENS = pilih(B, "sensor_*"); SENS_ND = [k for k in SENS if k != "sensor_dupont"]
    DUD = pilih(B, "dudukan_*"); CAT = ["tutup_cat", "beludru"]
    ESP = pilih(B, "esp_*", "bb_papan"); ESP_ND = [k for k in ESP if k != "esp_dupont"]
    OLED = pilih(B, "oled_*"); OLED_ND = [k for k in OLED if k != "oled_dupont"]
    KABEL = pilih(B, "kabel_*"); ENG = pilih(B, "engsel_*", "kait_*")
    SEMUA = [k for k in B if not k.startswith("kal_")]
    J = GEm.JENDELA; W = GEm.W; YC = GEm.YC
    K = GEm.KABEL
    def ln(k): return K[k]["panjang"]
    kabel = daftar_kabel(K)
    L = []
    def langkah(judul, waktu, isi, gambar=(), periksa="", awas="", **v3):
        L.append(dict(judul=judul, waktu=waktu, isi=isi, gambar=list(gambar), periksa=periksa, awas=awas, v3=v3))
    langkah("Siapkan bahan dan alat", "15 menit", [
        bom([("PVC board 3 mm", "± 570 cm² (± 24 x 24 cm)", "15 jenis potongan; pelat dudukan dan pipi dari PVC hitam"),
             ("Tutup cat semprot Ø 65", "1", "dipotong 22 mm dari muka"), ("ESP32 NodeMCU-32S 38 pin, TCS34725, OLED 0,96 inci I2C", "1 set", "sudah ada"),
             ("Busa ati / EVA lunak hitam", f"3 lembar {f1(GEm.W - 8)} x {f1(GEm.W - 8)} x 10 mm", "penekan daging"), ("Kertas beludru hitam (flok)", "± 20 x 20 cm", "pelapis tutup cat; pengganti: flanel hitam"),
             ("Engsel kupu-kupu 25 mm", "2", "dengan 8 baut M3 x 10 + mur"), ("Kait kotak kecil", "1", "pengunci depan"), ("Tali nilon", "15 cm", "pembatas buka ± 100°"),
             ("Baut M2,5 x 10 hitam + mur", "2", "sensor"), ("Baut M2 x 10 + mur", "4 + 8", "OLED: 1 mur ganjal + 1 mur pengunci per baut"),
             ("Kabel serabut 24-26 AWG: merah, hitam, kuning, biru, hijau", f"± {f1(sum(GKL.potong_cm(d[3]) for d in kabel) + 10)} cm total", "boleh kabel dupont yang dipotong soketnya; panjang tiap kabel di tabel kabel"), ("Selongsong panas Ø 2 mm", "14 x 15 mm", "1 per titik solder"),
             ("Busa dobel tape 3 mm, lem PVC, silikon hitam, selotip hitam", "sedikit", ""), ("Kertas HVS putih doff + beludru hitam", "untuk tatakan kalibrasi", ""),
             ("Plastik wrap", "1 lembar baru per sampel", "pelindung busa")]),
        f"<p><b>Alat:</b> {ALAT}</p>"], gambar=[("rakit/gambar/cara_baca.svg", "Cara membaca semua gambar kerja")],
        tampil=SEMUA, baru=[], pandang=[-0.75, 0.42, 1.5])
    langkah("Cetak pola 1:1", "10 menit", [
        "<ol><li>Cetak pola kecil 1:1 (pipi, pelat dudukan) dengan skala <b>100 %</b>. Ukur garis uji 50 mm.</li>"
        f"<li>Lembar besar ({f1(W)} mm) cukup diukur langsung dari gambar kerja: semuanya persegi panjang.</li></ol>",
        '<p class="dl"><a href="jepit/gambar/5_pola_1banding1.svg" target="_blank">Pola kecil 1:1</a></p>'],
        gambar=[(f"jepit/{GD}/5_pola_1banding1.svg", "Pola kecil 1:1")], tampil=PVC, baru=PVC, urai=0.45, pandang=[-0.75, 0.3, 1.25], label=[])
    langkah("Potong panel PVC", "60 menit", [
        "<ol><li>Gores 3-5 kali dengan cutter dan penggaris besi, lalu patahkan. Amplas tepi sampai lurus dan siku.</li>"
        f"<li>Baki: lantai {f1(W)} x {f1(W)}, dinding depan dan belakang {f1(W)} x {f1(GEm.F + GEm.Hc)}, dinding kiri dan kanan {f1(W - 2 * GEm.t)} x {f1(GEm.F + GEm.Hc)}.</li>"
        f"<li>Kepala: lantai {f1(W)} x {f1(W)} dengan jendela kabel {f1(J[1] - J[0])} x {f1(J[3] - J[2])}, 4 dinding setinggi {f1(GEm.P['kepala_dalam'])} mm, tutup atas dengan jendela OLED 25 x 15.</li>"
        "<li>Takik USB 13 x 10 di tepi bawah dinding kiri kepala.</li></ol>", CARA_UKUR,
        daftar_potong([GKLm.lembar_baki, GKLm.lembar_kepala, GKLm.lembar_kecil], GKLm)],
        gambar=[(f"jepit/{GD}/8_lembar_baki.svg", "Lembar baki"), (f"jepit/{GD}/9_lembar_kepala.svg", "Lembar kepala"), (f"jepit/{GD}/10_lembar_kecil.svg", "Lembar kecil")],
        periksa="Lantai baki dan lantai kepala ditumpuk: keempat tepinya rata.",
        tampil=PVC, baru=BAKI + KEP + ["kepala_tutup", "kepala_bibir"], urai=0.45, pandang=[-0.75, 0.3, 1.25], label=[])
    langkah("Siapkan tutup cat", "30 menit", [
        "<p>Tutup cat semprot yang dipakai berukuran <b>Ø 65 mm</b> (lebar luar) dan tinggi utuh sekitar 50 mm. "
        "Tanda <b>Ø</b> (huruf O dicoret, bukan angka nol) artinya <b>diameter</b>: lebar lingkaran diukur melewati pusatnya. Semua angka dalam milimeter.</p>"
        "<ol><li>Tandai 22 mm dari muka (bagian tutup yang tertutup) di 4 sisi, lilitkan selotip lurus di tanda itu, lalu gergaji. Sisa bagian atas dibuang. Tinggi jadi: <b>22 mm</b>.</li>"
        "<li>Cari pusat muka dengan 2 garis tengah bersilangan. Bor bertahap Ø 4, 8, 12 mm, lalu kikir bulat sampai <b>Ø 14 mm</b> (lubang selebar 14 mm). Haluskan tepinya.</li>"
        "<li>Jangan cat muka luar: muka luar menyentuh daging lewat plastik wrap.</li></ol>"],
        gambar=[("rakit/gambar/tutup_cat.svg", "Tutup cat: potong 22 mm, lubang Ø 14"), (f"jepit/{GD}/2_ruang_ukur.svg", "Ruang ukur")],
        periksa="Ukur dengan jangka sorong: tinggi 22 mm di keempat sisi (selisih paling banyak 0,5 mm) dan lubang 14 mm. Bila tutupmu bukan Ø 65, kabari Lyra.",
        tampil=["tutup_cat"], baru=["tutup_cat"], potong=[1, YC, 1], pandang=[-0.2, -0.35, 1.4])
    langkah("Lapisi bagian dalam tutup cat", "20 menit", [
        "<p>Pelapis beludru hitam (kertas flok berperekat) <b>tebalnya sekitar 0,8 mm</b>; di model dipakai 0,8 mm. Kain flanel hitam (1-1,5 mm) juga boleh. "
        "Angka 62 x 62 x 20,5 di model 3D adalah ukuran luar seluruh pelapis (diameter dalam tutup 62, tinggi 20,5), bukan tebalnya. Pelapis dipotong menjadi 2 bagian:</p>"
        "<ol><li><b>Cakram muka:</b> lingkaran Ø 62 mm dengan lubang Ø 16 mm di pusatnya. Lubang dibuat 2 mm lebih besar dari lubang tutup (Ø 14) supaya tepi beludru tidak terlihat sensor.</li>"
        "<li><b>Pita dinding:</b> 192 x 19,7 mm (panjang = keliling dalam, tinggi = dari atas cakram sampai tepi potong). Tempel melingkar di dinding dalam, ujungnya bertemu tanpa tumpang. "
        "Bila memakai flanel 1,5 mm, potong pita 188 mm.</li>"
        "<li>Tempel cakram dulu, baru pita di atasnya. Tekan rata, jangan ada lem yang mengilap di permukaan.</li></ol>"
        "<p>Bila memakai cat hitam doff sebagai pengganti: 2 lapis tipis, biarkan kering sekitar sehari sampai tidak berbau.</p>"],
        tampil=CAT, baru=["beludru"], potong=[1, YC, 1], pandang=[-0.2, 0.5, 1.4])
    langkah("Dudukan miring 40°", "20 menit", [
        "<ol><li>Bor 2 lubang Ø 2,8 di pelat dudukan sesuai pola.</li>"
        "<li>Rekatkan kedua pipi trapesium di punggung pelat, di sisi tepi panjangnya, sisi miring 40° menempel pelat.</li></ol>"],
        gambar=[(f"jepit/{GD}/10_lembar_kecil.svg", "Pelat dudukan dan pipi")],
        tampil=DUD, baru=DUD, pandang=[-0.4, 0.3, 2.0])
    langkah("Solder header dan pasang sensor", "25 menit", [
        "<ol><li>Solder header 7 pin: plastik di punggung papan, solder di sisi komponen.</li>"
        "<li>Baut papan ke pelat dudukan dengan 2 baut M2,5 hitam dari sisi komponen, mur di punggung pelat. Header menghadap punggung.</li>"
        "<li><b>Solder 5 kabel sensor sekarang</b> (titik S1-S5: LED, SDA, SCL, GND, VIN; pin INT dan 3V3 kosong), karena setelah dudukan dilem pin sulit dijangkau. Panjang dan warna dari tabel kabel di langkah 13.</li></ol>"],
        gambar=[("rakit/gambar/header_sensor.svg", "Arah header sensor"), ("rakit/gambar/solder_pin.svg", "Cara menyolder kabel ke pin")],
        tampil=DUD + SENS_ND, baru=SENS_ND, pandang=[-0.4, -0.2, 2.0], label=pilih(B, "sensor_pcb", "sensor_header", "sensor_baut", "sensor_chip"))
    langkah("Siapkan lantai kepala", "15 menit", [
        f"<ol><li>Potong jendela kabel {f1(J[1] - J[0])} x {f1(J[3] - J[2])} mm sesuai pola dan denah.</li>"
        f"<li>Tandai pusat tutup cat di sisi BAWAH lantai: {f1(GEm.XC)} mm dari depan dan {f1(GEm.YC)} mm dari kiri. Tandai juga letak kedua pipi (garis putus di gambar).</li></ol>"],
        gambar=[(f"jepit/{GD}/3_denah_lantai_kepala.svg", "Denah lantai kepala")],
        tampil=["kepala_lantai"], baru=["kepala_lantai"], pandang=[-0.75, 1.1, 1.4])
    langkah("Rekatkan dudukan di bawah lantai", "15 menit + kering", [
        "<p>Masukkan 5 kabel sensor lewat jendela dari bawah, lalu rekatkan sisi atas kedua pipi ke lantai pada posisi denah. Chip menghadap ke depan dan ke bawah, ke arah pusat lubang.</p>"],
        tampil=["kepala_lantai"] + DUD + SENS, baru=DUD + SENS, pandang=[-0.9, -0.45, 1.2], label=["dudukan_pelat", "sensor_pcb", "sensor_dupont"])
    langkah("Periksa, lalu rekatkan tutup cat", "15 menit", [
        "<ol><li>Letakkan tutup cat di atas tanda pusat, intip lewat lubang Ø 14: chip harus terlihat di sisi belakang lubang.</li>"
        "<li>Bila sudah benar, rekatkan tepi tutup cat dengan silikon hitam di sekelilingnya.</li></ol>"],
        gambar=[(f"jepit/{GD}/1_potongan.svg", "Potongan tengah alat")],
        tampil=["kepala_lantai"] + DUD + SENS + CAT, baru=CAT, potong=[1, YC, 1], pandang=[-0.05, -0.15, 1.3])
    langkah("Rakit baki dan kotak kepala", "50 menit + kering", [
        "<ol><li>Baki: lantai dan 4 dinding. Kepala: 4 dinding di atas lantai kepala.</li>"
        "<li>Takik USB 13 x 10 mm di tepi bawah dinding kiri kepala, pusatnya 20 mm dari depan.</li>"
        "<li>Lem bibir di sisi bawah tutup atas.</li></ol>"],
        gambar=[("rakit/gambar/m2_sambungan.svg", "Cara menyambung dinding")],
        periksa="Kepala diletakkan di atas baki: keempat sisi rata, tidak ada celah cahaya.",
        tampil=BAKI + KEP + DUD + SENS + CAT, baru=BAKI + KEP, pandang=[-0.75, 0.42, 1.8], label=[])
    langkah("Pasang ESP32 dan OLED", "25 menit", [
        "<ol><li>ESP32 terbalik di atas busa dobel tape, colokan USB menghadap takik. Tutup lampu merah dayanya dengan selotip hitam.</li>"
        "<li>OLED dibaut ke tutup atas menghadap jendela: baut M2 x 10 dari atas, 1 mur ganjal (1,6 mm) di antara tutup dan PCB, 1 mur pengunci di bawah PCB.</li></ol>"],
        gambar=[("rakit/gambar/m2_oled.svg", "Satu baut OLED")],
        tampil=BAKI + KEP + DUD + SENS + CAT + ESP_ND + OLED_ND + ["kepala_tutup", "kepala_bibir"], baru=ESP_ND + OLED_ND, samar=["kepala_tutup", "kepala_bibir"],
        pandang=[-0.75, 0.8, 1.2], fokus=KEP + ["kepala_tutup"], label=["esp_pcb", "esp_usb", "oled_pcb"])
    langkah("Solder kabel ke ESP32 dan OLED", "50 menit", [
        "<ol><li>Potong 4 kabel OLED sesuai tabel, solder ke titik O1-O4 di ujung pin OLED (tutup atas dibalik di meja).</li>"
        "<li>Angkat ESP32 dari busa supaya mudah disolder. Solder titik E1-E5 (semuanya di baris 3V3) dengan urutan G25, G26, G27, GND, 3V3. "
        "Pin dengan dua kabel (sensor dan OLED): kedua kabel masuk ke satu selongsong lalu disolder bersama.</li>"
        "<li>Kembalikan ESP32 ke busa, rapikan jalur seperti denah dan model 3D. Tutup jendela kabel dari atas dengan selotip hitam di sekeliling kabel.</li></ol>",
        kabel_tabel(kabel)],
        gambar=[("rakit/gambar/m2_skema.svg", "Peta titik solder Model 2"), ("rakit/gambar/solder_pin.svg", "Cara menyolder kabel ke pin"), (f"jepit/{GD}/7_denah_kabel.svg", "Denah jalur kabel di kepala")],
        periksa="Sebelum menyalakan: multimeter mode bunyi antara E1 (3V3) dan E5 (GND) TIDAK boleh berbunyi; tiap kabel berbunyi dari titik awal ke titik akhirnya.",
        awas="VIN sensor ke 3V3, BUKAN ke 5V. Pin 5V ESP32 tidak dipakai.",
        tampil=BAKI + KEP + DUD + SENS + CAT + ESP + OLED + KABEL + ["kepala_tutup", "kepala_bibir"], baru=KABEL + ["sensor_dupont", "esp_dupont", "oled_dupont"],
        samar=["kepala_tutup", "kepala_bibir"], pandang=[-0.75, 0.9, 1.2], fokus=KEP, label=[])
    langkah("Engsel, kait, tali pembatas", "30 menit", [
        "<ol><li>Tempatkan kepala di atas baki. Pasang 2 engsel di sisi belakang dengan baut M3 dan mur, poros tepat di garis sambungan.</li>"
        "<li>Pasang kait di sisi depan.</li><li>Ikat tali pembatas antara sisi kepala dan sisi baki supaya kepala berhenti di sekitar 100°.</li></ol>"],
        gambar=[(f"jepit/{GD}/4_terbuka.svg", "Alat terbuka")],
        periksa="Buka sampai berhenti: alat tidak terguling ke belakang.",
        tampil=[k for k in SEMUA if k not in BUSA + ["daging"]], baru=ENG, engsel=60, pandang=[0.9, 0.3, 1.4], fokus=BAKI + KEP)
    langkah("Busa, firmware, uji", "40 menit", [
        "<ol><li>Masukkan 3 lapis busa ke baki.</li><li>Unggah firmware (SDA G26, SCL G27, LED G25). Layar menyala dan perintah RAW menampilkan angka.</li>"
        "<li>Kalibrasi sekali per sesi: balok putih di atas busa, tutup, kalibrasi putih; balok hitam, kalibrasi hitam.</li>"
        "<li>Daging diiris 10 mm (minimal 30 x 30 mm), di atas plastik wrap baru, tutup, kunci, tunggu 3 detik, Ambil.</li></ol>"],
        periksa="Uji ulangan 10 kali pada kertas warna yang sama: simpangan R/G 0,03 atau kurang.",
        tampil=SEMUA, baru=BUSA + ["daging"], engsel=95, pandang=[-1.35, 0.85, 1.7], fokus=BAKI)
    return L, kb, dict(judul=judul_m, ringkas="86 x 86 x 106 mm, daging dimasukkan", file=berkas)


# ============================================================================ halaman
CSS = open(os.path.join(HERE, "rakit.css")).read()
JS = open(os.path.join(HERE, "rakit.js")).read()


def muat_bb():
    """Muat geometri dan gambar varian breadboard sebagai modul terpisah."""
    import importlib.util
    os.environ["JEPIT_VARIAN"] = "breadboard"
    sp = importlib.util.spec_from_file_location("geometri_bb", os.path.join(DES, "jepit", "geometri.py")); g = importlib.util.module_from_spec(sp); sp.loader.exec_module(g)
    os.environ["JEPIT_VARIAN"] = "solder"
    sp = importlib.util.spec_from_file_location("gkl_bb", os.path.join(DES, "jepit", "gambar_kabel_lembar.py")); k = importlib.util.module_from_spec(sp); sp.loader.exec_module(k); k.G = g
    return g, k


def kabel_tabel_bb(G_):
    T = GKL.TITIK_ESP; r = []
    for i, kb in enumerate(sorted(G_.KABEL.values(), key=lambda kb: (T.index(kb["ke"]), kb["dari"].startswith("OLED"))), 1):
        dev, pin = kb["dari"].split(); rb, cb = kb["lubang"]
        r.append(f'<tr><td><i class="kw" style="background:{kb["warna"]}"></i>{i}</td><td><b>baris {rb}, kolom {cb}</b></td><td>{kb["ke"]}</td><td>{GKL.titik_dev(dev, pin)} {dev} {pin}</td><td>{f1(kb["panjang"])}</td><td>{G_.NAMA_WARNA[G_.SINYAL[kb["ke"]]]}</td></tr>')
    return ('<div class="tw"><table class="kt"><tr><th>No</th><th>Lubang breadboard</th><th>Pin ESP32</th><th>Ujung betina ke</th><th>Jalur di model (mm)</th><th>Warna</th></tr>' + "".join(r) + "</table></div>"
            '<p class="mut">Semua kabel dupont jantan-betina 10 cm: ujung jantan ke lubang breadboard, ujung betina ke pin sensor atau OLED. Sisa panjang dilipat rapi di samping breadboard.</p>')


def model2b():
    G_, K_ = muat_bb()
    L, kb, info = model2(G_, K_, "gambar_bb", "2B", "penampil_model2b.html", "Model 2B: Jepit + breadboard")
    W = G_.W; TK = G_.TAKIK; zk0 = G_.Hc + G_.t
    open(os.path.join(DES, "rakit", "gambar", "m2b_sambungan.svg"), "w").write(GR.sambungan(
        "Model 2B: cara menyambung dinding baki dan kepala (dilihat dari atas)", W, W, G_.t, "y",
        dict(depan="DEPAN (kait)", belakang="BELAKANG (engsel, breadboard)", atas="dinding kanan (lubang USB)", bawah="dinding kiri"), f"lantai {f1(W)} x {f1(W)} di bawah semua dinding",
        [f"Dinding depan dan belakang {f1(W)} (luar penuh). Dinding kiri dan kanan {f1(W - 2 * G_.t)} mm masuk DI ANTARA keduanya: {f1(W)} - 3 - 3 = {f1(W - 2 * G_.t)}.",
         "Sama untuk baki dan kepala. Semua dinding BERDIRI DI ATAS lantainya; lantai tidak dijepit di antara dinding."]))
    def ganti_li(i, lama, baru):
        isi = L[i]["isi"]
        for j, x in enumerate(isi):
            if isinstance(x, str) and lama in x: isi[j] = x.replace(lama, baru); return
        raise KeyError(lama[:40])
    # 1. bahan
    K_.DAFTAR.clear(); K_.lembar_baki(); K_.lembar_kepala(); K_.lembar_kecil()
    luas = sum(w * h * j for _, judul, w, h, j, _c in K_.DAFTAR if "kalibrasi" not in judul.lower()) / 100
    L[0]["isi"][0] = bom([("PVC board 3 mm", f"± {math.ceil(luas * 1.15 / 10) * 10} cm²", "termasuk 15 % sisa potong; pelat dudukan dan pipi dari PVC hitam"),
        ("Tutup cat semprot Ø 65", "1", "dipotong 22 mm dari muka"), ("ESP32 NodeMCU-32S 38 pin, TCS34725, OLED 0,96 inci I2C", "1 set", "sudah ada"),
        ("Breadboard 400 lubang 8,5 x 5,5 cm", "1", "kedua rel daya dilepas; ditempel di dinding belakang kepala dengan perekat bawaannya"),
        ("Kabel dupont jantan-betina 10 cm", "9", "merah 2, hitam 2, kuning 2, biru 2, hijau 1"),
        ("Busa ati / EVA lunak hitam", f"3 lembar {f1(W - 8)} x {f1(W - 8)} x 10 mm", "penekan daging"), ("Kertas beludru hitam (flok)", "± 20 x 20 cm", "pelapis tutup cat; pengganti: flanel hitam"),
        ("Engsel kupu-kupu 25 mm", "2", "dengan 8 baut M3 x 10 + mur"), ("Kait kotak kecil", "1", "pengunci depan"), ("Tali nilon", "15 cm", "pembatas buka ± 100°"),
        ("Baut M2,5 x 10 hitam + mur", "2", "sensor"), ("Baut M2 x 10 + mur", "4 + 8", "OLED: 1 mur ganjal + 1 mur pengunci per baut"),
        ("Lem PVC, silikon hitam, selotip hitam", "sedikit", ""), ("Kertas HVS putih doff + beludru hitam", "untuk tatakan kalibrasi", ""), ("Plastik wrap", "1 lembar baru per sampel", "pelindung busa")])
    # 3. potong panel
    ganti_li(2, "<li>Takik USB 13 x 10 di tepi bawah dinding kiri kepala.</li>", "<li>Lubang USB 13 x 10 di dinding kanan kepala (lihat lembar kepala).</li>")
    # 7. sensor: colok dupont, tanpa solder kabel
    ganti_li(6, L[6]["isi"][0][L[6]["isi"][0].index("<li><b>Solder 5 kabel sensor sekarang</b>"):L[6]["isi"][0].index("</ol>")],
             "<li><b>Colok 5 kabel dupont sekarang</b> (ujung betina) ke pin header sensor: LED, SDA, SCL, GND, VIN. Pin INT dan 3V3 kosong. "
             "Warna mengikuti peta colokan di langkah 13. Lilitkan selotip tipis di kelima soket supaya tidak lepas.</li>")
    L[6]["gambar"] = [g for g in L[6]["gambar"] if "solder_pin" not in g[0]]
    # 11. rakit baki dan kepala
    ganti_li(10, "<li>Takik USB 13 x 10 mm di tepi bawah dinding kiri kepala, pusatnya 20 mm dari depan.</li>",
             f"<li>Lubang USB 13 x 10 mm di dinding kanan kepala: pusatnya {f1(TK['x'])} mm dari depan dan {f1((TK['z0'] + TK['z1']) / 2 - zk0)} mm dari tepi bawah dinding.</li>")
    L[10]["gambar"] = [("rakit/gambar/m2b_sambungan.svg", "Cara menyambung dinding")]
    # 12. breadboard, ESP32, OLED
    L[11]["judul"] = "Pasang breadboard, ESP32, dan OLED"
    L[11]["isi"] = ["<ol><li>Lepas kedua rel daya breadboard (geser keluar dari alurnya). Rel tidak dipakai.</li>"
                    "<li>Tempel breadboard di dinding belakang kepala dengan perekat bawaannya: berdiri di atas lantai kepala, merapat ke dinding kanan, "
                    "<b>baris 30 di sisi lubang USB</b> dan <b>kolom a di atas</b>.</li>"
                    "<li>Colok ESP32: baris pin yang ada tulisan 3V3 masuk ke <b>kolom c</b>, baris seberangnya ke kolom j, pin 5V di baris 30 dan pin 3V3 di baris 12. "
                    "Sisi komponen menghadap ke depan. Colokan USB tepat di depan lubang USB dinding kanan.</li>"
                    "<li>Kolom a dan b di samping pin ESP32 tetap kosong: tempat mencolok kabel.</li>"
                    "<li>OLED dibaut ke tutup atas menghadap jendela: baut M2 x 10 dari atas, 1 mur ganjal (1,6 mm) di antara tutup dan PCB, 1 mur pengunci di bawah PCB.</li></ol>"]
    L[11]["gambar"] = [("jepit/gambar_bb/6_skema_kabel.svg", "Letak ESP32 di breadboard"), ("rakit/gambar/m2_oled.svg", "Satu baut OLED")]
    L[11]["periksa"] = "Kabel USB bisa dicolok dari luar lewat lubang dinding kanan tanpa menggeser ESP32."
    _bawah = [k for k in G_.B if k.startswith("baki_") or k.startswith("busa_") or k in ("daging", "tutup_cat", "beludru", "engsel_bawah", "kait_bawah") or k.startswith("kal_")]
    for i_ in (11, 12):
        L[i_]["v3"]["tampil"] = [k for k in L[i_]["v3"]["tampil"] if k not in _bawah]
    L[11]["v3"].update(label=["bb_papan", "esp_pcb", "esp_usb", "oled_pcb"], samar=["kepala_tutup", "kepala_bibir", "kepala_depan"], pandang=[-1.45, 0.4, 1.3])
    L[12]["v3"].update(samar=["kepala_tutup", "kepala_bibir", "kepala_depan"] + [k for k in G_.B if k.startswith("oled_")], pandang=[-1.35, 0.5, 1.25])
    # 13. colok kabel
    L[12]["judul"] = "Colok kabel"
    L[12]["waktu"] = "20 menit"
    L[12]["isi"] = ["<ol><li>Colok 4 kabel dupont (ujung betina) ke pin OLED: GND, VCC, SCL, SDA.</li>"
                    "<li>Colok ujung jantan kesembilan kabel ke lubang breadboard sesuai tabel: kabel sensor di kolom b, kabel OLED di kolom a, sebaris dengan pin ESP32-nya.</li>"
                    "<li>Rapikan jalur seperti denah dan model 3D. Tutup jendela kabel dari atas dengan selotip hitam di sekeliling kabel.</li></ol>",
                    kabel_tabel_bb(G_)]
    L[12]["gambar"] = [("jepit/gambar_bb/6_skema_kabel.svg", "Peta colokan breadboard Model 2B"), ("jepit/gambar_bb/7_denah_kabel.svg", "Denah jalur kabel di kepala")]
    L[12]["periksa"] = "Sebelum menyalakan: hitung ulang tiap colokan dari tabel. Multimeter mode bunyi antara baris 12 (3V3) dan baris 25 (GND) TIDAK boleh berbunyi."
    L[12]["awas"] = "VIN sensor ke baris 12 (3V3), BUKAN baris 30 (5V). Jangan colok apa pun di baris 30."
    info["ringkas"] = info["ringkas"].replace("jepit", "jepit") + ", ESP32 di breadboard tanpa solder kabel"
    return L, kb, info


def ukuran_svg(src):
    import re
    t = open(os.path.join(DES, src)).read(3000)
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', t)
    return (round(float(m.group(3))), round(float(m.group(4)))) if m else (1000, 600)


def halaman(no, L, info, lain):
    tab = "".join(f'<a href="rakit_model{n}.html">{lbl.replace(": ", '<span class="nm">: ') + "</span>"}</a>' for n, lbl in lain)
    kartu = []
    for i, s in enumerate(L, 1):
        g = "".join(f'<figure><a href="{html.escape(src)}" target="_blank"><img src="{html.escape(src)}" alt="{html.escape(cap)}" loading="lazy" width="{ukuran_svg(src)[0]}" height="{ukuran_svg(src)[1]}"></a><figcaption>{cap} <span>ketuk untuk memperbesar</span></figcaption></figure>' for src, cap in s["gambar"])
        isi = "".join(x if x.lstrip().startswith("<") else f"<p>{x}</p>" for x in s["isi"])
        kartu.append(f'''<article class="step" id="l{i}" data-i="{i - 1}">
 <header><span class="no">{i}</span><div><h2>{s["judul"]}</h2><span class="wkt">± {s["waktu"]}</span></div><label class="ok"><input type="checkbox"> selesai</label></header>
 <div class="isi">{isi}</div>{g and '<div class="gb">' + g + '</div>'}
 {f'<p class="periksa"><b>Periksa:</b> {s["periksa"]}</p>' if s["periksa"] else ""}{f'<p class="awas"><b>Hati-hati:</b> {s["awas"]}</p>' if s["awas"] else ""}
</article>''')
    data = json.dumps([s["v3"] for s in L])
    nav = "".join(f'<a href="#l{i}">{i}</a>' for i in range(1, len(L) + 1))
    T = f'''<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0F1012">
<title>BeefFresh: tur rakit {info["judul"]}</title><style>{CSS}</style></head><body>
<nav class="top"><b>Beef<span>Fresh</span></b><a class="on" href="rakit_model{no}.html">{info["judul"].replace(": ", '<span class="nm">: ') + "</span>"}</a>{tab}<a href="tur.html">Tur desain</a><span id="prog">0/{len(L)}</span></nav>
<header class="hero"><span class="kick">Tur rakit · langkah demi langkah</span><h1>{info["judul"]}</h1><p>{info["ringkas"]}. {len(L)} langkah. Gulir pelan: model 3D di samping mengikuti langkah yang sedang dibaca, bagian yang dipasang berwarna merah berdenyut. Semua ukuran dalam milimeter dan diambil langsung dari model yang sama.</p></header>
<div class="wrap"><aside class="stage"><iframe id="v" src="rakit/{info["file"]}" title="Model 3D langkah rakit"></iframe><div class="stepnav">{nav}</div></aside>
<main class="steps">{"".join(kartu)}
<p class="foot">Ukuran yang masih anggapan: tebal PVC 3 mm, Ø pipa 1 inci 32 mm (Model 1), Ø dalam tutup cat 62 mm (Model 2). Ukur bahanmu sebelum memotong; bila berbeda, kabari Lyra supaya model dihitung ulang.</p></main></div>
<script>const LANGKAH={data};const KUNCI="beeffresh_rakit_{no}";{JS}</script></body></html>'''
    open(os.path.join(DES, f"rakit_model{no}.html"), "w").write(T)
    return len(T) // 1024


if __name__ == "__main__":
    L1, k1, i1 = model1(); L2, k2, i2 = model2(); L3, k3, i3 = model2b()
    T1, T2, T3 = (1, "Model 1: Genggam"), (2, "Model 2: Jepit"), ("2b", "Model 2B: Breadboard")
    h1 = halaman(1, L1, i1, [T2, T3]); h2 = halaman(2, L2, i2, [T3, T1]); h3 = halaman("2b", L3, i3, [T2, T1])
    print(f"Model 1: {len(L1)} langkah, {h1} KB, penampil {k1} KB; Model 2: {len(L2)} langkah, {h2} KB, penampil {k2} KB; Model 2B: {len(L3)} langkah, {h3} KB, penampil {k3} KB")

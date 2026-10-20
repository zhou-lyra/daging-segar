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


def kabel_tabel(daftar):
    """daftar: (warna, dari, ke, panjang_model_mm, catatan)."""
    r = []
    for i, (w, dari, ke, L, cat) in enumerate(daftar, 1):
        jadi = math.ceil((L + 20) / 5) * 5
        cara = "kabel 10 cm utuh" if jadi <= 100 else ("kabel 20 cm utuh, lipat sisanya" if jadi <= 200 else "kabel 30 cm")
        if cat: cara = cat
        r.append(f'<tr><td><i class="kw" style="background:{w}"></i>{i}</td><td>{dari}</td><td>{ke}</td><td>{f1(L)}</td><td><b>{f1(jadi / 10)} cm</b></td><td>{cara}</td></tr>')
    return ('<div class="tw"><table class="kt"><tr><th>No</th><th>Dari</th><th>Ke ESP32</th><th>Jalur di model (mm)</th><th>Panjang jadi</th><th>Kabel</th></tr>' + "".join(r) + "</table></div>"
            '<p class="mut">Panjang jadi = jalur di model + 2 cm cadangan, dari ujung soket ke ujung soket. Kabel Y: tangkai 3 cm di pin ESP32, lalu dua cabang.</p>')


def bom(baris):
    return '<div class="tw"><table class="kt"><tr><th>Bahan</th><th>Jumlah</th><th>Catatan</th></tr>' + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in baris) + "</table></div>"


ALAT = ("Cutter besar + penggaris besi 30 cm, penggaris siku, jangka sorong (sangat membantu), spidol halus, selotip kertas, gergaji besi kecil, bor tangan "
        "dengan mata bor 2, 2,5, 3, 4, 8 dan 12 mm (atau mata bor bertingkat), kikir bulat dan setengah bulat, amplas 240, solder 30-60 W + timah 0,8 mm, "
        "korek atau pemanas untuk selongsong, multimeter, lem PVC atau lem tembak, silikon hitam.")


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
    kabel = [(K["kabel_s_VIN"]["warna"], "Sensor VIN", "3V3 (Y)", ln("kabel_s_VIN") - 30, "cabang Y 3V3"), (K["kabel_o_VCC"]["warna"], "OLED VCC", "3V3 (Y)", ln("kabel_o_VCC") - 30, "cabang Y 3V3"),
             (K["kabel_s_SDA"]["warna"], "Sensor SDA", "GPIO 21 (Y)", ln("kabel_s_SDA") - 30, "cabang Y GPIO 21"), (K["kabel_o_SDA"]["warna"], "OLED SDA", "GPIO 21 (Y)", ln("kabel_o_SDA") - 30, "cabang Y GPIO 21"),
             (K["kabel_s_SCL"]["warna"], "Sensor SCL", "GPIO 22 (Y)", ln("kabel_s_SCL") - 30, "cabang Y GPIO 22"), (K["kabel_o_SCL"]["warna"], "OLED SCL", "GPIO 22 (Y)", ln("kabel_o_SCL") - 30, "cabang Y GPIO 22"),
             (K["kabel_s_GND"]["warna"], "Sensor GND", nama("GND", 1), ln("kabel_s_GND"), ""), (K["kabel_o_GND"]["warna"], "OLED GND", nama("GND", 0), ln("kabel_o_GND"), ""),
             (K["kabel_s_LED"]["warna"], "Sensor LED", "GPIO 26", ln("kabel_s_LED"), "")]
    L = []
    def langkah(judul, waktu, isi, gambar=(), periksa="", awas="", **v3):
        L.append(dict(judul=judul, waktu=waktu, isi=isi, gambar=list(gambar), periksa=periksa, awas=awas, v3=v3))
    langkah("Siapkan bahan dan alat", "15 menit", [
        bom([("PVC board 3 mm putih/abu", f"± {math.ceil(luas_putih)} cm²", "dinding, lantai, tutup, bibir; sisa potongan tutup cat tidak dipakai"),
             ("PVC board 3 mm HITAM", f"± {math.ceil(luas_hitam)} cm²", "pelat muka dan cakram; boleh PVC putih yang dicat hitam doff 2 lapis"),
             ("Pipa PVC 1 inci (Ø luar 32)", "4 cm", "potongan sisa sudah cukup"),
             ("ESP32 DOIT DevKit V1, TCS34725, OLED 0,96 inci I2C", "1 set", "sudah ada"),
             ("Baut M2,5 x 10 hitam + mur", "2", "papan sensor ke cakram"), ("Baut M2 x 10 + mur", "4 + 8", "OLED: 1 mur ganjal dan 1 mur pengunci per baut"),
             ("Kabel dupont betina-betina 10 cm dan 20 cm", "± 12", "jumlah tiap panjang: tabel kabel di langkah 14"), ("Selongsong panas Ø 3 mm", "3 x 20 mm", "kabel Y"),
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
        "<li>Amplas semua tepi sampai lurus dan siku. Tepi yang miring membuat celah cahaya.</li></ol>"],
        gambar=[("rakit/gambar/m1_lembar_badan.svg", "Lembar badan"), ("rakit/gambar/m1_lembar_tutup.svg", "Tutup dan bibir")],
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
    langkah("Kabel Y dan pemasangan kabel", "45 menit", [
        "<ol><li>Buat 3 kabel Y (3V3, GPIO 21, GPIO 22) sesuai gambar. Selongsong dimasukkan SEBELUM menyolder.</li>"
        "<li>Colok kabel sesuai tabel dan skema. Warna mengikuti tabel supaya mudah diperiksa.</li>"
        "<li>Kabel sensor naik dari header lalu ke ESP32; kabel OLED turun dari tutup. Atur supaya kabel tidak menekan modul sensor.</li></ol>",
        kabel_tabel(kabel)],
        gambar=[("rakit/gambar/kabel_y.svg", "Membuat kabel Y"), ("rakit/gambar/m1_skema.svg", "Skema kabel Model 1")],
        periksa="Sebelum menyalakan: multimeter mode bunyi antara 3V3 dan GND ESP32 TIDAK boleh berbunyi.",
        awas="Sensor VIN ke 3V3, bukan ke VIN ESP32. Pin VIN ESP32 berisi 5 V dari USB.",
        tampil=KEPALA + SENS + ["dudukan_cakram"] + BADAN + ESP + OLED + KABEL + ["tutup_atas"], baru=KABEL + ["sensor_dupont", "esp_dupont", "oled_dupont"], samar=["tutup_atas"],
        pandang=[0.75, 0.75, 1.3], label=[])
    langkah("Tutup, unggah firmware, uji", "30 menit", [
        "<ol><li>Pasang tutup (bibir masuk di dalam dinding). Jangan dilem: tutup harus bisa dibuka.</li>"
        "<li>Unggah firmware Data_Latih_Uji.ino (pin SDA 21, SCL 22, LED 26) lewat USB.</li>"
        "<li>Layar menyala dan perintah RAW di Serial Monitor menampilkan angka sensor: rangkaian benar.</li>"
        "<li>Kalibrasi: tempel alat di kertas HVS putih doff, kalibrasi putih; lalu di beludru hitam, kalibrasi hitam.</li>"
        "<li>Uji ulangan: ukur kertas warna yang sama 10 kali sambil mengangkat dan menempel ulang alat. Simpangan R/G harus 0,03 atau kurang.</li></ol>"],
        periksa="Saat ditempel di daging, bacaan LED-mati (Rgelap/Ggelap/Bgelap di RAW) hampir nol. Bila besar, ada cahaya bocor: periksa tepi pelat muka dan silikon.",
        tampil=SEMUA, baru=TUTUP, pandang=[0.75, 0.45, 1.5], label=["tutup_atas", "tanda_tekan"])
    return L, kb, dict(judul="Model 1: Genggam", ringkas=f"{f1(GR.L_TOT)} x {f1(GR.W_TOT)} x {f1(GA.Z_TOP + GA.t)} mm, ditempel ke daging", file="penampil_model1.html")


# ============================================================================ MODEL 2: JEPIT
def model2():
    B = GE.B
    URAI = {"busa_1": 6, "busa_2": 14, "busa_3": 22, "daging": 45, "tutup_cat": 75, "beludru": 75, "dudukan_pelat": 100, "dudukan_pipi": 100,
            "kepala_lantai": 120, "kepala_depan": 135, "kepala_belakang": 135, "kepala_kiri": 135, "kepala_kanan": 135, "engsel_atas": 135, "kait_atas": 135,
            "kepala_tutup": 200, "kepala_bibir": 200}
    def urai(k):
        if k in URAI: return URAI[k]
        if k.startswith("sensor_"): return 92
        if k.startswith("esp_"): return 145
        if k.startswith("oled_"): return 180
        return 0
    hinge = dict(x=GE.SUMBU_ENGSEL[0], z=GE.SUMBU_ENGSEL[1], yc=GE.YC)
    kb = penampil(B, urai, hinge, "BeefFresh Model 2: langkah rakit", "penampil_model2.html", grup_aks=("kal_putih", "kal_hitam"))
    BAKI = pilih(B, "baki_*"); BUSA = pilih(B, "busa_*")
    KEP = pilih(B, "kepala_lantai", "kepala_depan", "kepala_belakang", "kepala_kiri", "kepala_kanan")
    PVC = BAKI + KEP + pilih(B, "kepala_tutup", "kepala_bibir", "dudukan_*")
    SENS = pilih(B, "sensor_*"); SENS_ND = [k for k in SENS if k != "sensor_dupont"]
    DUD = pilih(B, "dudukan_*"); CAT = ["tutup_cat", "beludru"]
    ESP = pilih(B, "esp_*"); ESP_ND = [k for k in ESP if k != "esp_dupont"]
    OLED = pilih(B, "oled_*"); OLED_ND = [k for k in OLED if k != "oled_dupont"]
    KABEL = pilih(B, "kabel_*"); ENG = pilih(B, "engsel_*", "kait_*")
    SEMUA = [k for k in B if not k.startswith("kal_")]
    J = GE.JENDELA; W = GE.W; YC = GE.YC
    K = GE.KABEL
    def ln(k): return K[k]["panjang"]
    kabel = []
    for k, kv in K.items():
        if k.startswith("kabel_y_"): continue
        pn, b = (GE.SENSOR_KE if k.startswith("kabel_s_") else GE.OLED_KE)[k[8:]][0]
        y = pn in GE.CABANG
        Lk = ln(k) + (ln("kabel_y_" + pn) if y else 0) - (30 if y else 0)
        kabel.append((kv["warna"], kv["dari"], GE.nama_pin(pn, b) + (" (Y)" if y else ""), Lk, ("cabang Y " + GE.nama_pin(pn, b)) if y else ""))
    kabel.sort(key=lambda r: (r[4] == "", r[4], r[1]))
    L = []
    def langkah(judul, waktu, isi, gambar=(), periksa="", awas="", **v3):
        L.append(dict(judul=judul, waktu=waktu, isi=isi, gambar=list(gambar), periksa=periksa, awas=awas, v3=v3))
    langkah("Siapkan bahan dan alat", "15 menit", [
        bom([("PVC board 3 mm", "± 570 cm² (± 24 x 24 cm)", "15 jenis potongan; pelat dudukan dan pipi dari PVC hitam"),
             ("Tutup cat semprot Ø 65", "1", "dipotong 22 mm dari muka"), ("ESP32 DOIT DevKit V1, TCS34725, OLED 0,96 inci I2C", "1 set", "sudah ada"),
             ("Busa ati / EVA lunak hitam", "3 lembar 78 x 78 x 10 mm", "penekan daging"), ("Kertas beludru hitam (flok)", "± 20 x 20 cm", "pelapis tutup cat; pengganti: flanel hitam"),
             ("Engsel kupu-kupu 25 mm", "2", "dengan 8 baut M3 x 10 + mur"), ("Kait kotak kecil", "1", "pengunci depan"), ("Tali nilon", "15 cm", "pembatas buka ± 100°"),
             ("Baut M2,5 x 10 hitam + mur", "2", "sensor"), ("Baut M2 x 10 + mur", "4 + 8", "OLED: 1 mur ganjal + 1 mur pengunci per baut"),
             ("Kabel dupont betina-betina", "10 cm dan 20 cm", "lihat tabel kabel"), ("Selongsong panas Ø 3 mm", "3 x 20 mm", "kabel Y"),
             ("Busa dobel tape 3 mm, lem PVC, silikon hitam, selotip hitam", "sedikit", ""), ("Kertas HVS putih doff + beludru hitam", "untuk tatakan kalibrasi", ""),
             ("Plastik wrap", "1 lembar baru per sampel", "pelindung busa")]),
        f"<p><b>Alat:</b> {ALAT}</p>"], gambar=[("rakit/gambar/cara_baca.svg", "Cara membaca semua gambar kerja")],
        tampil=SEMUA, baru=[], pandang=[-0.75, 0.42, 1.5])
    langkah("Cetak pola 1:1", "10 menit", [
        "<ol><li>Cetak pola kecil 1:1 (pipi, pelat dudukan) dengan skala <b>100 %</b>. Ukur garis uji 50 mm.</li>"
        "<li>Lembar besar (86 mm) cukup diukur langsung dari gambar kerja: semuanya persegi panjang.</li></ol>",
        '<p class="dl"><a href="jepit/gambar/5_pola_1banding1.svg" target="_blank">Pola kecil 1:1</a></p>'],
        gambar=[("jepit/gambar/5_pola_1banding1.svg", "Pola kecil 1:1")], tampil=PVC, baru=PVC, urai=0.45, pandang=[-0.75, 0.3, 1.25], label=[])
    langkah("Potong panel PVC", "60 menit", [
        "<ol><li>Gores 3-5 kali dengan cutter dan penggaris besi, lalu patahkan. Amplas tepi sampai lurus dan siku.</li>"
        f"<li>Baki: lantai {f1(W)} x {f1(W)}, dinding depan dan belakang {f1(W)} x {f1(GE.F + GE.Hc)}, dinding kiri dan kanan {f1(W - 2 * GE.t)} x {f1(GE.F + GE.Hc)}.</li>"
        f"<li>Kepala: lantai {f1(W)} x {f1(W)} dengan jendela kabel {f1(J[1] - J[0])} x {f1(J[3] - J[2])}, 4 dinding setinggi {f1(GE.P['kepala_dalam'])} mm, tutup atas dengan jendela OLED 25 x 15.</li>"
        "<li>Takik USB 13 x 10 di tepi bawah dinding kiri kepala.</li></ol>"],
        gambar=[("jepit/gambar/8_lembar_baki.svg", "Lembar baki"), ("jepit/gambar/9_lembar_kepala.svg", "Lembar kepala"), ("jepit/gambar/10_lembar_kecil.svg", "Lembar kecil")],
        periksa="Lantai baki dan lantai kepala ditumpuk: keempat tepinya rata.",
        tampil=PVC, baru=BAKI + KEP + ["kepala_tutup", "kepala_bibir"], urai=0.45, pandang=[-0.75, 0.3, 1.25], label=[])
    langkah("Siapkan tutup cat", "30 menit", [
        "<ol><li>Lilitkan selotip di sekeliling tutup cat 22 mm dari muka sebagai garis potong, lalu gergaji dan ratakan di amplas.</li>"
        "<li>Bor lubang ukur di pusat muka bertahap Ø 4, 8, 12, lalu kikir sampai Ø 14. Haluskan tepinya.</li>"
        "<li>Jangan cat muka luar: muka luar menyentuh daging lewat plastik wrap.</li></ol>"],
        gambar=[("jepit/gambar/2_ruang_ukur.svg", "Ruang ukur")],
        tampil=["tutup_cat"], baru=["tutup_cat"], potong=[1, YC, 1], pandang=[-0.2, -0.35, 1.4])
    langkah("Lapisi bagian dalam tutup cat", "20 menit", [
        "<p>Tempel beludru hitam di muka dalam (sisakan lubang Ø 16) dan di dinding dalam. Bila memakai cat doff: 2 lapis tipis, biarkan kering sekitar sehari sampai tidak berbau.</p>"],
        tampil=CAT, baru=["beludru"], potong=[1, YC, 1], pandang=[-0.2, 0.5, 1.4])
    langkah("Dudukan miring 40°", "20 menit", [
        "<ol><li>Bor 2 lubang Ø 2,8 di pelat dudukan sesuai pola.</li>"
        "<li>Rekatkan kedua pipi trapesium di punggung pelat, di sisi tepi panjangnya, sisi miring 40° menempel pelat.</li></ol>"],
        gambar=[("jepit/gambar/10_lembar_kecil.svg", "Pelat dudukan dan pipi")],
        tampil=DUD, baru=DUD, pandang=[-0.4, 0.3, 2.0])
    langkah("Solder header dan pasang sensor", "25 menit", [
        "<ol><li>Solder header 7 pin: plastik di punggung papan, solder di sisi komponen.</li>"
        "<li>Baut papan ke pelat dudukan dengan 2 baut M2,5 hitam dari sisi komponen, mur di punggung pelat. Header menghadap punggung.</li></ol>"],
        gambar=[("rakit/gambar/header_sensor.svg", "Arah header sensor")],
        tampil=DUD + SENS_ND, baru=SENS_ND, pandang=[-0.4, -0.2, 2.0], label=pilih(B, "sensor_pcb", "sensor_header", "sensor_baut", "sensor_chip"))
    langkah("Siapkan lantai kepala", "15 menit", [
        f"<ol><li>Potong jendela kabel {f1(J[1] - J[0])} x {f1(J[3] - J[2])} mm sesuai pola dan denah.</li>"
        f"<li>Tandai pusat tutup cat di sisi BAWAH lantai: {f1(GE.XC)} mm dari depan dan {f1(GE.YC)} mm dari kiri. Tandai juga letak kedua pipi (garis putus di gambar).</li></ol>"],
        gambar=[("jepit/gambar/3_denah_lantai_kepala.svg", "Denah lantai kepala")],
        tampil=["kepala_lantai"], baru=["kepala_lantai"], pandang=[-0.75, 1.1, 1.4])
    langkah("Rekatkan dudukan di bawah lantai", "15 menit + kering", [
        "<p>Masukkan soket dupont sensor lewat jendela dari bawah, lalu rekatkan sisi atas kedua pipi ke lantai pada posisi denah. Chip menghadap ke depan dan ke bawah, ke arah pusat lubang.</p>"],
        tampil=["kepala_lantai"] + DUD + SENS, baru=DUD + SENS, pandang=[-0.9, -0.45, 1.2], label=["dudukan_pelat", "sensor_pcb", "sensor_dupont"])
    langkah("Periksa, lalu rekatkan tutup cat", "15 menit", [
        "<ol><li>Letakkan tutup cat di atas tanda pusat, intip lewat lubang Ø 14: chip harus terlihat di sisi belakang lubang.</li>"
        "<li>Bila sudah benar, rekatkan tepi tutup cat dengan silikon hitam di sekelilingnya.</li></ol>"],
        gambar=[("jepit/gambar/1_potongan.svg", "Potongan tengah alat")],
        tampil=["kepala_lantai"] + DUD + SENS + CAT, baru=CAT, potong=[1, YC, 1], pandang=[-0.05, -0.15, 1.3])
    langkah("Rakit baki dan kotak kepala", "50 menit + kering", [
        "<ol><li>Baki: lantai dan 4 dinding. Kepala: 4 dinding di atas lantai kepala.</li>"
        "<li>Takik USB 13 x 10 mm di tepi bawah dinding kiri kepala, pusatnya 20 mm dari depan.</li>"
        "<li>Lem bibir di sisi bawah tutup atas.</li></ol>"],
        periksa="Kepala diletakkan di atas baki: keempat sisi rata, tidak ada celah cahaya.",
        tampil=BAKI + KEP + DUD + SENS + CAT, baru=BAKI + KEP, pandang=[-0.75, 0.42, 1.8], label=[])
    langkah("Pasang ESP32 dan OLED", "25 menit", [
        "<ol><li>ESP32 terbalik di atas busa dobel tape, colokan USB menghadap takik. Tutup lampu merah dayanya dengan selotip hitam.</li>"
        "<li>OLED dibaut ke tutup atas menghadap jendela: baut M2 x 10 dari atas, 1 mur ganjal (1,6 mm) di antara tutup dan PCB, 1 mur pengunci di bawah PCB.</li></ol>"],
        gambar=[("rakit/gambar/m2_oled.svg", "Satu baut OLED")],
        tampil=BAKI + KEP + DUD + SENS + CAT + ESP_ND + OLED_ND + ["kepala_tutup", "kepala_bibir"], baru=ESP_ND + OLED_ND, samar=["kepala_tutup", "kepala_bibir"],
        pandang=[-0.75, 0.8, 1.2], fokus=KEP + ["kepala_tutup"], label=["esp_pcb", "esp_usb", "oled_pcb"])
    langkah("Kabel Y dan pemasangan kabel", "45 menit", [
        "<ol><li>Buat 3 kabel Y (3V3, GPIO 21, GPIO 22) sesuai gambar.</li>"
        "<li>Pasang kabel sesuai tabel, skema, dan denah. Tutup jendela kabel dari atas dengan selotip hitam di sekeliling kabel.</li></ol>",
        kabel_tabel(kabel)],
        gambar=[("rakit/gambar/kabel_y.svg", "Membuat kabel Y"), ("rakit/gambar/m2_skema.svg", "Skema kabel Model 2"), ("jepit/gambar/7_denah_kabel.svg", "Denah kabel di kepala")],
        periksa="Sebelum menyalakan: multimeter mode bunyi antara 3V3 dan GND ESP32 TIDAK boleh berbunyi.",
        awas="Sensor VIN ke 3V3, bukan ke VIN ESP32.",
        tampil=BAKI + KEP + DUD + SENS + CAT + ESP + OLED + KABEL + ["kepala_tutup", "kepala_bibir"], baru=KABEL + ["sensor_dupont", "esp_dupont", "oled_dupont"],
        samar=["kepala_tutup", "kepala_bibir"], pandang=[-0.75, 0.9, 1.2], fokus=KEP, label=[])
    langkah("Engsel, kait, tali pembatas", "30 menit", [
        "<ol><li>Tempatkan kepala di atas baki. Pasang 2 engsel di sisi belakang dengan baut M3 dan mur, poros tepat di garis sambungan.</li>"
        "<li>Pasang kait di sisi depan.</li><li>Ikat tali pembatas antara sisi kepala dan sisi baki supaya kepala berhenti di sekitar 100°.</li></ol>"],
        gambar=[("jepit/gambar/4_terbuka.svg", "Alat terbuka")],
        periksa="Buka sampai berhenti: alat tidak terguling ke belakang.",
        tampil=[k for k in SEMUA if k not in BUSA + ["daging"]], baru=ENG, engsel=60, pandang=[0.9, 0.3, 1.4], fokus=BAKI + KEP)
    langkah("Busa, firmware, uji", "40 menit", [
        "<ol><li>Masukkan 3 lapis busa ke baki.</li><li>Unggah firmware (pin 21, 22, 26). Layar menyala dan perintah RAW menampilkan angka.</li>"
        "<li>Kalibrasi sekali per sesi: balok putih di atas busa, tutup, kalibrasi putih; balok hitam, kalibrasi hitam.</li>"
        "<li>Daging diiris 10 mm (minimal 30 x 30 mm), di atas plastik wrap baru, tutup, kunci, tunggu 3 detik, Ambil.</li></ol>"],
        periksa="Uji ulangan 10 kali pada kertas warna yang sama: simpangan R/G 0,03 atau kurang.",
        tampil=SEMUA, baru=BUSA + ["daging"], engsel=95, pandang=[-1.35, 0.85, 1.7], fokus=BAKI)
    return L, kb, dict(judul="Model 2: Jepit", ringkas="86 x 86 x 106 mm, daging dimasukkan", file="penampil_model2.html")


# ============================================================================ halaman
CSS = open(os.path.join(HERE, "rakit.css")).read()
JS = open(os.path.join(HERE, "rakit.js")).read()


def ukuran_svg(src):
    import re
    t = open(os.path.join(DES, src)).read(3000)
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', t)
    return (round(float(m.group(3))), round(float(m.group(4)))) if m else (1000, 600)


def halaman(no, L, info, lain):
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
<nav class="top"><b>Beef<span>Fresh</span></b><a class="on" href="rakit_model{no}.html">{info["judul"].replace(": ", '<span class="nm">: ') + "</span>"}</a><a href="rakit_model{lain[0]}.html">{lain[1].replace(": ", '<span class="nm">: ') + "</span>"}</a><a href="tur.html">Tur desain</a><span id="prog">0/{len(L)}</span></nav>
<header class="hero"><span class="kick">Tur rakit · langkah demi langkah</span><h1>{info["judul"]}</h1><p>{info["ringkas"]}. {len(L)} langkah. Gulir pelan: model 3D di samping mengikuti langkah yang sedang dibaca, bagian yang dipasang berwarna merah berdenyut. Semua ukuran dalam milimeter dan diambil langsung dari model yang sama.</p></header>
<div class="wrap"><aside class="stage"><iframe id="v" src="rakit/{info["file"]}" title="Model 3D langkah rakit"></iframe><div class="stepnav">{nav}</div></aside>
<main class="steps">{"".join(kartu)}
<p class="foot">Ukuran yang masih anggapan: tebal PVC 3 mm, Ø pipa 1 inci 32 mm (Model 1), Ø dalam tutup cat 62 mm (Model 2). Ukur bahanmu sebelum memotong; bila berbeda, kabari Lyra supaya model dihitung ulang.</p></main></div>
<script>const LANGKAH={data};const KUNCI="beeffresh_rakit_{no}";{JS}</script></body></html>'''
    open(os.path.join(DES, f"rakit_model{no}.html"), "w").write(T)
    return len(T) // 1024


if __name__ == "__main__":
    L1, k1, i1 = model1(); L2, k2, i2 = model2()
    h1 = halaman(1, L1, i1, (2, "Model 2: Jepit")); h2 = halaman(2, L2, i2, (1, "Model 1: Genggam"))
    print(f"Model 1: {len(L1)} langkah, halaman {h1} KB, penampil {k1} KB;  Model 2: {len(L2)} langkah, halaman {h2} KB, penampil {k2} KB")

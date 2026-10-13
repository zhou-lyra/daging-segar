# Rumah alat BeefFresh (model 3D)

Model parametrik (OpenSCAD) untuk rumah ESP32 + OLED + sensor warna TCS34725 dengan **tabung gelap**
yang ditempelkan ke permukaan daging. Satuan mm.

> **Status jujur:** semua ukuran komponen di model adalah **angka standar / perkiraan** dari lembar data dan penjual.
> Model sudah lolos uji geometri otomatis (lihat bawah), tetapi **belum pernah dicetak dan dipasangi komponen aslimu**.
> Ukur komponenmu, ganti angkanya, lalu **cetak kupon uji pas dulu** sebelum mencetak badan penuh.

## Berkas siap cetak (`stl-siap-cetak/`)
| Berkas | Fungsi | Jumlah | Arah cetak |
|---|---|---|---|
| `beeffresh_base.stl` | badan bawah (ESP32, sensor, kabel) | 1 | sudah benar (lantai di meja) |
| `beeffresh_tutup.stl` | tutup + jendela OLED | 1 | sudah benar (sisi atas di meja) |
| `beeffresh_tabung_D5/D8/D11.stl` | tabung gelap, jarak chip→ujung tabung 5 / 8 / 11 mm | 1 tiap ukuran | sudah benar (flens di meja) |
| `beeffresh_kupon_uji.stl` | bingkai uji pas ESP32, OLED, sensor + dinding lubang USB | 1 | rata |
| `pratinjau_*.png` | gambar rakitan (utuh, terbuka, tampak bawah) | | |

Tiga tabung dicetak untuk **mencari jarak terbaik** (rekomendasi modul 3–10 mm; D11 sedikit di luar rentang itu sebagai pembanding).
Ukuran badan: **87,6 × 33,6 × 35,5 mm** (tutup terpasang) + tabung 1,6–7,6 mm di bawah. Tanpa penyangga (support).

## Susunan
- **ESP32** berbaring di atas satu rusuk tengah (di antara dua baris pin), USB menghadap lubang di dinding ujung. Satu sisi dijepit tab kecil.
- **OLED** di tutup, menghadap atas, ditahan 4 pin di lubang pemasangannya (ujung pin dilem / dipanaskan).
- **Sensor TCS34725** terbalik (chip menghadap bawah) di lantai, mengintip lewat jendela ke dalam **tabung gelap**. Ruang cekung di bawah papan menampung komponen SMD-nya.
- **Tabung** menempel di ceruk bawah lantai (tekan + lem). Ujung tabung ditempelkan ke permukaan daging, jadi jarak sensor ke daging tetap sama untuk semua sampel dan cahaya ruangan terhalang.
- Tutup dikunci 2 sekrup M2.5 (di tengah) + lip keliling.

## Yang HARUS kamu ukur (jangka sorong, 0,1 mm)
Ganti di `beeffresh_rumah.scad` (bagian bertanda `[UKUR]`):
| Variabel | Yang diukur |
|---|---|
| `esp_L`, `esp_W` | panjang × lebar papan ESP32 (sumber: ±51,8 × 28,2, tiruan bisa beda) |
| `esp_top_h` | tinggi komponen tertinggi di atas PCB |
| `esp_pin_down` | dari sisi bawah PCB sampai ujung pin |
| `esp_pin_row_gap` | jarak antar dua baris pin (pusat ke pusat, ±25,4) |
| `usb_cut_w/h/dz` | lebar × tinggi **colokan kabel USB-mu beserta selubungnya** dan tinggi pusatnya dari sisi atas PCB |
| `oled_L`, `oled_hole_off`, `oled_hole_d` | sisi modul OLED, jarak lubang dari pusat, diameter lubang |
| `oled_win_w/h`, `oled_act_dy` | jendela tampil: ukur area layar yang menyala dan letaknya dari pusat PCB. Default dibuat **besar (26 × 15)** supaya aman |
| `tcs_L`, `tcs_W` | ukuran papan sensor (Adafruit ±20,3; modul lain bisa 28 atau 40 mm) |
| `tcs_ap_cx/cy`, `tcs_ap_w/h` | posisi dan ukuran area yang harus terlihat: **chip + LED putihnya** |
| `tcs_holes`, `tcs_hole_d` | letak dan diameter lubang sekrup papan sensor (kosongkan `[]` bila tidak ada) |
| `chip_depth` | seberapa chip menonjol di bawah papan |

Model **menolak dirender** (assert) kalau lubang sekrup sensor terlalu dekat jendela cahaya, dan menghitung ulang panjang badan otomatis.

## Cetak (jasa 3D print)
- **Warna hitam doff** adalah syarat, supaya bagian dalam tabung tidak memantulkan cahaya. FDM PETG/ABS/ASA hitam paling masuk akal. Resin hitam juga bisa. Nylon MJF abu-abu pantulannya terang: minta dicelup hitam atau cat doff bagian dalam tabung.
- Layer 0,2 mm, dinding ≥ 3 perimeter (1,2 mm), isian 20–30%. Dinding terkecil di model **±1 mm**.
- Beri tahu jasa: toleransi pas untuk komponen, dan celah di model **0,3 mm** (`tol`). Kalau pas terlalu longgar atau ketat, ubah `tol` (FDM 0,25–0,35; resin 0,15–0,25).
- **Cetak kupon uji dulu** (16 KB, murah). Masukkan ESP32, OLED, papan sensor, dan colokan USB-mu ke bingkainya. Kalau pas, cetak badan penuh.

## Perakitan
1. Solder kabel ke papan (jangan pakai jumper breadboard; tidak muat): 3V3, GND, G26 (SDA), G27 (SCL) dari ESP32 ke OLED dan sensor (paralel).
2. Pasang pin penahan OLED ke lubang PCB, lem atau panaskan ujungnya.
3. Papan sensor: **chip menghadap bawah** ke lantai, kencangkan 2 sekrup M2.5 pendek (±5 mm) bila ada lubang. Lapisi tepi dengan pita hitam supaya cahaya dari dalam rumah tidak bocor ke jendela.
4. ESP32: masukkan miring ke bawah tab, turunkan ke rusuk, colokkan USB.
5. Tekan tabung ke ceruk bawah (lem sedikit). Tutup dengan 2 sekrup M2.5 (±8 mm).
6. Opsional: cincin busa hitam tipis di ujung tabung untuk menutup cahaya ke permukaan daging yang tidak rata.

## Mengubah dan memeriksa ulang
```
python3 -m venv ../.venv-cad && ../.venv-cad/bin/pip install trimesh numpy manifold3d scipy networkx rtree
sudo apt install openscad
../.venv-cad/bin/python verify.py            # uji: bentuk tertutup, tabrakan, celah >= 0,2 mm, dinding
../.venv-cad/bin/python verify.py -D esp_L=55 -D tcs_L=40 -D 'tcs_holes=[]'    # uji dengan ukuranmu
../.venv-cad/bin/python tebal.py             # perkiraan ketebalan dinding
```

## Yang SUDAH diuji otomatis (dengan komponen tiruan berukuran standar)
Semua bagian berbentuk tertutup (siap cetak); tidak ada tabrakan ESP32/OLED/sensor/colokan USB dengan dinding; celah ≥ 0,2 mm ke 5 arah; colokan USB longgar 0,5 mm di lubang; dinding minimum ±1 mm; tetap lolos pada 3 varian ukuran modul.

## Yang BELUM diuji (jangan dianggap pasti)
- Ukuran komponen **aslimu**. Itu perlu jangka sorong.
- Hasil cetak nyata (penyusutan, kekuatan tab dan pin, kekencangan tabung).
- Letak chip dan LED pada papan sensor milikmu (default: di pusat).
- Akses tombol **BOOT/EN** tidak dibuat: perlu posisi tombol pada boardmu. Selama aplikasi desktop dipakai, tombol itu tidak diperlukan.
- Kebocoran cahaya di sambungan tutup, papan sensor, dan tabung: tutup dengan pita/busa hitam bila ternyata bocor (cek: angka sensor berubah saat lampu ruangan dimatikan).
- Badan setinggi 35 mm dengan dasar rata 4,6 mm di atas daging: permukaan daging yang cembung bisa menyentuh bagian bawah badan.

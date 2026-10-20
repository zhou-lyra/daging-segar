# Tur rakit BeefFresh

Halaman: `../rakit_model1.html` (Model 1, Genggam) dan `../rakit_model2.html` (Model 2, Jepit).

Semua ukuran berasal dari satu sumber: `../genggam/geometri_a.py` dan `../jepit/geometri.py`. Kalau ada ukuran yang berubah, ubah di sana lalu jalankan:

```sh
cd desain/genggam && ../../.venv-cad/bin/python geometri_a.py
cd ../jepit && ../../.venv-cad/bin/python geometri.py && ../../.venv-cad/bin/python gambar.py
cd ../rakit
../../.venv-cad/bin/python gambar_rakit.py   # gambar/*.svg + pola 1:1 (mm)
../../.venv-cad/bin/python bangun_rakit.py   # penampil_model1/2.html + ../rakit_model1/2.html
```

- `bangun_rakit.py`: isi langkah, bahan, tabel kabel, dan keadaan 3D tiap langkah (bagian tampil, bagian baru, kamera, potongan, engsel).
- `penampil_langkah_template.html`: penampil WebGL yang menerima `postMessage({tipe:"langkah", ...})` dari halaman induk.
- `rakit.css`, `rakit.js`: tata letak dan sinkronisasi gulir. Centang "selesai" disimpan di localStorage perangkat.
- Pola cetak 1:1: `gambar/pola_m1_badan_1banding1.svg`, `gambar/pola_m1_pipa_1banding1.svg`, dan `../jepit/gambar/5_pola_1banding1.svg`. Cetak dengan skala 100 %, lalu periksa garis uji 50 mm.

Keputusan LED (Oktober 2026): hanya LED bawaan TCS34725 yang dipakai, tanpa LED kedua. Alasannya ada di `../led_spektrum.py` dan `../led_dua_mc.py` (model spektral, perkiraan).

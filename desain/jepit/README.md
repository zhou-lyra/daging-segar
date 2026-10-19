# BeefFresh Jepit (desain E)

Penjepit berengsel dari lembaran PVC. Kepala ukurnya tutup cat semprot dengan TCS34725 dimiringkan 40° dan LED bawaan sensor. Halaman utamanya `../penjepit.html`.

Satu sumber ukuran: `geometri.py`. File lain dibangun dari situ, jadi kalau ada ukuran yang berubah, ubah di `geometri.py` saja lalu jalankan ulang semuanya.

```sh
cd desain/jepit
../../.venv-cad/bin/python geometri.py        # model/jepit.glb, katalog.glb, bagian.json + pemeriksaan tabrakan
../../.venv-cad/bin/python cek_pandang.py     # chip dan LED melihat lubang ukur?
../../.venv-cad/bin/python cek_stabil.py      # terguling saat dibuka?
../../.venv-cad/bin/python gambar.py          # gambar/*.svg: potongan, ruang ukur, denah, terbuka, pola 1:1, skema + denah kabel, ukuran tiap lembar PVC
~/.local/bin/blender -b -P blender_jepit.py -- 32   # render/*.png + model/jepit.blend (8 = uji cepat)
../../.venv-cad/bin/python bangun_halaman.py  # penampil_3d.html + ../penjepit.html
```

Pemilihan sudut 40°: `../optik_jepit.py` (hitungan pantulan tunggal).

Di `model/jepit.blend`:
- Setiap komponen adalah objek terpisah, dikelompokkan dalam koleksi Baki bawah, Kepala (berengsel), dan Aksesori kalibrasi.
- Putar objek kosong **Poros engsel** pada sumbu Y untuk membuka kepala.
- Objek **Pemotong (Boolean)** memotong model di bidang tengah. Modifier "Potong" pada tiap objek mati secara default.
- Scene kedua, **Katalog komponen**, berisi setiap komponen yang dibaringkan dan diberi label.

Ukuran yang masih anggapan: tebal PVC 3 mm, diameter dalam tutup cat 62 mm, tebal muka tutup 1,5 mm, dan arah header sensor.

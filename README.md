# daging-segar (BeefFresh)
Akuisisi data warna daging (TCS34725 + ESP32 + OLED) untuk klasifikasi segar / mulai_membusuk / busuk.

## Pakai sehari-hari
```
./jalankan.sh        # aplikasi Qt6 (tema Zhou Lyra): tombol, tabel, grafik sebaran -> data_beeffresh.csv
```
Rancangan: 1 daging dipotong 12 (potongan 1-9 = LATIH, 10-12 = UJI, agar tidak ada kebocoran data), tiap potongan diukur di beberapa titik (default 4, bisa 2-8). Data tersimpan otomatis ke CSV tiap sampel; tombol 'Ekspor Excel (.xlsx)' membuat berkas Excel (lembar Data + Ringkasan). Setelah tiap sampel, pilihan maju otomatis ke titik/potongan berikutnya.
Pintasan: Spasi = ambil, 1/2/3 = kelas, panah atas/bawah = potongan, kiri/kanan = titik, Ctrl+Z = batalkan terakhir. 'Reset data uji coba' mengosongkan CSV dan menyimpan cadangannya di arsip/.
Grafik: sebaran RGB per kelas + skor keterpisahan kelas (heuristik kasar). Venv: .venv (PySide6, pyserial). Tombol BOOT di alat tetap berfungsi.
Jam_Ke = umur daging (jam sejak 'waktu nol', dari jam laptop; diatur lewat tombol di aplikasi, tersimpan di waktu_nol.json). Kolom Waktu = cap waktu asli.
Sebelum mulai / kalau cahaya berubah: tombol "Kalibrasi ulang" dengan kertas putih di depan sensor.

## Firmware
```
arduino-cli compile --fqbn esp32:esp32:esp32doit-devkit-v1 Data_Latih_Uji
arduino-cli upload  --fqbn esp32:esp32:esp32doit-devkit-v1 -p /dev/ttyUSB0 Data_Latih_Uji
```
Perintah serial 115200: `PING`, `AMBIL <kelas 0-2> <jenis 0-1>`, `KALIB`, `INFO <kelas> <jenis> <potongan> <titik> <umur_detik>` (mengisi layar OLED: kelas, potongan, titik, jenis, umur daging yang berjalan tiap detik; dikirim otomatis oleh aplikasi). Keluaran tetap berformat PLX-DAQ (`DATA,...`).
Wiring: SDA=GPIO26, SCL=GPIO27, OLED 0x3C, TCS34725 0x29, LED GPIO25.

Target: 48 latih + 12 uji per kelas. `arsip/` = data uji coba, bukan dataset.

## Pindah ke laptop Windows 11
1. Pasang Python 3 (python.org, centang "Add python.exe to PATH"; 3.12/3.13 paling aman).
2. Ambil kodenya (versi terbaru; kalau sebelumnya gagal, hapus folder `.venv` lalu jalankan lagi): `git clone https://github.com/zhou-lyra/daging-segar` (atau Download ZIP dari GitHub), lalu klik dua kali `jalankan.bat` (pertama kali memasang PySide6 + pyserial otomatis).
3. Driver USB-serial CP210x: biasanya terpasang otomatis lewat Windows Update; bila di Device Manager muncul tanda seru, pasang "CP210x Universal Windows Driver" dari Silicon Labs.
4. Port berupa COMx (otomatis dicari; atau `jalankan.bat COM5`). Tidak perlu arduino-cli selama firmware tidak diubah (firmware & kalibrasi tersimpan di ESP32).
5. Data: salin `data_beeffresh.csv` + `waktu_nol.json` bila ingin melanjutkan. Jangan menjalankan aplikasi di dua laptop sekaligus pada alat yang sama.

## Lisensi
Kode: MIT (lihat LICENSE). Font Cormorant Garamond dan Manrope di `assets/fonts/` berlisensi SIL Open Font License (OFL-*.txt).
Data pengukuran (`data_beeffresh.csv`, `waktu_nol.json`, `arsip/`) tidak disertakan di repositori.

## Rumah alat (model 3D)
`cad/` berisi model OpenSCAD parametrik rumah alat (ESP32 + OLED + sensor + tabung gelap), berkas STL siap cetak, dan pemeriksa otomatis. Baca `cad/README.md`. Ukuran komponen masih standar/perkiraan: ukur dulu, lalu cetak kupon uji pas.

## Perbaikan kotak lama (tanpa cetak 3D)
`kotak_lama/rancangan.html` berisi rancangan kepala ukur dari tutup cat semprot, busa, dan sisa PVC: kalkulator ukuran, gambar potongan dan denah, daftar bahan, langkah merakit, uji penerimaan, dan template cetak 1:1. `uji_kotak_lama/PROTOKOL.md` berisi urutan uji untuk mencari sumber pembacaan dasar sebelum merakit.

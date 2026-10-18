# Protokol uji kotak lama (±20 menit)

Tujuan: mencari **sumber pembacaan dasar** (R, G, B sama-sama sekitar 65 sampai 75 pada kertas bening dan pada daging) dan memperbaikinya di kotak yang sudah ada. Desain 3D (`cad/`) tetap sebagai cadangan.

## Aturan tetap untuk semua uji
- Pintu kotak **tertutup rapat**, kecuali uji H.
- Lampu ruangan sama dari awal sampai akhir. Jangan menggeser alat.
- Daging yang sama (potongan 2), titik yang sama, **tanpa menekan** daging.
- Setiap kondisi diukur **3 kali** lewat aplikasi. Label dan potongan di aplikasi boleh apa saja. Lyra memisahkan baris uji ini lewat kolom `Waktu`, jadi **catat jam mulai tiap kondisi** di kertas.
- Setelah mengubah bahan atau jarak apa pun: **kalibrasi putih ulang**.

## Urutan
| Kode | Kondisi | Cara |
|---|---|---|
| A | Kalibrasi putih | Kertas HVS putih doff di tempat daging, tanpa kertas bening. Tekan Kalibrasi. |
| B | **Hitam** | Kertas hitam doff (atau selotip hitam tebal) di tempat daging. Mestinya mendekati nol. |
| C | **Kosong** | Tidak ada apa-apa di atas sensor. |
| D | Kertas bening kosong | Seperti yang tadi dilakukan (baris 61 dan 62). |
| E | Daging, cara biasa | Daging di atas sensor seperti biasa. Ini patokan. |
| F | **Daging dengan jarak** | Cincin penyangga setinggi 6 mm dari kertas hitam doff mengelilingi sensor. Daging di atas cincin, **tanpa** kertas bening. Kalibrasi putih ulang dengan kertas putih di atas cincin yang sama. |
| G | F + pelat ditutup | Seperti F, tetapi pelat mengilap di sekitar sensor ditutup selotip atau kain beludru hitam doff. Kalibrasi putih ulang. |
| H | Pintu terbuka 1 cm | Seperti E, tetapi pintu dibuka sedikit. Tampak seberapa besar cahaya ruangan masuk. |
| I | Akrilik dibersihkan | Lap lembar akrilik dan permukaan hitam di sekitar sensor dengan kain mikrofiber (foto 17.00 menunjukkan banyak debu dan baret). Ulangi B dan C. |
| J | Pisahkan dua LED | Foto menunjukkan dua sumber cahaya: LED putih di papan sensor dan satu LED 5 mm sekitar satu lebar papan di sampingnya (kemungkinan GPIO 25). Tutup LED papan dengan potongan selotip hitam, ukur B dan C. Lalu lepas tutup itu dan cabut kabel LED 5 mm, ukur B dan C. Selisihnya menunjukkan LED mana yang menyumbang pembacaan dasar. |

## Cara membaca hasilnya
- **B ≈ 0 sampai 10:** tidak ada pembacaan dasar. Penyebabnya di tempat lain (kalibrasi putih atau LED).
- **B ≈ 40 sampai 70:** ada pembacaan dasar. Cari sumbernya:
  - E naik ke F: jarak nol dan kertas bening menjadi penyebab (pantulan LED langsung).
  - F naik ke G: pelat mengilap ikut menyumbang.
  - H jauh lebih tinggi dari E: pintu bocor cahaya.
- **Target setelah perbaikan:** B ≤ 10 dan R/G daging ≥ 1,4 dengan simpangan R/G ≤ 0,03.

## Temuan dari empat foto (17.00, galeri ponsel, EXIF utuh)
- Sensor TCS34725 (papan ungu, pin LED INT SDA SCL 3V3 GND VIN) dipasang dengan dua sekrup di permukaan hitam yang mengilap, berdebu, dan berbaret.
- Ada satu LED 5 mm terpisah sekitar satu lebar papan dari sensor, dan LED putih di papan sensor sendiri.
- Daging diletakkan di atas lembar akrilik bening tepat di atas sensor, jarak belum terukur. Akrilik berdebu dan berbaret.
- Pintu tertutup menampilkan garis putih di tepi: bisa celah cahaya atau hanya tepi cat. Uji H menjawabnya.

## Ukuran yang diperlukan untuk adaptor (jangka sorong)
- Ruang dalam: panjang, lebar, tinggi.
- Papan sensor: panjang × lebar, letak chip dan LED di papan, tinggi papan dari lantai.
- Bahan pelat di sekitar sensor (logam, cat, plastik), dan celah pintu bila ditutup.
- Foto sensor dari atas dengan penggaris di sampingnya, sebagai berkas asli (bukan lewat foto WhatsApp).

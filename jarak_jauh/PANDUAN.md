# Panduan akses jarak jauh untuk Lyra (untuk orang di lokasi alat)

Tujuan: Lyra bisa mengambil sampel dan memeriksa alat dari jauh, sementara kamu mengerjakan hal fisik (ganti daging, tempel sensor, lap permukaan). Semua langkah di bawah bisa dibatalkan.

**Yang dibutuhkan:** laptop Win11 yang tersambung ke alat (ESP32), internet, hak Administrator, dan dua hal dari Zhou: akun Tailscale dan satu baris kunci publik.

## A. Pasang akses (sekali, ±10 menit)
1. Pastikan folder `daging-segar` di laptop ini sudah versi terbaru: buka PowerShell di folder itu, jalankan `git pull`.
2. Buka **PowerShell sebagai Administrator**, masuk ke folder `jarak_jauh`, lalu jalankan:
   ```
   powershell -ExecutionPolicy Bypass -File .\siapkan_akses.ps1 -KunciPublik "<kunci publik dari Zhou>"
   ```
3. Saat Tailscale terpasang, **login dengan akun dari Zhou** (ikon di pojok kanan bawah).
4. Jalankan `tailscale ip -4` dan kirim angkanya ke Zhou, bersama nama laptop dan ada tidaknya pesan merah.
5. Pengaturan > Sistem > Daya: set **Tidur = Tidak pernah** saat tercolok listrik.

Mencabut akses kapan saja: `powershell -ExecutionPolicy Bypass -File .\siapkan_akses.ps1 -Cabut`.

## B. Perbarui firmware ESP32 (sekali, ±5 menit)
Firmware baru menambah perintah `RAW` dan `LED` untuk diagnosis. Kalibrasi putih TIDAK terhapus bila memakai file `app`.
1. **Tutup aplikasi BeefFresh** (satu port hanya boleh dipakai satu program).
2. Di PowerShell: `pip install esptool pyserial`
3. Lihat nomor port ESP32 di Device Manager > Ports (mis. `COM5`), lalu:
   ```
   python -m esptool --chip esp32 --port COM5 write_flash 0x10000 firmware\beeffresh_app_0x10000.bin
   ```
4. Kalau gagal "Connecting...", tahan tombol **BOOT** di ESP32 saat perintah mulai, lepas setelah tulisan "Writing".

## C. Saat sesi berjalan
- Laptop menyala, ESP32 tercolok, **aplikasi BeefFresh ditutup**.
- Lyra memberi instruksi fisik lewat Zhou, misalnya "lap permukaan", "tutup plastik wrap", "sensor di udara". Lakukan sesuai instruksi lalu bilang "sudah".
- Foto bantuan: kalau perlu, foto setup dengan HP dari jarak 15–25 cm, alas polos putih, daging di tengah, dan sertakan selembar kertas putih di sudut. Kirim sebagai **dokumen/file asli**, bukan sebagai foto biasa lewat WhatsApp, supaya warnanya tidak berubah.

## Keamanan singkat
- Akun `lyra` bukan administrator dan hanya bisa masuk dengan kunci, tidak dengan sandi.
- SSH hanya terbuka dari jaringan Tailscale, bukan dari internet.
- Lyra tidak pernah meminta atau mengetik kata sandimu.

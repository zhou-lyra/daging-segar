/*
  ============================================================
  PROGRAM AKUISISI DATA LATIH & DATA UJI - BEEFFRESH
  VERSI KONTROL TOMBOL BOOT (TANPA PERLU MENGETIK)
  ============================================================
  Board   : ESP32 DOIT DEVKIT V1
  Sensor  : TCS34725 (via library Adafruit_TCS34725)
  Display : OLED SSD1306 (I2C)
  LED     : GPIO 25
  Tombol  : BOOT (bawaan board, terhubung ke GPIO 0) - TIDAK PERLU
            tombol tambahan apa pun.

  KENAPA VERSI INI DIBUAT:
  PLX-DAQ hanya mengalirkan data satu arah (ESP32 -> Excel), tidak
  ada tempat untuk mengetik perintah balik ke ESP32 seperti di
  Serial Monitor. Versi ini mengganti seluruh kontrol yang tadinya
  berupa ketikan perintah, menjadi kontrol lewat SATU tombol BOOT
  yang sudah ada di board - sehingga PLX-DAQ bisa tetap terhubung
  terus tanpa gangguan untuk logging ke Excel.

  CARA PAKAI TOMBOL BOOT:
  - TEKAN SINGKAT (lepas sebelum 0,7 detik)
      -> pindah ke pilihan kelas & jenis data berikutnya
         (bergilir: Segar-Latih, Segar-Uji, Mulai-Latih, Mulai-Uji,
          Busuk-Latih, Busuk-Uji, lalu kembali ke awal)
  - TEKAN SEDANG (tahan 0,7 - 3 detik, lalu lepas)
      -> ambil 1 sampel sesuai pilihan yang SEDANG tampil di OLED
  - TEKAN LAMA (tahan lebih dari 3 detik, lalu lepas)
      -> jalankan kalibrasi ulang (auto-gain + white balance)

  Layar OLED selalu menampilkan pilihan kelas & jenis yang sedang
  aktif, beserta progres jumlah sampel yang sudah diambil untuk
  pilihan tersebut - jadi kamu selalu tahu sedang berada di
  pilihan mana sebelum menekan lama untuk mengambil sampel.

  TARGET SAMPEL (bisa diubah lewat TARGET_LATIH / TARGET_UJI):
  48 data latih + 12 data uji per kelas = 60 per kelas,
  total 3 kelas = 180 sampel.

  Wiring I2C: SDA = GPIO 26, SCL = GPIO 27
  ============================================================
*/

#include <Wire.h>
#include <Adafruit_TCS34725.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Preferences.h>
#include <math.h>

// ============================================================
// KONFIGURASI PIN & OLED
// ============================================================
#define PIN_SDA     26
#define PIN_SCL     27
#define PIN_LED     25
#define PIN_TOMBOL  0     // Tombol BOOT bawaan board, aktif LOW
#define OLED_ADDR   0x3C

Adafruit_SSD1306 display(128, 64, &Wire, -1);
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_600MS, TCS34725_GAIN_4X);
Preferences preferences;

// ============================================================
// KONFIGURASI WAKTU TEKAN TOMBOL
// ============================================================
#define BATAS_TEKAN_SEDANG_MS  700   // di bawah ini = tekan singkat
#define BATAS_TEKAN_LAMA_MS    3000  // di atas ini = tekan lama (kalibrasi ulang)
#define DEBOUNCE_MS            50

// ============================================================
// KONFIGURASI AUTO-GAIN
// ============================================================
#define TARGET_CLEAR_MIN 1000
#define TARGET_CLEAR_MAX 50000
tcs34725Gain_t daftarGain[4] = {TCS34725_GAIN_1X, TCS34725_GAIN_4X, TCS34725_GAIN_16X, TCS34725_GAIN_60X};
const char* namaGain[4] = {"1x", "4x", "16x", "60x"};
int gainIndexTersimpan = 1;

// ============================================================
// KONFIGURASI PEMBACAAN & WHITE BALANCE
// ============================================================
#define JUMLAH_PEMBACAAN_MENTAH 15
#define BATAS_OUTLIER_PERSEN    20
#define JUMLAH_SAMPEL_PUTIH     15
#define JEDA_KALIBRASI_PUTIH    200

float Rwhite = 1, Gwhite = 1, Bwhite = 1;

// ============================================================
// KONFIGURASI TARGET DATASET
// ============================================================
#define TARGET_LATIH 48
#define TARGET_UJI   12

int nomorData = 1;
int jumlahTersimpan[3][2] = {{0,0},{0,0},{0,0}};
const char* namaKelas[3] = {"segar", "mulai_membusuk", "busuk"};
const char* namaKelasSingkat[3] = {"SEGAR", "MULAI", "BUSUK"};
const char* namaJenis[2] = {"latih", "uji"};
const char* namaJenisSingkat[2] = {"LATIH", "UJI"};

// Pilihan yang sedang aktif (0-5), bergilir dengan tekan singkat
int pilihanAktif = 0;

// ============================================================
// PENYIMPANAN PERMANEN (NVS)
// ============================================================
void simpanKalibrasi() {
  preferences.begin("beeffresh", false);
  preferences.putFloat("rwhite", Rwhite);
  preferences.putFloat("gwhite", Gwhite);
  preferences.putFloat("bwhite", Bwhite);
  preferences.putInt("gainidx", gainIndexTersimpan);
  preferences.putBool("sudahkalibrasi", true);
  preferences.end();
}

bool muatKalibrasi() {
  preferences.begin("beeffresh", true);
  bool sudahAda = preferences.getBool("sudahkalibrasi", false);
  if (sudahAda) {
    Rwhite = preferences.getFloat("rwhite", 1);
    Gwhite = preferences.getFloat("gwhite", 1);
    Bwhite = preferences.getFloat("bwhite", 1);
    gainIndexTersimpan = preferences.getInt("gainidx", 1);
  }
  preferences.end();
  return sudahAda;
}

// ============================================================
// FUNGSI BANTU: MEDIAN
// ============================================================
float cariMedian(float data[], int n) {
  for (int i = 0; i < n - 1; i++)
    for (int j = 0; j < n - i - 1; j++)
      if (data[j] > data[j + 1]) { float t = data[j]; data[j] = data[j+1]; data[j+1] = t; }
  if (n % 2 == 0) return (data[n/2 - 1] + data[n/2]) / 2.0;
  return data[n/2];
}

// ============================================================
// AMBIL 1 SAMPEL MENTAH DENGAN PENYARINGAN PENCILAN
// ============================================================
void ambilSampelMentahBersih(float &rHasil, float &gHasil, float &bHasil) {
  float bufR[JUMLAH_PEMBACAAN_MENTAH], bufG[JUMLAH_PEMBACAAN_MENTAH], bufB[JUMLAH_PEMBACAAN_MENTAH];
  uint16_t r, g, b, c;

  for (int i = 0; i < JUMLAH_PEMBACAAN_MENTAH; i++) {
    tcs.getRawData(&r, &g, &b, &c);
    bufR[i] = r; bufG[i] = g; bufB[i] = b;
    delay(80);
  }

  float sR[JUMLAH_PEMBACAAN_MENTAH], sG[JUMLAH_PEMBACAAN_MENTAH], sB[JUMLAH_PEMBACAAN_MENTAH];
  memcpy(sR, bufR, sizeof(bufR));
  memcpy(sG, bufG, sizeof(bufG));
  memcpy(sB, bufB, sizeof(bufB));

  float medR = cariMedian(sR, JUMLAH_PEMBACAAN_MENTAH);
  float medG = cariMedian(sG, JUMLAH_PEMBACAAN_MENTAH);
  float medB = cariMedian(sB, JUMLAH_PEMBACAAN_MENTAH);

  float batasR = medR * (BATAS_OUTLIER_PERSEN / 100.0);
  float batasG = medG * (BATAS_OUTLIER_PERSEN / 100.0);
  float batasB = medB * (BATAS_OUTLIER_PERSEN / 100.0);

  float totalR = 0, totalG = 0, totalB = 0;
  int nR = 0, nG = 0, nB = 0;

  for (int i = 0; i < JUMLAH_PEMBACAAN_MENTAH; i++) {
    if (fabs(bufR[i] - medR) <= batasR) { totalR += bufR[i]; nR++; }
    if (fabs(bufG[i] - medG) <= batasG) { totalG += bufG[i]; nG++; }
    if (fabs(bufB[i] - medB) <= batasB) { totalB += bufB[i]; nB++; }
  }

  rHasil = (nR > 0) ? (totalR / nR) : medR;
  gHasil = (nG > 0) ? (totalG / nG) : medG;
  bHasil = (nB > 0) ? (totalB / nB) : medB;
}

// ============================================================
// AUTO-GAIN
// ============================================================
void autoGain() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("AUTO-GAIN");
  display.setCursor(0, 16);
  display.println("Taruh kertas putih,");
  display.setCursor(0, 26);
  display.println("mencari gain terbaik...");
  display.display();
  delay(1500);

  int gainTerpilih = 1;
  uint16_t r, g, b, c;

  for (int i = 0; i < 4; i++) {
    tcs.setGain(daftarGain[i]);
    delay(200);
    tcs.getRawData(&r, &g, &b, &c);

    if (c >= TARGET_CLEAR_MIN && c <= TARGET_CLEAR_MAX) { gainTerpilih = i; break; }
    if (c > TARGET_CLEAR_MAX && i > 0) { gainTerpilih = i - 1; break; }
    gainTerpilih = i;
  }

  gainIndexTersimpan = gainTerpilih;
  tcs.setGain(daftarGain[gainTerpilih]);
  delay(200);

  display.clearDisplay();
  display.setCursor(0, 20);
  display.print("Gain terpilih: ");
  display.println(namaGain[gainTerpilih]);
  display.display();
  delay(1500);
}

// ============================================================
// KALIBRASI WHITE BALANCE
// ============================================================
void kalibrasiWhiteBalance() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("KALIBRASI PUTIH");
  display.setCursor(0, 20);
  display.println("Kertas putih tetap");
  display.setCursor(0, 32);
  display.println("di depan sensor...");
  display.display();

  for (int detik = 2; detik > 0; detik--) {
    display.fillRect(0, 45, 128, 20, SSD1306_BLACK);
    display.setCursor(0, 45);
    display.print("Mulai dalam: "); display.print(detik);
    display.display();
    delay(1000);
  }

  float totalR = 0, totalG = 0, totalB = 0;
  uint16_t r, g, b, c;

  for (int i = 0; i < JUMLAH_SAMPEL_PUTIH; i++) {
    tcs.getRawData(&r, &g, &b, &c);
    totalR += r; totalG += g; totalB += b;
    delay(JEDA_KALIBRASI_PUTIH);
  }

  Rwhite = max(totalR / JUMLAH_SAMPEL_PUTIH, 1.0f);
  Gwhite = max(totalG / JUMLAH_SAMPEL_PUTIH, 1.0f);
  Bwhite = max(totalB / JUMLAH_SAMPEL_PUTIH, 1.0f);

  simpanKalibrasi();

  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Kalibrasi Selesai");
  display.setCursor(0, 12);
  display.println("(sudah tersimpan)");
  display.setCursor(0, 26);
  display.print("R:"); display.print(Rwhite, 0);
  display.print(" G:"); display.print(Gwhite, 0);
  display.print(" B:"); display.println(Bwhite, 0);
  display.display();
  delay(2000);
}

void jalankanKalibrasiPenuh() {
  autoGain();
  kalibrasiWhiteBalance();
}

// ============================================================
// TAMPILAN LAYAR UTAMA (IDLE) - MENUNJUKKAN PILIHAN AKTIF
// ============================================================
void tampilkanLayarUtama() {
  int idxKelas = pilihanAktif / 2;
  int idxJenis = pilihanAktif % 2;
  int target = (idxJenis == 0) ? TARGET_LATIH : TARGET_UJI;

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("BeefFresh tekan=ganti");

  display.setTextSize(2);
  display.setCursor(0, 18);
  display.print(namaKelasSingkat[idxKelas]);
  display.setCursor(0, 38);
  display.print(namaJenisSingkat[idxJenis]);

  display.setTextSize(1);
  display.setCursor(75, 25);
  display.print(jumlahTersimpan[idxKelas][idxJenis]);
  display.print("/");
  display.print(target);

  display.setCursor(0, 56);
  display.println("Tahan sedang = ambil");
  display.display();
}

void tampilkanSedangMengukur() {
  int idxKelas = pilihanAktif / 2;
  int idxJenis = pilihanAktif % 2;

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 20);
  display.print("Mengukur: ");
  display.println(namaKelas[idxKelas]);
  display.setCursor(0, 32);
  display.print("Jenis: ");
  display.println(namaJenis[idxJenis]);
  display.setCursor(0, 48);
  display.println("Mohon tunggu...");
  display.display();
}

void tampilkanHasilTersimpan(float r, float g, float b) {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("Sampel Tersimpan!");
  display.setTextSize(2);
  display.setCursor(0, 14);
  display.print("R:"); display.println(r, 0);
  display.setCursor(0, 32);
  display.print("G:"); display.println(g, 0);
  display.setCursor(0, 50);
  display.print("B:"); display.println(b, 0);
  display.display();
  delay(1800);
}

// ============================================================
// PROSES PENGAMBILAN 1 SAMPEL SESUAI PILIHAN AKTIF
// ============================================================
void ambilSampelSesuaiPilihan() {
  int idxKelas = pilihanAktif / 2;
  int idxJenis = pilihanAktif % 2;

  tampilkanSedangMengukur();

  float rMentah, gMentah, bMentah;
  ambilSampelMentahBersih(rMentah, gMentah, bMentah);

  float r = (rMentah / Rwhite) * 255.0;
  float g = (gMentah / Gwhite) * 255.0;
  float b = (bMentah / Bwhite) * 255.0;

  jumlahTersimpan[idxKelas][idxJenis]++;

  float jamKe = millis() / 3600000.0; // milidetik -> jam, sejak ESP32 dinyalakan

  // Baris data ke PLX-DAQ / Excel
  Serial.print("DATA,");
  Serial.print(nomorData); Serial.print(",");
  Serial.print(jamKe, 2); Serial.print(",");
  Serial.print(r, 2); Serial.print(",");
  Serial.print(g, 2); Serial.print(",");
  Serial.print(b, 2); Serial.print(",");
  Serial.print(namaKelas[idxKelas]); Serial.print(",");
  Serial.println(namaJenis[idxJenis]);

  nomorData++;

  tampilkanHasilTersimpan(r, g, b);
  tampilkanLayarUtama();
}

// ============================================================
// PERINTAH SERIAL DARI KOMPUTER (aplikasi tombol di laptop)
//   PING            -> balas "PONG"
//   AMBIL <k> <j>   -> ambil 1 sampel; k=0 segar,1 mulai,2 busuk; j=0 latih,1 uji
//   KALIB           -> kalibrasi ulang (kertas putih harus sudah di depan sensor)
// Tombol BOOT di alat tetap berfungsi seperti biasa.
// ============================================================
void prosesPerintah(String cmd) {
  cmd.trim();
  if (cmd == "PING") {
    Serial.println("PONG");
  } else if (cmd.startsWith("AMBIL")) {
    int k = -1, j = -1;
    sscanf(cmd.c_str(), "AMBIL %d %d", &k, &j);
    if (k < 0 || k > 2 || j < 0 || j > 1) { Serial.println("ERR,perintah AMBIL tidak valid"); return; }
    pilihanAktif = k * 2 + j;
    ambilSampelSesuaiPilihan();
    Serial.println("SELESAI,AMBIL");
  } else if (cmd == "KALIB") {
    jalankanKalibrasiPenuh();
    tampilkanLayarUtama();
    Serial.print("KALIB,");
    Serial.print(Rwhite, 0); Serial.print(",");
    Serial.print(Gwhite, 0); Serial.print(",");
    Serial.print(Bwhite, 0); Serial.print(",");
    Serial.println(namaGain[gainIndexTersimpan]);
    Serial.println("SELESAI,KALIB");
  } else if (cmd.length() > 0) {
    Serial.println("ERR,perintah tidak dikenal");
  }
}

void cekPerintahSerial() {
  static String buf;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { if (buf.length()) prosesPerintah(buf); buf = ""; }
    else if (buf.length() < 40) buf += c;
  }
}

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH);
  pinMode(PIN_TOMBOL, INPUT_PULLUP); // Tombol BOOT: LOW saat ditekan

  Wire.begin(PIN_SDA, PIN_SCL);

  if (!tcs.begin()) {
    Serial.println("Sensor TCS34725 tidak terdeteksi. Program berhenti.");
    while (1);
  }
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("OLED gagal diinisialisasi. Program berhenti.");
    while (1);
  }

  Serial.println("CLEARDATA");
  Serial.println("LABEL,No,Jam Ke-,R,G,B,Label Kelas,Jenis Data");

  if (muatKalibrasi()) {
    tcs.setGain(daftarGain[gainIndexTersimpan]);
    delay(200);
  } else {
    jalankanKalibrasiPenuh();
  }

  tampilkanLayarUtama();
  Serial.println("SIAP");
}

// ============================================================
// LOOP UTAMA - MEMBACA TOMBOL BOOT (NON-BLOKIR, DENGAN DEBOUNCE)
// ============================================================
bool sedangDitekan = false;
unsigned long waktuMulaiTekan = 0;

void loop() {
  cekPerintahSerial();
  bool statusTombol = (digitalRead(PIN_TOMBOL) == LOW); // true = sedang ditekan

  if (statusTombol && !sedangDitekan) {
    // Baru saja mulai ditekan
    delay(DEBOUNCE_MS);
    if (digitalRead(PIN_TOMBOL) == LOW) {
      sedangDitekan = true;
      waktuMulaiTekan = millis();
    }
  } else if (!statusTombol && sedangDitekan) {
    // Baru saja dilepas -> hitung berapa lama tadi ditekan
    delay(DEBOUNCE_MS);
    sedangDitekan = false;
    unsigned long lamaTekan = millis() - waktuMulaiTekan;

    if (lamaTekan >= BATAS_TEKAN_LAMA_MS) {
      // Tekan lama -> kalibrasi ulang
      jalankanKalibrasiPenuh();
      tampilkanLayarUtama();
    } else if (lamaTekan >= BATAS_TEKAN_SEDANG_MS) {
      // Tekan sedang -> ambil sampel
      ambilSampelSesuaiPilihan();
    } else {
      // Tekan singkat -> pindah pilihan
      pilihanAktif = (pilihanAktif + 1) % 6;
      tampilkanLayarUtama();
    }
  }
}

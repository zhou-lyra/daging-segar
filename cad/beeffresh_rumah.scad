/*
  BeefFresh - rumah alat (OpenSCAD, satuan mm)
  =====================================================================
  Isi: ESP32 DOIT DevKit V1 + OLED SSD1306 0.96" + sensor warna TCS34725.
  Sensor menghadap ke BAWAH ke dalam tabung gelap (ruang gelap) yang ditempelkan ke permukaan daging.

  SEMUA ukuran komponen di bawah bertanda [UKUR] adalah ANGKA STANDAR/PERKIRAAN dari lembar data & penjual.
  Modul tiruan berbeda-beda: UKUR modulmu dengan jangka sorong, ganti angkanya, lalu cetak "kupon uji pas"
  (part="coupon") dulu sebelum mencetak badan penuh.

  Cara memakai:  openscad -o base.stl -D 'part="base"' beeffresh_rumah.scad
  part: base | lid | tube | coupon | assembly | ghost_esp | ghost_oled | ghost_tcs | ghost_usb
  Arah cetak (sudah dihitung oleh part *_print): base -> lantai di meja; lid -> sisi atas di meja;
  tube -> flens di meja.
*/
part   = "assembly";
d_ukur = 8;          // jarak muka chip sensor ke ujung tabung (mm). Rekomendasi modul: 3-10 mm.
$fn    = 48;
eps    = 0.01;

// ===================== KELONGGARAN CETAK =====================
tol      = 0.30;     // celah komponen-ke-dinding per sisi. FDM 0.25-0.35; resin/MJF 0.15-0.25
fit      = 0.15;     // celah pas geser (lip tutup)
wall     = 2.4;      // dinding (kelipatan 0.4 / 0.6 mm nozzle)
floor_t  = 5.4;      // lantai: ceruk flens 1.75 + rongga sensor + dudukan
lid_t    = 3.0;
lip_h    = 3.0;      // lip tutup yang masuk ke dalam dinding
lip_t    = 1.2;
corner_r = 2.0;

// ===================== ESP32 DOIT DevKit V1 (30 pin) [UKUR] =====================
esp_L = 51.8;  esp_W = 28.2;  esp_pcb = 1.6;
esp_top_h           = 4.5;    // komponen tertinggi di atas PCB
esp_pin_down        = 11.0;   // ujung pin ke bawah dari sisi bawah PCB (header + plastik)
esp_pin_floor_clear = 3.0;    // ruang antara ujung pin dan lantai (tempat solder kabel)
esp_pin_row_gap     = 25.4;   // jarak pusat-ke-pusat dua baris pin
esp_rib_w           = 12;     // lebar rusuk penyangga (harus < jarak antar baris pin - 2.54)
esp_rib_end         = 4;
usb_cut_w = 14;  usb_cut_h = 9;  usb_cut_dz = 1.3;   // lubang kabel micro-USB; dz = pusat colokan di atas sisi atas PCB (colokan 12x8)
usb_recept_over = 1.4;        // receptacle USB menjorok melewati tepi papan

// ===================== OLED SSD1306 0.96" [UKUR] =====================
oled_L   = 27.3;  oled_pcb = 1.4;
oled_win_w = 26;  oled_win_h = 15;   // jendela AMAN (lebih besar dari area tampil 21.7x10.9) sampai diukur
oled_act_dy = 0;                      // pergeseran pusat area tampil dari pusat PCB (sumbu Y, mm)
oled_back_clear = 6.0;                // ruang di bawah PCB OLED untuk header/kabel
oled_hole_off = 11.65;                // lubang pemasangan OLED dari pusat PCB (X dan Y) [UKUR]
oled_hole_d   = 2.0;                  // diameter lubang pemasangan OLED [UKUR]

// ===================== TCS34725 [UKUR] =====================
tcs_L = 20.3;  tcs_W = 20.3;  tcs_pcb = 1.6;
tcs_ap_w = 13;  tcs_ap_h = 13;        // jendela cahaya menembus lantai (harus memuat chip + LED)
tcs_ap_cx = 0;  tcs_ap_cy = 0;        // pusat jendela dari pusat papan [UKUR posisi chip+LED]
tcs_holes = [[-8.2,-8.2],[8.2,8.2]];  // lubang sekrup M2.5 dari pusat papan [UKUR]; kosongkan [] bila tak ada
tcs_hole_d = 2.5;
chip_depth = 1.2;                     // chip/LED menonjol di bawah papan
ledge      = 1.4;                     // tepi papan yang bertumpu pada lantai
pocket_d   = 0.8;                     // kantong penahan posisi papan
relief_d   = 1.8;                     // ruang untuk komponen SMD di sisi bawah papan

// ===================== TABUNG GELAP =====================
chamber_id = 24;  tube_wall = 2.0;
flange_t   = 1.6;
tube_od    = chamber_id + 2*tube_wall;
flange_d   = tube_od + 2;

// ===================== TURUNAN (jangan diubah) =====================
esp_x0 = tol;
inW    = max(esp_W, tcs_W, oled_L) + 2*tol;
esp_y0 = (inW - esp_W)/2;
gap    = 6;
pocket_L = tcs_L + 2*tol;  pocket_W = tcs_W + 2*tol;
pocket_cx = esp_x0 + esp_L + tol + gap + pocket_L/2;
pocket_cy = inW/2;
tube_cx = pocket_cx + tcs_ap_cx;
tube_cy = pocket_cy + tcs_ap_cy;
recess_r = (flange_d + 0.3)/2;
inL    = max(tube_cx + max(tube_od/2, recess_r + 1.2) - wall, pocket_cx + pocket_L/2 + tol);   // juga harus memuat kantong sensor yang lebar
outL   = inL + 2*wall;
outW   = inW + 2*wall;

z_pcb_bot = floor_t + esp_pin_floor_clear + esp_pin_down;
z_pcb_top = z_pcb_bot + esp_pcb;
z_comp_top = z_pcb_top + esp_top_h;
z_cav_top  = z_comp_top + oled_back_clear + 1;       // tinggi dinding base
z_b        = floor_t - pocket_d;                      // sisi bawah papan sensor
chip_z     = z_b - chip_depth;                        // muka chip dari dasar rumah
tube_len   = d_ukur - chip_z;

oled_cx = esp_x0 + esp_L/2;
oled_cy = inW/2;
boss_d  = 5.6;
boss_x  = esp_x0 + esp_L + tol + gap/2;
boss_y1 = boss_d/2 - 0.4;
boss_y2 = inW - boss_d/2 + 0.4;

assert(tube_len > 1, "d_ukur terlalu kecil untuk geometri ini");
assert(tube_od + 1 <= outW, "tabung lebih lebar dari badan: kecilkan chamber_id");
assert(esp_rib_w < esp_pin_row_gap - 3, "rusuk ESP32 menabrak baris pin");
// lubang sekrup sensor harus menyisakan >= 0,8 mm dinding terhadap jendela cahaya
function jarak_lubang_jendela(h) = norm([max(abs(h[0]) - tcs_ap_w/2, 0), max(abs(h[1]) - tcs_ap_h/2, 0)]);
for (h = tcs_holes) assert(jarak_lubang_jendela(h) >= 1.1 + 0.8, "lubang sekrup sensor terlalu dekat jendela cahaya: perkecil tcs_ap_w/h atau geser lubang");

// ===================== UTILITAS =====================
module rbox(x, y, z, r) {
  hull() for (i=[0,1], j=[0,1]) translate([r + i*(x-2*r), r + j*(y-2*r), 0]) cylinder(r=r, h=z);
}

// ===================== BASE =====================
module base() {
  difference() {
    union() {
      difference() {
        translate([-wall, -wall, 0]) rbox(outL, outW, z_cav_top, corner_r);
        translate([0, 0, floor_t]) cube([inL, inW, z_cav_top]);
      }
      // rusuk penyangga ESP32 (di antara dua baris pin)
      translate([esp_x0 + esp_rib_end, inW/2 - esp_rib_w/2, floor_t - eps])
        cube([esp_L - 2*esp_rib_end, esp_rib_w, z_pcb_bot - floor_t + eps]);
      // penahan ujung papan (sisi sensor)
      translate([esp_x0 + esp_L + tol, inW/2 - 5, floor_t - eps]) cube([2, 10, z_pcb_top - floor_t + eps]);
      // tab retensi (satu sisi saja supaya papan bisa dimasukkan dengan memiringkan)
      for (fx = [0.30, 0.65]) translate([esp_x0 + esp_L*fx - 3, inW - 1.1, z_pcb_top + 0.6])
        cube([6, 1.1 + eps, 1.5]);
      // boss sekrup tutup
      for (by = [boss_y1, boss_y2]) translate([boss_x, by, floor_t - eps])
        cylinder(d=boss_d, h=z_cav_top - floor_t + eps);
    }
    // pilot sekrup tutup (M2.5 self-tapping)
    for (by = [boss_y1, boss_y2]) translate([boss_x, by, z_cav_top - 10]) cylinder(d=2.2, h=10 + eps);
    // ceruk flens tabung dari bawah
    translate([tube_cx, tube_cy, -eps]) cylinder(r=recess_r, h=flange_t + 0.15 + eps);
    // jendela cahaya sensor menembus lantai
    translate([tube_cx - tcs_ap_w/2, tube_cy - tcs_ap_h/2, -eps]) cube([tcs_ap_w, tcs_ap_h, floor_t]);
    // kantong penahan papan sensor
    translate([pocket_cx - pocket_L/2, pocket_cy - pocket_W/2, z_b]) cube([pocket_L, pocket_W, pocket_d + eps]);
    // ruang relief untuk komponen SMD di bawah papan sensor
    translate([pocket_cx - (tcs_L - 2*ledge)/2, pocket_cy - (tcs_W - 2*ledge)/2, z_b - relief_d])
      cube([tcs_L - 2*ledge, tcs_W - 2*ledge, relief_d + eps]);
    // lubang kabel USB di dinding ujung
    translate([-wall - 1, inW/2 - usb_cut_w/2, z_pcb_top + usb_cut_dz - usb_cut_h/2])
      cube([wall + 2, usb_cut_w, usb_cut_h]);
  }
}

// base + tonjolan penumpu sekrup papan sensor. Ditambahkan SETELAH ruang relief dipotong,
// kalau tidak tonjolan ikut terpotong. Setiap tonjolan berlubang pilot M2.
module base_final() {
  difference() {
    union() {
      base();
      for (h = tcs_holes) translate([pocket_cx + h[0], pocket_cy + h[1], z_b - relief_d - 0.5])
        cylinder(d=tcs_hole_d + 3.2, h=relief_d + 0.5);
    }
    // lubang pilot M2: satu langkah akhir melewati tonjolan DAN lantai (menghindari permukaan ganda)
    for (h = tcs_holes) translate([pocket_cx + h[0], pocket_cy + h[1], z_b - 3])
      cylinder(d=2.2, h=3 + eps);
  }
}

// ===================== TUTUP =====================
module lid() {
  union() {
    difference() {
      translate([-wall, -wall, 0]) rbox(outL, outW, lid_t, corner_r);
      // kantong PCB OLED dari sisi bawah
      translate([oled_cx - (oled_L+0.4)/2, oled_cy - (oled_L+0.4)/2, -eps])
        cube([oled_L + 0.4, oled_L + 0.4, oled_pcb + 0.3 + eps]);
      // jendela tampilan
      translate([oled_cx - oled_win_w/2, oled_cy + oled_act_dy - oled_win_h/2, -eps])
        cube([oled_win_w, oled_win_h, lid_t + 2*eps]);
      // lubang sekrup + countersink
      for (by = [boss_y1, boss_y2]) {
        translate([boss_x, by, -eps]) cylinder(d=2.9, h=lid_t + 2*eps);
        translate([boss_x, by, lid_t - 1.4]) cylinder(d1=2.9, d2=5.8, h=1.4 + eps);
      }
    }
    // lip (turun ke dalam dinding), dengan takik di sekitar boss
    translate([0, 0, -lip_h]) difference() {
      translate([fit, fit, 0]) cube([inL - 2*fit, inW - 2*fit, lip_h + eps]);
      translate([fit + lip_t, fit + lip_t, -eps]) cube([inL - 2*fit - 2*lip_t, inW - 2*fit - 2*lip_t, lip_h + 2*eps]);
      for (by = [boss_y1, boss_y2]) translate([boss_x - (boss_d/2 + 0.8), by - 3.0, -eps]) cube([boss_d + 1.6, 6.0, lip_h + 2*eps]);   // takik persegi (bukan bundar: tidak meninggalkan serpihan tipis)
      // PCB OLED (27,3 mm) lebih lebar daripada celah antar-lip, jadi lip ditiadakan sepanjang kantong OLED
      translate([oled_cx - (oled_L + 0.4)/2, -1, -eps]) cube([oled_L + 0.4, inW + 2, lip_h + 2*eps]);
    }
    // pin penahan PCB OLED (menembus lubang pemasangan; ujungnya dipanaskan/dilem)
    for (sx = [-1, 1], sy = [-1, 1]) translate([oled_cx + sx*oled_hole_off, oled_cy + sy*oled_hole_off, -0.4])
      cylinder(d=oled_hole_d - 0.2, h=oled_pcb + 0.3 + 0.4 + eps);
  }
}

// ===================== TABUNG GELAP =====================
module tube(D = d_ukur) {
  L = D - chip_z;
  difference() {
    union() {
      cylinder(d=flange_d, h=flange_t);
      translate([0, 0, -L]) cylinder(d=tube_od, h=L + eps);
    }
    translate([0, 0, -L - eps]) cylinder(d=chamber_id, h=L + flange_t + 2*eps);
  }
}

// ===================== KUPON UJI PAS =====================
module frame(L, W, h, w = 1.6) {
  difference() {
    cube([L + 2*w, W + 2*w, h]);
    translate([w, w, -eps]) cube([L, W, h + 2*eps]);
  }
}
module coupon() {
  frame(esp_L + 2*tol, esp_W + 2*tol, 5);                                            // papan ESP32
  translate([0, esp_W + 2*tol + 8, 0]) frame(oled_L + 0.4, oled_L + 0.4, 5);          // OLED
  translate([oled_L + 14, esp_W + 2*tol + 8, 0]) frame(pocket_L, pocket_W, 5);       // sensor TCS
  // potongan dinding dengan lubang USB (uji colokan kabel)
  translate([0, esp_W + 2*tol + 8 + oled_L + 12, 0]) difference() {
    cube([usb_cut_w + 10, wall, usb_cut_h + 6]);
    translate([5, -eps, 3]) cube([usb_cut_w, wall + 2*eps, usb_cut_h]);
  }
}

// ===================== BENDA TIRUAN KOMPONEN (untuk uji tabrakan) =====================
module ghost_esp() {
  translate([esp_x0, esp_y0, z_pcb_bot]) cube([esp_L, esp_W, esp_pcb]);                              // PCB
  translate([esp_x0 + esp_L - 25.5 - 1, inW/2 - 9, z_pcb_top]) cube([25.5, 18, 3.2]);               // modul WROOM
  translate([esp_x0 - usb_recept_over, inW/2 - 3.75, z_pcb_top]) cube([5.5 + usb_recept_over, 7.5, 2.6]); // receptacle USB
  for (s = [-1, 1]) translate([esp_x0 + 6, inW/2 + s*esp_pin_row_gap/2 - 1.27, z_pcb_bot - esp_pin_down])
    cube([38.1, 2.54, esp_pin_down]);                                                                  // header + pin
}
module ghost_usb() {   // colokan kabel + selubung (menembus lubang dinding)
  translate([esp_x0 - usb_recept_over - 22, inW/2 - 6, z_pcb_top + 1.3 - 4]) cube([22, 12, 8]);
}
module ghost_oled() {
  difference() {                                                                                             // PCB di kantong tutup (berlubang)
    translate([oled_cx - oled_L/2, oled_cy - oled_L/2, z_cav_top]) cube([oled_L, oled_L, oled_pcb]);
    for (sx = [-1, 1], sy = [-1, 1]) translate([oled_cx + sx*oled_hole_off, oled_cy + sy*oled_hole_off, z_cav_top - 1])
      cylinder(d=oled_hole_d, h=oled_pcb + 2);
  }
  translate([oled_cx - 5.08, oled_cy + oled_L/2 - 4, z_cav_top - oled_back_clear]) cube([10.16, 2.54, oled_back_clear]); // header di bawah
}
module ghost_tcs() {
  translate([pocket_cx - tcs_L/2, pocket_cy - tcs_W/2, z_b]) cube([tcs_L, tcs_W, tcs_pcb]);                  // PCB
  difference() {                                                                                              // komponen SMD (relief), tidak ada di sekitar lubang sekrup
    translate([pocket_cx - 7.5, pocket_cy - 7.5, z_b - 1.0]) cube([15, 15, 1.0 + eps]);
    for (h = tcs_holes) translate([pocket_cx + h[0], pocket_cy + h[1], z_b - 2]) cylinder(d=tcs_hole_d + 3.2 + 1.0, h=3);
  }
  translate([tube_cx - 2, tube_cy - 1.5, z_b - chip_depth]) cube([4, 3, chip_depth + eps]);                  // chip
}

echo(derived = [inL, inW, outL, outW, z_cav_top, z_pcb_bot, tube_cx, tube_cy, tube_len, chip_z]);

// ===================== PEMILIH =====================
if (part == "base")            base_final();
else if (part == "lid")        lid();
else if (part == "tube")       tube();
else if (part == "coupon")     coupon();
else if (part == "base_print") base_final();
else if (part == "lid_print")  translate([0, 0, lid_t]) rotate([180, 0, 0]) lid();
else if (part == "tube_print") translate([0, 0, flange_t]) rotate([180, 0, 0]) tube();
else if (part == "lid_asm")    translate([0, 0, z_cav_top]) lid();
else if (part == "tube_asm")   translate([tube_cx, tube_cy, 0]) tube();
else if (part == "ghost_esp")  ghost_esp();
else if (part == "ghost_usb")  ghost_usb();
else if (part == "ghost_oled") ghost_oled();
else if (part == "ghost_tcs")  ghost_tcs();
else if (part == "assembly_open") {   // tanpa tutup, untuk melihat susunan di dalam
  color("#2b2b30") base_final();
  color("#111") translate([tube_cx, tube_cy, 0]) tube();
  color("#2e9e4f") ghost_esp();
  color("#c9974a") ghost_tcs();
}
else if (part == "assembly_cut") {    // potongan memanjang di tengah lebar, untuk melihat susunan dalam
  difference() {
    union() {
      color("#2b2b30") base_final();
      color("#3a3a42") translate([0, 0, z_cav_top]) lid();
      color("#111") translate([tube_cx, tube_cy, 0]) tube();
      color("#2e9e4f") ghost_esp();
      color("#4a7bd0") ghost_oled();
      color("#c9974a") ghost_tcs();
    }
    translate([-20, -20, -20]) cube([outL + 40, inW/2 + 20, 120]);
  }
}
else if (part == "assembly") {
  color("#2b2b30") base_final();
  color("#3a3a42", 0.85) translate([0, 0, z_cav_top]) lid();
  color("#111") translate([tube_cx, tube_cy, 0]) tube();
  color("#2e9e4f") ghost_esp();
  color("#4a7bd0") ghost_oled();
  color("#c9974a") ghost_tcs();
}

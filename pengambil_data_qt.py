#!/usr/bin/env python3
"""BeefFresh – Pengambil Data (PySide6 / Qt6, tema Zhou Lyra: malam + emas).

Jalankan:  ./jalankan.sh   (atau .venv/bin/python pengambil_data_qt.py [port] [file.csv])
Butuh firmware Data_Latih_Uji dengan perintah serial AMBIL / KALIB / PING.
Tombol BOOT di alat tetap berfungsi; datanya ikut tercatat.
"""
import csv, glob, json, math, os, sys, threading
from datetime import datetime

import serial
from PySide6.QtCore import QDateTime, QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontDatabase, QKeySequence, QPainter, QPen, QPolygonF, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QDateTimeEdit, QDialog, QFrame,
                               QGridLayout, QHBoxLayout, QScrollArea, QHeaderView, QLabel, QMessageBox, QProgressBar, QPushButton, QTableWidget,
                               QTableWidgetItem, QToolTip, QVBoxLayout, QWidget)

BASE = os.path.dirname(os.path.abspath(__file__))
NIGHT, SURF, LINE = "#0d1024", "#121631", "#262c5a"
GOLD, GOLDHI, IVORY, MUTED = "#c9974a", "#ecd092", "#f6efe2", "#8f8aa6"
OK, WARN, BAD = "#5fbf7f", "#e0a93b", "#d9594c"
KELAS = [("segar", "SEGAR", "#5fbf7f"), ("mulai_membusuk", "MULAI MEMBUSUK", "#e0a93b"), ("busuk", "BUSUK", "#d9594c")]
JENIS = [("latih", "LATIH"), ("uji", "UJI")]
TARGET = {"latih": 48, "uji": 12}
HEADER = ["No", "Jam_Ke", "R", "G", "B", "Label_Kelas", "Jenis_Data", "Waktu", "Potongan", "Titik"]
N_POTONGAN = 12
POTONGAN_UJI = {10, 11, 12}   # potongan ini hanya untuk data UJI (tidak pernah dipakai melatih -> tanpa kebocoran data)
TITIK_DEFAULT = 4
TIMEOUT_UKUR_S, TIMEOUT_KALIB_S = 45, 90
SERIF, SANS = "Cormorant Garamond", "Manrope"

QSS = f"""
* {{ font-family: '{SANS}'; color: {IVORY}; font-size: 13px; }}
QWidget#root {{ background: {NIGHT}; }}
QScrollArea {{ background: {NIGHT}; border: none; }}
QScrollBar:vertical {{ background: {NIGHT}; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {LINE}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QLabel#wordmark {{ font-family: '{SERIF}'; font-size: 34px; font-weight: 600; color: {GOLDHI}; }}
QLabel#kecil {{ color: {MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 2px; }}
QLabel#redup {{ color: {MUTED}; font-size: 12px; }}
QLabel#umur {{ font-size: 34px; font-weight: 300; color: {GOLDHI}; }}
QLabel#pilihan {{ font-size: 24px; font-weight: 600; }}
QFrame#hr {{ background: {LINE}; max-height: 1px; min-height: 1px; border: none; }}
QFrame#vr {{ background: {LINE}; max-width: 1px; min-width: 1px; border: none; }}
QPushButton {{ background: transparent; border: none; color: {MUTED}; text-align: left; padding: 6px 0; }}
QPushButton:hover {{ color: {GOLDHI}; }}
QPushButton:disabled {{ color: #55526b; }}
QPushButton#kelas {{ color: {IVORY}; font-weight: 700; letter-spacing: 1px; padding: 8px 10px; }}
QPushButton#kelas:hover {{ background: {SURF}; color: {IVORY}; }}
QPushButton#kelas:checked {{ background: {SURF}; }}
QPushButton#jenis {{ font-weight: 700; letter-spacing: 1px; padding: 8px 4px; margin-right: 18px; border-bottom: 2px solid {LINE}; }}
QPushButton#jenis:checked {{ color: {GOLDHI}; border-bottom: 2px solid {GOLD}; }}
QPushButton#pot, QPushButton#tit {{ border: 1px solid {LINE}; text-align: center; padding: 6px 0; min-width: 28px; border-radius: 2px; color: {IVORY}; font-weight: 600; }}
QPushButton#pot[uji="true"] {{ border: 1px dashed {GOLD}; }}
QPushButton#pot:checked, QPushButton#tit:checked {{ background: {GOLD}; color: {NIGHT}; border: 1px solid {GOLDHI}; }}
QPushButton#ambil {{ background: {GOLD}; color: {NIGHT}; text-align: center; font-size: 15px; font-weight: 800;
    letter-spacing: 3px; padding: 16px; border-radius: 2px; }}
QPushButton#ambil:hover {{ background: {GOLDHI}; color: {NIGHT}; }}
QPushButton#ambil:disabled {{ background: {SURF}; color: #55526b; }}
QPushButton#solid {{ background: {GOLD}; color: {NIGHT}; text-align: center; font-weight: 700; padding: 8px 16px; border-radius: 2px; }}
QPushButton#garis {{ border: 1px solid {LINE}; text-align: center; padding: 8px 16px; border-radius: 2px; color: {IVORY}; }}
QProgressBar {{ background: {LINE}; border: none; max-height: 3px; min-height: 3px; }}
QProgressBar::chunk {{ background: {GOLD}; }}
QComboBox {{ background: {SURF}; border: 1px solid {LINE}; border-radius: 2px; padding: 4px 10px; }}
QComboBox QAbstractItemView {{ background: {SURF}; selection-background-color: {GOLD}; selection-color: {NIGHT}; border: 1px solid {LINE}; }}
QTableWidget {{ background: {NIGHT}; alternate-background-color: {SURF}; border: none; gridline-color: transparent; font-size: 12px; }}
QHeaderView::section {{ background: {NIGHT}; color: {MUTED}; border: none; border-bottom: 1px solid {LINE}; padding: 6px; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QTableWidget::item:selected {{ background: {LINE}; }}
QDialog, QMessageBox {{ background: {SURF}; }}
QDateTimeEdit {{ background: {NIGHT}; border: 1px solid {LINE}; padding: 5px; }}
QToolTip {{ background: {SURF}; color: {IVORY}; border: 1px solid {GOLD}; padding: 4px; }}
"""


def cari_port():
    """Cari port ESP32 (CP210x / CH340 / ESP32-S USB) di Linux, Windows (COMx), dan macOS."""
    from serial.tools import list_ports
    ports = list(list_ports.comports())
    cocok = [p for p in ports if p.vid in (0x10C4, 0x1A86, 0x303A, 0x0403)]   # Silicon Labs, WCH, Espressif, FTDI
    pilihan = cocok or [p for p in ports if "USB" in (p.hwid or "").upper() or "ACM" in p.device or "USB" in p.device]
    return sorted(pilihan, key=lambda p: p.device)[0].device if pilihan else None


def rgb_ok(row):
    return tuple(float(x) for x in row[2:5])


def durasi(jam):
    t = int(round(jam * 3600)); h, r = divmod(t, 3600); m, d = divmod(r, 60)
    return (f"{h} j " if h else "") + (f"{m} mnt " if (h or m) else "") + f"{d} dtk"


def koma(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def kekuatan_pisah(rows):
    """Skor keterpisahan antar-kelas di ruang RGB: jarak pusat / rata-rata radius sebaran.
    Heuristik kasar untuk panduan, bukan akurasi klasifikasi."""
    stat = {}
    for nk, _, _ in KELAS:
        pts = [rgb_ok(r) for r in rows if r[5] == nk]
        if len(pts) < 3:
            continue
        c = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
        rad = math.sqrt(sum(sum((p[i] - c[i]) ** 2 for i in range(3)) for p in pts) / len(pts))
        stat[nk] = (c, max(rad, 1e-6))
    out, ks, nama = [], [k for k, _, _ in KELAS if k in stat], {k: n for k, n, _ in KELAS}
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a, b = stat[ks[i]], stat[ks[j]]
            s = math.dist(a[0], b[0]) / ((a[1] + b[1]) / 2)
            out.append((nama[ks[i]].title(), nama[ks[j]].title(), s, "terpisah baik" if s >= 3 else "cukup" if s >= 1.5 else "tumpang tindih"))
    return out


def garis(vertikal=False):
    f = QFrame(); f.setObjectName("vr" if vertikal else "hr"); return f


def teks_kecil(t):
    l = QLabel(t); l.setObjectName("kecil"); return l


# ------------------------------------------------------------------ grafik
class Grafik(QWidget):
    MODE = ["Kromatisitas (r–g)", "R vs G", "R vs B", "G vs B", "Jam vs R", "Jam vs G", "Jam vs B"]
    SUMBU = [("r = R/(R+G+B)", "g = G/(R+G+B)"), ("R", "G"), ("R", "B"), ("G", "B"),
             ("Umur daging (jam)", "R"), ("Umur daging (jam)", "G"), ("Umur daging (jam)", "B")]

    def __init__(self):
        super().__init__()
        self.rows, self.mode, self.titik, self.garis = [], 0, [], True
        self.setMouseTracking(True); self.setMinimumHeight(200)

    def set_data(self, rows): self.rows = rows; self.update()
    def set_mode(self, i): self.mode = i; self.update()
    def set_garis(self, on): self.garis = bool(on); self.update()

    def xy(self, row):
        r, g, b = rgb_ok(row)
        if self.mode == 0:
            s = max(r + g + b, 1e-6); return r / s, g / s
        if self.mode >= 4: return float(row[1]), (r, g, b)[self.mode - 4]
        return {1: (r, g), 2: (r, b), 3: (g, b)}[self.mode]

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        L, R_, T, B = 56, 4, 30, 34
        area = QRectF(L, T, w - L - R_, h - T - B)
        xs = [self.xy(r) for r in self.rows]
        ms_y = 0.04 if self.mode == 0 else 30
        ms_x = 0.04 if self.mode == 0 else (1.0 if self.mode >= 4 else 30)
        if xs:
            x0, x1 = min(a for a, _ in xs), max(a for a, _ in xs)
            y0, y1 = min(b for _, b in xs), max(b for _, b in xs)
        else:
            x0, x1, y0, y1 = (0.2, 0.5, 0.2, 0.5) if self.mode == 0 else (0, 255, 0, 255)

        def pad(lo, hi, ms):
            span = max(hi - lo, ms) * 1.25; c = (lo + hi) / 2
            return c - span / 2, c + span / 2
        x0, x1 = pad(x0, x1, ms_x); y0, y1 = pad(y0, y1, ms_y)
        sx = lambda v: area.left() + (v - x0) / (x1 - x0) * area.width()
        sy = lambda v: area.bottom() - (v - y0) / (y1 - y0) * area.height()
        fy = "{:.3f}" if self.mode == 0 else "{:.0f}"
        fx = "{:.3f}" if self.mode == 0 else ("{:.1f}" if self.mode >= 4 else "{:.0f}")
        p.setFont(QFont(SANS, 8))
        for i in range(5):
            gx = x0 + (x1 - x0) * i / 4; gy = y0 + (y1 - y0) * i / 4
            p.setPen(QPen(QColor(LINE), 1, Qt.DotLine))
            p.drawLine(QPointF(sx(gx), area.top()), QPointF(sx(gx), area.bottom()))
            p.drawLine(QPointF(area.left(), sy(gy)), QPointF(area.right(), sy(gy)))
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(sx(gx) - 30, area.bottom() + 5, 60, 14), Qt.AlignCenter, fx.format(gx))
            p.drawText(QRectF(0, sy(gy) - 7, L - 8, 14), Qt.AlignRight | Qt.AlignVCenter, fy.format(gy))
        p.setPen(QPen(QColor(LINE), 1)); p.drawLine(area.bottomLeft(), area.bottomRight()); p.drawLine(area.topLeft(), area.bottomLeft())
        lx, ly = self.SUMBU[self.mode]
        p.setPen(QColor(MUTED)); p.setFont(QFont(SANS, 9))
        p.drawText(QRectF(area.left(), h - 17, area.width(), 15), Qt.AlignCenter, lx)
        p.drawText(QRectF(0, 6, 260, 16), Qt.AlignLeft | Qt.AlignVCenter, "↑ " + ly)
        self.titik = []
        warna = {k: QColor(c) for k, _, c in KELAS}
        if self.garis and len(self.rows) >= 2:
            # 1) lintasan tiap titik ukur (potongan+titik yang sama) berurutan menurut waktu
            seri = {}
            for row, (a, b) in zip(self.rows, xs):
                if row[8] and row[9]: seri.setdefault((row[8], row[9]), []).append((float(row[1]), int(row[0]), a, b))
            p.setBrush(Qt.NoBrush)
            for pts in seri.values():
                pts.sort()
                if len(pts) >= 2:
                    pen = QPen(QColor(IVORY)); pen.setWidthF(1.2); c = QColor(IVORY); c.setAlpha(70); pen.setColor(c); p.setPen(pen)
                    p.drawPolyline(QPolygonF([QPointF(sx(a), sy(b)) for _, _, a, b in pts]))
            # 2) tren rata-rata terhadap umur daging (hanya sumbu jam): rata-rata per selang waktu
            if self.mode >= 4 and len(self.rows) >= 6:
                tmin, tmax = min(a for a, _ in xs), max(a for a, _ in xs)
                if tmax > tmin:
                    nb = max(2, min(12, len(self.rows) // 3)); lebar = (tmax - tmin) / nb; kotak = {}
                    for a, b in xs: kotak.setdefault(min(int((a - tmin) / lebar), nb - 1), []).append((a, b))
                    tren = [(sum(a for a, _ in v) / len(v), sum(b for _, b in v) / len(v)) for _, v in sorted(kotak.items())]
                    if len(tren) >= 2:
                        p.setPen(QPen(QColor(GOLDHI), 2.6)); p.drawPolyline(QPolygonF([QPointF(sx(a), sy(b)) for a, b in tren]))
        for row, (a, b) in zip(self.rows, xs):
            pt = QPointF(sx(a), sy(b)); col = warna.get(row[5], QColor("#888"))
            if row[6] == "uji":
                p.setPen(QPen(col, 2)); p.setBrush(Qt.NoBrush); p.drawEllipse(pt, 6, 6)
            else:
                p.setPen(QPen(QColor(NIGHT), 1)); p.setBrush(QBrush(col)); p.drawEllipse(pt, 5, 5)
            self.titik.append((pt, row))
        for nk, _, c in KELAS:
            pts = [self.xy(r) for r in self.rows if r[5] == nk]
            if len(pts) >= 2:
                mx = sum(a for a, _ in pts) / len(pts); my = sum(b for _, b in pts) / len(pts)
                p.setPen(QPen(QColor(c), 2))
                p.drawLine(QPointF(sx(mx) - 9, sy(my)), QPointF(sx(mx) + 9, sy(my)))
                p.drawLine(QPointF(sx(mx), sy(my) - 9), QPointF(sx(mx), sy(my) + 9))
        if not self.rows:
            p.setPen(QColor(MUTED)); p.setFont(QFont(SANS, 11))
            p.drawText(area, Qt.AlignCenter, "Belum ada data. Ambil sampel pertama untuk melihat sebarannya.")
        # legenda: satu baris di kanan atas, di luar area plot
        p.setFont(QFont(SANS, 8)); fm = p.fontMetrics(); x = w - R_
        for teks, c in [("● latih  ○ uji  + pusat" + ("  ━ tren rata-rata" if self.mode >= 4 and self.garis else ""), None)] + [(n.title(), c) for _, n, c in reversed(KELAS)]:
            tw = fm.horizontalAdvance(teks); x -= tw
            p.setPen(QColor(MUTED if c is None else IVORY)); p.drawText(QRectF(x, 6, tw + 2, 16), Qt.AlignVCenter, teks)
            if c:
                x -= 12; p.setPen(Qt.NoPen); p.setBrush(QColor(c)); p.drawEllipse(QPointF(x + 4, 14), 4, 4)
            x -= 18

    def mouseMoveEvent(self, e):
        best, bd = None, 12
        for pt, row in self.titik:
            d = math.hypot(pt.x() - e.position().x(), pt.y() - e.position().y())
            if d < bd: best, bd = row, d
        if best:
            QToolTip.showText(e.globalPosition().toPoint(), f"#{best[0]}  {best[5]} / {best[6]}\nR {best[2]}  G {best[3]}  B {best[4]}\numur {best[1]} jam" + (f"   ·   P{best[8]} T{best[9]}" if best[8] else ""), self)
        else:
            QToolTip.hideText()


# ------------------------------------------------------------------ serial
class SerialIO(QObject):
    baris = Signal(str)
    putus = Signal(str)

    def __init__(self, port):
        super().__init__(); self.port, self.ser = port, None

    def buka(self):
        s = serial.Serial()
        s.port, s.baudrate, s.timeout = self.port, 115200, 0.5
        s.dtr = False; s.rts = False
        s.open(); self.ser = s
        threading.Thread(target=self._baca, daemon=True).start()

    def _baca(self):
        buf = b""
        while self.ser and self.ser.is_open:
            try:
                buf += self.ser.read(256)
            except Exception as e:
                self.putus.emit(str(e)); return
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                t = line.decode(errors="replace").strip().replace("\x00", "")
                if t: self.baris.emit(t)

    def kirim(self, teks):
        if self.ser and self.ser.is_open: self.ser.write((teks + "\n").encode())


# ------------------------------------------------------------------ jendela
class Jendela(QWidget):
    def __init__(self, port, csv_path):
        super().__init__()
        self.setObjectName("root"); self.setWindowTitle("BeefFresh"); self.resize(1220, 780); self.setMinimumSize(900, 520)
        self.csv_path, self.sibuk = csv_path, False
        self.rows = self.muat_csv()
        self.t0_path = os.path.join(os.path.dirname(os.path.abspath(csv_path)), "waktu_nol.json")
        cfg = self.muat_pengaturan()
        try: self.t0 = datetime.fromisoformat(cfg["t0"])
        except Exception: self.t0 = None
        self.titik_max = int(cfg.get("titik", TITIK_DEFAULT))
        self.kelas_i, self.potongan, self.titik = 0, 1, 1
        self.pending = None
        self.timer_sibuk = QTimer(self, singleShot=True); self.timer_sibuk.timeout.connect(self.timeout)
        self.bangun()
        self.io = SerialIO(port)
        self.io.baris.connect(self.tangani)
        self.io.putus.connect(lambda m: (self.set_sibuk(False), self.status(f"Koneksi putus: {m}", BAD)))
        try:
            self.io.buka(); self.status(f"Terhubung ke {port}", OK); self.io.kirim("PING")
        except Exception as e:
            self.status(f"Gagal membuka {port}: {e}", BAD)
        self.refresh()

    # --- csv
    def muat_csv(self):
        if not os.path.exists(self.csv_path): return []
        with open(self.csv_path, newline="") as f:
            return [(x + [""] * 10)[:10] for x in list(csv.reader(f))[1:] if 7 <= len(x) <= 10]

    def tulis_csv(self):
        tmp = self.csv_path + ".tmp"
        with open(tmp, "w", newline="") as f:
            w = csv.writer(f); w.writerow(HEADER); w.writerows(self.rows)
        os.replace(tmp, self.csv_path)

    def tambah(self, r, g, b, kelas, jenis, potongan="", titik=""):
        # Jam_Ke = umur daging (jam sejak waktu nol, jam laptop); jam internal ESP32 diabaikan.
        now = datetime.now()
        row = [str((int(self.rows[-1][0]) + 1) if self.rows else 1), f"{self.umur_jam(now):.2f}", r, g, b, kelas, jenis,
               now.isoformat(timespec="seconds"), str(potongan), str(titik)]
        baru = not os.path.exists(self.csv_path)
        with open(self.csv_path, "a", newline="") as f:
            w = csv.writer(f)
            if baru: w.writerow(HEADER)
            w.writerow(row)
        self.rows.append(row); return row

    def hitung(self, k, j): return sum(1 for x in self.rows if x[5] == k and x[6] == j)

    # --- waktu nol (umur daging)
    def muat_pengaturan(self):
        try: return json.load(open(self.t0_path))
        except Exception: return {}

    def simpan_pengaturan(self):
        d = {"titik": self.titik_max}
        if self.t0: d["t0"] = self.t0.isoformat(timespec="seconds")
        json.dump(d, open(self.t0_path, "w"))

    def simpan_t0(self, dt):
        self.t0 = dt; self.simpan_pengaturan(); self.update_umur()

    def umur_jam(self, now=None):
        return ((now or datetime.now()) - self.t0).total_seconds() / 3600 if self.t0 else 0.0

    def update_umur(self):
        if self.t0:
            self.lbl_umur.setText(f"{koma(self.umur_jam())} jam"); self.lbl_nol.setText(f"= {durasi(self.umur_jam())}   ·   nol: {self.t0:%d %b %Y, %H:%M}")
        else:
            self.lbl_umur.setText("— jam"); self.lbl_nol.setText("waktu nol belum diatur")

    def dialog_waktu_nol(self):
        d = QDialog(self); d.setWindowTitle("Waktu nol daging"); v = QVBoxLayout(d); v.setSpacing(10)
        v.addWidget(QLabel("Kapan daging mulai dibiarkan / dipantau?\nJam pada data dihitung dari titik ini."))
        e = QDateTimeEdit(QDateTime(self.t0) if self.t0 else QDateTime.currentDateTime()); e.setCalendarPopup(True)
        e.setDisplayFormat("dd MMM yyyy   HH:mm"); v.addWidget(e)
        if self.rows:
            n = QLabel("Jam pada data yang sudah tersimpan tidak ikut berubah."); n.setObjectName("redup"); v.addWidget(n)
        r = QHBoxLayout()
        b_now = QPushButton("Jadikan sekarang"); b_now.setObjectName("garis")
        b_ok = QPushButton("Simpan"); b_ok.setObjectName("solid")
        b_no = QPushButton("Batal"); b_no.setObjectName("garis")
        r.addWidget(b_now); r.addStretch(); r.addWidget(b_no); r.addWidget(b_ok); v.addLayout(r)
        hasil = {}
        b_now.clicked.connect(lambda: (hasil.update(t=datetime.now()), d.accept()))
        b_ok.clicked.connect(lambda: (hasil.update(t=e.dateTime().toPython()), d.accept()))
        b_no.clicked.connect(d.reject)
        if d.exec() == QDialog.Accepted and "t" in hasil: self.simpan_t0(hasil["t"])

    # --- ui
    def bangun(self):
        luar = QVBoxLayout(self); luar.setContentsMargins(0, 0, 0, 0)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame); sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        luar.addWidget(sc)
        inner = QWidget(); inner.setObjectName("root"); sc.setWidget(inner)
        root = QVBoxLayout(inner); root.setContentsMargins(28, 12, 28, 10); root.setSpacing(0)

        head = QHBoxLayout()
        kiri = QVBoxLayout(); kiri.setSpacing(2)
        wm = QLabel("BeefFresh"); wm.setObjectName("wordmark"); kiri.addWidget(wm)
        self.lbl_status = QLabel(); kiri.addWidget(self.lbl_status)
        head.addLayout(kiri); head.addStretch()
        kan = QVBoxLayout(); kan.setSpacing(0)
        kan.addWidget(teks_kecil("UMUR DAGING"), 0, Qt.AlignRight)
        self.lbl_umur = QLabel(); self.lbl_umur.setObjectName("umur"); kan.addWidget(self.lbl_umur, 0, Qt.AlignRight)
        self.lbl_nol = QLabel(); self.lbl_nol.setObjectName("redup"); kan.addWidget(self.lbl_nol, 0, Qt.AlignRight)
        head.addLayout(kan)
        root.addLayout(head); root.addSpacing(8); root.addWidget(garis()); root.addSpacing(10)

        body = QHBoxLayout(); body.setSpacing(0); root.addLayout(body, 1)

        # rel kiri
        rail = QVBoxLayout(); rail.setSpacing(0)
        rail.addWidget(teks_kecil("KELAS DAGING")); rail.addSpacing(4)
        self.bar = {}; self.grp_kelas = QButtonGroup(self)
        for i, (nk, nama, warna) in enumerate(KELAS):
            b = QPushButton(f"{i + 1}   {nama}"); b.setObjectName("kelas"); b.setCheckable(True); b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet(f"QPushButton#kelas{{border-left:3px solid {LINE};}} QPushButton#kelas:checked{{border-left:3px solid {warna};}}")
            self.grp_kelas.addButton(b, i); rail.addWidget(b)
            bl, bu = QProgressBar(), QProgressBar()
            for pb, jn in ((bl, "latih"), (bu, "uji")):
                pb.setMaximum(TARGET[jn]); pb.setTextVisible(False)
                pb.setStyleSheet(f"QProgressBar::chunk{{background:{warna};}}")
            lbl = QLabel(); lbl.setObjectName("redup")
            self.bar[nk] = (bl, bu, lbl)
            rail.addSpacing(2); rail.addWidget(lbl); rail.addSpacing(2); rail.addWidget(bl); rail.addSpacing(1); rail.addWidget(bu); rail.addSpacing(8)
        self.grp_kelas.button(0).setChecked(True)
        self.grp_kelas.idToggled.connect(lambda i, on: on and self.pilih(kelas=i))

        rail.addWidget(teks_kecil("POTONGAN DAGING")); rail.addSpacing(6)
        gp = QGridLayout(); gp.setSpacing(4); self.grp_pot = QButtonGroup(self)
        for n in range(1, N_POTONGAN + 1):
            b = QPushButton(str(n)); b.setObjectName("pot"); b.setCheckable(True); b.setFocusPolicy(Qt.NoFocus); b.setFixedHeight(28)
            b.setProperty("uji", "true" if n in POTONGAN_UJI else "false")
            self.grp_pot.addButton(b, n); gp.addWidget(b, (n - 1) // 6, (n - 1) % 6)
        self.grp_pot.button(1).setChecked(True)
        self.grp_pot.idToggled.connect(lambda i, on: on and self.pilih(potongan=i))
        rail.addLayout(gp); rail.addSpacing(3)
        ket = QLabel(f"garis putus-putus = potongan UJI ({min(POTONGAN_UJI)}–{max(POTONGAN_UJI)}), tidak dipakai melatih"); ket.setObjectName("redup"); ket.setWordWrap(True); rail.addWidget(ket)
        rail.addSpacing(8)
        rt = QHBoxLayout(); rt.addWidget(teks_kecil("TITIK UKUR")); rt.addStretch()
        self.cb_titik = QComboBox(); self.cb_titik.addItems([f"{n} titik" for n in range(2, 9)]); self.cb_titik.setCurrentIndex(self.titik_max - 2)
        self.cb_titik.currentIndexChanged.connect(self.ubah_jumlah_titik); rt.addWidget(self.cb_titik); rail.addLayout(rt); rail.addSpacing(6)
        self.row_titik = QHBoxLayout(); self.row_titik.setSpacing(4); self.grp_tit = QButtonGroup(self)
        self.bangun_titik(); rail.addLayout(self.row_titik)
        self.grp_tit.idToggled.connect(lambda i, on: on and self.pilih(titik=i))
        rail.addStretch()

        rail.addWidget(garis()); rail.addSpacing(8); rail.addWidget(teks_kecil("ALAT & DATA")); rail.addSpacing(2)
        for teks, fn in (("Kalibrasi putih…", self.kalibrasi), ("Waktu nol daging…", self.dialog_waktu_nol),
                         ("Batalkan sampel terakhir", self.batalkan), ("Reset data uji coba…", self.reset_data)):
            b = QPushButton(teks); b.setFocusPolicy(Qt.NoFocus); b.setCursor(Qt.PointingHandCursor); b.setFixedHeight(26); b.clicked.connect(fn); rail.addWidget(b)
        rail_w = QWidget(); rail_w.setLayout(rail); rail_w.setFixedWidth(250)
        body.addWidget(rail_w); body.addSpacing(22); body.addWidget(garis(True)); body.addSpacing(22)

        # kanan
        isi = QVBoxLayout(); isi.setSpacing(0); body.addLayout(isi, 1)
        atas = QHBoxLayout(); atas.setSpacing(20)
        v = QVBoxLayout(); v.setSpacing(2)
        v.addWidget(teks_kecil("SAMPEL BERIKUTNYA"))
        self.lbl_pilihan = QLabel(); self.lbl_pilihan.setObjectName("pilihan"); v.addWidget(self.lbl_pilihan)
        v.addSpacing(8)
        self.btn_ambil = QPushButton("AMBIL SAMPEL"); self.btn_ambil.setObjectName("ambil"); self.btn_ambil.setFocusPolicy(Qt.NoFocus)
        self.btn_ambil.setCursor(Qt.PointingHandCursor); self.btn_ambil.clicked.connect(self.ambil); v.addWidget(self.btn_ambil)
        petunjuk = QLabel("Spasi = ambil   ·   1 2 3 = kelas   ·   ↑ ↓ = potongan   ·   ← → = titik   ·   Ctrl+Z = batalkan"); petunjuk.setObjectName("redup")
        v.addSpacing(4); v.addWidget(petunjuk)
        atas.addLayout(v, 1)
        sw = QVBoxLayout(); sw.setSpacing(4); sw.addWidget(teks_kecil("SAMPEL TERAKHIR"))
        self.swatch = QFrame(); self.swatch.setFixedSize(130, 64); self.swatch.setStyleSheet(f"background:{SURF};")
        self.lbl_rgb = QLabel("—"); self.lbl_rgb.setObjectName("redup")
        sw.addWidget(self.swatch); sw.addWidget(self.lbl_rgb); atas.addLayout(sw)
        isi.addLayout(atas); isi.addSpacing(10); isi.addWidget(garis()); isi.addSpacing(8)

        rg = QHBoxLayout(); rg.addWidget(teks_kecil("SEBARAN WARNA")); rg.addStretch()
        self.cb = QComboBox(); self.cb.addItems(Grafik.MODE)
        self.chk_garis = QCheckBox("Garis"); self.chk_garis.setChecked(True); self.chk_garis.setFocusPolicy(Qt.NoFocus); rg.addWidget(self.chk_garis); rg.addSpacing(10); rg.addWidget(self.cb); isi.addLayout(rg); isi.addSpacing(6)
        self.grafik = Grafik(); isi.addWidget(self.grafik, 3)
        self.cb.currentIndexChanged.connect(self.grafik.set_mode); self.chk_garis.toggled.connect(self.grafik.set_garis)
        self.lbl_pisah = QLabel(); self.lbl_pisah.setObjectName("redup"); self.lbl_pisah.setWordWrap(True)
        isi.addSpacing(2); isi.addWidget(self.lbl_pisah); isi.addSpacing(8)

        isi.addWidget(teks_kecil("DATA TERSIMPAN")); isi.addSpacing(4)
        self.tabel = QTableWidget(0, len(HEADER)); self.tabel.setHorizontalHeaderLabels(HEADER)
        self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers); self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel.setAlternatingRowColors(True); self.tabel.verticalHeader().hide(); self.tabel.setFocusPolicy(Qt.NoFocus)
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.tabel.setMinimumHeight(88)
        isi.addWidget(self.tabel, 2)
        self.lbl_file = QLabel(); self.lbl_file.setObjectName("redup"); isi.addSpacing(4); isi.addWidget(self.lbl_file)

        self.timer_umur = QTimer(self); self.timer_umur.timeout.connect(self.update_umur); self.timer_umur.start(30000)
        self.update_umur()
        QShortcut(QKeySequence(Qt.Key_F11), self, self.toggle_penuh)
        QShortcut(QKeySequence(Qt.Key_Escape), self, lambda: self.isFullScreen() and self.showNormal())
        QShortcut(QKeySequence(Qt.Key_Space), self, self.ambil)
        for i in range(3): QShortcut(QKeySequence(str(i + 1)), self, lambda i=i: self.grp_kelas.button(i).setChecked(True))
        QShortcut(QKeySequence(Qt.Key_Up), self, lambda: self.set_pot(self.potongan - 1 if self.potongan > 1 else N_POTONGAN))
        QShortcut(QKeySequence(Qt.Key_Down), self, lambda: self.set_pot(self.potongan + 1 if self.potongan < N_POTONGAN else 1))
        QShortcut(QKeySequence(Qt.Key_Left), self, lambda: self.set_titik(self.titik - 1 if self.titik > 1 else self.titik_max))
        QShortcut(QKeySequence(Qt.Key_Right), self, lambda: self.set_titik(self.titik + 1 if self.titik < self.titik_max else 1))
        QShortcut(QKeySequence("Ctrl+Z"), self, self.batalkan)

    @property
    def jenis_i(self):
        return 1 if self.potongan in POTONGAN_UJI else 0

    def toggle_penuh(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def closeEvent(self, e):
        if self.sibuk and not self.konfirm("Keluar", "Pengukuran atau kalibrasi sedang berjalan.\nTetap keluar?"):
            e.ignore(); return
        ser, self.io.ser = self.io.ser, None   # hentikan thread pembaca lebih dulu, lalu tutup port
        try:
            if ser: ser.close()
        except Exception: pass
        e.accept()

    def pilih(self, kelas=None, potongan=None, titik=None):
        if kelas is not None: self.kelas_i = kelas
        if potongan is not None: self.potongan = potongan
        if titik is not None: self.titik = titik
        self.refresh()

    def set_pot(self, n): self.grp_pot.button(n).setChecked(True)
    def set_titik(self, n): self.grp_tit.button(n).setChecked(True)

    def bangun_titik(self):
        while self.row_titik.count():   # kosongkan semua item, termasuk stretch lama (kalau tidak, tombol bergeser ke kanan)
            w = self.row_titik.takeAt(0).widget()
            if w is not None: self.grp_tit.removeButton(w); w.deleteLater()
        for n in range(1, self.titik_max + 1):
            b = QPushButton(str(n)); b.setObjectName("tit"); b.setCheckable(True); b.setFocusPolicy(Qt.NoFocus); b.setFixedHeight(28)
            self.grp_tit.addButton(b, n); self.row_titik.addWidget(b)
        self.row_titik.addStretch()
        self.titik = min(self.titik, self.titik_max)
        self.grp_tit.button(self.titik).setChecked(True)

    def ubah_jumlah_titik(self, i):
        self.titik_max = i + 2; self.simpan_pengaturan(); self.bangun_titik(); self.refresh()

    def status(self, teks, warna):
        self.lbl_status.setText(f'<span style="color:{warna}">●</span>&nbsp;&nbsp;<span style="color:{MUTED}">{teks}</span>')

    def set_sibuk(self, v, detik=0, label="MENGUKUR…"):
        self.sibuk = v; self.btn_ambil.setEnabled(not v)
        if not v: self.pending = None
        self.btn_ambil.setText(label if v else "AMBIL SAMPEL")
        self.timer_sibuk.stop()
        if v: self.timer_sibuk.start(detik * 1000)

    def timeout(self):
        self.set_sibuk(False); self.status("Alat tidak menjawab (timeout). Cek kabel USB lalu coba lagi.", BAD)

    # --- aksi
    def konfirm(self, judul, teks):
        m = QMessageBox(self); m.setWindowTitle(judul); m.setText(teks)
        m.setStandardButtons(QMessageBox.Yes | QMessageBox.No); m.setDefaultButton(QMessageBox.Yes)
        m.button(QMessageBox.Yes).setText("Ya"); m.button(QMessageBox.No).setText("Tidak")
        return m.exec() == QMessageBox.Yes

    def ambil(self):
        if self.sibuk or not self.io.ser: return
        if not self.t0:
            if not self.konfirm("Waktu nol belum diatur", "Jadikan SEKARANG sebagai jam 0 (awal pemantauan daging)?\n\nPilih Tidak untuk mengatur waktu lain lewat 'Waktu nol daging…'."):
                return
            self.simpan_t0(datetime.now())
        k, j = self.kelas_i, self.jenis_i
        self.pending = (self.potongan, self.titik)   # posisi dikunci saat perintah dikirim
        self.set_sibuk(True, TIMEOUT_UKUR_S); self.status("Mengukur. Jangan geser sampel (±12 detik)", WARN)
        self.io.kirim(f"AMBIL {k} {j}")

    def kalibrasi(self):
        if self.sibuk or not self.io.ser: return
        if not self.konfirm("Kalibrasi putih", "Taruh KERTAS PUTIH rapat di depan sensor,\ndengan jarak dan cahaya yang sama seperti saat mengukur daging.\n\nMulai kalibrasi?"):
            return
        self.set_sibuk(True, TIMEOUT_KALIB_S, "KALIBRASI…"); self.status("Kalibrasi berjalan (±22 detik). Biarkan kertas putih di tempat", WARN)
        self.io.kirim("KALIB")

    def batalkan(self):
        if not self.rows or self.sibuk: return
        r = self.rows[-1]
        if self.konfirm("Batalkan sampel", f"Hapus sampel terakhir?\n#{r[0]}  {r[5]} / {r[6]}   R{r[2]} G{r[3]} B{r[4]}"):
            self.rows.pop(); self.tulis_csv()
            if r[8].isdigit() and r[9].isdigit():   # kembali ke posisi sampel yang dibatalkan, siap diambil ulang
                self.set_pot(int(r[8])); self.set_titik(min(int(r[9]), self.titik_max))
            self.refresh()

    def reset_data(self):
        if self.sibuk: return
        n = len(self.rows)
        m = QMessageBox(self); m.setWindowTitle("Reset data uji coba")
        m.setText(f"Kosongkan semua data ({n} sampel)?\n\nCadangan lengkap disimpan otomatis di folder arsip/, jadi bisa dikembalikan.")
        b1 = m.addButton("Hapus data saja", QMessageBox.AcceptRole)
        b2 = m.addButton("Hapus data + waktu nol", QMessageBox.DestructiveRole)
        m.addButton("Batal", QMessageBox.RejectRole); m.exec()
        pilih = m.clickedButton()
        if pilih not in (b1, b2): return
        if n and os.path.exists(self.csv_path):
            arsip = os.path.join(os.path.dirname(os.path.abspath(self.csv_path)), "arsip"); os.makedirs(arsip, exist_ok=True)
            tujuan = os.path.join(arsip, f"cadangan_{datetime.now():%Y%m%d_%H%M%S}.csv")
            os.replace(self.csv_path, tujuan)
        self.rows = []
        if pilih is b2: self.t0 = None; self.simpan_pengaturan(); self.update_umur()
        self.set_pot(1); self.set_titik(1); self.refresh()
        self.status("Data dikosongkan" + (f" · cadangan: arsip/{os.path.basename(tujuan)}" if n else ""), OK)

    def tangani(self, line):
        if line.startswith("DATA,"):
            p = line.split(",")
            if len(p) == 8:
                pot, tit = self.pending or (self.potongan, self.titik)
                self.tambah(p[3], p[4], p[5], p[6], p[7], pot, tit)
                if self.pending:   # maju otomatis ke titik / potongan berikutnya (hanya untuk pengambilan dari aplikasi)
                    if tit < self.titik_max: self.set_titik(tit + 1)
                    else:
                        self.set_titik(1); self.set_pot(pot % N_POTONGAN + 1)
                self.pending = None; self.refresh()
        elif line.startswith("SELESAI,"):
            self.set_sibuk(False); self.status("Siap", OK)
        elif line.startswith("ERR,"):
            self.set_sibuk(False); self.status(line[4:], BAD)
        elif line.startswith("KALIB,"):
            p = line.split(",")
            if len(p) == 5: self.status(f"Kalibrasi tersimpan · referensi putih R{p[1]} G{p[2]} B{p[3]} · gain {p[4]}", OK)
        elif line == "SIAP" or "rst:" in line or "ets Jul" in line:
            # Alat baru restart. Kalau itu terjadi di tengah pengukuran/kalibrasi, perintahnya hilang.
            if self.sibuk:
                self.set_sibuk(False); self.status("Alat restart sendiri di tengah proses. Periksa kabel USB, lalu ulangi.", BAD)
            elif line == "SIAP":
                self.status("Alat siap", OK)
        elif line == "PONG":
            self.status("Alat siap", OK)

    # --- tampilan
    def refresh(self):
        k, j = self.kelas_i, self.jenis_i
        n_pot = sum(1 for x in self.rows if x[8] == str(self.potongan))
        self.lbl_pilihan.setText(f"{KELAS[k][1].title()}  ·  Potongan {self.potongan}  ·  Titik {self.titik}   ({JENIS[j][1].lower()}, {n_pot} sampel di potongan ini)")
        for nk, _, _ in KELAS:
            bl, bu, lbl = self.bar[nk]; a, b = self.hitung(nk, "latih"), self.hitung(nk, "uji")
            bl.setValue(min(a, TARGET["latih"])); bu.setValue(min(b, TARGET["uji"]))
            lbl.setText(f"latih {a}/{TARGET['latih']}   ·   uji {b}/{TARGET['uji']}")
        self.tabel.setRowCount(0)
        for row in self.rows[-300:]:
            i = self.tabel.rowCount(); self.tabel.insertRow(i)
            for c, val in enumerate(row):
                it = QTableWidgetItem(val); it.setTextAlignment(Qt.AlignCenter)
                if c == 5: it.setForeground(QColor(next((cc for kk, _, cc in KELAS if kk == val), IVORY)))
                self.tabel.setItem(i, c, it)
        self.tabel.scrollToBottom()
        self.grafik.set_data(self.rows)
        if self.rows:
            r, g, b = (max(0, min(255, int(v))) for v in rgb_ok(self.rows[-1]))
            self.swatch.setStyleSheet(f"background:rgb({r},{g},{b});")
            q = self.rows[-1]; self.lbl_rgb.setText(f"#{q[0]}   R {q[2]}   G {q[3]}   B {q[4]}")
        ps = kekuatan_pisah(self.rows)
        self.lbl_pisah.setText("Keterpisahan kelas (skor kasar, ≥3 sampel per kelas):   " + (
            "     ".join(f"{a} ↔ {b}: {koma(s, 1)} ({lab})" for a, b, s, lab in ps) if ps else "belum cukup data"))
        self.lbl_file.setText(f"{len(self.rows)} sampel  ·  {self.csv_path}")


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else cari_port()
    csv_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "data_beeffresh.csv")
    app = QApplication(sys.argv); app.setStyle("Fusion")
    for f in glob.glob(os.path.join(BASE, "assets", "fonts", "*.ttf")): QFontDatabase.addApplicationFont(f)
    app.setStyleSheet(QSS)
    if not port:
        QMessageBox.critical(None, "BeefFresh", "ESP32 tidak terdeteksi.\nColok dengan kabel data lalu jalankan ulang."); return 1
    w = Jendela(port, csv_path); w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

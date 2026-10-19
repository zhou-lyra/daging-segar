#!/usr/bin/env python3
"""Pengendali ESP32 BeefFresh lewat baris perintah (untuk dipakai jarak jauh lewat SSH).
Satu perintah = satu jawaban JSON di satu baris, supaya mudah dibaca program.

Pemakaian (tutup dulu aplikasi Qt: satu port serial hanya boleh dipakai satu proses):
  python ukur.py cari                 # daftar port serial
  python ukur.py ping
  python ukur.py raw                  # rata-rata 5 bacaan MENTAH + gain + referensi putih + keadaan LED
  python ukur.py ambil 0 0            # ambil 1 sampel: kelas 0=segar 1=mulai_membusuk 2=busuk, jenis 0=latih 1=uji
  python ukur.py led 0                # matikan LED bawaan sensor (GPIO 26), led 1 = nyalakan
  python ukur.py kalib                # kalibrasi putih (kertas putih HARUS sudah di depan sensor)
  python ukur.py --port COM5 ping     # pilih port sendiri
Prasyarat: pip install pyserial. Firmware harus yang berisi perintah RAW/LED (jarak_jauh/firmware)."""
import json, sys, time
import serial
from serial.tools import list_ports

BAUD = 115200
VID_ESP = {0x10C4, 0x1A86, 0x0403, 0x303A}   # CP210x, CH340, FTDI, Espressif


def cari_port():
    return [p for p in list_ports.comports() if p.vid in VID_ESP] or list(list_ports.comports())


def buka(port):
    s = serial.Serial(); s.port = port; s.baudrate = BAUD; s.timeout = 0.5
    s.dtr = False; s.rts = False                  # jangan mereset ESP32 saat port dibuka
    s.open(); time.sleep(0.3); s.reset_input_buffer(); return s


def kirim(s, perintah, selesai, batas=60):
    s.write((perintah + "\n").encode()); s.flush()
    baris, t0 = [], time.time()
    while time.time() - t0 < batas:
        b = s.readline().decode(errors="replace").strip()
        if not b: continue
        baris.append(b)
        if b.startswith(selesai) or b.startswith("ERR") or b == "PONG": break
    return baris


def main(argv):
    port = None
    if argv[:1] == ["--port"]: port, argv = argv[1], argv[2:]
    if not argv: print(__doc__); return 2
    cmd, arg = argv[0], argv[1:]
    if cmd == "cari":
        print(json.dumps([{"port": p.device, "deskripsi": p.description, "vid": p.vid} for p in cari_port()])); return 0
    if port is None:
        ada = cari_port()
        if not ada: print(json.dumps({"ok": False, "galat": "tidak ada port serial; ESP32 tercolok?"})); return 1
        port = ada[0].device
    try:
        s = buka(port)
    except Exception as e:
        print(json.dumps({"ok": False, "port": port, "galat": f"gagal membuka port (aplikasi Qt masih terbuka?): {e}"})); return 1
    try:
        int(arg[0]) if cmd in ("led", "ambil") else 0; int(arg[1]) if cmd == "ambil" else 0
    except (ValueError, IndexError):
        s.close(); print(json.dumps({"ok": False, "galat": "argumen tidak valid (led 0|1, ambil <kelas 0-2> <jenis 0-1>)"})); return 2
    with s:
        if cmd == "ping": b = kirim(s, "PING", "PONG", 5)
        elif cmd == "raw": b = kirim(s, "RAW", "SELESAI,RAW", 20)
        elif cmd == "ambil": b = kirim(s, f"AMBIL {int(arg[0])} {int(arg[1])}", "SELESAI,AMBIL", 30)
        elif cmd == "led": b = kirim(s, f"LED {int(arg[0])}", "LED,", 5)
        elif cmd == "kalib": b = kirim(s, "KALIB", "SELESAI,KALIB", 120)
        else: print(__doc__); return 2
    out = {"ok": not any(x.startswith("ERR") for x in b) and bool(b), "port": port, "cmd": cmd, "baris": b}
    for x in b:
        f = x.split(",")
        if f[0] == "RAW" and len(f) >= 10:
            r, g, bl, c = map(float, f[1:5]); out["raw"] = dict(R=r, G=g, B=bl, C=c, gain=f[5], Rputih=float(f[6]), Gputih=float(f[7]), Bputih=float(f[8]), led=int(f[9]),
                                                               R_per_G=round(r / g, 3) if g else None)
            if len(f) >= 13: out["raw"].update(Rgelap=float(f[10]), Ggelap=float(f[11]), Bgelap=float(f[12]))
        if f[0] == "DATA" and len(f) >= 8:
            out["data"] = dict(no=int(f[1]), R=float(f[3]), G=float(f[4]), B=float(f[5]), kelas=f[6], jenis=f[7], R_per_G=round(float(f[3]) / float(f[4]), 3))
    print(json.dumps(out, ensure_ascii=False)); return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

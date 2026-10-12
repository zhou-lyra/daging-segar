#!/usr/bin/env bash
# Peluncur BeefFresh (Qt6). Grup dialout dipastikan lewat sg bila sesi belum memuatnya.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
# Lewat XWayland (xcb) agar bilah judul + tombol minimize/layar penuh/tutup digambar oleh GNOME, bukan oleh Qt (di Wayland murni tombolnya tak terlihat). Fallback ke wayland bila xcb tak ada.
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb;wayland}"
if id -nG | grep -qw dialout; then exec .venv/bin/python pengambil_data_qt.py "$@"; else exec sg dialout -c ".venv/bin/python pengambil_data_qt.py $*"; fi

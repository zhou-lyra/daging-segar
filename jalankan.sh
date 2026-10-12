#!/usr/bin/env bash
# Peluncur BeefFresh (Qt6). Grup dialout dipastikan lewat sg bila sesi belum memuatnya.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
if id -nG | grep -qw dialout; then exec .venv/bin/python pengambil_data_qt.py "$@"; else exec sg dialout -c ".venv/bin/python pengambil_data_qt.py $*"; fi

#!/bin/sh
# Render semua frame film (CPU; GTX 1050 Ti di mesin ini lebih lambat dari CPU). Sekitar 1,5 sampai 2 jam.
cd "$(dirname "$0")"
for m in banding jepit genggam; do ~/.local/bin/blender -b -P blender_film.py -- $m 12 0 100000 80 CPU 2>&1 | grep -E "^FRAME|Error|Traceback"; done
echo SELESAI

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p dist
"${CXX:-x86_64-w64-mingw32-g++}" -std=c++17 -O2 -s -ffunction-sections -fdata-sections -Wall -Wextra -Werror \
 -static -static-libgcc -static-libstdc++ -municode -mwindows \
 -Wl,--gc-sections,--no-insert-timestamp main.cpp -o dist/PACSScroll.exe -luser32 -lshell32 -lgdi32 -lgdiplus
(cd dist && sha256sum PACSScroll.exe > SHA256SUMS.txt)

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p dist
"${CXX:-x86_64-w64-mingw32-g++}" -std=c++17 -O2 -Wall -Wextra -Werror \
  -static -static-libgcc -static-libstdc++ -municode -mwindows \
  -Wl,--no-insert-timestamp main.cpp -o dist/PACSLocalizer.exe -luser32 -lshell32
(cd dist && sha256sum PACSLocalizer.exe > SHA256SUMS.txt)

#!/bin/sh
set -eu

version="b5046"
checksum="c19be78b5f00d8d29a25da41042cb7afa094cbf6280a225abe614b03b20029ab"
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
vendor="$root/Vendor"
archive="${TMPDIR:-/tmp}/llama-${version}-xcframework.zip"

mkdir -p "$vendor"
curl -L --fail -o "$archive" "https://github.com/ggml-org/llama.cpp/releases/download/${version}/llama-${version}-xcframework.zip"
actual="$(shasum -a 256 "$archive" | awk '{print $1}')"
test "$actual" = "$checksum"
rm -rf "$vendor/llama.xcframework"
unzip -q "$archive" -d "$vendor"
mv "$vendor/build-apple/llama.xcframework" "$vendor/llama.xcframework"
rmdir "$vendor/build-apple"

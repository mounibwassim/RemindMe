#!/bin/bash
set -e

APK="/mnt/c/Users/User/Documents/Projects/RemindMe/bin/remindme-2.0.7-armeabi-v7a_arm64-v8a-release-unsigned.apk"
OUT="/mnt/c/Users/User/Documents/Projects/RemindMe/bin/RemindMe-2.0.7.apk"
WORK="/home/mounib/apk_work"

echo "[1] Work dir: $WORK"
rm -rf "$WORK"
mkdir -p "$WORK/extract" "$WORK/tar_contents"

echo "[2] Unzipping APK..."
unzip -q "$APK" -d "$WORK/extract"
chmod -R 755 "$WORK/extract"

echo "[3] Extracting private.tar..."
tar -xzf "$WORK/extract/assets/private.tar" -C "$WORK/tar_contents"
chmod -R 755 "$WORK/tar_contents"

echo "[4] Before patch:"
cat "$WORK/tar_contents/p4a_env_vars.txt"

echo "[5] Injecting Adreno vars..."
printf "ADRENO_DISABLE_SHADER_DISK_CACHE=1\nSDL_OPENGLES_MAJOR=2\nSDL_OPENGLES_MINOR=0\n" >> "$WORK/tar_contents/p4a_env_vars.txt"

echo "[6] After patch:"
cat "$WORK/tar_contents/p4a_env_vars.txt"

echo "[7] Repacking private.tar..."
cd "$WORK/tar_contents"
tar -czf "$WORK/extract/assets/private.tar" .

echo "[8] Repacking APK..."
cd "$WORK/extract"
zip -qr "$OUT" .

echo "[9] Cleanup..."
rm -rf "$WORK"

echo "=== DONE ==="
ls -lh "$OUT"

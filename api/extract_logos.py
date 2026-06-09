#!/usr/bin/env python3
"""
Jalankan script ini SATU KALI di komputer lokal untuk mengekstrak
semua logo dari playlist malingenak.m3u ke folder logos/.

Setelah selesai, commit dan push folder logos/ ke GitHub.
Vercel akan otomatis serve file di logos/ sebagai static files.

Usage:
    pip install requests
    python3 extract_logos.py
"""
import re
import base64
import hashlib
import os
import requests

PLAYLIST_URL = "https://ayomalinggo.blog/maling/malingenak.m3u"
OUTPUT_DIR   = "logos"

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
}

print(f"Fetching {PLAYLIST_URL} ...")
resp = requests.get(PLAYLIST_URL, headers=headers, timeout=30)
resp.encoding = "utf-8"
content = resp.text
print(f"Dapat {len(content):,} karakter, {content.count('#EXTINF')} channel")

RE_B64 = re.compile(r'tvg-logo="data:image/(?P<mime>\w+);base64,(?P<b64>[^"]+)"')

os.makedirs(OUTPUT_DIR, exist_ok=True)

logos = {}
for m in RE_B64.finditer(content):
    lid = hashlib.md5(m.group("b64").encode()).hexdigest()[:16]
    if lid not in logos:
        logos[lid] = (m.group("mime"), m.group("b64"))

print(f"Ditemukan {len(logos)} logo unik")

saved = 0
skipped = 0
for lid, (mime, b64) in logos.items():
    path = os.path.join(OUTPUT_DIR, f"{lid}.png")
    if os.path.exists(path):
        skipped += 1
        continue
    img_bytes = base64.b64decode(b64)
    with open(path, "wb") as f:
        f.write(img_bytes)
    saved += 1
    print(f"  Simpan {path} ({len(img_bytes):,} bytes)")

print()
print(f"Selesai! {saved} logo baru, {skipped} sudah ada.")
print()
print("Langkah selanjutnya:")
print("  git add logos/")
print('  git commit -m "Add logo PNG files"')
print("  git push")

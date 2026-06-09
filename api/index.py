from flask import Flask, Response
import requests
import re
import base64
import hashlib

app = Flask(__name__)

# ---------------------------------------------------------------
# Cache logo: { hash_id -> (mime_type, raw_bytes) }
# Diisi saat playlist di-fetch, lalu di-serve via /logo/<id>
# ---------------------------------------------------------------
logo_cache = {}

RE_BASE64_LOGO = re.compile(
    r'tvg-logo="data:image/(?P<mime>\w+);base64,(?P<b64>[^"]+)"'
)

def extract_logo(extinf_line, base_url):
    """
    Jika tvg-logo berformat data:URI base64:
      - Decode -> simpan di logo_cache
      - Ganti dengan URL /logo/<hash> yang bisa di-serve Flask
    Jika tvg-logo sudah berupa URL http/https: biarkan.
    Jika tidak ada tvg-logo: biarkan.
    """
    def replacer(m):
        mime = m.group('mime')      # 'png', 'jpeg', dll.
        b64  = m.group('b64')
        # Buat ID unik dari konten gambar
        logo_id = hashlib.md5(b64.encode()).hexdigest()[:16]
        if logo_id not in logo_cache:
            try:
                img_bytes = base64.b64decode(b64)
                logo_cache[logo_id] = (f'image/{mime}', img_bytes)
            except Exception:
                return m.group(0)   # Gagal decode, biarkan asli
        return f'tvg-logo="{base_url}/logo/{logo_id}"'

    return RE_BASE64_LOGO.sub(replacer, extinf_line)


# ---------------------------------------------------------------
# Endpoint: serve gambar logo
# ---------------------------------------------------------------
@app.route('/logo/<logo_id>')
def serve_logo(logo_id):
    if logo_id not in logo_cache:
        return Response('Not Found', status=404)
    mime, img_bytes = logo_cache[logo_id]
    return Response(
        img_bytes,
        mimetype=mime,
        headers={
            'Cache-Control': 'public, max-age=86400',
            'Content-Length': str(len(img_bytes)),
        }
    )


# ---------------------------------------------------------------
# Endpoint: merge playlist
# ---------------------------------------------------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK PLAYLIST LO DI BAWAH INI ---
    playlists = [
        {"url": "https://ayo.maling.pl/Vision/channels.php",                                         "group": "VISION+"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/ch.php",                                     "group": "TV CHANNEL"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php",                                  "group": "EVENT"},
        {"url": "https://ayomalinggo.blog/maling/malingenak.m3u",                                    "group": "AUTO LIVE 1"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/tvri.php",                                   "group": "TVRI CHANNEL"},
        {"url": "https://malingya.goblogtv.workers.dev",                                              "group": "LIVE AUTO II"},
        {"url": "https://ayo.maling.pl/thth/1.php",                                                  "group": "EVENT+"},
        {"url": "https://ayo.maling.pl/sawitku.m3u",                                                 "group": "EVENT SAWIT"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php",                               "group": "SPORTS NEW"},
        {"url": "https://raw.githubusercontent.com/apistech/project/refs/heads/main/IndihomeTV.m3u", "group": "INDIHOME"},
        {"url": "https://enakmalinggo.blog/maling/logo.php",                                         "group": "OLAHRAGA"},
        {"url": "https://enakmalinggo.blog/maling/dens.php",                                         "group": "DENS"},
    ]
    # -------------------------------------------------

    # Deteksi base URL server ini (untuk membuat link /logo/<id>)
    # Contoh: http://192.168.1.10:5000  atau  https://mydomain.com
    from flask import request
    base_url = request.host_url.rstrip('/')

    merged_content = "#EXTM3U\n"
    seen_urls = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }

    for pl in playlists:
        try:
            resp = requests.get(pl["url"], headers=headers, timeout=10)
            if resp.status_code != 200:
                continue

            resp.encoding = 'utf-8'
            lines = resp.text.splitlines()
            current_extinf = ""

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#EXTM3U"):
                    continue

                if line.startswith("#EXTINF"):
                    # Konversi logo base64 -> URL endpoint /logo/<id>
                    line = extract_logo(line, base_url)

                    # Tambahkan group-title jika belum ada
                    if "group-title=" not in line:
                        line = re.sub(
                            r"(#EXTINF:-?\d+)",
                            rf'\1 group-title="{pl["group"]}"',
                            line, count=1
                        )
                    current_extinf = line

                elif not line.startswith("#"):
                    # Baris URL stream
                    if current_extinf and line not in seen_urls:
                        seen_urls.add(line)
                        merged_content += current_extinf + "\n" + line + "\n"
                    current_extinf = ""

                elif current_extinf:
                    # Tag tambahan (#EXTVLCOPT, #KODIPROP, dll.)
                    current_extinf += "\n" + line

        except Exception:
            pass

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

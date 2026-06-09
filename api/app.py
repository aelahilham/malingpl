from flask import Flask, Response, request
import requests
import re
import base64
import hashlib
import os

app = Flask(__name__)

# Base URL untuk logo statis di Vercel
# Format: https://NAMA-PROJECT.vercel.app
# Dideteksi otomatis dari VERCEL_URL environment variable,
# atau fallback ke host dari request.
def get_base_url():
    vercel_url = os.environ.get('VERCEL_URL')
    if vercel_url:
        return f'https://{vercel_url}'
    return request.host_url.rstrip('/')

RE_B64 = re.compile(
    r'tvg-logo="data:image/(?P<mime>\w+);base64,(?P<b64>[^"]+)"'
)

def convert_logo(extinf_line, base_url):
    """
    Ganti tvg-logo base64 dengan URL file statis di folder /logos/.
    File PNG-nya sudah di-generate oleh extract_logos.py dan ada di repo.
    """
    def rep(m):
        lid = hashlib.md5(m.group('b64').encode()).hexdigest()[:16]
        return f'tvg-logo="{base_url}/logos/{lid}.png"'
    return RE_B64.sub(rep, extinf_line)


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

    base_url = get_base_url()
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
                    # Konversi logo base64 -> URL file statis /logos/<id>.png
                    line = convert_logo(line, base_url)

                    if "group-title=" not in line:
                        line = re.sub(
                            r"(#EXTINF:-?\d+)",
                            rf'\1 group-title="{pl["group"]}"',
                            line, count=1
                        )
                    current_extinf = line

                elif not line.startswith("#"):
                    if current_extinf and line not in seen_urls:
                        seen_urls.add(line)
                        merged_content += current_extinf + "\n" + line + "\n"
                    current_extinf = ""

                elif current_extinf:
                    current_extinf += "\n" + line

        except Exception:
            pass

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

from flask import Flask, Response
import requests
import re

app = Flask(__name__)

# Regex untuk mendeteksi dan menghapus tvg-logo berformat data:URI base64
# (tidak didukung oleh IPTV player manapun)
RE_BASE64_LOGO = re.compile(r'\s*tvg-logo="data:[^"]*"')

def strip_base64_logo(extinf_line):
    """Hapus tvg-logo berformat data:URI dari baris #EXTINF."""
    return RE_BASE64_LOGO.sub('', extinf_line)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK PLAYLIST LO DI BAWAH INI ---
    playlists = [
        {"url": "https://ayo.maling.pl/Vision/channels.php",                                    "group": "VISION+"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/ch.php",                                "group": "TV CHANNEL"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php",                             "group": "EVENT"},
        {"url": "https://ayomalinggo.blog/maling/malingenak.m3u",                               "group": "AUTO LIVE 1"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/tvri.php",                              "group": "TVRI CHANNEL"},
        {"url": "https://malingya.goblogtv.workers.dev",                                         "group": "LIVE AUTO II"},
        {"url": "https://ayo.maling.pl/thth/1.php",                                             "group": "EVENT+"},
        {"url": "https://ayo.maling.pl/sawitku.m3u",                                            "group": "EVENT SAWIT"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php",                          "group": "SPORTS NEW"},
        {"url": "https://raw.githubusercontent.com/apistech/project/refs/heads/main/IndihomeTV.m3u", "group": "INDIHOME"},
        {"url": "https://enakmalinggo.blog/maling/logo.php",                                    "group": "OLAHRAGA"},
        {"url": "https://enakmalinggo.blog/maling/dens.php",                                    "group": "DENS"},
    ]
    # -------------------------------------------------

    merged_content = "#EXTM3U\n"
    seen_urls = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }

    for pl in playlists:
        try:
            response = requests.get(pl["url"], headers=headers, timeout=10)

            if response.status_code != 200:
                continue

            response.encoding = 'utf-8'
            lines = response.text.splitlines()

            current_extinf = ""

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#EXTM3U"):
                    continue

                if line.startswith("#EXTINF"):
                    # Hapus tvg-logo base64 — format ini tidak didukung player IPTV.
                    # Player hanya bisa baca tvg-logo berupa URL http/https.
                    line = strip_base64_logo(line)

                    # Tambahkan group-title jika belum ada
                    if "group-title=" not in line:
                        line = re.sub(
                            r"(#EXTINF:-?\d+)",
                            rf'\1 group-title="{pl["group"]}"',
                            line,
                            count=1
                        )
                    current_extinf = line

                elif not line.startswith("#"):
                    # Baris URL stream
                    stream_url = line
                    if current_extinf and stream_url not in seen_urls:
                        seen_urls.add(stream_url)
                        merged_content += current_extinf + "\n" + stream_url + "\n"
                    current_extinf = ""

                elif current_extinf:
                    # Tag tambahan (#EXTVLCOPT, #KODIPROP, dll.)
                    current_extinf += "\n" + line

        except Exception:
            pass

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

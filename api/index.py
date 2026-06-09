from flask import Flask, Response
import requests
import re

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK PLAYLIST LO DI BAWAH INI ---
    playlists = [
        {"url": "https://ayo.maling.pl/Vision/channels.php", "group": "VISION+"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/ch.php", "group": "TV CHANNEL"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php", "group": "EVENT"},
        {"url": "https://ayomalinggo.blog/maling/malingenak.m3u", "group": "AUTO LIVE 1"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/tvri.php", "group": "TVRI CHANNEL"},
        {"url": "https://malingya.goblogtv.workers.dev", "group": "LIVE AUTO II"},
        {"url": "https://ayo.maling.pl/thth/1.php", "group": "EVENT+"},
        {"url": "https://ayo.maling.pl/sawitku.m3u", "group": "EVENT SAWIT"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php", "group": "SPORTS NEW"},
        {"url": "https://raw.githubusercontent.com/apistech/project/refs/heads/main/IndihomeTV.m3u", "group": "INDIHOME"},
        {"url": "https://enakmalinggo.blog/maling/logo.php", "group": "OLAHRAGA"},
        {"url": "https://enakmalinggo.blog/maling/dens.php", "group": "DENS"}
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

            if response.status_code == 200:
                response.encoding = 'utf-8'
                raw_text = response.text

                # --- FIX UTAMA ---
                # Beberapa playlist (seperti malingenak.m3u) menyimpan tvg-logo
                # berformat "data:image/...;base64,..." yang sangat panjang dan
                # mengandung karakter newline di dalam nilai base64-nya (akibat
                # encoding atau format file yang tidak standar).
                #
                # Strategi: gabungkan dulu semua baris yang bukan header
                # #EXTM3U, bukan #EXTINF, bukan #EXTVLCOPT/#KODIPROP, dan bukan
                # URL stream menjadi satu baris dengan baris #EXTINF sebelumnya.
                #
                # Caranya: split per blok channel menggunakan regex, sehingga
                # kita tidak bergantung pada asumsi "satu baris = satu item".

                # Normalisasi: pisahkan teks menjadi token-token channel
                # Setiap channel diawali oleh baris #EXTINF
                # Kita cari semua posisi #EXTINF dan potong teks di sana.

                # Pisahkan baris, tapi tangani base64 multiline dengan cara
                # menggabungkan baris lanjutan ke baris #EXTINF yang sebelumnya.
                raw_lines = raw_text.splitlines()
                lines = []
                buffer = ""

                for raw_line in raw_lines:
                    stripped = raw_line.strip()
                    if not stripped:
                        continue

                    if stripped.startswith("#EXTM3U"):
                        continue

                    # Deteksi apakah baris ini adalah awal tag yang dikenal
                    is_known_tag = (
                        stripped.startswith("#EXTINF")
                        or stripped.startswith("#EXTVLCOPT")
                        or stripped.startswith("#KODIPROP")
                        or stripped.startswith("#EXT-X-")
                        or stripped.startswith("#EXTGRP")
                    )

                    # Deteksi apakah baris ini adalah URL stream
                    is_stream_url = (
                        stripped.startswith("http://")
                        or stripped.startswith("https://")
                        or stripped.startswith("rtmp://")
                        or stripped.startswith("rtsp://")
                        or stripped.startswith("rtp://")
                        or stripped.startswith("udp://")
                    )

                    if is_known_tag or is_stream_url:
                        # Simpan buffer sebelumnya (jika ada) ke lines
                        if buffer:
                            lines.append(buffer)
                            buffer = ""
                        if is_known_tag:
                            # Mulai buffer baru untuk tag ini
                            buffer = stripped
                        else:
                            # URL stream langsung masuk sebagai baris tersendiri
                            lines.append(stripped)
                    else:
                        # Baris ini adalah lanjutan dari baris sebelumnya
                        # (misalnya base64 yang terpotong ke baris baru)
                        if buffer:
                            buffer += stripped  # Sambung tanpa spasi
                        # Jika tidak ada buffer aktif, abaikan baris ini

                # Jangan lupa flush buffer terakhir
                if buffer:
                    lines.append(buffer)

                # Sekarang proses lines seperti biasa
                current_extinf = ""

                for line in lines:
                    if line.startswith("#EXTINF"):
                        # Tambahkan group-title jika belum ada
                        if "group-title=" not in line:
                            line = line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{pl["group"]}"', 1)
                            # Kalau format durasinya bukan -1 persis, coba cara lain
                            if "group-title=" not in line:
                                line = re.sub(
                                    r"(#EXTINF:-?\d+)",
                                    rf'\1 group-title="{pl["group"]}"',
                                    line,
                                    count=1
                                )
                        current_extinf = line

                    elif not line.startswith("#"):
                        stream_url = line

                        if current_extinf and stream_url not in seen_urls:
                            seen_urls.add(stream_url)
                            merged_content += current_extinf + "\n" + stream_url + "\n"

                        current_extinf = ""

                    elif line.startswith("#") and current_extinf:
                        # Tag tambahan seperti #EXTVLCOPT, #KODIPROP, dll.
                        current_extinf += "\n" + line

        except Exception:
            pass

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

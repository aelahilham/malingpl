from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK HTTP TOOLKIT LO DI BAWAH INI ---
    playlists = [
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php", "group": "EVENT"},
        {"url": "https://ayo.maling.pl/thth/1.php", "group": "EVENT+"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php", "group": "SPORTS NEW"}
    ]
    # -------------------------------------------------

    merged_content = "#EXTM3U\n"
    
    # Penyamaran sebagai HP Android agar tidak diblokir server OTT
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }
    
    for pl in playlists:
        try:
            response = requests.get(pl["url"], headers=headers, timeout=10)
            
            # Kalau sukses ditarik
            if response.status_code == 200:
                lines = response.text.splitlines()
                for line in lines:
                    if line.startswith("#EXTM3U"):
                        continue
                    
                    if line.startswith("#EXTINF"):
                        if "group-title=" not in line:
                            line = line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{pl["group"]}"')
                    
                    merged_content += line + "\n"
        except Exception:
            pass # Kalau satu link gagal/error, biarkan lanjut ke link berikutnya

    return Response(merged_content, mimetype='audio/mpegurl')

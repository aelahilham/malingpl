from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK PLAYLIST LO DI BAWAH INI ---
    playlists = [
        {"url": "https://ayo.maling.pl/Vision/channels.php", "group": "VISION+"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php", "group": "EVENT"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/ch.php", "group": "TV CHANNEL"},
        {"url": "https://raw.githubusercontent.com/apistech/project/refs/heads/main/IndihomeTV.m3u", "group": "INDIHOME"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/tvri.php", "group": "TVRI CHANNEL"},
        {"url": "https://ayo.maling.pl/thth/1.php", "group": "EVENT+"},
        {"url": "https://ayo.maling.pl/sawitku.m3u", "group": "EVENT SAWIT"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php", "group": "SPORTS NEW"},
        {"url": "https://enakmalinggo.blog/maling/logo.php", "group": "OLAHRAGA"},
        {"url": "https://enakmalinggo.blog/maling/dens.php", "group": "DENS"}
    ]
    # -------------------------------------------------

    merged_content = "#EXTM3U\n"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }
    
    for pl in playlists:
        try:
            response = requests.get(pl["url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                # ---> FIX 1: Paksa Python baca hasil tarikan sebagai UTF-8
                response.encoding = 'utf-8'
                
                lines = response.text.splitlines()
                for line in lines:
                    if line.startswith("#EXTM3U"):
                        continue
                    
                    if line.startswith("#EXTINF"):
                        if "group-title=" not in line:
                            line = line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{pl["group"]}"')
                    
                    merged_content += line + "\n"
        except Exception:
            pass 

    # ---> FIX 2: Kasih tau aplikasi IPTV lo kalo output ini formatnya UTF-8
    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')

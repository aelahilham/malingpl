from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    # --- MASUKIN LINK HTTP TOOLKIT LO DI BAWAH INI ---
    playlists = [
        {"url": "LINK_HTTP_TOOLKIT_VISION_PLUS", "group": "VISION+"},
        {"url": "LINK_HTTP_TOOLKIT_EVEN", "group": "EVENT"},
        {"url": "LINK_HTTP_TOOLKIT_TV_CHANNEL", "group": "TV CHANNEL"},
        {"url": "LINK_HTTP_TOOLKIT_VISION_PLUS", "group": "INDIHOME"},
        {"url": "LINK_HTTP_TOOLKIT_EVEN", "group": "TVRI CHANNEL"},
        {"url": "LINK_HTTP_TOOLKIT_TV_CHANNEL", "group": "EVENT+"},
        {"url": "LINK_HTTP_TOOLKIT_VISION_PLUS", "group": "SPORTS NEW"},
        {"url": "LINK_HTTP_TOOLKIT_EVEN", "group": "OLAHRAGA"},
        {"url": "LINK_HTTP_TOOLKIT_TV_CHANNEL", "group": "DENS"}
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

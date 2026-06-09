from flask import Flask, Response
import requests

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
                raw_lines = response.text.splitlines()
                
                # ---> UBAHAN: Pre-processing untuk menyatukan baris yang terputus <---
                lines = []
                for line in raw_lines:
                    cleaned_line = line.strip()
                    if not cleaned_line:
                        continue
                    
                    # Deteksi apakah baris ini adalah awal tag M3U atau merupakan link streaming
                    if cleaned_line.startswith("#") or cleaned_line.startswith("http") or "://" in cleaned_line:
                        lines.append(line)
                    else:
                        # Jika tidak diawali tanda di atas, berarti ini adalah teks base64/nama channel yang terpotong
                        if lines:
                            lines[-1] += line  # Gabungkan kembali tanpa menghilangkan spasi
                # ---------------------------------------------------------------------
                
                current_extinf = ""
                
                for line in lines:
                    line = line.strip() # Sekarang aman untuk di-strip karena baris sudah digabung utuh
                    if not line:
                        continue
                        
                    if line.startswith("#EXTM3U"):
                        continue
                    
                    # Simpan metadata channel sementara
                    if line.startswith("#EXTINF"):
                        if "group-title=" not in line:
                            line = line.replace("#EXTINF:-1", f'#EXTINF:-1 group-title="{pl["group"]}"')
                        current_extinf = line
                            
                    # Kalau nemu baris URL Streaming
                    elif not line.startswith("#"):
                        stream_url = line # Ini adalah link streamingnya
                        
                        # Cek apakah URL udah pernah direkam
                        if current_extinf and stream_url not in seen_urls:
                            seen_urls.add(stream_url)
                            merged_content += current_extinf + "\n" + stream_url + "\n"
                        
                        # Reset untuk channel berikutnya
                        current_extinf = ""
                        
                    # Handle tag tambahan IPTV (misal: #EXTVLCOPT, #KODIPROP)
                    elif line.startswith("#") and current_extinf:
                        current_extinf += "\n" + line
                        
        except Exception:
            pass 

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

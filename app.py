from flask import Flask, Response, request, abort
import requests
import re
import base64
import time
import unicodedata
from urllib.parse import quote, unquote

app = Flask(__name__)

SOURCE_CACHE = {}
CACHE_TTL = 300 

def fetch_playlist(url):
    now = time.time()
    if url in SOURCE_CACHE and (now - SOURCE_CACHE[url]['time'] < CACHE_TTL):
        return SOURCE_CACHE[url]['data']
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "Accept": "*/*"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            SOURCE_CACHE[url] = {'data': resp.text, 'time': now}
            return resp.text
    except Exception:
        pass
    return None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    playlists = [
        {"url": "https://ayo.maling.pl/Vision/channels.php", "group": "VISION+"},
        {"url": "https://ayomalinggo.blog/maling/malingenak.m3u", "group": "AUTO LIVE 1""},
        {"url": "https://ayomalinggo.blog/maling/sportzfy_proxy.php?type=events", "group": "USA LIVE 01"},
        {"url": "https://ayomalinggo.blog/maling/sportzfy_proxy.php?type=channels", "group": "USA LIVE 02"},
        {"url": "https://malingya.goblogtv.workers.dev/", "group": "LIVE AUTO II"},
        {"url": "https://ayo.maling.pl/thth/1.php", "group": "EVEN+"},
        {"url": "https://enakmalinggo.blog/maling/93.php", "group": "LIVE TV"},
        {"url": "https://ayomalinggo.blog/maling/Nweb.php?action=m3u", "group": "SPORT ARB"},
        {"url": "https://ayomalinggo.blog/maling/exo_playlist.php", "group": "SPORT ARAB"},
        {"url": "http://hometv.biz.id/get.php?username=SIARAN_TRIAL&password=dZhP257HGH&type=m3u_plus&output=m3u8", "group": "TV MALING"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php", "group": "SPORT NEW"},
        {"url": "https://enakmalinggo.blog/maling/logo.php", "group": "OLAHRAGA"},
        {"url": "https://raw.githubusercontent.com/apistech/project/refs/heads/main/IndihomeTV.m3u", "group": "INDIEHOME"},
        {"url": "https://enakmalinggo.blog/maling/dens.php", "group": "DENS"},
        {"url": "https://thth.dasarweddus.workers.dev/", "group": "AUTO 1 SPORT"},
        {"url": "https://ayo.maling.pl/Rak/1.php", "group": "AUTO 2 SPORT"},
        {"url": "https://ayomalinggo.blog/maling/TOKEN/sbs_m3u.php", "group": "WORLD CUP 2026"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/ch.php", "group": "TV CHANNEL"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php", "group": "EVENT"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/tvri.php", "group": "TVRI CHANNEL"},
        {"url": "https://ayomalinggo.blog/maling/tolol/1.php", "group": "SAWIT TV"}
    ]

    merged_content = "#EXTM3U\n"
    
    group_counts = {}
    group_versions = {}
    
    for pl in playlists:
        playlist_text = fetch_playlist(pl["url"])
        if not playlist_text:
            continue
            
        lines = playlist_text.splitlines()
        
        # Buffer untuk nyimpen metadata sebelum ketemu stream URL
        current_extinf = ""
        ext_tags = []
        stream_headers = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#EXTM3U"):
                continue
            
            if line.startswith("#EXTINF"):
                
                # 1. Bersihin koma nyasar
                if line.count(',') > 1:
                    attrs, name = line.rsplit(',', 1)
                    attrs = attrs.replace('",', '" ')
                    attrs = re.sub(r',\s*(?=[a-zA-Z0-9_-]+=)', ' ', attrs)
                    attrs = re.sub(r'^(#EXTINF:[-0-9]+),', r'\1 ', attrs)
                    line = f"{attrs},{name}"
                
                # 2. Proses Nama, Karakter Gaib, dan Duplikasi Grup
                if "," in line:
                    attrs, name = line.rsplit(',', 1)
                    
                    # Basmi Karakter Gaib
                    name = "".join(c for c in name if unicodedata.category(c) not in ['Cc', 'Cf', 'Cn', 'Co', 'Cs'])
                    
                    # Ubah Nama Channel jadi HURUF BESAR
                    name = name.strip().upper()
                    
                    # Ekstrak base group name
                    match_group = re.search(r'group-title="([^"]+)"', attrs)
                    if match_group:
                        base_group_name = match_group.group(1).upper()
                    else:
                        base_group_name = pl["group"].upper()
                    
                    base_group_name = "".join(c for c in base_group_name if unicodedata.category(c) not in ['Cc', 'Cf', 'Cn', 'Co', 'Cs'])
                    
                    group_key = (pl["url"], base_group_name)
                    
                    # Penomoran pakai kurung siku [2], [3], dst
                    if group_key not in group_versions:
                        if base_group_name not in group_counts:
                            group_counts[base_group_name] = 1
                            group_versions[group_key] = base_group_name
                        else:
                            group_counts[base_group_name] += 1
                            group_versions[group_key] = f"{base_group_name} [{group_counts[base_group_name]}]"
                    
                    final_group_name = group_versions[group_key]
                    
                    if match_group:
                        attrs = re.sub(r'group-title="[^"]+"', f'group-title="{final_group_name}"', attrs)
                    else:
                        attrs = re.sub(r'^(#EXTINF:[-0-9]+)\s*', rf'\1 group-title="{final_group_name}" ', attrs)
                        
                    line = f"{attrs},{name}"
                
                # 3. Ekstrak untuk kebutuhan ngecek Base64 
                channel_name_for_check = line.split(",")[-1].strip().lower()
                
                if re.search(r'tvg-logo=["\']data:image/', line, flags=re.IGNORECASE):
                    safe_url = quote(pl["url"])
                    safe_ch = quote(channel_name_for_check)
                    new_logo_url = f"{request.host_url}logo?pl_url={safe_url}&ch={safe_ch}"
                    line = re.sub(r'tvg-logo=["\']data:image/[^"\']+["\']', f'tvg-logo="{new_logo_url}"', line, flags=re.IGNORECASE)

                # Reset buffer buat channel baru ini
                current_extinf = line
                ext_tags = []
                stream_headers = ""
                
            # Nangkap metadata tambahan (kayak #EXTVLCOPT)
            elif line.startswith("#") and current_extinf:
                ext_tags.append(line)
                
            # Nangkap header yang kepisah (kayak |Referer=...)
            elif line.startswith("|") and current_extinf:
                stream_headers += line
                
            # Ini pasti link stream aslinya (http/https/dsb)
            elif not line.startswith("#") and current_extinf:
                stream_url = line 
                
                # Jahit #EXTINF
                merged_content += current_extinf + "\n"
                
                # Jahit tag tambahan (kalau ada)
                if ext_tags:
                    merged_content += "\n".join(ext_tags) + "\n"
                
                # Jahit link stream + headernya jadi SATU BARIS
                merged_content += stream_url + stream_headers + "\n"
                
                # Kosongin buffer biar siap baca channel selanjutnya
                current_extinf = ""
                ext_tags = []
                stream_headers = ""

    return Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')

@app.route('/logo')
def serve_logo():
    pl_url = request.args.get('pl_url')
    channel_name = request.args.get('ch')
    
    if not pl_url or not channel_name:
        return abort(400)
        
    text = fetch_playlist(unquote(pl_url))
    if not text:
        return abort(404)
        
    lines = text.splitlines()
    for line in lines:
        if line.startswith("#EXTINF"):
            current_ch = line.split(",")[-1].strip().lower() if "," in line else line.lower()
            if current_ch == channel_name.lower():
                match = re.search(r'tvg-logo=["\']data:image/([^;]+);base64,([^"\']+)["\']', line, flags=re.IGNORECASE)
                if match:
                    img_format = match.group(1)
                    b64_data = match.group(2)
                    try:
                        img_bytes = base64.b64decode(b64_data)
                        return Response(
                            img_bytes, 
                            mimetype=f'image/{img_format}',
                            headers={'Cache-Control': 'public, max-age=2592000, s-maxage=2592000'}
                        )
                    except Exception:
                        pass
                break
                
    return abort(404)

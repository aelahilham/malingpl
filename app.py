from flask import Flask, Response, request, abort
import requests
import re
import base64
import time
import datetime
import unicodedata
import os
from urllib.parse import quote, unquote
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

SOURCE_CACHE = {}
# Balikin ke 300 (5 menit) biar aman dari amukan blokir Cloudflare provider lu
CACHE_TTL = 300 

def fetch_playlist(url):
    now = time.time()
    if url in SOURCE_CACHE and (now - SOURCE_CACHE[url]['time'] < CACHE_TTL):
        return SOURCE_CACHE[url]['data']
    
    # Deteksi kalau url-nya berupa lokasi file di PC (misal: D:/iptv/tnt.txt)
    if not url.startswith("http"):
        try:
            if os.path.exists(url):
                with open(url, 'r', encoding='utf-8-sig') as f:
                    return f.read()
        except Exception:
            pass
        return None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        if resp.status_code == 200:
            text = resp.text.lstrip('\ufeff') 
            SOURCE_CACHE[url] = {'data': text, 'time': now}
            return text
    except Exception:
        pass
    return None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    playlists = [
        {"url": "https://ayo.maling.pl/Vision/channels.php", "group": "VISION+"},
        {"url": "https://ayomalinggo.blog/maling/malingenak.m3u", "group": "AUTO LIVE 1"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/tvri.php", "group": "TVRI CHANNEL"},
        {"url": "https://malingya.goblogtv.workers.dev/", "group": "LIVE AUTO II"},
        {"url": "https://ayo.maling.pl/thth/1.php", "group": "EVENT+"},
        {"url": "https://enakmalinggo.blog/maling/93.php", "group": "LIVE TV"},
        {"url": "https://ayomalinggo.blog/maling/Nweb.php?action=m3u", "group": "SPORT ARB"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/hasilnya.php", "group": "SPORT NEW"},
        {"url": "http://hometv.biz.id/get.php?username=SIARAN_TRIAL&password=dZhP257HGH&type=m3u_plus&output=m3u8", "group": "TV MALING"},
        {"url": "https://enakmalinggo.blog/maling/logo.php", "group": "OLAHRAGA"},
        {"url": "https://raw.githubusercontent.com/apistech/project/refs/heads/main/IndihomeTV.m3u", "group": "INDIHOME"},
        {"url": "https://enakmalinggo.blog/maling/dens.php", "group": "DENS"},
        {"url": "https://thth.dasarweddus.workers.dev/", "group": "AUTO 1 SPORT"},
        {"url": "https://ayo.maling.pl/Rak/1.php", "group": "AUTO 2 SPORT"},
        {"url": "https://ayomalinggo.blog/maling/TOKEN/sbs_m3u.php", "group": "WORLD CUP 2026"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/ch.php", "group": "TV CHANNEL"},
        {"url": "https://ayomalinggo.blog/maling/XXXX69/event.php", "group": "EVENT"}
        # MASUKIN LINK ATAU LOKASI FILE PLAYLIST BARU LU DI SINI:
        # PENTING: Kalo file lokal, pake garis miring ke depan (/). Contoh:
        # {"url": "D:/folder/playlist_baru.txt", "group": "TNT SPORTS"}
    ]

    merged_content = "#EXTM3U\n"
    
    # Penanda waktu biar lu yakin player lu narik data terbaru, bukan cache
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    merged_content += f'#EXTINF:-1 group-title="SYSTEM LOG", 🟢 UPDATE: {current_time}\nhttp://localhost/status.m3u8\n'
    
    group_counts = {}
    group_versions = {}
    
    for pl in playlists:
        pl_url = pl.get("url", "")
        pl_group = pl.get("group", "TANPA GRUP")
        
        if not pl_url:
            continue
            
        playlist_text = fetch_playlist(pl_url)
        if not playlist_text:
            continue
            
        lines = playlist_text.splitlines()
        current_extinf = ""
        ext_tags = []
        stream_headers = ""
        
        for line in lines:
            try:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#EXTM3U"):
                    continue
                
                if line.startswith("#EXTINF"):
                    
                    if line.count(',') > 1:
                        attrs, name = line.rsplit(',', 1)
                        attrs = attrs.replace('",', '" ')
                        attrs = re.sub(r',\s*(?=[a-zA-Z0-9_-]+=)', ' ', attrs)
                        attrs = re.sub(r'^(#EXTINF:[-0-9]+),', r'\1 ', attrs)
                        line = f"{attrs},{name}"
                    
                    if "," in line:
                        attrs, name = line.rsplit(',', 1)
                        
                        name = "".join(c for c in name if unicodedata.category(c) not in ['Cc', 'Cf', 'Cn', 'Co', 'Cs'])
                        name = name.strip().upper()
                        
                        match_group = re.search(r'group-title="([^"]+)"', attrs)
                        if match_group:
                            base_group_name = match_group.group(1).upper()
                        else:
                            base_group_name = pl_group.upper()
                        
                        base_group_name = "".join(c for c in base_group_name if unicodedata.category(c) not in ['Cc', 'Cf', 'Cn', 'Co', 'Cs'])
                        
                        group_key = (pl_url, base_group_name)
                        
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
                    
                    channel_name_for_check = line.split(",")[-1].strip().lower()
                    if re.search(r'tvg-logo=["\']data:image/', line, flags=re.IGNORECASE):
                        safe_url = quote(pl_url)
                        safe_ch = quote(channel_name_for_check)
                        new_logo_url = f"{request.host_url}logo?pl_url={safe_url}&ch={safe_ch}"
                        line = re.sub(r'tvg-logo=["\']data:image/[^"\']+["\']', f'tvg-logo="{new_logo_url}"', line, flags=re.IGNORECASE)

                    current_extinf = line
                    ext_tags = []
                    stream_headers = ""
                    
                # Pertahankan #KODIPROP dan tag lain
                elif line.startswith("#") and current_extinf:
                    ext_tags.append(line)
                    
                # Pertahankan Header
                elif line.startswith("|") and current_extinf:
                    stream_headers += line
                    
                # Gabungkan dengan rapi
                elif not line.startswith("#") and current_extinf:
                    stream_url = line 
                    
                    merged_content += current_extinf + "\n"
                    if ext_tags:
                        merged_content += "\n".join(ext_tags) + "\n"
                    merged_content += stream_url + stream_headers + "\n"
                    
                    current_extinf = ""
                    ext_tags = []
                    stream_headers = ""
                    
            except Exception:
                pass

    resp = Response(merged_content, mimetype='audio/mpegurl; charset=utf-8')
    # Maksa player buat buang cache
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/logo')
def serve_logo():
    pl_url = request.args.get('pl_url')
    channel_name = request.args.get('ch')
    if not pl_url or not channel_name: return abort(400)
    text = fetch_playlist(unquote(pl_url))
    if not text: return abort(404)
    lines = text.splitlines()
    for line in lines:
        if line.startswith("#EXTINF"):
            current_ch = line.split(",")[-1].strip().lower() if "," in line else line.lower()
            if current_ch == channel_name.lower():
                match = re.search(r'tvg-logo=["\']data:image/([^;]+);base64,([^"\']+)["\']', line, flags=re.IGNORECASE)
                if match:
                    try:
                        return Response(base64.b64decode(match.group(2)), mimetype=f'image/{match.group(1)}', headers={'Cache-Control': 'public, max-age=2592000, s-maxage=2592000'})
                    except Exception: pass
                break
    return abort(404)

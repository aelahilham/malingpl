from flask import Flask, Response, request, abort
import requests
import re
import base64
import time
import unicodedata
import traceback
from urllib.parse import quote, unquote
import urllib3

# Matiin warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

SOURCE_CACHE = {}
# Bikin 0 dulu biar murni tanpa cache sama sekali pas lagi ngetes
CACHE_TTL = 0 

def fetch_playlist(url):
    now = time.time()
    if url in SOURCE_CACHE and (now - SOURCE_CACHE[url]['time'] < CACHE_TTL):
        return SOURCE_CACHE[url]['data']
    
    try:
        headers = {
            # Balik ke User-Agent awal yang terbukti jalan buat FolaPlay
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "Accept": "*/*"
        }
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        if resp.status_code == 200:
            # Buang karakter BOM gaib tanpa maksa ganti encoding
            text = resp.text.lstrip('\ufeff') 
            SOURCE_CACHE[url] = {'data': text, 'time': now}
            return text
        else:
            return f"#EXTINF:-1 group-title=\"DEBUG LOG\", ❌ HTTP ERROR {resp.status_code}: {url}\nhttp://localhost/error.m3u8"
    except Exception as e:
        return f"#EXTINF:-1 group-title=\"DEBUG LOG\", ❌ GAGAL FETCH: {str(e)}\nhttp://localhost/error.m3u8"

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    try:
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
            # ↓↓↓ TARUH LINK M3U TNT SPORTS LU DI BAWAH SINI ↓↓↓
            # {"url": "ISI_LINK_M3U_TNT_LU_DISINI", "group": "TNT SPORTS"}
        ]

        merged_content = "#EXTM3U\n"
        
        group_counts = {}
        group_versions = {}
        
        for pl in playlists:
            playlist_text = fetch_playlist(pl["url"])
            
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
                            
                            name = "".join(c for c in name if unicodedata.category(c) not in ['Cc', 'Cf', 'Cn', 'Co', 'Cs'])
                            name = name.strip().upper()
                            
                            match_group = re.search(r'group-title="([^"]+)"', attrs)
                            if match_group:
                                base_group_name = match_group.group(1).upper()
                            else:
                                base_group_name = pl["group"].upper()
                            
                            base_group_name = "".join(c for c in base_group_name if unicodedata.category(c) not in ['Cc', 'Cf', 'Cn', 'Co', 'Cs'])
                            
                            group_key = (pl["url"], base_group_name)
                            
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
                        
                        # 3. Ekstrak logo Base64 
                        channel_name_for_check = line.split(",")[-1].strip().lower()
                        if re.search(r'tvg-logo=["\']data:image/', line, flags=re.IGNORECASE):
                            safe_url = quote(pl["url"])
                            safe_ch = quote(channel_name_for_check)
                            new_logo_url = f"{request.host_url}logo?pl_url={safe_url}&ch={safe_ch}"
                            line = re.sub(r'tvg-logo=["\']data:image/[^"\']+["\']', f'tvg-logo="{new_logo_url}"', line, flags=re.IGNORECASE)

                        current_extinf = line
                        ext_tags = []
                        stream_headers = ""
                        
                    # Nangkap KODIPROP dan tag referensi lain (Utuh!)
                    elif line.startswith("#") and current_extinf:
                        ext_tags.append(line)
                        
                    # Nangkap header yang kepisah (kayak |Referer=)
                    elif line.startswith("|") and current_extinf:
                        stream_headers += line
                        
                    # Susun URL Video Akhir
                    elif not line.startswith("#") and current_extinf:
                        stream_url = line 
                        
                        merged_content += current_extinf + "\n"
                        if ext_tags:
                            merged_content += "\n".join(ext_tags) + "\n"
                        merged_content += stream_url + stream_headers + "\n"
                        
                        # Reset
                        current_extinf = ""
                        ext_tags = []
                        stream_headers = ""
                        
                except Exception as loop_err:
                    # Kalau ada baris yang bikin error, gak bakal merusak full playlist
                    pass

        # Balikkan hasil dengan header Anti-Cache dan tipe x-mpegURL
        resp = Response(merged_content, mimetype='application/x-mpegURL; charset=utf-8')
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        return resp

    except Exception as e:
        # INI PENTING: Kalau Python beneran Crash, lu bakal dapet list ini di Player TV lu!
        error_msg = traceback.format_exc().replace('\n', ' || ')
        crash_m3u = f"#EXTM3U\n#EXTINF:-1 group-title=\"💥 SCRIPT CRASH\", LOG: {str(e)}\nhttp://localhost/crash.m3u8\n"
        crash_m3u += f"#EXTINF:-1 group-title=\"💥 SCRIPT CRASH\", {error_msg}\nhttp://localhost/crash2.m3u8\n"
        
        resp = Response(crash_m3u, mimetype='application/x-mpegURL; charset=utf-8')
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        return resp

@app.route('/logo')
def serve_logo():
    # ... (Bagian logo tetap sama, tidak disentuh biar aman) ...
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

from flask import Flask, Response, request, abort
import requests
import re
import base64
import time
import datetime
import unicodedata
import traceback
import os
from urllib.parse import quote, unquote
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

SOURCE_CACHE = {}
# Set ke 0 dulu biar lu gampang ngetes tanpa cache
CACHE_TTL = 0 

def fetch_playlist(url):
    now = time.time()
    if url in SOURCE_CACHE and (now - SOURCE_CACHE[url]['time'] < CACHE_TTL):
        return SOURCE_CACHE[url]['data']
    
    # Kalo URL gak diawali http, kita anggap itu file lokal di komputer lu
    if not url.startswith("http"):
        try:
            if os.path.exists(url):
                with open(url, 'r', encoding='utf-8-sig') as f:
                    return f.read()
            else:
                return f'#EXTINF:-1 group-title="DEBUG LOG", ❌ FILE LOKAL GAK KETEMU: {url}\nhttp://localhost/error.m3u8\n'
        except Exception as e:
            return f'#EXTINF:-1 group-title="DEBUG LOG", ❌ ERROR BACA FILE: {e}\nhttp://localhost/error.m3u8\n'

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "Accept": "*/*"
        }
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        if resp.status_code == 200:
            text = resp.text.lstrip('\ufeff') 
            SOURCE_CACHE[url] = {'data': text, 'time': now}
            return text
        else:
            return f'#EXTINF:-1 group-title="DEBUG LOG", ❌ HTTP ERROR {resp.status_code}: {url}\nhttp://localhost/error.m3u8\n'
    except Exception as e:
        return f'#EXTINF:-1 group-title="DEBUG LOG", ❌ GAGAL FETCH KONEKSI: {str(e)}\nhttp://localhost/error.m3u8\n'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_playlist(path):
    try:
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
            # PASTIKAN MASUKIN LINK ATAU PATH FILE TNT LU DI BAWAH SINI!
            # {"url": "C:/folder/sportzfy_proxy.php.txt", "group": "TNT SPORTS"}
        ]

        merged_content = "#EXTM3U\n"
        
        # Indikator di Player biar ketahuan ini hasil script paling baru atau bukan
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        merged_content += f'#EXTINF:-1 group-title="SYSTEM LOG", 🟢 SCRIPT UPDATE: {current_time}\nhttp://localhost/status.m3u8\n'
        
        group_counts = {}
        group_versions = {}
        
        for pl in playlists:
            # Amankan kalau lu lupa nulis "group"
            pl_url = pl.get("url", "")
            pl_group = pl.get("group", "TANPA GRUP")
            
            if not pl_url:
                continue
                
            playlist_text = fetch_playlist(pl_url)
            
            # Kalau ke-blokir Cloudflare atau HTML doang
            if not playlist_text or "#EXTINF" not in playlist_text:
                merged_content += f'#EXTINF:-1 group-title="DEBUG LOG", ❌ DIBLOKIR PROVIDER: {pl_group}\nhttp://localhost/error.m3u8\n'
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
                        
                    elif line.startswith("#") and current_extinf:
                        ext_tags.append(line)
                        
                    elif line.startswith("|") and current_extinf:
                        stream_headers += line
                        
                    elif not line.startswith("#") and current_extinf:
                        stream_url = line 
                        
                        merged_content += current_extinf + "\n"
                        if ext_tags:
                            merged_content += "\n".join(ext_tags) + "\n"
                        merged_content += stream_url + stream_headers + "\n"
                        
                        current_extinf = ""
                        ext_tags = []

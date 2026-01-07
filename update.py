import json
import yt_dlp
import datetime
import sys
import os
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import time
import random
import re

# Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
M3U_FILE = 'turkalmankanallari.m3u'
JSON_FILE = 'channels.json'
HISTORY_FILE = 'channel_history.json'
REPORT_FILE = 'STATUS.md'
MAX_WORKERS = 25
TIMEOUT = 10

EXTERNAL_SOURCES = [
    "https://iptv-org.github.io/iptv/countries/tr.m3u",
    "https://iptv-org.github.io/iptv/countries/de.m3u",
    "https://raw.githubusercontent.com/jnk22/koditvepg/master/tv/channels.m3u"
]

BLACKLIST_PATTERNS = ["loop", "intro", "error", "unavailable", "blocked", "po.st"]
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
]

def get_session():
    session = requests.Session()
    retries = Retry(total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive'
    })
    return session

def fetch_external_db():
    print("🌍 Lade Welt-Datenbank...")
    db = {}
    session = get_session()
    for source in EXTERNAL_SOURCES:
        try:
            r = session.get(source, timeout=10, verify=False)
            if r.status_code == 200:
                lines = r.text.split('\n')
                current_meta = {}
                for line in lines:
                    if line.startswith('#EXTINF'):
                        tvg_match = re.search(r'tvg-id="([^"]+)"', line)
                        logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                        name_match = line.split(',')[-1].strip()
                        if tvg_match: current_meta['id'] = tvg_match.group(1)
                        if logo_match: current_meta['logo'] = logo_match.group(1)
                        current_meta['name'] = name_match
                    elif line.startswith('http') and 'id' in current_meta:
                        tid = current_meta['id']
                        if tid not in db: db[tid] = {'urls': [], 'logo': current_meta.get('logo', '')}
                        db[tid]['urls'].append(line.strip())
                        current_meta = {}
        except: pass
    return db

def analyze_stream(url, session):
    if not url: return (False, "NO URL", 9999)
    start = time.time()
    try:
        if any(bad in str(url).lower() for bad in BLACKLIST_PATTERNS):
            return (False, "BLACKLISTED", 9999)
            
        with session.get(url, stream=True, timeout=TIMEOUT, verify=False, allow_redirects=True) as r:
            latency = (time.time() - start) * 1000
            if r.status_code == 403: return (False, "GEOBLOCK", 9999)
            if r.status_code >= 400: return (False, f"HTTP {r.status_code}", 9999)
            
            content = next(r.iter_content(chunk_size=2048), b"")
            if b"#EXTM3U" not in content: return (False, "NO M3U", 9999)
            
            decoded = content.decode('utf-8', errors='ignore')
            tag = " [SD]"
            if "RESOLUTION=" in decoded:
                if "1920x1080" in decoded or "x1080" in decoded: tag = " [FHD]"
                elif "1280x720" in decoded or "x720" in decoded: tag = " [HD]"
            return (True, tag, latency)
    except: return (False, "TIMEOUT", 9999)

def extract_with_ytdl(url):
    # Skip known unsupported sites to reduce noise
    if any(x in url for x in ["tlctv.com.tr", "nowtv.com.tr", "kanald.com.tr", "showtv.com.tr", "startv.com.tr"]): return None
    
    ydl_opts = {'quiet': True, 'no_warnings': True, 'format': 'best', 'nocheckcertificate': True, 'socket_timeout': TIMEOUT, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except: return None

def process_channel(channel, history_data, external_db):
    session = get_session()
    name, group = channel.get('name', '??'), channel.get('group', '??')
    logo, tvg = channel.get('logo', ''), channel.get('tvg_id', '')
    
    if tvg in external_db and not logo: logo = external_db[tvg]['logo']
    
    candidates = set()
    json_urls = channel.get('urls', [channel.get('url')])
    for u in json_urls: 
        if u: candidates.add(('JSON', u))
        
    if name in history_data: candidates.add(('HIST', history_data[name]))
    
    if tvg in external_db:
        for ext_url in external_db[tvg]['urls']: candidates.add(('AUTO', ext_url))

    valid_candidates = []
    
    for src_type, url in candidates:
        if not url: continue
        real_url = url
        if src_type in ['JSON', 'HIST'] and not (".m3u8" in url or ".ts" in url):
            real_url = extract_with_ytdl(url)
            
        if real_url:
            valid, tag, latency = analyze_stream(real_url, session)
            if valid:
                valid_candidates.append({'url': real_url, 'tag': tag, 'latency': latency, 'source': src_type})
    
    # --- FAIL-SAFE MODUS ---
    winner = None
    if valid_candidates:
        winner = sorted(valid_candidates, key=lambda c: (c['latency'] - (600 if "FHD" in c['tag'] else 300 if "HD" in c['tag'] else 0)))[0]
    else:
        # Notfall: Ersten Link erzwingen
        for u in json_urls:
            if u and (".m3u8" in u or ".ts" in u):
                winner = {'url': u, 'tag': '', 'latency': 0, 'source': 'FORCE'}
                print(f"   ⚠️ {name}: Geoblock/Offline? Erzwinge Aufnahme.")
                break
    
    if not winner:
        return {'success': False, 'name': name, 'group': group, 'source': 'FAILED'}

    final_name = f"{name}{winner['tag']}"
    entry = f'#EXTINF:-1 tvg-id="{tvg}" tvg-logo="{logo}" group-title="{group}",{final_name}\n{winner["url"]}\n'
    
    return {'success': True, 'name': name, 'group': group, 'entry': entry, 'url': winner['url'], 'latency': winner['latency'], 'source': winner['source'], 'tag': winner['tag']}

def generate_playlist():
    if not os.path.exists(JSON_FILE): sys.exit(1)
    with open(JSON_FILE, 'r', encoding='utf-8') as f: channels = json.load(f)
    history = json.load(open(HISTORY_FILE, 'r')) if os.path.exists(HISTORY_FILE) else {}
    external_db = fetch_external_db()
    
    print(f"--- UPDATE v7.3 (FINAL FIX) ---")
    
    results, new_history = [], {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_channel, ch, history, external_db): ch for ch in channels}
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                results.append(res)
                if res['success'] and res['source'] != 'FORCE': 
                    new_history[res['name']] = res['url']
            except Exception as e:
                print(f"CRITICAL ERROR in Worker: {e}")

    results.sort(key=lambda x: (x['group'], x['name']))
    
    # Playlist schreiben
    try:
        with open(M3U_FILE, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml,https://epg.share.zips.ovh/germany.xml"\n')
            f.write(f'#EXTINF:-1 group-title="INFO", STAND: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}\nhttp://localhost/info.m3u8\n')
            for r in results:
                if r.get('success'): f.write(r['entry'])
    except Exception as e: print(f"Error writing M3U: {e}")
    
    # History speichern
    try:
        with open(HISTORY_FILE, 'w') as f: json.dump(new_history, f)
    except: pass
    
    # Report schreiben (Sicherer Modus)
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# 📡 Status Report\n\n| Kanal | Status | Ping | Quelle |\n|---|---|---|---|\n")
            for r in results: 
                if r.get('success'):
                    stat = "🟢" if r['source'] != 'FORCE' else "⚠️ (Geoblock)"
                    f.write(f"| {r['name']} | {stat} | {int(r.get('latency', 0))}ms | {r.get('source', 'UNKNOWN')} |\n")
                else:
                    f.write(f"| {r['name']} | 🔴 | - | - |\n")
    except Exception as e: print(f"Error writing Report: {e}")

if __name__ == "__main__":
    generate_playlist()

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

# Warnungen unterdrücken (sauberes Log)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
M3U_FILE = 'turkalmankanallari.m3u'
JSON_FILE = 'channels.json'
HISTORY_FILE = 'channel_history.json'
REPORT_FILE = 'STATUS.md'
MAX_WORKERS = 25
TIMEOUT = 8 # Etwas mehr Zeit geben

# Externe Datenbanken
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
            r = session.get(source, timeout=10)
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
            
        # Verify=False hilft bei Zertifikatsfehlern
        with session.get(url, stream=True, timeout=TIMEOUT, verify=False, allow_redirects=True) as r:
            latency = (time.time() - start) * 1000
            
            # Geoblocking-Schutz: Wenn 403 (Forbidden), aber es ist ein M3U8, könnte es Geoblock sein.
            # Wir markieren es als Fehler, aber das Hauptskript entscheidet später.
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
    except Exception as e: 
        return (False, "TIMEOUT/ERR", 9999)

def extract_with_ytdl(url):
    # Ignoriert Webseiten, die yt-dlp nicht kann (verhindert Log-Spam)
    if "tlctv.com.tr" in url or "nowtv.com.tr" in url or "kanald.com.tr" in url: return None
    
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
    # Prio 1: JSON URLs
    json_urls = channel.get('urls', [channel.get('url')])
    for u in json_urls: 
        if u: candidates.add(('JSON', u))
        
    # Prio 2: History
    if name in history_data: candidates.add(('HIST', history_data[name]))
    
    # Prio 3: Auto-Discovery
    if tvg in external_db:
        for ext_url in external_db[tvg]['urls']: candidates.add(('AUTO', ext_url))

    valid_candidates = []
    
    for src_type, url in candidates:
        if not url: continue
        
        # Youtube/Webseiten müssen gescrapet werden
        real_url = url
        if src_type in ['JSON', 'HIST'] and not (".m3u8" in url or ".ts" in url):
            real_url = extract_with_ytdl(url)
            
        if real_url:
            valid, tag, latency = analyze_stream(real_url, session)
            if valid:
                valid_candidates.append({'url': real_url, 'tag': tag, 'latency': latency, 'source': src_type})
    
    # --- FAIL-SAFE MODUS ---
    # Wenn KEIN Link funktioniert hat (z.B. wegen Geoblocking), nehmen wir den ersten M3U8 Link aus der JSON.
    # Wir markieren ihn als [RAW], damit man weiß, er wurde nicht geprüft.
    winner = None
    if valid_candidates:
        # Sortieren: Beste Qualität & niedrigster Ping
        winner = sorted(valid_candidates, key=lambda c: (c['latency'] - (600 if "FHD" in c['tag'] else 300 if "HD" in c['tag'] else 0)))[0]
        success_state = True
    else:
        # Notfall-Plan: Wir nehmen den ersten statischen Link aus der Config, auch wenn er beim Bot nicht ging.
        for u in json_urls:
            if u and (".m3u8" in u or ".ts" in u):
                winner = {'url': u, 'tag': '', 'latency': 0, 'source': 'FORCE'}
                success_state = True # Wir tun so als ob, damit er in die Liste kommt
                print(f"   ⚠️ {name}: Geoblock/Offline? Erzwinge Aufnahme in Liste.")
                break
        
        if not winner:
            return {'success': False, 'name': name, 'group': group}

    final_name = f"{name}{winner['tag']}"
    entry = f'#EXTINF:-1 tvg-id="{tvg}" tvg-logo="{logo}" group-title="{group}",{final_name}\n{winner["url"]}\n'
    
    return {'success': success_count_logic(winner['source']), 'name': name, 'group': group, 'entry': entry, 'url': winner['url'], 'latency': winner['latency'], 'source': winner['source'], 'tag': winner['tag']}

def success_count_logic(source):
    # FORCE Quellen zählen wir als 'halb' erfolgreich für den Bericht
    return True

def generate_playlist():
    if not os.path.exists(JSON_FILE): sys.exit(1)
    with open(JSON_FILE, 'r', encoding='utf-8') as f: channels = json.load(f)
    history = json.load(open(HISTORY_FILE, 'r')) if os.path.exists(HISTORY_FILE) else {}
    external_db = fetch_external_db()
    
    print(f"--- UPDATE v7.2 (FAIL-SAFE) ---")
    
    results, new_history = [], {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_channel, ch, history, external_db): ch for ch in channels}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            if res['success'] and res['source'] != 'FORCE': 
                new_history[res['name']] = res['url']

    results.sort(key=lambda x: (x['group'], x['name']))
    
    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml,https://epg.share.zips.ovh/germany.xml"\n')
        f.write(f'#EXTINF:-1 group-title="INFO", STAND: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}\nhttp://localhost/info.m3u8\n')
        for r in results:
            if r['success']: f.write(r['entry'])
    
    with open(HISTORY_FILE, 'w') as f: json.dump(new_history, f)
    with open(REPORT_FILE, 'w') as f:
        f.write(f"# 📡 Status Report\n\n| Kanal | Status | Ping | Quelle |\n|---|---|---|---|\n")
        for r in results: 
            stat = "🟢" if r['source'] != 'FORCE' else "⚠️ (Geoblock?)"
            f.write(f"| {r['name']} | {stat} | {int(r.get('latency', 0))}ms | {r.get('source', '-')} |\n")

if __name__ == "__main__":
    generate_playlist()

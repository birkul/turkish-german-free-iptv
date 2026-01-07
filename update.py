import json
import yt_dlp
import datetime
import sys
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import time
import random
import re

# --- KONFIGURATION ---
M3U_FILE = 'turkalmankanallari.m3u'
JSON_FILE = 'channels.json'
HISTORY_FILE = 'channel_history.json'
REPORT_FILE = 'STATUS.md'
MAX_WORKERS = 25
TIMEOUT = 6

# Externe Datenbanken für Auto-Discovery
EXTERNAL_SOURCES = [
    "https://iptv-org.github.io/iptv/countries/tr.m3u",
    "https://iptv-org.github.io/iptv/countries/de.m3u",
    "https://raw.githubusercontent.com/jnk22/koditvepg/master/tv/channels.m3u"
]

BLACKLIST_PATTERNS = ["loop", "intro", "error", "unavailable", "blocked"]
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
]

def get_session():
    session = requests.Session()
    retries = Retry(total=1, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
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
    if not url: return (False, "NO URL", 9999) # FIX: Crash verhindert
    start = time.time()
    try:
        if any(bad in str(url).lower() for bad in BLACKLIST_PATTERNS):
            return (False, "BLACKLISTED", 9999)
        with session.get(url, stream=True, timeout=TIMEOUT, verify=False, allow_redirects=True) as r:
            latency = (time.time() - start) * 1000
            if r.status_code >= 400: return (False, "HTTP ERR", 9999)
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
    ydl_opts = {'quiet': True, 'no_warnings': True, 'format': 'best', 'nocheckcertificate': True, 'socket_timeout': TIMEOUT, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except: return None

def process_channel(channel, history_data, external_db):
    session = get_session()
    name, group, logo, tvg = channel.get('name', '??'), channel.get('group', '??'), channel.get('logo', ''), channel.get('tvg_id', '')
    if tvg in external_db and not logo: logo = external_db[tvg]['logo']
    
    candidates = set()
    for u in channel.get('urls', [channel.get('url')]): candidates.add(('JSON', u))
    if name in history_data: candidates.add(('HIST', history_data[name]))
    if tvg in external_db:
        for ext_url in external_db[tvg]['urls']: candidates.add(('AUTO', ext_url))

    valid_candidates = []
    for src_type, url in candidates:
        if not url: continue
        real_url = extract_with_ytdl(url) if (src_type in ['JSON', 'HIST'] and ".m3u8" not in url) else url
        v, t, l = analyze_stream(real_url, session)
        if v: valid_candidates.append({'url': real_url, 'tag': t, 'latency': l, 'source': src_type})

    if not valid_candidates: return {'success': False, 'name': name, 'group': group}
    winner = sorted(valid_candidates, key=lambda c: (c['latency'] - (600 if "FHD" in c['tag'] else 300 if "HD" in c['tag'] else 0)))[0]
    entry = f'#EXTINF:-1 tvg-id="{tvg}" tvg-logo="{logo}" group-title="{group}",{name}{winner["tag"]}\n{winner["url"]}\n'
    return {'success': True, 'name': name, 'group': group, 'entry': entry, 'url': winner['url'], 'latency': winner['latency'], 'source': winner['source'], 'tag': winner['tag']}

def generate_playlist():
    if not os.path.exists(JSON_FILE): sys.exit(1)
    with open(JSON_FILE, 'r', encoding='utf-8') as f: channels = json.load(f)
    history = json.load(open(HISTORY_FILE, 'r')) if os.path.exists(HISTORY_FILE) else {}
    external_db = fetch_external_db()
    
    results, new_history = [], {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_channel, ch, history, external_db): ch for ch in channels}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            if res['success']: new_history[res['name']] = res['url']

    results.sort(key=lambda x: (x['group'], x['name']))
    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml,https://epg.share.zips.ovh/germany.xml"\n')
        f.write(f'#EXTINF:-1 group-title="INFO", STAND: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}\nhttp://localhost/info.m3u8\n')
        for r in results:
            if r['success']: f.write(r['entry'])
    
    with open(HISTORY_FILE, 'w') as f: json.dump(new_history, f)
    with open(REPORT_FILE, 'w') as f:
        f.write(f"# 📡 Status Report\n\n🟢 Online: {len([r for r in results if r['success']])} | 🔴 Offline: {len([r for r in results if not r['success']])}\n\n| Kanal | Status | Ping |\n|---|---|---|\n")
        for r in results: f.write(f"| {r['name']} | {'🟢' if r['success'] else '🔴'} | {int(r.get('latency', 0)) if r['success'] else '-'}ms |\n")

if __name__ == "__main__":
    generate_playlist()

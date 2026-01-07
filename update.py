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
REPO_NAME = "turkish-german-free-iptv"
M3U_FILE = 'turkalmankanallari.m3u'
JSON_FILE = 'channels.json'
HISTORY_FILE = 'channel_history.json'
REPORT_FILE = 'STATUS.md'
MAX_WORKERS = 25
TIMEOUT = 6

# Externe Datenbanken für Auto-Discovery & Metadaten
EXTERNAL_SOURCES = [
    "https://iptv-org.github.io/iptv/countries/tr.m3u",
    "https://iptv-org.github.io/iptv/countries/de.m3u",
    "https://raw.githubusercontent.com/jnk22/koditvepg/master/tv/channels.m3u"
]

# Blacklist (Links die wir nie wollen)
BLACKLIST_PATTERNS = [
    "loop", "intro", "error", "unavailable", "blocked"
]

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
        'Origin': 'https://www.youtube.com',
        'Connection': 'keep-alive'
    })
    return session

def fetch_external_db():
    """Lädt externe Listen für Links UND Metadaten (Logos, EPG)."""
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
                        # Extrahiere ID, Logo und Name
                        tvg_match = re.search(r'tvg-id="([^"]+)"', line)
                        logo_match = re.search(r'tvg-logo="([^"]+)"', line)
                        name_match = line.split(',')[-1].strip()
                        
                        if tvg_match: current_meta['id'] = tvg_match.group(1)
                        if logo_match: current_meta['logo'] = logo_match.group(1)
                        current_meta['name'] = name_match
                        
                    elif line.startswith('http') and 'id' in current_meta:
                        tvg_id = current_meta['id']
                        if tvg_id not in db:
                            db[tvg_id] = {'urls': [], 'logo': current_meta.get('logo', '')}
                        db[tvg_id]['urls'].append(line.strip())
                        # Logo Update falls in DB vorhanden
                        if not db[tvg_id]['logo'] and 'logo' in current_meta:
                            db[tvg_id]['logo'] = current_meta['logo']
                        current_meta = {} # Reset
        except Exception as e:
            print(f"   ⚠️ Fehler bei Quelle {source}: {e}")
            
    print(f"   -> {len(db)} externe Kanäle indiziert.")
    return db

def analyze_stream(url, session):
    start = time.time()
    try:
        # Blacklist Check
        if any(bad in url.lower() for bad in BLACKLIST_PATTERNS):
            return (False, "BLACKLISTED", 9999)

        with session.get(url, stream=True, timeout=TIMEOUT, verify=False, allow_redirects=True) as r:
            latency = (time.time() - start) * 1000
            if r.status_code >= 400: return (False, "HTTP ERR", 9999)
            
            content = next(r.iter_content(chunk_size=2048), b"")
            if b"#EXTM3U" not in content: return (False, "NO M3U", 9999)

            decoded = content.decode('utf-8', errors='ignore')
            tag = "[SD]"
            if "RESOLUTION=" in decoded:
                if "1920x1080" in decoded or "x1080" in decoded: tag = " [FHD]"
                elif "1280x720" in decoded or "x720" in decoded: tag = " [HD]"
            
            return (True, tag, latency)
    except:
        return (False, "TIMEOUT", 9999)

def extract_with_ytdl(url):
    ydl_opts = {
        'quiet': True, 'no_warnings': True, 'format': 'best',
        'nocheckcertificate': True, 'socket_timeout': TIMEOUT, 'extract_flat': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except:
        return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        try: with open(HISTORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {}

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f: json.dump(history, f, indent=2)

def process_channel(channel, history_data, external_db):
    session = get_session()
    name = channel.get('name', 'Unbekannt')
    group = channel.get('group', 'Ungrouped')
    logo = channel.get('logo', '')
    tvg = channel.get('tvg_id', '')
    
    # --- INTELLIGENZ: Metadaten Anreicherung ---
    # Wenn wir kein Logo oder EPG haben, schauen wir in der Welt-DB nach
    if tvg and tvg in external_db:
        ext_data = external_db[tvg]
        if not logo and ext_data['logo']:
            logo = ext_data['logo'] # Logo geklaut!
            print(f"   ✨ Logo für {name} automatisch gefunden.")

    # URLs sammeln
    candidates = set()
    json_urls = channel.get('urls', [])
    if not json_urls and 'url' in channel: json_urls = [channel['url']]
    
    for u in json_urls: candidates.add(('JSON', u))
    if name in history_data: candidates.add(('HIST', history_data[name]))
    
    # Auto-Discovery Links hinzufügen
    if tvg and tvg in external_db:
        for ext_url in external_db[tvg]['urls']:
            candidates.add(('AUTO', ext_url))

    valid_candidates = []
    
    # Das Rennen
    for src_type, url in candidates:
        if not url: continue
        real_url = url
        if src_type in ['JSON', 'HIST'] and not (".m3u8" in url or ".ts" in url):
            real_url = extract_with_ytdl(url)
            
        if real_url:
            valid, tag, latency = analyze_stream(real_url, session)
            if valid:
                valid_candidates.append({
                    'url': real_url, 'tag': tag, 'latency': latency, 'source': src_type
                })

    if not valid_candidates:
        return {'success': False, 'name': name, 'group': group, 'msg': "Alle Quellen tot"}

    # Gewinner ermitteln
    def sort_key(c):
        score = c['latency']
        if "[FHD]" in c['tag']: score -= 600
        elif "[HD]" in c['tag']: score -= 300
        if c['source'] == 'JSON': score -= 100
        return score

    winner = sorted(valid_candidates, key=sort_key)[0]
    
    final_name = f"{name}{winner['tag']}"
    entry = f'#EXTINF:-1 tvg-id="{tvg}" tvg-logo="{logo}" group-title="{group}",{final_name}\n{winner["url"]}\n'
    
    return {
        'success': True,
        'name': name,
        'group': group,
        'entry': entry,
        'url': winner['url'],
        'latency': winner['latency'],
        'source': winner['source'],
        'tag': winner['tag']
    }

def generate_report(results, duration):
    """Erstellt eine schöne STATUS.md für GitHub."""
    total = len(results)
    online = len([r for r in results if r['success']])
    
    md = f"# 📡 IPTV Status Report\n\n"
    md += f"**Letztes Update:** {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    md += f"**Statistik:**\n"
    md += f"- 🟢 Online: **{online}**\n"
    md += f"- 🔴 Offline: **{total - online}**\n"
    md += f"- ⏱️ Dauer: **{duration:.2f}s**\n\n"
    
    md += "| Kanal | Status | Qualität | Ping | Quelle | Gruppe |\n"
    md += "|---|---|---|---|---|---|\n"
    
    for r in results:
        if r['success']:
            status = "🟢"
            ping = f"{int(r['latency'])}ms"
            src = r['source']
            tag = r['tag'].strip() or "SD"
        else:
            status = "🔴"
            ping = "-"
            src = "-"
            tag = "-"
            
        md += f"| {r['name']} | {status} | {tag} | {ping} | {src} | {r['group']} |\n"
        
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(md)

def generate_playlist():
    start_time = time.time()
    
    if not os.path.exists(JSON_FILE): sys.exit(1)
    with open(JSON_FILE, 'r', encoding='utf-8') as f: channels = json.load(f)
    
    history = load_history()
    external_db = fetch_external_db()
    new_history = {}
    
    print(f"--- GENIUS UPDATE v7.0 ({len(channels)} Kanäle) ---")

    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_channel, ch, history, external_db): ch for ch in channels}
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            
            if res['success']:
                new_history[res['name']] = res['url']
                print(f"✅ {res['name']} ({int(res['latency'])}ms) [{res['source']}]")
            else:
                print(f"❌ {res['name']}")

    # Sortieren
    results.sort(key=lambda x: (x['group'], x['name']))

    # M3U Schreiben
    current_date = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml,https://epg.share.zips.ovh/germany.xml"\n')
        f.write(f'#EXTINF:-1 group-title="INFO", UPDATED: {current_date}\nhttp://localhost/info.m3u8\n')
        
        for res in results:
            if res['success']:
                f.write(res['entry'])

    save_history(new_history)
    duration = time.time() - start_time
    generate_report(results, duration)
    
    print(f"\n--- FERTIG ({duration:.2f}s) ---")
    print(f"Report gespeichert in {REPORT_FILE}")

if __name__ == "__main__":
    generate_playlist()

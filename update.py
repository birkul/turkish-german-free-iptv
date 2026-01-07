import json
import yt_dlp
import datetime
import sys
import os
import requests
import concurrent.futures
import time
import random


M3U_FILE = 'turkalmankanallari.m3u'
JSON_FILE = 'channels.json'
MAX_WORKERS = 20  
TIMEOUT = 5       


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'tr-TR,tr;q=0.9,de-DE;q=0.8,en-US;q=0.7,en;q=0.6',
        'Referer': 'https://www.google.com/'
    }

def check_direct_stream(url):
    """Prüft blitzschnell, ob ein m3u8 Link erreichbar ist."""
    try:
        r = requests.head(url, timeout=TIMEOUT, headers=get_headers(), allow_redirects=True)
        return r.status_code < 400
    except:
        return False

def extract_with_ytdl(url):
    """Holt Stream aus YouTube oder Webseiten."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'nocheckcertificate': True,
        'http_headers': get_headers(),
        'socket_timeout': TIMEOUT
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return info['url']
    except:
        return None

def process_channel(channel):
    """Verarbeitet EINEN Kanal (wird parallel ausgeführt)."""
    name = channel.get('name', 'Unbekannt')
    group = channel.get('group', 'Ungrouped')
    logo = channel.get('logo', '')
    tvg = channel.get('tvg_id', '')
    
    
    urls = channel.get('urls', [])
    if not urls and 'url' in channel:
        urls = [channel['url']]

    found_stream = None
    
    
    for url in urls:
        if not url: continue
        
        
        if ".m3u8" in url or ".ts" in url:
            if check_direct_stream(url):
                found_stream = url
                break
        
        
        else:
            stream = extract_with_ytdl(url)
            if stream:
                found_stream = stream
                break
    
    if found_stream:
        
        entry = f'#EXTINF:-1 tvg-id="{tvg}" tvg-logo="{logo}" group-title="{group}",{name}\n{found_stream}\n'
        return (True, name, entry)
    else:
        
        return (False, name, None)

def generate_playlist():
    start_time = time.time()
    print(f"--- TURBO-UPDATE GESTARTET ({MAX_WORKERS} Threads) ---")
    
    if not os.path.exists(JSON_FILE):
        print(f"FEHLER: {JSON_FILE} fehlt!")
        sys.exit(1)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        channels = json.load(f)

    
    m3u_content = '#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml,https://epg.share.zips.ovh/germany.xml"\n'
    update_date = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    m3u_content += f'#EXTINF:-1 group-title="INFO", LEZTES UPDATE: {update_date}\nhttp://localhost/dummy.m3u8\n'

    results = []
    
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        future_to_channel = {executor.submit(process_channel, ch): ch for ch in channels}
        
        
        for future in concurrent.futures.as_completed(future_to_channel):
            success, name, entry = future.result()
            if success:
                results.append(entry)
                print(f"✅ [OK] {name}")
            else:
                print(f"❌ [OFFLINE] {name}")




    for line in results:
        m3u_content += line

    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    duration = time.time() - start_time
    print(f"\n--- BERICHT ---")
    print(f"Zeit benötigt: {round(duration, 2)} Sekunden")
    print(f"Kanäle Online: {len(results)} von {len(channels)}")
    print(f"Datei gespeichert: {M3U_FILE}")

if __name__ == "__main__":
    generate_playlist()

import json
import yt_dlp
import datetime
import sys
import os
import requests

# --- KONFIGURATION ---
M3U_FILE = 'turkalmankanallari.m3u'
JSON_FILE = 'channels.json'


COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6',
    'Referer': 'https://www.google.com/'
}

def is_link_working(url):
    """Prüft kurz, ob der Link überhaupt erreichbar ist (Status 200)."""
    if not url: return False
    if "youtube.com" in url: return True 
    try:
        r = requests.head(url, timeout=5, headers=COMMON_HEADERS)
        return r.status_code < 400
    except:
        return False

def extract_with_ytdl(url):
    """Der Kern-Trickser: Versucht alles aus einer URL rauszuholen."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'nocheckcertificate': True,
        'http_headers': COMMON_HEADERS
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return info['url']
    except:
        return None

def get_best_stream(url_list):
    """Geht alle URLs für einen Sender durch, bis eine funktioniert."""
    for url in url_list:
        print(f"      -> Teste Quelle: {url[:50]}...")
        
        # 1. IF: Ist es ein direkter Stream?
        if any(ext in url for ext in [".m3u8", ".ts", ".mpd"]):
            if is_link_working(url):
                return url
        
        # 2. IF: Ist es YouTube oder eine Webseite?
        scraped = extract_with_ytdl(url)
        if scraped:
            return scraped
            
    return None

def generate_playlist():
    if not os.path.exists(JSON_FILE):
        print("Kritischer Fehler: JSON Datei fehlt!")
        sys.exit(1)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        channels = json.load(f)

    m3u_content = '#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml,https://epg.share.zips.ovh/germany.xml"\n'
    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    m3u_content += f'#EXTINF:-1 group-title="INFO", --- STAND: {update_time} ---\nhttp://localhost/dummy.m3u8\n'

    success_count = 0
    for ch in channels:
        name = ch.get('name', 'Unbekannt')
        group = ch.get('group', 'All')
        logo = ch.get('logo', '')
        tvg = ch.get('tvg_id', '')
        
        urls = ch.get('urls', [ch.get('url')]) 

        print(f"Verarbeite: {name}...")
        best_link = get_best_stream(urls)

        if best_link:
            m3u_content += f'#EXTINF:-1 tvg-id="{tvg}" tvg-logo="{logo}" group-title="{group}",{name}\n{best_link}\n'
            success_count += 1
        else:
            print(f"   !!! ALLE QUELLEN OFFLINE für {name}")

    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    print(f"\nGigantischer Trickser fertig: {success_count} Kanäle sind scharf geschaltet!")

if __name__ == "__main__":
    generate_playlist()

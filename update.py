import json
import yt_dlp
import datetime
import sys
import os


M3U_FILE = 'turkalmankanallari.m3u'
JSON_FILE = 'channels.json'

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

def get_stream_url(web_url):
    
    if ".m3u8" in web_url or ".ts" in web_url:
        return web_url
        
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(web_url, download=False)
            return info.get('url')
    except Exception:
        return None

def generate_playlist():
    print(f"--- Starte Update für {M3U_FILE} ---")
    
   
    if not os.path.exists(JSON_FILE):
        print(f"FEHLER: {JSON_FILE} nicht gefunden!")
        sys.exit(1)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        channels = json.load(f)

    
    m3u_content = '#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml,https://epg.share.zips.ovh/germany.xml"\n'
    
    
    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    m3u_content += f'#EXTINF:-1 group-title="INFO" tvg-logo="", UPDATED: {update_time}\n'
    m3u_content += "http://localhost/dummy.m3u8\n"

    count = 0

    
    for channel in channels:
        name = channel.get('name', 'Unbekannt')
        group = channel.get('group', 'Ungrouped')
        logo = channel.get('logo', '')
        tvg_id = channel.get('tvg_id', '')
        web_url = channel.get('url', '')
        
        print(f"Prüfe: {name} ({group})...")
        
        stream_url = get_stream_url(web_url)

        if stream_url:
            
            m3u_content += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n'
            m3u_content += f"{stream_url}\n"
            count += 1
        else:
            print(f"   -> FEHLER: Kein Stream für {name}")

    
    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"\nERFOLG: {count} Kanäle gespeichert in {M3U_FILE}.")

if __name__ == "__main__":
    generate_playlist()

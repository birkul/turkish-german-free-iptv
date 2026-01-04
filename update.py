import json
import yt_dlp
import datetime
import sys
import re
import os


M3U_FILE = 'turk_kanallari.m3u'
JSON_FILE = 'channels.json'

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

def load_existing_links():
    """Liest die bestehende M3U Datei und speichert Links, falls vorhanden."""
    existing_links = {}
    if not os.path.exists(M3U_FILE):
        return existing_links

    try:
        with open(M3U_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            entries = re.findall(r'#EXTINF:.*?,(.*?)\n(http[^\n]+)', content)
            for name, link in entries:
                existing_links[name.strip()] = link.strip()
    except Exception as e:
        print(f"Warnung: Konnte alte M3U nicht lesen: {e}")
    
    return existing_links

def get_stream_url(web_url):
    """Versucht neuen Link zu holen. Gibt None zurück, wenn es fehlschlägt."""
    
    if ".m3u8" in web_url:
        return web_url
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(web_url, download=False)
            return info.get('url')
    except Exception:
        return None

def generate_playlist():
    print("--- Starte Smart-Update ---")
    
    
    old_links = load_existing_links()
    print(f"Bereits bekannte Kanäle in der alten Liste: {len(old_links)}")

    
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except FileNotFoundError:
        print("Fehler: channels.json fehlt!")
        sys.exit(1)

    
    m3u_content = "#EXTM3U\n"
    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    m3u_content += f'#EXTINF:-1 group-title="INFO" tvg-logo="", UPDATED: {update_time}\n'
    m3u_content += "http://localhost/dummy.m3u8\n"

    success_count = 0
    kept_count = 0

    for channel in channels:
        name = channel['name']
        group = channel['group']
        web_url = channel['url']
        
        print(f"Prüfe: {name} ...")
        
        
        new_stream_url = get_stream_url(web_url)

        final_url = None

        if new_stream_url:
            print(f"   -> Neuer Link gefunden!")
            final_url = new_stream_url
            success_count += 1
        else:
            
            if name in old_links:
                print(f"   -> Update fehlgeschlagen, nutze ALTEN Link.")
                final_url = old_links[name]
                kept_count += 1
            else:
                print(f"   -> FEHLER: Kein Link gefunden und kein alter Link vorhanden.")

        
        if final_url:
            m3u_content += f'#EXTINF:-1 group-title="{group}" tvg-name="{name}", {name}\n'
            m3u_content += f"{final_url}\n"


    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"\nFertig! {success_count} neu geholt, {kept_count} aus Backup behalten.")

if __name__ == "__main__":
    generate_playlist()

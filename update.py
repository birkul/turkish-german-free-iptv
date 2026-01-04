import json
import yt_dlp
import datetime
import sys

# Downloader ayarlari (Browser simulasyonu)
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'referer': 'https://www.google.com/'
}

def get_stream_url(web_url):
    """Holt die echte m3u8 Adresse von der Webseite."""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # bilgileri bul
            info = ydl.extract_info(web_url, download=False)
            return info.get('url')
    except Exception as e:
        # hatalari görmezden gel, damit das Skript nicht abstuerzt
        return None

def generate_playlist():
    print("--- Starte Update der Kanalliste ---")
    
    # JSON Listeyi tara
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except FileNotFoundError:
        print("Fehler: channels.json nicht gefunden!")
        sys.exit(1)

    # M3U Header yaz
    m3u_content = "#EXTM3U\n"
    # Listenin nezaman güncellendigi hakkindaki tarih
    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    m3u_content += f'#EXTINF:-1 group-title="INFO" tvg-logo="", UPDATED: {update_time}\n'
    m3u_content += "http://localhost/dummy.m3u8\n"

    success_count = 0

    for channel in channels:
        name = channel['name']
        group = channel['group']
        web_url = channel['url']

        print(f"Bearbeite: {name}...")
        
        # Link al
        stream_url = get_stream_url(web_url)

        if stream_url:
            # M3U satiri
            # tvg-name logo icin önemli
            m3u_content += f'#EXTINF:-1 group-title="{group}" tvg-name="{name}", {name}\n'
            m3u_content += f"{stream_url}\n"
            success_count += 1
        else:
            print(f"  -> Kein Stream gefunden fuer {name}")

    # kayit et
    with open('turk_kanallari.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"\nFertig! {success_count} Kanäle gefunden und gespeichert.")

if __name__ == "__main__":
    generate_playlist()

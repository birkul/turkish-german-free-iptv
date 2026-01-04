import json
import yt_dlp
import datetime
import sys
import re
import os

M3U_FILE = 'turk_kanallari.m3u'
JSON_FILE = 'channels.json'

ydl_opts = {
    'quiet': True, 'no_warnings': True, 'format': 'best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

def load_existing_links():
    existing_links = {}
    if os.path.exists(M3U_FILE):
        try:
            with open(M3U_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                entries = re.findall(r'#EXTINF:.*?,(.*?)\n(http[^\n]+)', content)
                for name, link in entries:
                    existing_links[name.strip()] = link.strip()
        except: pass
    return existing_links

def get_stream_url(web_url):
    
    if any(x in web_url for x in ['.m3u8', '.mpd', '.ts']):
        return web_url
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(web_url, download=False)
            return info.get('url')
    except:
        return None

def generate_playlist():
    old_links = load_existing_links()
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except:
        sys.exit(1)

   
    m3u_content = '#EXTM3U x-tvg-url="https://epg.tvcdn.net/guide/tr-guide.xml"\n'
    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    m3u_content += f'#EXTINF:-1 group-title="INFO", --- UPDATED: {update_time} ---\nhttp://localhost/dummy.m3u8\n'

    for ch in channels:
        name = ch['name']
        group = ch.get('group', 'Genel')
        logo = ch.get('logo', '')
        tvg_id = ch.get('tvg_id', '')
        url = ch['url']

        print(f"Update: {name}")
        new_url = get_stream_url(url)
        final_url = new_url if new_url else old_links.get(name)

        if final_url:
            
            line = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n{final_url}\n'
            m3u_content += line

    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

if __name__ == "__main__":
    generate_playlist()

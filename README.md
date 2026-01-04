# 📺 Turk-free-IPTV

![Status](https://img.shields.io/github/actions/workflow/status/toleranta/turk-iptv-auto/main.yml?label=Auto-Update&style=flat-square)

---

## 🇹🇷 Türkçe: Otomatik Güncellenen Türk Kanalları

Bu proje, **Türkçe Ulusal, Haber, Spor, Belgesel ve Çocuk kanallarını** içeren, her 6 saatte bir otomatik olarak güncellenen bir **M3U IPTV** listesidir. 

Liste **Github Actions** sayesinde sürekli canlı tutulur. Eğer bir yayın linki değişirse, bot bunu algılar ve günceller. Logolar ve EPG (Yayın Akışı) desteği mevcuttur.

### 🔗 Kurulum (IBOplayer, TiviMate, VLC vb.)

IPTV oynatıcınıza aşağıdaki linki eklemeniz yeterlidir. Bu link **asla değişmez**, ancak içindeki kanallar her gün güncellenir.

**M3U Linki:**
https://raw.githubusercontent.com/DEIN_BENUTZERNAME/turk-iptv-auto/main/turk_kanallari.m3u


**EPG (Yayın Akışı) Linki:**
https://epg.tvcdn.net/guide/tr-guide.xml

### ✨ Özellikler
* **Otomatik Güncelleme:** Her 6 saatte bir linkler kontrol edilir.
* **Akıllı Sistem:** Eğer bir kanalın yeni linki bulunamazsa, çalışan eski link korunur.
* **Kategoriler:** Ulusal, Haber, Spor, Çocuk, Belgesel, Dini, Müzik.
* **Görsel Zenginlik:** Kanal logoları dahildir.

---

## 🇩🇪 Deutsch: Automatische Türkische IPTV Liste

Dies ist eine **selbst-aktualisierende M3U-Playlist** für türkische Free-TV Sender. Das Projekt nutzt ein Python-Skript und GitHub Actions, um alle 6 Stunden nach funktionierenden Stream-Links zu suchen.

Ideal für Apps wie **IBOplayer, TiviMate, Televizo oder VLC**.

### 🔗 Installation

Füge einfach diesen Link in deinen Player ein. Der Link bleibt statisch, aber der Inhalt (die Stream-Tokens) wird im Hintergrund aktualisiert.

**M3U Playlist URL:**
https://raw.githubusercontent.com/DEIN_BENUTZERNAME/turk-iptv-auto/main/turk_kanallari.m3u


**EPG URL (TV Guide):**
https://epg.tvcdn.net/guide/tr-guide.xml


### ✨ Features
* **Auto-Update:** Läuft 4x täglich vollautomatisch.
* **Smart-Fallback:** Wenn ein Sender offline ist, behält das Skript den letzten funktionierenden Link.
* **Kategorisiert:** Ordnerstruktur für Nachrichten, Sport, Kinder, etc.
* **Vollständig:** Inklusive Sender-Logos und TV-Guide IDs.

---

## 🇬🇧 English: Automated Turkish IPTV List

An **auto-updating M3U playlist** for free-to-air Turkish TV channels. Powered by Python and GitHub Actions, this list refreshes every 6 hours to ensure stream links remain active.

Compatible with all major IPTV players like **TiviMate, IBOplayer, VLC, Kodi**, etc.

### 🔗 How to use

Add the following permanent link to your player. You do not need to update the link manually; the content refreshes automatically.

**M3U Playlist URL:**
https://raw.githubusercontent.com/DEIN_BENUTZERNAME/turk-iptv-auto/main/turk_kanallari.m3u


**EPG URL (Electronic Program Guide):**
https://epg.tvcdn.net/guide/tr-guide.xml


### ✨ Features
* **Automated:** Scrapes fresh links every 6 hours.
* **Reliable:** Includes "Smart Fallback" to keep old links if scraping fails.
* **Organized:** Grouped by National, News, Sports, Kids, etc.
* **Rich Metadata:** Includes channel logos and EPG IDs.

---

### ⚠️ Legal Disclaimer / Yasal Uyari / Rechtlicher Hinweis
* **TR:** Bu listede sadece **şifresiz (Free-to-Air)** ve halka açık yayın yapan kanallar bulunur. Telif hakkı içeren ücretli platformlar (Exxen, BeinSports şifreli kanallar vb.) bulunmaz.
* **DE:** Diese Liste enthält ausschließlich **frei empfangbare (Free-to-Air)** Sender. Keine Pay-TV Inhalte.
* **EN:** This list contains only **Free-to-Air (FTA)** channels publicly available on the internet. No paid/encrypted content included.

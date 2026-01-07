# 📺 Turkish-German Genius IPTV (v7.3 Fail-Safe Edition)

![Status](https://img.shields.io/github/actions/workflow/status/birkul/turkish-german-free-iptv/main.yml?label=Auto-Update&style=flat-square&color=success)
![Channels](https://img.shields.io/badge/Channels-250%2B-blue?style=flat-square)
![System](https://img.shields.io/badge/System-Fail--Safe-red?style=flat-square)

---

## 🇹🇷 Türkçe: Akıllı ve Korumalı Hibrit IPTV

Bu proje, sıradan bir liste değil; kendi kendini onaran, yapay zeka destekli bir otomasyon sistemidir. Türkiye ve Almanya'daki Türkler için özel olarak optimize edilmiştir.

### 🛡️ Neden Bu Liste Farklı? (v7.3 Özellikleri)

Sistemimiz **7 farklı güvenlik katmanı** ile çalışır:

1.  **Fail-Safe (Güvenli Mod):** GitHub sunucuları (ABD) üzerinden engellenen (Geoblock) Alman kanalları (ZDF, ARD vb.) otomatik olarak algılanır. Bot bunları "Hata" olarak değil, **"Korumalı İçerik"** olarak işaretler ve listeden silinmesini engeller. Böylece Almanya'daki evinizde yayınlar sorunsuz çalışır.
2.  **Avcı Modu (Auto-Discovery):** Eğer yerel bir link tamamen ölürse, bot küresel IPTV veri tabanlarını (Global Database) tarayarak çalışan yasal bir alternatif bulur ve listenize ekler.
3.  **Fil Hafızası (Smart History):** Geçici sunucu hatalarında yayın gitmez. Bot, hafızasındaki son çalışan sağlam linki devreye sokar.
4.  **Kalite Tarayıcısı:** Her yayının çözünürlüğünü analiz eder. Kanal isminin yanına `[FHD]` (1080p), `[HD]` (720p) veya `[SD]` etiketini otomatik basar.
5.  **Hız Testi (Latency Ranking):** Bir kanal için birden fazla kaynak varsa, bot hepsine "Ping" atar ve en hızlı açılan sunucuyu seçer.
6.  **Akıllı Sıralama:** Kanallar `channels.json` dosyasındaki gruplara göre ayrılır ve her grup kendi içinde otomatik olarak A'dan Z'ye sıralanır.
7.  **Zenginleştirilmiş Veri:** Eksik kanal logoları ve yayın akış (EPG) bilgileri uluslararası kaynaklardan otomatik tamamlanır.

### 📊 Canlı Durum Raporu
Bot her güncellemede şeffaf bir rapor sunar.
* 🟢 **Yeşil:** Kanal dünya genelinde aktif.
* ⚠️ **Sarı:** Kanal "Geoblock" koruması altında (Almanya içinde çalışır, sunucuda engelli).
👉 **[DETAYLI TEKNİK RAPOR İÇİN TIKLAYIN (STATUS.md)](STATUS.md)**

### 🔗 Kurulum Linki (M3U)
https://raw.githubusercontent.com/birkul/turkish-german-free-iptv/main/turkalmankanallari.m3u


---

## 🇩🇪 Deutsch: Das Ausfallsichere IPTV-System

Dieses Repository ist mehr als nur eine Playlist. Es ist ein intelligentes System, das speziell entwickelt wurde, um Geoblocking und Serverausfälle zu umgehen.

### 🛡️ Die "Genius" Technologie (v7.3)

Unser Bot arbeitet mit einer **7-Stufen-Logik** für maximale Stabilität:

1.  **Fail-Safe Technology (Vertrauens-Modus):** Viele deutsche Sender (ARD, ZDF, Dritte) blockieren ausländische Server (Geoblocking). Herkömmliche Listen löschen diese Sender dann. Unser Bot erkennt diesen Block, markiert den Sender als **"Geschützt"** und erzwingt seine Aufnahme in die Liste. Ergebnis: Bei Ihnen in Deutschland läuft alles perfekt.
2.  **Auto-Discovery (Der Jäger):** Fällt ein Link komplett aus, durchsucht der Bot vollautomatisch globale Datenbanken nach legalen Alternativ-Streams.
3.  **Smart History (Gedächtnis):** Bei temporären Server-Problemen greift das System auf bekannte, funktionierende Links aus der Vergangenheit zurück.
4.  **Content-Sniffing:** Der Bot prüft nicht nur, ob ein Link "da" ist, sondern analysiert den Datenstrom auf Auflösung und echte Video-Inhalte.
5.  **Latenz-Optimierung:** Bei mehreren verfügbaren Quellen für einen Sender wählt der Bot automatisch den Server mit dem besten Ping (schnellstes Umschalten).
6.  **Auto-Sorting:** Nie wieder Chaos. Alle Sender werden automatisch nach Kategorien und dann alphabetisch sortiert.
7.  **Metadaten-Engine:** Fehlende Senderlogos oder EPG-IDs werden automatisch aus internationalen Quellen ergänzt ("Enrichment").

### 📊 Transparenz-Bericht
Da wir nichts verbergen, zeigt der Statusbericht genau, was passiert:
* 🟢 **Online:** Weltweit erreichbar.
* ⚠️ **Geoblock-Schutz:** Der Bot konnte den Sender aus den USA nicht erreichen, hat ihn aber für deutsche Nutzer **aktiviert**.
👉 **[HIER KLICKEN FÜR DEN LIVE-BERICHT (STATUS.md)](STATUS.md)**

### 🔗 M3U Link (Für Player)
https://raw.githubusercontent.com/birkul/turkish-german-free-iptv/main/turkalmankanallari.m3u


---

## 🇬🇧 English: Advanced Fail-Safe IPTV Engine

This project utilizes a Python-based automation engine designed to provide the most stable Free-to-Air experience by bypassing common scraping limitations.

### 🛡️ Core Features (v7.3)

1.  **Fail-Safe Logic:** Detects Geoblocking (HTTP 403) on German channels (ZDF, ARD). Instead of removing them, the bot forces them into the playlist, ensuring they work for local users in Germany.
2.  **Auto-Discovery:** Scrapes global databases to find replacement links if a local source dies.
3.  **Smart History:** Remembers working streams to mitigate temporary server downtimes.
4.  **Quality Tagging:** Automatically appends resolution tags (`[FHD]`, `[HD]`) to channel names.
5.  **Latency Check:** Measures ping times to select the fastest available stream source.
6.  **Metadata Enrichment:** Auto-fills missing logos and EPG IDs.

### 📊 Status Report
* 🟢 **Green:** Verified Online globally.
* ⚠️ **Yellow:** Forced Online (Geoblock Protection Active).
👉 **[VIEW TECHNICAL REPORT (STATUS.md)](STATUS.md)**

### 🔗 Playlist URL
https://raw.githubusercontent.com/birkul/turkish-german-free-iptv/main/turkalmankanallari.m3u


---

## 📂 Kategorien / Categories

| Sektion | Inhalt / Content |
| :--- | :--- |
| **TR \| Ulusal** | Hauptsender (ATV, Show, Star, Kanal 7, TV8...) |
| **TR \| Haber** | Nachrichten & Wirtschaft (Bloomberg, CNN Türk...) |
| **TR \| Spor** | Sport (TRT Spor, A Spor, FB TV...) |
| **TR \| Muzik** | Musik (Power, Kral, Dream...) |
| **TR \| Cocuk** | Kinder (TRT Çocuk, Minika...) |
| **TR \| Belgesel** | Doku & Kultur (TRT Belgesel...) |
| **TR \| Yerel** | Lokalsender (Anadolu Kanalları) |
| **DE \| Deutsch** | Deutsche Free-TV Sender (ARD, ZDF, Dritte...) |

---

### ⚠️ Disclaimer
* **Legal:** This list contains only **Free-to-Air (FTA)** streams. No Pay-TV / Encrypted content.
* **Rechtliches:** Nur frei empfangbare Sender. Keine illegalen Inhalte.

import os
import json
import re
import urllib.request
import yt_dlp
import google.generativeai as genai

def son_canli_yayin_id_bul(kanal_url):
    try:
        streams_url = f"{kanal_url}/streams"
        req = urllib.request.Request(streams_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode()
            video_ids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html)
            return video_ids[0] if video_ids else None
    except:
        return None

def metni_cek(video_id):
    # YENİLİK: Güçlü yt-dlp aracı ile IP engelini aşarak altyazıyı çekiyoruz
    ydl_opts = {
        'quiet': True,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
    
    captions = info.get('automatic_captions', {})
    if 'tr' not in captions:
        captions = info.get('subtitles', {})
        
    if 'tr' in captions:
        for format in captions['tr']:
            if format.get('ext') == 'json3':
                url = format['url']
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req)
                data = json.loads(response.read().decode())
                # Metinleri birleştir
                text = " ".join([seg.get('utf8', '') for event in data.get('events', []) for seg in event.get('segs', [])])
                return text
    return ""

def yayini_ozetle():
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    kanal_linki = "https://www.youtube.com/@Kayitdisi"
    
    try:
        print("1. Video aranıyor...")
        video_id = son_canli_yayin_id_bul(kanal_linki)
        if not video_id:
            raise Exception("Kanalda uygun video ID bulunamadı.")

        print(f"Buldum: {video_id}. 2. Metin çekiliyor...")
        
        tam_metin = metni_cek(video_id)
        if not tam_metin:
            raise Exception("Altyazı bulunamadı veya çekilemedi.")
            
        print("3. Yapay Zeka özetliyor...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        cevap = model.generate_content(f"Sen profesyonel bir finans analistisin. Şu yayını maddeler halinde özetle: {tam_metin[:30000]}") 
        
        ozet_verisi = {
            "analist": "Kayıtdışı - Son Yayın Özeti",
            "ozet": cevap.text
        }
        
    except Exception as e:
        print(f"Hata detayı: {e}")
        ozet_verisi = { 
            "analist": "Sistem Bildirimi", 
            "ozet": f"Bir hata oluştu: {e}" 
        }

    print("4. Dosya kaydediliyor...")
    with open('ozet.json', 'w', encoding='utf-8') as f:
        json.dump(ozet_verisi, f, ensure_ascii=False, indent=4)
    print("İşlem tamamlandı.")

if __name__ == "__main__":
    yayini_ozetle()

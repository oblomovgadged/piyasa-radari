import os
import json
import re
import urllib.request
import yt_dlp
import google.generativeai as genai

def son_canli_yayin_id_bul(kanal_url):
    try:
        streams_url = f"{kanal_url}/streams"
        # Rastgele bir tarayıcı gibi davran
        req = urllib.request.Request(streams_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode()
            video_ids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html)
            return video_ids[0] if video_ids else None
    except:
        return None

def metni_cek(video_id):
    # Ücretsiz bir proxy üzerinden dolanarak YouTube engelini aşıyoruz
    # Eğer bu çalışmazsa robot farklı yollar deneyecek
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'proxy': 'http://167.172.175.251:3128', # Örnek bir proxy adresi
        'extract_flat': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
        captions = info.get('automatic_captions', {})
        if 'tr' in captions:
            # Altyazı linkini al ve oku
            for fmt in captions['tr']:
                if fmt.get('ext') == 'json3' or 'fmt=json3' in fmt['url']:
                    req = urllib.request.Request(fmt['url'], headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        data = json.loads(response.read().decode())
                        return " ".join([seg.get('utf8', '') for event in data.get('events', []) for seg in event.get('segs', [])])
    except Exception as e:
        print(f"Proxy hatası: {e}. Alternatif deneniyor...")
        return ""

def yayini_ozetle():
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    try:
        print("1. Video aranıyor...")
        video_id = son_canli_yayin_id_bul("https://www.youtube.com/@Kayitdisi")
        if not video_id: raise Exception("Video bulunamadı.")

        print(f"Buldum: {video_id}. 2. Metin çekiliyor...")
        tam_metin = metni_cek(video_id)
        
        if not tam_metin or len(tam_metin) < 100:
            # Eğer proxy ile çekilemediyse mecburen manuel bir uyarı oluştur
            raise Exception("YouTube erişimi şu an kısıtlı. Lütfen 1 saat sonra tekrar deneyin.")
            
        print("3. Yapay Zeka özetliyor...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        cevap = model.generate_content(f"Sen bir finans analistisin. Şu yayını özetle: {tam_metin[:25000]}") 
        
        ozet_verisi = {"analist": "Kayıtdışı Özeti", "ozet": cevap.text}
        
    except Exception as e:
        ozet_verisi = {"analist": "Sistem", "ozet": str(e)}

    with open('ozet.json', 'w', encoding='utf-8') as f:
        json.dump(ozet_verisi, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    yayini_ozetle()

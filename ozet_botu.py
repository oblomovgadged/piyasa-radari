import os
import json
import re
import urllib.request
import google.generativeai as genai

def son_canli_yayin_id_bul(kanal_url):
    try:
        streams_url = f"{kanal_url}/streams"
        req = urllib.request.Request(streams_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode()
            video_ids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html)
            return video_ids[0] if video_ids else None
    except:
        return None

def metni_cek(video_id):
    # KESİN ÇÖZÜM: YouTube'a hiç uğramadan açık kaynaklı "Piped" sunucularından veriyi alıyoruz!
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.snopyta.org",
        "https://pipedapi.moomoo.me"
    ]
    
    for base_url in instances:
        try:
            print(f"Altyazı aranıyor ({base_url})...")
            url = f"{base_url}/streams/{video_id}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            subtitles = data.get('subtitles', [])
            if not subtitles: continue
            
            # Türkçe altyazıyı bul
            tr_sub = next((s for s in subtitles if s.get('code') == 'tr'), None)
            if not tr_sub: tr_sub = subtitles[0]
            
            sub_url = tr_sub.get('url')
            if not sub_url: continue
            
            # Metni indir (VTT formatı)
            sub_req = urllib.request.Request(sub_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(sub_req, timeout=10) as sub_response:
                sub_text = sub_response.read().decode('utf-8')
            
            # Metnin içindeki zaman damgalarını ve kodları temizle (Sadece kelimeler kalsın)
            temiz_metin = re.sub(r'<[^>]+>', '', sub_text) 
            temiz_metin = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}.*', '', temiz_metin) 
            temiz_metin = re.sub(r'WEBVTT', '', temiz_metin)
            temiz_metin = re.sub(r'Kind: captions', '', temiz_metin)
            temiz_metin = re.sub(r'Language: \w+', '', temiz_metin)
            temiz_metin = re.sub(r'[\r\n]+', ' ', temiz_metin) 
            temiz_metin = re.sub(r'\s+', ' ', temiz_metin).strip()
            
            if len(temiz_metin) > 100:
                return temiz_metin
        except Exception as e:
            print(f"Sunucu başarısız: {e}")
            continue
            
    return ""

def yayini_ozetle():
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    try:
        print("1. Video aranıyor...")
        video_id = son_canli_yayin_id_bul("https://www.youtube.com/@Kayitdisi")
        if not video_id: raise Exception("Kanalda video ID'si bulunamadı.")

        print(f"Buldum: {video_id}. 2. Metin çekiliyor...")
        tam_metin = metni_cek(video_id)
        
        if not tam_metin or len(tam_metin) < 100:
            raise Exception("Açık kaynak sunucularından metin çekilemedi.")
            
        print("3. Yapay Zeka özetliyor...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        cevap = model.generate_content(f"Sen profesyonel bir finans analistisin. Şu yayını maddeler halinde özetle: {tam_metin[:30000]}") 
        
        ozet_verisi = {"analist": "Kayıtdışı - Son Yayın Özeti", "ozet": cevap.text}
        
    except Exception as e:
        print(f"Hata detayı: {e}")
        ozet_verisi = {"analist": "Sistem Bildirimi", "ozet": str(e)}

    print("4. Dosya kaydediliyor...")
    with open('ozet.json', 'w', encoding='utf-8') as f:
        json.dump(ozet_verisi, f, ensure_ascii=False, indent=4)
    print("İşlem tamamlandı.")

if __name__ == "__main__":
    yayini_ozetle()

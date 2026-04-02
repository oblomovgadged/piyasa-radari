import os
import json
import re
import urllib.request
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

def son_canli_yayin_id_bul(kanal_url):
    try:
        streams_url = f"{kanal_url}/streams"
        with urllib.request.urlopen(streams_url) as response:
            html = response.read().decode()
            video_ids = re.findall(r'watch\?v=([^\"&? \n]+)', html)
            return video_ids[0] if video_ids else None
    except:
        return None

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
        
        # GÜNCELLEME: Hata veren kısmı tamamen kaldırdık. 
        # API'ye diyoruz ki: Önce Türkçe(tr) ara, bulamazsan İngilizce(en) çek.
        altyazilar = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr', 'en'])

        tam_metin = " ".join([parca['text'] for parca in altyazilar])
        
        print("3. Yapay Zeka özetliyor...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        cevap = model.generate_content(f"Sen profesyonel bir finans analistisin. Şu yayını maddeler halinde özetle: {tam_metin[:30000]}") 
        
        ozet_verisi = {
            "analist": "Kayıtdışı - Son Yayın Özeti",
            "ozet": cevap.text if cevap.text else "Yapay zeka özet oluşturamadı."
        }
        
    except Exception as e:
        print(f"Hata detayı: {e}")
        # YouTube videoya henüz altyazı eklememişse kibar bir uyarı ver
        ozet_verisi = { 
            "analist": "Sistem Bildirimi", 
            "ozet": "Son yayının altyazıları (transcript) YouTube tarafından henüz işlenmemiş. Sistem daha sonra tekrar deneyecektir." 
        }

    print("4. Dosya kaydediliyor...")
    with open('ozet.json', 'w', encoding='utf-8') as f:
        json.dump(ozet_verisi, f, ensure_ascii=False, indent=4)
    print("İşlem tamamlandı.")

if __name__ == "__main__":
    yayini_ozetle()

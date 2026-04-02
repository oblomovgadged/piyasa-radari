import os
import json
import re
import urllib.request
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

def son_canli_yayin_id_bul(kanal_url):
    streams_url = f"{kanal_url}/streams"
    with urllib.request.urlopen(streams_url) as response:
        html = response.read().decode()
        video_ids = re.findall(r'watch\?v=([^\"&? \n]+)', html)
        return video_ids[0] if video_ids else None

def yayini_ozetle():
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # Senin takip ettiğin kanal
    kanal_linki = "https://www.youtube.com/@Kayitdisi"
    
    try:
        print("1. Kanaldaki en son canlı yayın aranıyor...")
        video_id = son_canli_yayin_id_bul(kanal_linki)
        
        if not video_id:
            print("Video bulunamadı!")
            return

        print(f"Buldum! Video ID: {video_id}")
        print("2. Konuşma metni çekiliyor...")
        
        altyazilar = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr'])
        tam_metin = " ".join([parca['text'] for parca in altyazilar])
        
        print("3. Yapay Zeka özetliyor...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        talimat = f"Sen profesyonel bir finans analistisin. Kayıtdışı kanalının şu yayın metnini analiz et. Maddeler halinde; piyasa yönü, ekonomik beklentiler ve önemli seviyeleri özetle: {tam_metin}"
        
        cevap = model.generate_content(talimat)
        
        print("4. Dosya güncelleniyor...")
        ozet_verisi = {
            "analist": "Kayıtdışı - Son Yayın Özeti",
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "ozet": cevap.text
        }
        
        with open('ozet.json', 'w', encoding='utf-8') as f:
            json.dump(ozet_verisi, f, ensure_ascii=False, indent=4)
        print("Bitti! Haritan güncellenmeye hazır.")

    except Exception as hata:
        print(f"Hata: {hata}")

if __name__ == "__main__":
    yayini_ozetle()

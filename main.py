import asyncio
import requests
import os
import nest_asyncio
import yt_dlp
import subprocess
from tqdm import tqdm
import edge_tts

nest_asyncio.apply()

# --- الإعدادات ---
VOICE_NAME = "ar-EG-SalmaNeural" 
STORY_URL = "https://meja.do.am/work/you.txt"
# ملاحظة: إذا استمر الحظر، يفضل رفع فيديو خلفية واحد على Catbox واستخدام رابطه مباشرة هنا
YOUTUBE_URL = "https://www.youtube.com/watch?v=8LJUxJi7r5U"
OUTPUT_VIDEO = "final_output.mp4"

def fetch_story(url):
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        return res.text.strip()
    except: return None

async def generate():
    print("🚀 بدء العمل...")
    
    text = fetch_story(STORY_URL)
    if not text: return

    # 1. توليد الصوت
    communicate = edge_tts.Communicate(text, VOICE_NAME)
    await communicate.save("audio.mp3")
    print("✅ تم توليد الصوت.")

    # 2. تحميل الفيديو (مع محاولة تجاوز طلب تسجيل الدخول)
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': 'raw_input.mp4',
        'quiet': True,
        'no_warnings': True,
        # المحرك التالي هو السر في تجاوز بعض أنواع الحظر
        'extractor_args': {'youtube': {'player_client': ['ios', 'android']}} 
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([YOUTUBE_URL])
        print("✅ تم تحميل الفيديو.")
    except Exception as e:
        print(f"❌ يوتيوب ما زال يحظر السيرفر. الحل هو استخدام رابط مباشر للفيديو بدلاً من يوتيوب.")
        return

    # 3. الرندر الفائق
    print("🎬 جاري الرندر...")
    final_cmd = (
        'ffmpeg -y -stream_loop -1 -i raw_input.mp4 -i audio.mp3 '
        '-vf "crop=iw*0.8:ih*0.6:iw*0.1:ih*0.1,scale=480:854" '
        '-c:v libx264 -preset ultrafast -crf 30 '
        '-c:a aac -shortest '
        f'{OUTPUT_VIDEO}'
    )
    subprocess.run(final_cmd, shell=True)

    # 4. الرفع
    if os.path.exists(OUTPUT_VIDEO):
        with open(OUTPUT_VIDEO, "rb") as f:
            res = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}).text
            print(f"\n🔗 الرابط النهائي: {res}")

if __name__ == "__main__":
    asyncio.run(generate())

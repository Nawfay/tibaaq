import yt_dlp
import os
from uuid import uuid4

def download_video(url: str, source: str) -> str:
    output_dir = f"downloads/{source}"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{uuid4()}.mp4")

    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'format': 'mp4'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path

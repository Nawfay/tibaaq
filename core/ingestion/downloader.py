import yt_dlp
import os

def download_video_and_metadata(url: str, id: str) -> tuple[str, dict]:
    output_dir = f"tmp"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, id)
    readable_output_path = f"{output_path}.m4a"

    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'format': 'bestaudio/best',
        "writethumbnail": True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '128',
        },
        {
            "key": "FFmpegThumbnailsConvertor",
            "format": "jpg"
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    return readable_output_path, {
        "description": info.get("description", ""),
        "title": info.get("title"),
    }

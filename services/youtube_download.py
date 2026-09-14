"""YouTube video download service using yt-dlp."""

import os
import asyncio
from typing import Dict, Any
from yt_dlp import YoutubeDL
from config.settings import settings

async def download_youtube_video(youtube_url: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "video.%(ext)s")

    ydl_opts: Dict[str, Any] = {
        "format": "mp4/bestvideo+bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "overwrites": True
    }

    if settings.ytdlp_proxy:
        ydl_opts["proxy"] = settings.ytdlp_proxy

    if settings.ytdlp_cookies_path and os.path.exists(settings.ytdlp_cookies_path):
        ydl_opts["cookiefile"] = settings.ytdlp_cookies_path

    loop = asyncio.get_event_loop()
    
    def _download():
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info)
            return filename

    downloaded_file = await loop.run_in_executor(None, _download)
    return downloaded_file

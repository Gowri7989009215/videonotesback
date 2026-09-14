"""YouTube video ID extraction and transcript fetching service."""

import re
from typing import List, Dict, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi

def extract_youtube_id(url: str) -> Optional[str]:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/shorts\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def fetch_youtube_transcript(video_id: str) -> List[Dict[str, Any]]:
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        formatted = []
        for item in transcript:
            formatted.append({
                "text": item.text if hasattr(item, "text") else item.get("text", ""),
                "start": item.start if hasattr(item, "start") else item.get("start", 0.0),
                "duration": item.duration if hasattr(item, "duration") else item.get("duration", 0.0)
            })
        return formatted
    except Exception as e:
        print(f"[YouTubeTranscript] Warning: Failed to fetch transcript for {video_id}: {e}")
        return []

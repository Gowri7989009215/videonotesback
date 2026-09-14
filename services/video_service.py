"""FFmpeg frame extraction and FPDF2 PDF generation service."""

import os
import asyncio
from typing import List, Dict, Any
from fpdf import FPDF
from config.settings import settings

async def extract_audio_from_video(video_path: str, output_audio_path: str) -> str:
    os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
    cmd = f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{output_audio_path}"'
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.communicate()
    return output_audio_path

async def extract_frames(video_path: str, output_dir: str, interval_seconds: int = 3) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%04d.jpg")
    cmd = f'ffmpeg -y -i "{video_path}" -vf "fps=1/{interval_seconds}" "{pattern}"'
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.communicate()

    frames = sorted([
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.endswith(".jpg")
    ])
    return frames

async def generate_pdf(frames: List[str], transcript_items: List[Dict[str, Any]], pdf_path: str) -> int:
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    loop = asyncio.get_event_loop()
    def _build_pdf():
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        for idx, frame in enumerate(frames):
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, f"Frame {idx + 1}", ln=True)
            
            pdf.image(frame, x=10, w=190)
            pdf.ln(5)
            
            pdf.set_font("Helvetica", "", 10)
            if idx < len(transcript_items):
                item = transcript_items[idx]
                text = item.get("text") or item.get("word") or ""
                pdf.multi_cell(0, 5, text)
            
        pdf.output(pdf_path)
        return len(frames)

    return await loop.run_in_executor(None, _build_pdf)

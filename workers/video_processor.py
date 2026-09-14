"""Worker task for background video processing pipeline."""

import os
from typing import Dict, Any
from models.video import (
    find_job_by_id,
    find_video_by_id,
    update_job_status,
    create_output,
    create_note
)
from services.youtube_service import extract_youtube_id, fetch_youtube_transcript
from services.youtube_download import download_youtube_video
from services.video_service import extract_audio_from_video, extract_frames, generate_pdf
from services.transcription_service import transcribe_audio
from services.ai_service import generate_ai_analysis
from utils.email import send_job_completion_email
from models.user import find_user_by_id
from config.settings import settings

async def process_video_job(payload: Dict[str, Any]):
    job_id = payload.get("job_id")
    if not job_id:
        return

    job = await find_job_by_id(job_id)
    if not job:
        return

    video_id = job.get("videoId")
    video = await find_video_by_id(video_id) if video_id else None

    await update_job_status(job_id, "processing", progress=10)

    try:
        temp_dir = os.path.join(settings.storage_root, "temp", job_id)
        frames_dir = os.path.join(settings.storage_root, "frames", job_id)
        pdf_path = os.path.join(settings.storage_root, "pdfs", f"{job_id}.pdf")
        os.makedirs(temp_dir, exist_ok=True)

        video_path = None
        transcript_items = []

        if video and video.get("youtubeUrl"):
            yt_url = video["youtubeUrl"]
            yt_id = extract_youtube_id(yt_url)
            if yt_id:
                transcript_items = await fetch_youtube_transcript(yt_id)
            video_path = await download_youtube_video(yt_url, temp_dir)
        elif video and video.get("filename"):
            video_path = os.path.join(settings.storage_root, "uploads", video["filename"])

        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not accessible: {video_path}")

        await update_job_status(job_id, "processing", progress=30)

        interval = job.get("intervalSeconds", 3)
        frames = await extract_frames(video_path, frames_dir, interval_seconds=interval)
        await update_job_status(job_id, "processing", progress=60)

        if not transcript_items and "transcript" in job.get("mode", ""):
            audio_path = os.path.join(temp_dir, "audio.wav")
            await extract_audio_from_video(video_path, audio_path)
            transcript_items = await transcribe_audio(audio_path)

        await update_job_status(job_id, "processing", progress=80)

        page_count = await generate_pdf(frames, transcript_items, pdf_path)
        await create_output(job_id, pdf_path, page_count)

        transcript_text = " ".join([
            item.get("text") or item.get("word") or ""
            for item in transcript_items
        ])

        analysis = await generate_ai_analysis(transcript_text or "No speech detected in video.")

        await create_note(
            user_id=video["userId"] if video else "",
            video_id=video_id,
            job_id=job_id,
            title=analysis.get("title", "Video Lecture Notes"),
            summary=analysis.get("summary", ""),
            action_items=analysis.get("action_items", []),
            key_takeaways=analysis.get("key_takeaways", []),
            flashcards=analysis.get("flashcards", []),
            quiz_questions=analysis.get("quiz_questions", [])
        )

        await update_job_status(job_id, "completed", progress=100)

        if video:
            user = await find_user_by_id(video["userId"])
            if user and user.get("email"):
                await send_job_completion_email(user["email"], job_id)

    except Exception as e:
        print(f"[Worker Error] Job {job_id} failed: {e}")
        await update_job_status(job_id, "failed", error_message=str(e))

from utils.background import register_handler
register_handler("process_video", process_video_job)

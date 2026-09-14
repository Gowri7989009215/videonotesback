"""Background job creation and retrieval router."""

from fastapi import APIRouter, Depends, HTTPException, status
from routers.auth import get_current_user
from models.schemas import CreateJobRequest
from models.video import (
    create_video,
    create_job,
    find_job_by_id,
    find_jobs_by_user,
    find_note_by_id,
    find_notes_by_user
)
from utils.background import dispatch_background

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("")
async def create_new_job(req: CreateJobRequest, user = Depends(get_current_user)):
    user_id = str(user["id"])
    video_id = req.video_id

    if not video_id and req.youtube_url:
        video = await create_video(user_id=user_id, youtube_url=req.youtube_url)
        video_id = video["id"]

    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either video_id or youtube_url must be provided"
        )

    job = await create_job(
        user_id=user_id,
        video_id=video_id,
        mode=req.mode,
        interval_seconds=req.interval_seconds
    )

    await dispatch_background("process_video", {"job_id": job["id"]})
    return job

@router.get("")
async def list_jobs(user = Depends(get_current_user)):
    user_id = str(user["id"])
    return await find_jobs_by_user(user_id)

@router.get("/{job_id}")
async def get_job(job_id: str, user = Depends(get_current_user)):
    job = await find_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.get("/{job_id}/notes")
async def get_job_notes(job_id: str, user = Depends(get_current_user)):
    notes = await find_notes_by_user(str(user["id"]))
    for note in notes:
        if note["jobId"] == job_id:
            return note
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notes not found for this job")

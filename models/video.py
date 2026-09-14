"""Video, Job, Output, and Notes database operations."""

import uuid
import json
from typing import Optional, List, Dict, Any
from config.database import query, query_one, execute

async def create_video(user_id: str, filename: Optional[str] = None, youtube_url: Optional[str] = None) -> Dict[str, Any]:
    video_id = str(uuid.uuid4())
    input_type = "youtube" if youtube_url else "upload"
    file_path = filename if filename else (youtube_url or "youtube")
    title = filename if filename else (youtube_url or "Video")
    sql = """
    INSERT INTO videos (id, user_id, input_type, title, file_path, youtube_url, created_at)
    VALUES ($1, $2::uuid, $3, $4, $5, $6, NOW())
    RETURNING id, user_id, input_type, title, file_path, youtube_url, created_at
    """
    row = await query_one(sql, video_id, user_id, input_type, title, file_path, youtube_url)
    return {
        "id": str(row["id"]),
        "userId": str(row["user_id"]),
        "filename": row["file_path"],
        "youtubeUrl": row["youtube_url"],
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None
    }

async def find_video_by_id(video_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM videos WHERE id = $1::uuid"
    row = await query_one(sql, video_id)
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "userId": str(row["user_id"]),
        "filename": row["file_path"],
        "youtubeUrl": row["youtube_url"],
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None
    }

async def create_job(user_id: str, video_id: Optional[str], mode: str, interval_seconds: int) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    sql = """
    INSERT INTO jobs (id, user_id, video_id, mode, interval_seconds, status, progress, created_at)
    VALUES ($1, $2::uuid, $3::uuid, $4, $5, 'pending', 0, NOW())
    RETURNING *
    """
    row = await query_one(sql, job_id, user_id, video_id, mode, interval_seconds)
    return format_job_dict(row)

async def find_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT j.*, o.pdf_path, o.frame_count as page_count, o.created_at as output_created_at
    FROM jobs j
    LEFT JOIN outputs o ON o.job_id = j.id
    WHERE j.id = $1::uuid
    """
    row = await query_one(sql, job_id)
    if not row:
        return None
    return format_job_dict(row)

async def find_jobs_by_user(user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    sql = """
    SELECT j.*, o.pdf_path, o.frame_count as page_count, o.created_at as output_created_at
    FROM jobs j
    LEFT JOIN outputs o ON o.job_id = j.id
    WHERE j.user_id = $1::uuid
    ORDER BY j.created_at DESC
    LIMIT $2 OFFSET $3
    """
    rows = await query(sql, user_id, limit, offset)
    return [format_job_dict(r) for r in rows]

async def update_job_status(job_id: str, status: str, error_message: Optional[str] = None, progress: Optional[int] = None):
    if status in ["completed", "failed"]:
        sql = """
        UPDATE jobs
        SET status = $2, error_message = $3, progress = COALESCE($4, progress), completed_at = NOW()
        WHERE id = $1::uuid
        """
        await execute(sql, job_id, status, error_message, progress)
    else:
        sql = """
        UPDATE jobs
        SET status = $2, error_message = $3, progress = COALESCE($4, progress)
        WHERE id = $1::uuid
        """
        await execute(sql, job_id, status, error_message, progress)

async def create_output(job_id: str, pdf_path: str, page_count: int) -> Dict[str, Any]:
    out_id = str(uuid.uuid4())
    sql = """
    INSERT INTO outputs (id, job_id, pdf_path, frame_count, created_at)
    VALUES ($1, $2::uuid, $3, $4, NOW())
    ON CONFLICT (job_id) DO UPDATE SET pdf_path = $3, frame_count = $4, created_at = NOW()
    RETURNING id, job_id, pdf_path, frame_count as page_count, created_at
    """
    row = await query_one(sql, out_id, job_id, pdf_path, page_count)
    return {
        "id": str(row["id"]),
        "jobId": str(row["job_id"]),
        "pdfPath": row["pdf_path"],
        "pageCount": row["page_count"],
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None
    }

async def find_output_by_job_id(job_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT id, job_id, pdf_path, frame_count as page_count, created_at FROM outputs WHERE job_id = $1::uuid"
    row = await query_one(sql, job_id)
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "jobId": str(row["job_id"]),
        "pdfPath": row["pdf_path"],
        "pageCount": row["page_count"],
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None
    }

async def create_note(
    user_id: str,
    video_id: Optional[str],
    job_id: str,
    title: str,
    summary: str,
    action_items: List[str],
    key_takeaways: List[str],
    flashcards: List[Dict[str, str]],
    quiz_questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    note_id = str(uuid.uuid4())
    content = {
        "title": title,
        "summary": summary,
        "action_items": action_items,
        "key_takeaways": key_takeaways,
        "flashcards": flashcards,
        "quiz_questions": quiz_questions
    }
    sql = """
    INSERT INTO notes (id, job_id, user_id, note_type, content, ai_provider, ai_model, created_at)
    VALUES ($1, $2::uuid, $3::uuid, 'summary', $4::jsonb, 'ai', 'default', NOW())
    RETURNING *
    """
    row = await query_one(sql, note_id, job_id, user_id, json.dumps(content))
    return format_note_dict(row)

async def find_notes_by_user(user_id: str) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM notes WHERE user_id = $1::uuid ORDER BY created_at DESC"
    rows = await query(sql, user_id)
    return [format_note_dict(r) for r in rows]

async def find_note_by_id(note_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM notes WHERE id = $1::uuid"
    row = await query_one(sql, note_id)
    if not row:
        return None
    return format_note_dict(row)

async def cleanup_stale_jobs(timeout_minutes: int = 15):
    sql = """
    UPDATE jobs
    SET status = 'failed', error_message = 'Job timed out in processing queue'
    WHERE status = 'processing' AND created_at < NOW() - ($1 || ' minutes')::interval
    """
    await execute(sql, str(timeout_minutes))

def format_job_dict(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    output = None
    if row.get("pdf_path"):
        output = {
            "id": str(row.get("id")),
            "pdfUrl": f"/api/files/pdf/{row.get('id')}",
            "frameCount": row.get("page_count", 0),
            "createdAt": row["output_created_at"].isoformat() if row.get("output_created_at") else None
        }
    return {
        "id": str(row["id"]),
        "mode": row["mode"],
        "intervalSeconds": row["interval_seconds"],
        "status": row["status"],
        "progress": row.get("progress", 0),
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
        "completedAt": row["completed_at"].isoformat() if row.get("completed_at") else None,
        "videoId": str(row["video_id"]) if row.get("video_id") else None,
        "errorMessage": row.get("error_message"),
        "output": output
    }

def format_note_dict(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    raw_content = row.get("content", {})
    content = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
    return {
        "id": str(row["id"]),
        "userId": str(row["user_id"]),
        "jobId": str(row["job_id"]),
        "title": content.get("title", "Video Lecture Notes"),
        "summary": content.get("summary", ""),
        "actionItems": content.get("action_items", []),
        "keyTakeaways": content.get("key_takeaways", []),
        "flashcards": content.get("flashcards", []),
        "quizQuestions": content.get("quiz_questions", []),
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None
    }

async def get_user_stats(user_id: str) -> Dict[str, int]:
    sql = """
    SELECT
        (SELECT COUNT(*) FROM videos WHERE user_id = $1::uuid) as total_videos,
        (SELECT COUNT(*) FROM jobs WHERE user_id = $1::uuid) as total_jobs,
        (SELECT COUNT(*) FROM jobs WHERE user_id = $1::uuid AND status = 'completed') as completed_jobs,
        (SELECT COUNT(*) FROM notes WHERE user_id = $1::uuid) as total_notes
    """
    row = await query_one(sql, user_id)
    if not row:
        return {"totalVideos": 0, "totalJobs": 0, "completedJobs": 0, "totalNotes": 0}
    return {
        "totalVideos": int(row["total_videos"]),
        "totalJobs": int(row["total_jobs"]),
        "completedJobs": int(row["completed_jobs"]),
        "totalNotes": int(row["total_notes"])
    }

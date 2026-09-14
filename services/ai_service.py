"""AI Services: Summary, Flashcards, Quizzes generation using LLMs."""

import json
import httpx
from typing import Dict, Any, List
from config.settings import settings

async def generate_ai_analysis(transcript_text: str) -> Dict[str, Any]:
    prompt = f"""
    Analyze the following video transcript and return a structured JSON response with:
    - title: String (concise title for the note)
    - summary: String (detailed comprehensive summary)
    - action_items: List of Strings (key action items)
    - key_takeaways: List of Strings (main takeaways)
    - flashcards: List of Objects with 'question' and 'answer'
    - quiz_questions: List of Objects with 'question', 'options' (list of 4 strings), and 'correct_answer' (string)

    Transcript:
    {transcript_text[:10000]}

    Return ONLY valid JSON.
    """

    if settings.openai_api_key:
        return await _generate_openai(prompt)
    elif settings.gemini_api_key:
        return await _generate_gemini(prompt)
    elif settings.anthropic_api_key:
        return await _generate_anthropic(prompt)
    else:
        return _generate_fallback(transcript_text)

async def _generate_openai(prompt: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

async def _generate_gemini(prompt: str) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)

async def _generate_anthropic(prompt: str) -> Dict[str, Any]:
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        text = data["content"][0]["text"]
        return json.loads(text)

def _generate_fallback(transcript_text: str) -> Dict[str, Any]:
    return {
        "title": "Video Lecture Notes",
        "summary": transcript_text[:500] + ("..." if len(transcript_text) > 500 else ""),
        "action_items": ["Review video notes and key takeaways."],
        "key_takeaways": ["Automated note generation completed."],
        "flashcards": [{"question": "What is covered in this video?", "answer": transcript_text[:100]}],
        "quiz_questions": [{
            "question": "What is the main topic of this video?",
            "options": ["Video processing", "General lecture", "Tutorial", "Overview"],
            "correct_answer": "Video processing"
        }]
    }

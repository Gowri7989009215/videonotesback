"""Offline audio transcription using Vosk or Faster-Whisper."""

import os
import json
import asyncio
import wave
from typing import List, Dict, Any, Optional
from config.settings import settings

async def transcribe_audio(audio_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if settings.vosk_model_path and os.path.exists(settings.vosk_model_path):
        return await _transcribe_vosk(audio_path)
    
    try:
        return await _transcribe_whisper(audio_path)
    except Exception as e:
        print(f"[Transcription] Whisper failed: {e}. Falling back to empty transcript.")
        return []

async def _transcribe_vosk(audio_path: str) -> List[Dict[str, Any]]:
    from vosk import Model, KaldiRecognizer
    
    loop = asyncio.get_event_loop()
    def _run():
        model = Model(settings.vosk_model_path)
        wf = wave.open(audio_path, "rb")
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if "result" in res:
                    for w in res["result"]:
                        results.append({
                            "word": w["word"],
                            "start": w["start"],
                            "end": w["end"]
                        })
        final_res = json.loads(rec.FinalResult())
        if "result" in final_res:
            for w in final_res["result"]:
                results.append({
                    "word": w["word"],
                    "start": w["start"],
                    "end": w["end"]
                })
        return results

    return await loop.run_in_executor(None, _run)

async def _transcribe_whisper(audio_path: str) -> List[Dict[str, Any]]:
    from faster_whisper import WhisperModel

    loop = asyncio.get_event_loop()
    def _run():
        model = WhisperModel(settings.whisper_model_name, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, word_timestamps=True)
        results = []
        for segment in segments:
            if segment.words:
                for w in segment.words:
                    results.append({
                        "word": w.word.strip(),
                        "start": w.start,
                        "end": w.end
                    })
            else:
                results.append({
                    "text": segment.text.strip(),
                    "start": segment.start,
                    "end": segment.end
                })
        return results

    return await loop.run_in_executor(None, _run)

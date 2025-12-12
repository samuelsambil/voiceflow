
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import os
import io
import base64
from datetime import datetime
import tempfile
import soundfile as sf

app = FastAPI(title="VibeVoice Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    mode: str = "chat"
    personality: str = "friend"
    voice_name: str = "Emma"

class ThoughtRequest(BaseModel):
    brain_dump: str
    personality: str = "coach"

class DailyBriefingRequest(BaseModel):
    personality: str = "friend"

user_data = {
    "streaks": 0,
    "badges": [],
    "total_interactions": 0,
    "last_interaction": None,
    "thoughts_organized": 0,
    "voice_interactions": 0
}

BADGES = {
    "first_step": {"name": "🎯 First Step", "requirement": 1, "description": "Your first interaction"},
    "consistent_5": {"name": "🔥 On Fire", "requirement": 5, "description": "5-day streak"},
    "consistent_10": {"name": "⚡ Unstoppable", "requirement": 10, "description": "10-day streak"},
    "thought_master": {"name": "🧠 Thought Master", "requirement": 10, "description": "Organized 10 thoughts"},
    "voice_user": {"name": "🎤 Voice Power", "requirement": 10, "description": "10 voice interactions"},
    "early_bird": {"name": "🌅 Early Bird", "requirement": 1, "description": "Morning briefing"},
}

def generate_ai_response(prompt: str, personality: str = "friend") -> str:
    personalities = {
        "coach": "You are a motivational life coach. Be supportive, energetic, and action-oriented. Keep responses concise (2-3 sentences).",
        "friend": "You are a caring, supportive friend. Be warm, understanding, and encouraging. Keep responses conversational and brief (2-3 sentences).",
        "executive": "You are a professional executive assistant. Be efficient, organized, and direct. Keep responses brief and professional (2-3 sentences)."
    }
    
    system_prompt = personalities.get(personality, personalities["friend"])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer([text], return_tensors="pt").to(chat_model.device)
        generated_ids = chat_model.generate(
            model_inputs.input_ids,
            max_new_tokens=150,
            temperature=0.7,
            do_sample=True,
            top_p=0.9
        )
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response.strip()
    except Exception as e:
        return "I'm here to help! Tell me more about what's on your mind."

def transcribe_audio(audio_file_path: str) -> str:
    try:
        segments, info = whisper_model.transcribe(audio_file_path, language="en", beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

def generate_speech(text: str, voice_name: str = "Emma") -> bytes:
    try:
        audio_data = tts_model.synthesize(text=text, speaker_name=voice_name, stream=False)
        output = io.BytesIO()
        sf.write(output, audio_data, 24000, format='WAV')
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"TTS error: {e}")
        return b""

def update_streak():
    now = datetime.now()
    last = user_data.get("last_interaction")
    
    if last is None:
        user_data["streaks"] = 1
        user_data["last_interaction"] = now.isoformat()
        check_badge("first_step")
        return
    
    last_date = datetime.fromisoformat(last)
    diff = (now.date() - last_date.date()).days
    
    if diff == 0:
        pass
    elif diff == 1:
        user_data["streaks"] += 1
        check_badge("consistent_5")
        check_badge("consistent_10")
    else:
        user_data["streaks"] = 1
    
    user_data["last_interaction"] = now.isoformat()

def check_badge(badge_key: str):
    badge = BADGES.get(badge_key)
    if not badge or badge["name"] in user_data["badges"]:
        return
    
    earned = False
    if badge_key == "first_step" and user_data["total_interactions"] >= 1:
        earned = True
    elif badge_key == "consistent_5" and user_data["streaks"] >= 5:
        earned = True
    elif badge_key == "consistent_10" and user_data["streaks"] >= 10:
        earned = True
    elif badge_key == "thought_master" and user_data.get("thoughts_organized", 0) >= 10:
        earned = True
    elif badge_key == "voice_user" and user_data.get("voice_interactions", 0) >= 10:
        earned = True
    
    if earned:
        user_data["badges"].append(badge["name"])

@app.get("/")
def read_root():
    return {
        "message": "VibeVoice Prototype API is running! 🚀",
        "features": ["Chat", "Voice (VibeVoice TTS)", "Thought Organization", "Daily Briefing"],
        "models": {"chat": "Qwen2.5-0.5B", "stt": "Faster-Whisper", "tts": "VibeVoice-0.5B"}
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "models_loaded": True, "streaks": user_data["streaks"], "badges": len(user_data["badges"])}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        update_streak()
        user_data["total_interactions"] += 1
        
        response_text = generate_ai_response(request.message, request.personality)
        
        audio_base64 = None
        if request.mode in ["voice", "hybrid"]:
            audio_bytes = generate_speech(response_text, request.voice_name)
            if audio_bytes:
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                user_data["voice_interactions"] = user_data.get("voice_interactions", 0) + 1
                check_badge("voice_user")
        
        return {
            "response": response_text,
            "audio_base64": audio_base64,
            "mode": request.mode,
            "streaks": user_data["streaks"],
            "new_badges": user_data["badges"][-1:] if user_data["badges"] else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await file.read()
            temp_audio.write(content)
            temp_path = temp_audio.name
        
        text = transcribe_audio(temp_path)
        os.unlink(temp_path)
        
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/organize-thought")
def organize_thought(request: ThoughtRequest):
    try:
        update_streak()
        user_data["total_interactions"] += 1
        user_data["thoughts_organized"] = user_data.get("thoughts_organized", 0) + 1
        check_badge("thought_master")
        
        prompt = f"""The user is brain dumping their thoughts. Organize this into a clear, actionable plan:

Brain dump: {request.brain_dump}

Provide:
1. A brief summary (1 sentence)
2. 3-5 clear action steps
3. One encouraging note

Keep it concise and actionable."""
        
        response = generate_ai_response(prompt, request.personality)
        
        return {"organized_plan": response, "streaks": user_data["streaks"], "thoughts_organized": user_data.get("thoughts_organized", 0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/daily-briefing")
def daily_briefing(request: DailyBriefingRequest):
    try:
        update_streak()
        check_badge("early_bird")
        
        now = datetime.now()
        day = now.strftime("%A, %B %d, %Y")
        
        prompt = f"""Create a brief, motivating daily briefing for {day}.

Include:
1. A warm greeting
2. One focus intention for the day
3. A quick productivity tip
4. An encouraging note

Keep it brief, warm, and actionable (3-4 sentences)."""
        
        response = generate_ai_response(prompt, request.personality)
        
        return {"briefing": response, "date": day, "streaks": user_data["streaks"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    return {
        "streaks": user_data["streaks"],
        "badges": user_data["badges"],
        "total_interactions": user_data["total_interactions"],
        "thoughts_organized": user_data.get("thoughts_organized", 0),
        "voice_interactions": user_data.get("voice_interactions", 0)
    }

@app.get("/badges")
def get_badges():
    progress = []
    for key, badge in BADGES.items():
        earned = badge["name"] in user_data["badges"]
        progress.append({"name": badge["name"], "description": badge["description"], "earned": earned, "requirement": badge["requirement"]})
    return {"badges": progress}

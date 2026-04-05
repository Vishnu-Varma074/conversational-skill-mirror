import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from groq import Groq
from dotenv import load_dotenv
import json

# ====================== LOAD ENVIRONMENT VARIABLES ======================
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key or api_key.strip() == "":
    raise ValueError("GROQ_API_KEY is missing. Please add it in .env file.")

print("✅ GROQ_API_KEY loaded successfully!")

# ====================== INITIALIZE FASTAPI ======================
app = FastAPI(
    title="Conversational Skill Mirror API",
    description="Interview & Public Speaking Coach",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== CACHED WHISPER MODEL ======================
# Model is loaded only once when the backend starts (caching)
print("Loading Whisper 'tiny' model... (this may take 10-20 seconds)")

whisper_model = None

@app.on_event("startup")
async def load_model():
    global whisper_model
    try:
        whisper_model = WhisperModel(
            "tiny", 
            device="cpu", 
            compute_type="int8"
        )
        print("✅ Whisper 'tiny' model loaded successfully and cached!")
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        raise

groq_client = Groq(api_key=api_key)

# ====================== SYSTEM PROMPT ======================
SYSTEM_PROMPT = """
You are an expert communication coach. Analyze the transcript and return ONLY valid JSON:

{
  "filler_count": integer,
  "fillers": ["list of fillers"],
  "pace_wpm": integer,
  "clarity_score": integer,
  "bias_detected": ["list or empty"],
  "topic_coverage": integer,
  "cultural_nuance_feedback": "string",
  "strengths": ["bullet points"],
  "improvement_areas": ["bullet points"],
  "improved_response": "full polished response",
  "confidence_boosting_tips": ["tips"],
  "role_play_continuation": "next question suggestion"
}
"""

# ====================== ANALYZE ENDPOINT ======================
@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    question: str = ""
):
    if whisper_model is None:
        raise HTTPException(status_code=500, detail="Whisper model not loaded yet. Please try again later.")

    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".webm")):
        raise HTTPException(status_code=400, detail="Only audio files are supported.")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # Use cached model
        segments, info = whisper_model.transcribe(
            tmp_path,
            beam_size=5,
            language=None,
            condition_on_previous_text=False
        )

        transcript = " ".join(segment.text for segment in segments).strip()

        if not transcript or len(transcript) < 5:
            return {"error": "No clear speech detected. Please speak clearly."}

        # Groq Analysis
        user_prompt = f"""
        Question: {question or "General interview or public speaking response"}
        Transcript: {transcript}
        """

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )

        analysis = json.loads(completion.choices[0].message.content)

        return {
            "transcript": transcript,
            "duration_seconds": round(info.duration, 2),
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# Health Check
@app.get("/")
async def root():
    return {"message": "Conversational Skill Mirror Backend is running! 🎉", "status": "healthy"}

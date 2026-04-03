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

# ====================== API KEY VALIDATION ======================
api_key = os.getenv("GROQ_API_KEY")
if not api_key or api_key.strip() == "":
    raise ValueError("""
    ❌ ERROR: GROQ_API_KEY is missing or empty!

    Please create a file named .env in the 'backend' folder with this exact line:
    GROQ_API_KEY=gsk_your_actual_key_here

    Tips:
    - Use Notepad → Save As → All Files → File name: ".env" (include quotes while saving)
    - Do not add quotes around the key
    - Restart the backend after creating .env
    """)

print("✅ GROQ_API_KEY loaded successfully!")

# ====================== INITIALIZE FASTAPI ======================
app = FastAPI(
    title="Conversational Skill Mirror API",
    description="Backend API for Interview & Public Speaking Coach using GenAI + NLP",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== LOAD WHISPER MODEL ======================
print("Loading faster-whisper 'small' model... (first time may take 15-30 seconds)")
model = WhisperModel("small", device="cpu", compute_type="int8")   # Change to "cuda" if you have GPU
print("✅ Whisper model loaded successfully!")

groq_client = Groq(api_key=api_key)

# ====================== SYSTEM PROMPT FOR ANALYSIS ======================
SYSTEM_PROMPT = """
You are an expert communication coach specializing in Indian English, Hinglish, and non-native speakers (Hyderabad/Telangana context).
Analyze the spoken response carefully and return ONLY valid JSON with this exact structure:

{
  "filler_count": integer,
  "fillers": ["list of filler words"],
  "pace_wpm": integer,
  "clarity_score": integer,           // 1-10
  "bias_detected": ["list or empty"],
  "topic_coverage": integer,          // 1-10
  "cultural_nuance_feedback": "string (1-2 sentences)",
  "strengths": ["bullet points"],
  "improvement_areas": ["bullet points"],
  "improved_response": "full polished, confident, professional rephrased answer",
  "confidence_boosting_tips": ["3-4 actionable tips"],
  "role_play_continuation": "suggested next interviewer question + ideal reply"
}
"""

# ====================== MAIN ANALYZE ENDPOINT ======================
@app.post("/analyze",
          summary="Analyze Audio for Interview/Public Speaking",
          description="Receives audio recording from Streamlit frontend and returns detailed feedback using Whisper + Groq.")
async def analyze_audio(
    file: UploadFile = File(..., description="Audio file recorded from microphone (supports wav, mp3, m4a, webm up to 4 minutes)"),
    question: str = ""
):
    """
    This endpoint is called by the Streamlit frontend.
    """
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".webm")):
        raise HTTPException(status_code=400, detail="Only audio files (wav, mp3, m4a, webm) are supported.")

    # Save uploaded audio temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # 1. Transcribe audio using faster-whisper
        segments, info = model.transcribe(
            tmp_path,
            beam_size=5,
            language=None,                    # auto-detect language
            condition_on_previous_text=False
        )
        
        transcript = " ".join(segment.text for segment in segments).strip()

        if not transcript or len(transcript) < 5:
            return {"error": "No clear speech detected. Please speak louder and clearly."}

        # 2. Send to Groq for intelligent analysis
        user_prompt = f"""
        Question / Topic: {question or "General interview or public speaking response"}
        Transcript: {transcript}
        """

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
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
        # Cleanup temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ====================== HEALTH CHECK ENDPOINT ======================
@app.get("/")
async def root():
    return {
        "message": "Conversational Skill Mirror Backend is running successfully! 🎉",
        "status": "healthy",
        "version": "1.0.0"
    }


# ====================== RUN INSTRUCTIONS ======================
if __name__ == "__main__":
    print("\n🚀 Backend is ready!")
    print("Streamlit frontend can now connect to this backend.")
    print("Test the API at: http://127.0.0.1:8000/docs")
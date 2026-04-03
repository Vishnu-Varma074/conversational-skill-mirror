import streamlit as st
import requests

st.set_page_config(page_title="Skill Mirror", page_icon="🎤", layout="wide")
st.title("🎤 Conversational Skill Mirror")
st.markdown("**Interview & Public Speaking Coach** – Record → Analyze → Improve")

# Mode selection
mode = st.radio("Select Mode", ["Interview Practice", "Public Speaking"], horizontal=True)

if mode == "Interview Practice":
    placeholder = "Tell me about yourself / Why should we hire you?..."
    recommended = "Recommended: 45–120 seconds | Maximum supported: 4 minutes"
else:
    placeholder = "Give a short talk on any topic..."
    recommended = "Recommended: 60–180 seconds | Maximum supported: 4 minutes"

question = st.text_input("Practice Question / Topic (optional)", placeholder=placeholder)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎙️ Record your response")
    st.caption(f"💡 {recommended}\nLonger recordings take more time to analyze.")

    audio_input = st.audio_input("Click to record (speak clearly)")

    if st.button("📤 Analyze Speech", type="primary", use_container_width=True):
        if audio_input is None:
            st.error("❌ Please record audio first!")
        else:
            # Optional: Rough size check (4 min ≈ 15MB max)
            audio_size_mb = len(audio_input.getvalue()) / (1024 * 1024)
            if audio_size_mb > 20:
                st.warning("⚠️ Recording is quite long (>20 MB). Analysis may be slow.")

            with st.spinner("Transcribing + Analyzing with Groq... (up to 40 seconds for 4-min audio)"):
                try:
                    files = {"file": ("recording.wav", audio_input.getvalue(), "audio/wav")}
                    data = {"question": question}

                    response = requests.post(
                        "http://127.0.0.1:8000/analyze",
                        files=files,
                        data=data,
                        timeout=60   # Increased timeout for longer audio
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.result = result
                        st.success("✅ Analysis complete!")
                    else:
                        st.error(f"❌ Backend error {response.status_code}: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Backend is not running!\n\nStart it with:\n`uvicorn main:app --host 127.0.0.1 --port 8000`")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

# ====================== DISPLAY RESULTS ======================
if "result" in st.session_state:
    result = st.session_state.result

    if "error" in result:
        st.error(f"⚠️ {result['error']}")
    else:
        transcript = result.get("transcript", "No transcript available")
        analysis = result.get("analysis", {})

        st.subheader("📝 Original Transcript")
        st.write(transcript)

        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Fillers", analysis.get("filler_count", 0))
        c2.metric("Pace", f"{analysis.get('pace_wpm', 0)} WPM")
        c3.metric("Clarity", f"{analysis.get('clarity_score', 0)}/10")
        c4.metric("Topic Coverage", f"{analysis.get('topic_coverage', 0)}/10")

        st.subheader("💡 Feedback")
        st.write("**Cultural Nuance:**", analysis.get("cultural_nuance_feedback", "N/A"))

        tab1, tab2, tab3 = st.tabs(["✅ Strengths", "🔧 Improvements", "⚠️ Bias Check"])
        with tab1: 
            for x in analysis.get("strengths", ["N/A"]): st.write(f"• {x}")
        with tab2: 
            for x in analysis.get("improvement_areas", ["N/A"]): st.write(f"• {x}")
        with tab3:
            bias = analysis.get("bias_detected", [])
            if bias:
                st.write("\n".join([f"• {b}" for b in bias]))
            else:
                st.success("No bias detected ✅")

        st.subheader("🔥 Improved Response")
        st.write(analysis.get("improved_response", "N/A"))

        st.subheader("🚀 Confidence Tips")
        for tip in analysis.get("confidence_boosting_tips", []):
            st.write(f"• {tip}")

        st.subheader("🎭 Next Question Suggestion")
        st.write(analysis.get("role_play_continuation", "N/A"))

st.caption("Supports up to 4 minutes • Built with faster-whisper + Groq")
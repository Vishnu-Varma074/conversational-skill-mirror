import streamlit as st
import requests

st.set_page_config(page_title="Skill Mirror", page_icon="🎤", layout="wide")

st.title("🎤 Conversational Skill Mirror")
st.markdown("**AI Interview & Public Speaking Coach**")

mode = st.radio("Select Mode", ["Interview Practice", "Public Speaking"], horizontal=True)

if mode == "Interview Practice":
    placeholder = "Tell me about yourself..."
else:
    placeholder = "Talk about any topic..."

question = st.text_input("Practice Question / Topic (optional)", placeholder=placeholder)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎙️ Record your response")
    st.caption("💡 Tip: Keep recording under 60 seconds for better results.\nProcessing may take 1.5 - 2.5 minutes on free tier.")

    audio_input = st.audio_input("Click to record")

    if st.button("📤 Analyze Speech", type="primary", use_container_width=True):
        if audio_input is None:
            st.error("❌ Please record audio first!")
        else:
            with st.spinner("⏳ Analyzing your speech... This may take 1.5 to 2.5 minutes. Please be patient."):
                try:
                    files = {"file": ("recording.wav", audio_input.getvalue(), "audio/wav")}
                    data = {"question": question}

                    response = requests.post(
                        "https://conversational-skill-mirror-bu23.onrender.com/analyze",
                        files=files,
                        data=data,
                        timeout=180   # 3 minutes timeout
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.result = result
                        st.success("✅ Analysis complete!")
                    else:
                        st.error(f"❌ Backend returned error {response.status_code}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Please make sure backend is running.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

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

        st.subheader("🎭 Next Question")
        st.write(analysis.get("role_play_continuation", "N/A"))

st.caption("Built with faster-whisper + Groq | Processing time may vary on free tier")

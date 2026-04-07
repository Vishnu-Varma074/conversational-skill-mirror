import streamlit as st
import requests

st.set_page_config(page_title="Skill Mirror", page_icon="🎤", layout="wide")

st.title("🎤 Conversational Skill Mirror")
st.markdown("**AI-Powered Interview & Public Speaking Coach**")

st.caption("💡 Keep recordings under 60 seconds. Processing may take 1.5 - 2.5 minutes on free tier.")

mode = st.radio("Select Mode", ["Interview Practice", "Public Speaking"], horizontal=True)

placeholder = "Tell me about yourself..." if mode == "Interview Practice" else "Talk about any topic..."
question = st.text_input("Practice Question / Topic (optional)", placeholder=placeholder)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎙️ Record your response")
    audio_input = st.audio_input("Click to record")

    if st.button("📤 Analyze Speech", type="primary", use_container_width=True):
        if audio_input is None:
            st.error("❌ Please record audio first!")
        else:
            with st.spinner("⏳ Analyzing your speech... This may take 1.5 to 2.5 minutes. Please wait patiently."):
                try:
                    files = {"file": ("recording.wav", audio_input.getvalue(), "audio/wav")}
                    data = {"question": question}

                    response = requests.post(
                        "https://conversational-skill-mirror-bu23.onrender.com/analyze",
                        files=files,
                        data=data,
                        timeout=180
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.result = result
                        st.success("✅ Analysis complete!")
                    else:
                        st.error(f"❌ Backend error: {response.status_code} - {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Please check if backend is running.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

# ====================== SHOW RESULTS ======================
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

        tab1, tab2, tab3 = st.tabs(["✅ Strengths", "🔧 Improvement Areas", "⚠️ Bias Check"])
        with tab1:
            for item in analysis.get("strengths", ["No strengths recorded"]):
                st.write(f"• {item}")
        with tab2:
            for item in analysis.get("improvement_areas", ["No improvement areas recorded"]):
                st.write(f"• {item}")
        with tab3:
            bias = analysis.get("bias_detected", [])
            if bias:
                st.write("\n".join([f"• {b}" for b in bias]))
            else:
                st.success("No significant bias detected ✅")

        st.subheader("🔥 Improved Response")
        st.write(analysis.get("improved_response", "No improved response generated"))

        st.subheader("🚀 Confidence Boosting Tips")
        for tip in analysis.get("confidence_boosting_tips", []):
            st.write(f"• {tip}")

        st.subheader("🎭 Role-Play Continuation")
        st.write(analysis.get("role_play_continuation", "No continuation available"))

st.caption("Built with faster-whisper + Groq | Free tier - slow processing expected")

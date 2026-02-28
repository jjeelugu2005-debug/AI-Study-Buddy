import streamlit as st
from openai import OpenAI
import json
import re

# --- FREE MODEL DICTIONARY ---
# These are reliable, 100% free OpenRouter endpoints
FREE_MODELS = {"Gemini-2.0": "google/gemini-2.0-flash-001",
    "Liquid LFM 1.2B Thinking": "liquid/lfm-2.5-1.2b-thinking:free",
    "Liquid LFM 1.2B Instruct": "liquid/lfm-2.5-1.2b-instruct:free",
    
    "DeepSeek R1 Qwen3 8B (Reasoning)": "deepseek/deepseek-r1-qwen-8b:free",
    "Mistral Small 3.2 24B": "mistralai/mistral-small-3.2-24b-instruct:free",
    "Llama 3.3 8B Instruct": "meta-llama/llama-3.3-8b-instruct:free",
    "Gemma 3 12B": "google/gemma-3-12b-it:free",
    "Mistral Nemo": "mistralai/mistral-nemo:free",
    "Llama 4 Maverick": "meta-llama/llama-4-maverick:free",
    "Grok 4 Fast": "x-ai/grok-4-fast:free",
    "Kimi Dev 72B": "moonshotai/kimi-dev-72b:free",
    "DeepSeek Prover V2": "deepseek/deepseek-prover-v2:free",
    "LongCat Flash Chat": "meituan/longcat-flash-chat:free"
}
# --- API CONFIGURATION ---
# Replace with your actual OpenRouter API Key
import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
import json
import re

# Load environment variables from .env file
load_dotenv()

# Securely read API key
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if not openrouter_api_key:
    st.error("OpenRouter API key not found. Please set it in your .env file.")
    st.stop()

# Initialize OpenRouter Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
    default_headers={
        "HTTP-Referer": "http://localhost:8501", # Required by OpenRouter
        "X-Title": "AI Study Buddy App" # Recommended
    }
)
# --- PAGE SETUP ---
st.set_page_config(page_title="AI Study Buddy", page_icon="🎓", layout="wide")

st.title("🎓 AI Study Buddy")
st.caption("Powered by Free OpenRouter Models")

# --- SIDEBAR: MODEL SELECTION ---
st.sidebar.title("⚙️ Settings")
st.sidebar.write("Switch between AI models instantly:")

# Dropdown menu tied to the dictionary keys
selected_model_name = st.sidebar.selectbox("Choose a Free AI Model:", list(FREE_MODELS.keys()))
MODEL_ID = FREE_MODELS[selected_model_name]

st.sidebar.info(f"Currently using: `{MODEL_ID}`")

# --- INITIALIZE SESSION STATE (APP MEMORY) ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# --- UI LAYOUT: TABS ---
tab1, tab2, tab3 = st.tabs(["💬 AI Tutor Chat", "📝 Smart Summarizer", "🎯 Interactive Quiz"])

# --- TAB 1: AI TUTOR CHAT ---
with tab1:
    st.header("Chat with your AI Tutor")
    
    # Render chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if prompt := st.chat_input("What concept should we break down today?"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            sys_prompt = "You are a friendly, encouraging AI tutor. Explain this simply, suitable for a student: "
            
            # API Call
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": sys_prompt + prompt}]
            )
            
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

# --- TAB 2: SMART SUMMARIZER ---
with tab2:
    st.header("📝 Note Summarizer")
    notes = st.text_area("Paste your study notes here:", height=200)
    summary_style = st.selectbox("Summary Style", ["Bullet Points", "Short Paragraph"])
    
    if st.button("Summarize Now"):
        if notes:
            with st.spinner(f"Analyzing text with {selected_model_name}..."):
                style_instruction = "Use detailed bullet points." if summary_style == "Bullet Points" else "Write a dense, short paragraph."
                prompt = f"Extract the key points from these notes. {style_instruction}\n\n{notes}"
                
                # API Call
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.success("Summary Generated!")
                st.info(response.choices[0].message.content)
        else:
            st.warning("Please paste some notes first.")
# --- TAB 3: INTERACTIVE QUIZ ---
with tab3:
    st.header("🎯 Generate an Interactive Quiz")
    topic = st.text_input("Enter a topic for your quiz:")

    # Generate Quiz
    if st.button("Generate 3-Question Quiz"):
        if topic:
            with st.spinner(f"Crafting your custom quiz using {selected_model_name}..."):
                prompt = f"""
                Create a 3-question multiple-choice quiz about '{topic}'.
                Return ONLY a valid JSON array.
                Format:
                [
                  {{
                    "question": "Question?",
                    "options": ["A. Option1", "B. Option2", "C. Option3", "D. Option4"],
                    "answer": "A",
                    "explanation": "Why correct."
                  }}
                ]
                """

                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[{"role": "user", "content": prompt}]
                )

                raw_output = response.choices[0].message.content

                # Clean markdown wrapping
                clean_json = re.sub(r'```json\n?', '', raw_output)
                clean_json = re.sub(r'```\n?', '', clean_json).strip()

                try:
                    st.session_state.quiz_data = json.loads(clean_json)
                    st.session_state.quiz_submitted = False
                    st.session_state.user_answers = {}
                except:
                    st.error("Quiz formatting failed. Try another model.")
        else:
            st.warning("Please enter a topic.")

    # Display Quiz
    if st.session_state.quiz_data:
        st.divider()
        st.subheader("📝 Answer the Questions")

        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")

            selected = st.radio(
                "Choose one:",
                q["options"],
                key=f"question_{i}",
                index=None
            )

            st.session_state.user_answers[i] = selected
            st.write("")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Submit Answers"):
                st.session_state.quiz_submitted = True

        with col2:
            if st.button("Reset Quiz"):
                st.session_state.quiz_data = None
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = {}
                st.rerun()

        # Grade Section
        if st.session_state.quiz_submitted:
            st.divider()
            score = 0

            for i, q in enumerate(st.session_state.quiz_data):
                user_answer = st.session_state.user_answers.get(i)

                correct_letter = q["answer"].strip()

                # Match by first character (A/B/C/D)
                if user_answer and user_answer.startswith(correct_letter):
                    score += 1
                    st.success(f"Q{i+1}: Correct! {q['explanation']}")
                else:
                    st.error(
                        f"Q{i+1}: Incorrect. Correct answer: {correct_letter}\n\n{q['explanation']}"
                    )

            st.metric("Final Score", f"{score} / {len(st.session_state.quiz_data)}")

            if score == len(st.session_state.quiz_data):
                st.balloons()
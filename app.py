import os
import random
import streamlit as st
from anthropic import Anthropic
import time
import json

# --- API KEY ---

def load_dotenv(dotenv_path=".env"):
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
client = Anthropic(api_key=API_KEY) if API_KEY else None

# --- CONFIG ---
INTERESTS = ["Minecraft", "Soccer", "Chess", "Space Travel"]
SKILLS = ["Main Idea", "Inference", "Vocabulary in Context", "Author's Purpose", "Key Detail"]
DIFFICULTY_MAP = {
    1:  "very simple, 2nd grade reading level, short sentences",
    2:  "simple, 3rd grade reading level",
    3:  "3rd to 4th grade reading level",
    4:  "4th grade reading level",
    5:  "5th grade reading level, some complex sentences",
    6:  "6th grade reading level",
    7:  "6th to 7th grade reading level, varied sentence structure",
    8:  "7th grade reading level",
    9:  "7th to 8th grade reading level, complex vocabulary",
    10: "8th grade reading level, challenging vocabulary and structure"
}

# --- PAGE CONFIG ---
st.set_page_config(page_title="FUN ED", page_icon="⭐", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f7f2; }
    .passage-box {
        background-color: #ffffff;
        padding: 28px 32px;
        border: 1px solid #e0ddd5;
        border-radius: 12px;
        line-height: 1.9;
        font-size: 1.1em;
        color: #1a1a1a;
        margin-bottom: 20px;
    }
    .correct-box {
        background-color: #e8f5e9;
        border: 1px solid #81c784;
        border-radius: 8px;
        padding: 16px 20px;
        color: #1b5e20;
        font-size: 1em;
        margin-top: 12px;
    }
    .wrong-box {
        background-color: #fdecea;
        border: 1px solid #e57373;
        border-radius: 8px;
        padding: 16px 20px;
        color: #7f0000;
        font-size: 1em;
        margin-top: 12px;
    }
    .diff-label {
        font-size: 0.8em;
        color: #888;
        margin-bottom: 4px;
    }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

if client is None:
    st.error("Missing Anthropic API key. Set ANTHROPIC_API_KEY or CLAUDE_API_KEY in your environment, or add it to a .env file.")
    st.stop()

# --- SESSION STATE ---
if "difficulty" not in st.session_state:
    st.session_state.difficulty = 5
if "correct" not in st.session_state:
    st.session_state.correct = 0
if "total" not in st.session_state:
    st.session_state.total = 0
if "question_data" not in st.session_state:
    st.session_state.question_data = None
if "answered" not in st.session_state:
    st.session_state.answered = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "interests" not in st.session_state:
    st.session_state.interests = []
if "skill_index" not in st.session_state:
    st.session_state.skill_index = 0
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "started" not in st.session_state:
    st.session_state.started = False
if "error_message" not in st.session_state:
    st.session_state.error_message = ""

# --- PROMPT ENGINE ---
def build_prompt(interest, skill, difficulty, question_number):
    level_desc = DIFFICULTY_MAP[difficulty]
    if question_number in [1, 4, 7, 10]:
        topic_instruction = f"Use the student's interest ({interest}) as the passage topic."
        topic_description = f"Interest theme: {interest}"
    elif question_number in [2, 5, 8]:
        topic_instruction = "Use a neutral real-world topic such as science, nature, or history. No pop culture."
        topic_description = "Interest theme: neutral real-world topic (science, nature, history)"
    else:
        topic_instruction = "Write in a formal academic STAR test style with a dry, objective tone and no pop culture."
        topic_description = "Interest theme: formal academic real-world topic"

    return f"""You are a Renaissance STAR Reading exam generator for a 6th grade student named Ediz.

Generate a reading passage and ONE multiple choice question.

Question number: {question_number}
{topic_description}
Reading level: {level_desc}
Skill being tested: {skill}

PASSAGE TYPE RULE – follow this exactly:
- Look at the question number provided: {question_number}
- If question_number is 1, 4, 7, 10: use the student's interest ({interest})
- If question_number is 2, 5, 8: use a neutral real-world topic (science, nature, history)
- If question_number is 3, 6, 9: write in formal academic STAR test style — dry, objective tone, no pop culture
- Never use the student's interest two questions in a row.

Instructions:
- {topic_instruction}
- Write a passage of 80 to 120 words.
- Use language appropriate for the difficulty level.
- Ask ONE question that tests exactly one STAR skill type.
- Use one of these skill-specific question stems based on the selected skill:
  - Main Idea: "What is the main idea of this passage?"
  - Inference: "What can the reader conclude from this passage?" or "What does this suggest?"
  - Vocabulary in Context: "As used in the passage, the word [X] most nearly means..."
  - Author's Purpose: "Why did the author most likely write this passage?"
  - Key Detail: "According to the passage, what..."
- Provide exactly 4 answer choices labeled A, B, C, D.
- Only one choice may be correct.
- Wrong answer choices must be plausible but clearly wrong on careful reading — not obviously silly.
- Include a brief explanation referencing the passage.

Keep the existing JSON output format exactly as is.

Respond ONLY in this exact JSON format, no markdown, no extra text:
{{
  "passage": "...",
  "question": "...",
  "choices": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "answer": "A",
  "explanation": "...",
  "skill": "{skill}"
}}"""

# --- API CALL ---
MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"]

def extract_json_object(text):
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None
        return None


def extract_text_from_message(message):
    if not hasattr(message, "content") or not message.content:
        return ""
    parts = []
    for block in message.content:
        if hasattr(block, "text"):
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts).strip()


def generate_question(interest, skill, difficulty, question_number):
    if client is None:
        return None

    prompt = build_prompt(interest, skill, difficulty, question_number)
    for model_name in MODELS:
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model=model_name,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                raw = extract_text_from_message(response)
                data = extract_json_object(raw)
                if data:
                    return data
            except json.JSONDecodeError:
                return None
            except Exception:
                time.sleep((attempt + 1) * 2)
    return None


def load_new_question(interest, skill):
    if st.session_state.question_count >= 10:
        return False
    question_number = st.session_state.question_count + 1
    data = generate_question(interest, skill, st.session_state.difficulty, question_number)
    if data:
        st.session_state.question_data = data
        st.session_state.question_count += 1
        st.session_state.skill_index = (st.session_state.skill_index + 1) % len(SKILLS)
        return True
    return False

if not st.session_state.started:
    st.markdown("# ⭐ FUN ED")
    st.markdown("*Ediz's adventure-filled learning world*")
    st.write("---")
    st.markdown("### What do you like?")
    with st.form("onboarding_form"):
        likes = {
            "Minecraft": st.checkbox("Minecraft", key="interest_minecraft"),
            "Soccer": st.checkbox("Soccer", key="interest_soccer"),
            "Chess": st.checkbox("Chess", key="interest_chess"),
            "Space Travel": st.checkbox("Space Travel", key="interest_space_travel"),
            "Animals": st.checkbox("Animals", key="interest_animals"),
            "Gaming": st.checkbox("Gaming", key="interest_gaming"),
        }
        start_pressed = st.form_submit_button("Let's Go!", use_container_width=True)

    if start_pressed:
        selected = [name for name, value in likes.items() if value]
        if selected:
            st.session_state.interests = selected
            st.session_state.skill_index = 0
            st.session_state.question_data = None
            st.session_state.answered = False
            st.session_state.last_result = None
            st.session_state.show_results = False
            st.session_state.question_count = 0
            st.session_state.error_message = ""
            with st.spinner("Generating your first question..."):
                selected_interest = random.choice(st.session_state.interests)
                selected_skill = SKILLS[st.session_state.skill_index]
                if load_new_question(selected_interest, selected_skill):
                    st.session_state.started = True
                    st.rerun()
                else:
                    st.session_state.error_message = "Could not generate a question. Please try again."
        else:
            st.warning("Choose at least one interest to continue.")

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    st.stop()

# --- ADAPTIVE ENGINE ---
def update_difficulty(correct):
    if correct:
        st.session_state.difficulty = min(10, st.session_state.difficulty + 1)
    else:
        st.session_state.difficulty = max(1, st.session_state.difficulty - 1)

# --- UI ---
st.markdown("# ⭐ FUN ED")
st.markdown("*Ediz's adventure-filled learning world*")
st.write("---")

col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown("### Settings")
    st.write("")
    st.markdown("<div class='diff-label'>Difficulty Level</div>", unsafe_allow_html=True)
    st.progress(st.session_state.difficulty / 10)
    st.markdown(f"**Level {st.session_state.difficulty}/10**")
    st.write("")
    st.markdown(f"**Score:** {st.session_state.correct} / {st.session_state.total}")
    st.write("")

    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.difficulty = 5
        st.session_state.correct = 0
        st.session_state.total = 0
        st.session_state.question_count = 0
        st.session_state.question_data = None
        st.session_state.answered = False
        st.session_state.last_result = None
        st.session_state.show_results = False
        st.session_state.interests = []
        st.session_state.started = False

with col2:
    if st.session_state.show_results:
        score = st.session_state.correct
        if score == 10:
            stars = 5
        elif score >= 9:
            stars = 4
        elif score >= 7:
            stars = 3
        elif score >= 5:
            stars = 2
        else:
            stars = 1
        st.markdown("### Great job! You completed 10 questions!")
        st.markdown(f"**You got {score} out of 10!**")
        st.markdown(f"**You reached Level {st.session_state.difficulty}!**")
        st.markdown("**Rating:** " + "⭐" * stars)
        if st.button("Play Again", use_container_width=True):
            st.session_state.correct = 0
            st.session_state.total = 0
            st.session_state.difficulty = 5
            st.session_state.question_count = 0
            st.session_state.question_data = None
            st.session_state.answered = False
            st.session_state.last_result = None
            st.session_state.show_results = False
            st.session_state.skill_index = 0
            st.session_state.started = True
            selected_interest = random.choice(st.session_state.interests)
            selected_skill = SKILLS[st.session_state.skill_index]
            if load_new_question(selected_interest, selected_skill):
                st.rerun()
            else:
                st.error("Could not generate question. Try again.")
    elif st.session_state.question_data:
        q = st.session_state.question_data

        st.markdown(f"<div class='passage-box'>{q['passage']}</div>", unsafe_allow_html=True)
        st.markdown(f"**{q['question']}**")
        st.write("")

        for letter in ["A", "B", "C", "D"]:
            label = f"{letter}. {q['choices'][letter]}"
            if not st.session_state.answered:
                if st.button(label, key=f"choice_{letter}", use_container_width=True):
                    st.session_state.answered = True
                    st.session_state.total += 1
                    if letter == q["answer"]:
                        st.session_state.correct += 1
                        update_difficulty(True)
                        st.session_state.last_result = ("correct", letter, q)
                    else:
                        update_difficulty(False)
                        st.session_state.last_result = ("wrong", letter, q)
                    st.rerun()

        if st.session_state.answered:
            if st.button("Next Question", use_container_width=True):
                if st.session_state.question_count >= 10:
                    st.session_state.show_results = True
                    st.session_state.question_data = None
                    st.session_state.answered = False
                    st.session_state.last_result = None
                    st.rerun()
                else:
                    st.session_state.question_data = None
                    st.session_state.answered = False
                    st.session_state.last_result = None
                    with st.spinner("Loading the next question..."):
                        selected_interest = random.choice(st.session_state.interests)
                        selected_skill = SKILLS[st.session_state.skill_index]
                        if load_new_question(selected_interest, selected_skill):
                            st.rerun()
                        else:
                            st.error("Could not generate question. Try again.")

        if st.session_state.last_result:
            result, chosen, q = st.session_state.last_result
            if result == "correct":
                st.markdown(f"<div class='correct-box'>✅ Correct! {q['explanation']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='wrong-box'>❌ Not quite. Correct answer: {q['answer']}. {q['explanation']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("### 👈 Pick your interests and click Let's Go to start")
        st.markdown("Passages will be written around Ediz's interests at the right difficulty level.")

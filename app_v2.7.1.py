import os
import random
import streamlit as st
from anthropic import Anthropic
import time
import json
import traceback

# --- VERSION ---
VERSION = "2.7"  # May 6, 2026 - Session selector (Reading/Math), continuous save, View Report button

# --- PROGRESS FILE ---
PROGRESS_FILE = "session_progress.json"

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
API_KEY = (
    os.getenv("ANTHROPIC_API_KEY")
    or os.getenv("CLAUDE_API_KEY")
    or st.secrets.get("ANTHROPIC_API_KEY")
    or st.secrets.get("CLAUDE_API_KEY")
)
client = Anthropic(api_key=API_KEY) if API_KEY else None

# --- CONFIG ---
INTERESTS = ["Minecraft", "Soccer", "Chess", "Space Travel"]

ELA_DOMAINS = {
    "Reading Comprehension": 4,
    "Vocabulary in Context": 4,
    "Literary Analysis": 4,
    "Text Structure": 4,
    "Argument & Evidence": 4,
}

MATH_DOMAINS = {
    "Ratios & Proportions": 4,
    "Fractions & Decimals": 4,
    "Expressions & Equations": 4,
    "Geometry": 4,
    "Statistics & Data": 4,
}

ALL_DOMAINS = list(ELA_DOMAINS.keys()) + list(MATH_DOMAINS.keys())

TOTAL_QUESTIONS = 20

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

# --- PROGRESS PERSISTENCE ---
def save_progress_snapshot():
    data = {
        "student_name": st.session_state.get("student_name", ""),
        "session_mode": st.session_state.get("session_mode", ""),
        "interests": st.session_state.get("interests", []),
        "question_count": st.session_state.get("question_count", 0),
        "correct": st.session_state.get("correct", 0),
        "total": st.session_state.get("total", 0),
        "correct_ela": st.session_state.get("correct_ela", 0),
        "total_ela": st.session_state.get("total_ela", 0),
        "correct_math": st.session_state.get("correct_math", 0),
        "total_math": st.session_state.get("total_math", 0),
        "domain_correct": st.session_state.get("domain_correct", {}),
        "domain_total": st.session_state.get("domain_total", {}),
        "difficulty": st.session_state.get("difficulty", 3),
        "max_difficulty_ela": st.session_state.get("max_difficulty_ela", 3),
        "max_difficulty_math": st.session_state.get("max_difficulty_math", 3),
        "session_start_time": st.session_state.get("session_start_time"),
    }
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def load_progress_snapshot():
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def clear_progress_snapshot():
    try:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
    except Exception:
        pass


def restore_snapshot_to_state(snap):
    st.session_state.student_name = snap.get("student_name", "")
    st.session_state.session_mode = snap.get("session_mode", "")
    st.session_state.interests = snap.get("interests", [])
    st.session_state.question_count = snap.get("question_count", 0)
    st.session_state.correct = snap.get("correct", 0)
    st.session_state.total = snap.get("total", 0)
    st.session_state.correct_ela = snap.get("correct_ela", 0)
    st.session_state.total_ela = snap.get("total_ela", 0)
    st.session_state.correct_math = snap.get("correct_math", 0)
    st.session_state.total_math = snap.get("total_math", 0)
    st.session_state.domain_correct = snap.get("domain_correct", {d: 0 for d in ALL_DOMAINS})
    st.session_state.domain_total = snap.get("domain_total", {d: 0 for d in ALL_DOMAINS})
    st.session_state.difficulty = snap.get("difficulty", 3)
    st.session_state.max_difficulty_ela = snap.get("max_difficulty_ela", 3)
    st.session_state.max_difficulty_math = snap.get("max_difficulty_math", 3)
    st.session_state.session_start_time = snap.get("session_start_time")


# --- SESSION STATE ---
if "difficulty" not in st.session_state:
    st.session_state.difficulty = 3
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
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "pronoun" not in st.session_state:
    st.session_state.pronoun = ""
if "session_mode" not in st.session_state:
    st.session_state.session_mode = ""  # "ELA" or "Math"
if "dismissed_snapshot" not in st.session_state:
    st.session_state.dismissed_snapshot = False

if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = None


def generate_question_sequence(mode="ELA"):
    seq = []
    if mode == "ELA":
        for domain, count in ELA_DOMAINS.items():
            seq.extend([{"subject": "ELA", "domain": domain}] * count)
    else:  # Math
        for domain, count in MATH_DOMAINS.items():
            seq.extend([{"subject": "Math", "domain": domain}] * count)
    random.shuffle(seq)
    return seq


if "question_type_sequence" not in st.session_state:
    st.session_state.question_type_sequence = generate_question_sequence("ELA")
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "started" not in st.session_state:
    st.session_state.started = False
if "error_message" not in st.session_state:
    st.session_state.error_message = ""

# Stats by subject
if "correct_ela" not in st.session_state:
    st.session_state.correct_ela = 0
if "total_ela" not in st.session_state:
    st.session_state.total_ela = 0
if "time_ela" not in st.session_state:
    st.session_state.time_ela = 0.0
if "correct_math" not in st.session_state:
    st.session_state.correct_math = 0
if "total_math" not in st.session_state:
    st.session_state.total_math = 0
if "time_math" not in st.session_state:
    st.session_state.time_math = 0.0

# Current question metadata
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None
if "current_subject" not in st.session_state:
    st.session_state.current_subject = None
if "current_domain" not in st.session_state:
    st.session_state.current_domain = None

# Max difficulty reached per subject
if "max_difficulty_ela" not in st.session_state:
    st.session_state.max_difficulty_ela = 3
if "max_difficulty_math" not in st.session_state:
    st.session_state.max_difficulty_math = 3

# Track used topics to avoid repetition
if "used_topics" not in st.session_state:
    st.session_state.used_topics = []

# Domain-level tracking
if "domain_correct" not in st.session_state:
    st.session_state.domain_correct = {d: 0 for d in ALL_DOMAINS}
if "domain_total" not in st.session_state:
    st.session_state.domain_total = {d: 0 for d in ALL_DOMAINS}

# --- PROMPT ENGINE ---
def build_reading_prompt(interest, difficulty, domain, student_name="", pronoun=""):
    level_desc = DIFFICULTY_MAP[difficulty]
    correct_answer = random.choice(["A", "B", "C", "D"])

    if difficulty <= 2:
        word_count = "60 to 80 words"
        sentence_complexity = "Use short, simple sentences (5-10 words each)."
    elif difficulty <= 4:
        word_count = "80 to 100 words"
        sentence_complexity = "Use mostly simple sentences with occasional compound sentences."
    elif difficulty <= 6:
        word_count = "100 to 130 words"
        sentence_complexity = "Mix simple and compound sentences. Introduce some complex sentences."
    elif difficulty <= 8:
        word_count = "130 to 160 words"
        sentence_complexity = "Use varied sentence structures including complex sentences with multiple clauses."
    else:
        word_count = "160 to 200 words"
        sentence_complexity = "Use sophisticated sentence structures with embedded clauses and varied syntax."

    used_topics = st.session_state.get("used_topics", [])[-6:]
    if used_topics:
        topic_restriction = f"\n\n**TOPIC RESTRICTION:** Do NOT use: {', '.join(used_topics)}. Choose a different topic."
    else:
        topic_restriction = ""

    domain_guidance = {
        "Reading Comprehension": (
            "Focus: reading comprehension\n"
            "- Write a passage with clear events, setting, and characters\n"
            "- Question tests understanding of what happened, why, or what it means\n"
            "- Use inference stems: 'most likely', 'best supported by', 'primarily suggests'\n"
            "- Wrong answers: plausible misreadings, partial truths, or reversed logic"
        ),
        "Vocabulary in Context": (
            "Focus: vocabulary in context\n"
            "- Choose 1-2 challenging words students can infer from context clues\n"
            "- Question: 'As used in the passage, the word ___ most nearly means...'\n"
            "- Correct answer: meaning derived from context, NOT dictionary definition\n"
            "- Wrong answers: other real meanings of the word that don't fit context"
        ),
        "Literary Analysis": (
            "Focus: literary analysis and character\n"
            "- Create a character who changes, faces conflict, or reveals traits through actions\n"
            "- Question: 'How does [character]'s behavior reveal...?' or 'What does [event] suggest about [character]?'\n"
            "- Use inference stems: 'most likely', 'primarily suggests', 'best supported by'\n"
            "- Wrong answers: reverses character logic, uses passage words with wrong meaning"
        ),
        "Text Structure": (
            "Focus: text structure and author's craft\n"
            "- Use a clear organizational structure: chronological, cause-effect, problem-solution, or compare-contrast\n"
            "- Include at least one figurative device: metaphor, simile, personification, or hyperbole\n"
            "- Question: 'How does the author organize the text?' or 'What does the phrase [X] suggest?'\n"
            "- Wrong answers: incorrect structure identification, or literal interpretation of figurative language"
        ),
        "Argument & Evidence": (
            "Focus: argument and evidence\n"
            "- Write a short argumentative passage with a clear claim and supporting evidence\n"
            "- Question: 'Which evidence best supports the claim?' or 'What weakens the argument?'\n"
            "- Correct answer: strongest/most relevant evidence\n"
            "- Wrong answers: irrelevant facts, contradictory evidence, off-topic details"
        ),
    }

    guidance = domain_guidance.get(domain, "Write a passage and ask a comprehension question.")

    name_instruction = f"The protagonist must be named {student_name} and use {pronoun} pronouns." if student_name else ""

    return f"""You are generating a 6th grade STAR Reading comprehension question.

Domain: {domain}
Difficulty: {level_desc}
Topic: Use {interest} as the real-world context for the passage. Make it engaging.{topic_restriction}
{name_instruction}

Passage requirements:
- Length: {word_count}
- {sentence_complexity}

Question requirements:
{guidance}

Answer requirements:
- The correct answer MUST be choice {correct_answer}
- Provide exactly 4 choices labeled A, B, C, D
- Only one is correct
- Wrong answers must be plausible, not obviously wrong

Vocabulary: include 3-5 challenging words with student-friendly definitions.

Return ONLY valid JSON, no extra text:
{{
  "passage": "...",
  "question": "...",
  "choices": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "answer": "{correct_answer}",
  "explanation": "...",
  "domain": "{domain}",
  "subject": "Reading",
  "topic": "2-4 word topic description",
  "vocabulary": [
    {{"word": "...", "definition": "..."}},
    {{"word": "...", "definition": "..."}}
  ]
}}

IMPORTANT: correct answer must be in choice {correct_answer}."""


def build_math_prompt(interest, difficulty, domain):
    level_desc = DIFFICULTY_MAP[difficulty]
    correct_answer = random.choice(["A", "B", "C", "D"])

    domain_guidance = {
        "Numbers & Operations / Fractions": "fractions, decimals, and operations with rational numbers",
        "Algebra / Expressions": "algebraic expressions, equations, and solving for unknowns",
        "Geometry & Measurement": "area, perimeter, volume, angles, or coordinate geometry",
        "Data Analysis": "reading graphs, calculating mean/median/mode/range, or interpreting data",
        "Ratios & Proportions": "ratios, proportions, percentages, and unit rates",
        "Fractions & Decimals": "fractions, decimals, and operations with rational numbers",
        "Expressions & Equations": "algebraic expressions, equations, and solving for unknowns",
        "Geometry": "area, perimeter, volume, angles, or coordinate geometry",
        "Statistics & Data": "reading graphs, calculating mean/median/mode/range, or interpreting data",
    }

    guidance = domain_guidance.get(domain, "general math problem")

    return f"""You are generating a 6th grade STAR Math word problem.

Domain: {domain}
Topic: {guidance}
Difficulty: {level_desc}
Context: Use {interest} as the real-world scenario.
The correct answer MUST be choice {correct_answer}.

Requirements:
- Write a word problem (2-4 sentences) using {interest} as context
- Test specifically: {guidance}
- All 4 answer choices must be plausible numbers (close to each other, no obviously wrong answers)
- Only choice {correct_answer} is correct
- Include step-by-step explanation

Return ONLY valid JSON, no extra text:
{{
  "passage": "word problem text here",
  "question": "What is the answer?",
  "choices": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "answer": "{correct_answer}",
  "explanation": "Step-by-step: ...",
  "domain": "{domain}",
  "subject": "Math",
  "topic": "{domain}",
  "vocabulary": []
}}

IMPORTANT: correct answer must be in choice {correct_answer}."""

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


def generate_question(interest, domain, subject, difficulty, question_number):
    if client is None:
        return None

    if subject == "Math":
        prompt = build_math_prompt(interest, difficulty, domain)
    else:
        student_name = st.session_state.get("student_name", "")
        pronoun = st.session_state.get("pronoun", "")
        prompt = build_reading_prompt(interest, difficulty, domain, student_name, pronoun)
    for model_name in MODELS:
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model=model_name,
                    max_tokens=1800,
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


def load_new_question(interest):
    if st.session_state.question_count >= TOTAL_QUESTIONS:
        return False
    question_number = st.session_state.question_count + 1

    item = st.session_state.question_type_sequence[st.session_state.question_count]
    subject = item["subject"]
    domain = item["domain"]

    try:
        data = generate_question(interest, domain, subject, st.session_state.difficulty, question_number)
    except Exception:
        return False
    if data:
        st.session_state.question_data = data
        st.session_state.question_count += 1
        st.session_state.current_subject = subject
        st.session_state.current_domain = domain
        st.session_state.question_start_time = time.time()
        if st.session_state.session_start_time is None:
            st.session_state.session_start_time = time.time()

        if "topic" in data and data["topic"]:
            if "used_topics" not in st.session_state:
                st.session_state.used_topics = []
            st.session_state.used_topics.append(data["topic"])

        return True
    return False


def reset_session_state(keep_profile=False):
    st.session_state.difficulty = 3
    st.session_state.correct = 0
    st.session_state.total = 0
    st.session_state.question_count = 0
    st.session_state.question_data = None
    st.session_state.answered = False
    st.session_state.last_result = None
    st.session_state.show_results = False
    st.session_state.session_start_time = None
    st.session_state.correct_ela = 0
    st.session_state.total_ela = 0
    st.session_state.time_ela = 0.0
    st.session_state.correct_math = 0
    st.session_state.total_math = 0
    st.session_state.time_math = 0.0
    st.session_state.question_start_time = None
    st.session_state.current_subject = None
    st.session_state.current_domain = None
    st.session_state.max_difficulty_ela = 3
    st.session_state.max_difficulty_math = 3
    st.session_state.used_topics = []
    st.session_state.domain_correct = {d: 0 for d in ALL_DOMAINS}
    st.session_state.domain_total = {d: 0 for d in ALL_DOMAINS}
    if not keep_profile:
        st.session_state.interests = []
        st.session_state.started = False
        st.session_state.student_name = ""
        st.session_state.pronoun = ""
        st.session_state.session_mode = ""
    clear_progress_snapshot()


# --- ONBOARDING ---
if not st.session_state.started:
    st.markdown("# ⭐ FUN ED")
    st.markdown("*Your adventure-filled learning world*")
    st.write("---")

    # Check for saved progress from a previous session
    snapshot = load_progress_snapshot()
    if snapshot and snapshot.get("question_count", 0) > 0 and not st.session_state.dismissed_snapshot:
        snap_name = snapshot.get("student_name", "Unknown")
        snap_q = snapshot.get("question_count", 0)
        snap_mode = snapshot.get("session_mode", "")
        mode_label = "📚 Reading" if snap_mode == "ELA" else "🔢 Math" if snap_mode == "Math" else ""
        st.info(f"📋 **Previous session found** — {snap_name}, {mode_label}, {snap_q}/{TOTAL_QUESTIONS} questions completed")
        col_snap_a, col_snap_b = st.columns(2)
        with col_snap_a:
            if st.button("📊 View Previous Report", use_container_width=True):
                restore_snapshot_to_state(snapshot)
                st.session_state.show_results = True
                st.session_state.started = True
                st.session_state.question_data = None
                st.session_state.answered = False
                st.session_state.last_result = None
                st.rerun()
        with col_snap_b:
            if st.button("🆕 Start New Session", use_container_width=True):
                st.session_state.dismissed_snapshot = True
                clear_progress_snapshot()
                st.rerun()
        st.stop()

    # If profile is filled, show session type selector (no extra flag needed)
    if st.session_state.student_name and st.session_state.interests:
        student_name = st.session_state.student_name
        st.markdown(f"### Hi {student_name}! Choose your session:")
        st.write("")
        col_ela, col_math = st.columns(2)
        with col_ela:
            st.markdown("#### 📚 Reading")
            st.markdown("20 questions — comprehension, vocabulary, literary analysis")
            if st.button("Start Reading Session", use_container_width=True, key="btn_ela"):
                st.session_state.session_mode = "ELA"
                st.session_state.question_type_sequence = generate_question_sequence("ELA")
                with st.spinner("Generating your first question..."):
                    selected_interest = random.choice(st.session_state.interests)
                    if load_new_question(selected_interest):
                        st.session_state.started = True
                        st.rerun()
                    else:
                        st.error("Could not generate a question. Please try again.")
        with col_math:
            st.markdown("#### 🔢 Math")
            st.markdown("20 questions — ratios, fractions, equations, geometry")
            if st.button("Start Math Session", use_container_width=True, key="btn_math"):
                st.session_state.session_mode = "Math"
                st.session_state.question_type_sequence = generate_question_sequence("Math")
                with st.spinner("Generating your first question..."):
                    selected_interest = random.choice(st.session_state.interests)
                    if load_new_question(selected_interest):
                        st.session_state.started = True
                        st.rerun()
                    else:
                        st.error("Could not generate a question. Please try again.")
        st.write("")
        if st.button("← Back", key="btn_back"):
            st.session_state.student_name = ""
            st.session_state.interests = []
            st.rerun()
        st.stop()

    # Onboarding form
    with st.form("onboarding_form"):
        st.markdown("### What's your name?")
        student_name_input = st.text_input("Name", placeholder="Enter your name", label_visibility="collapsed")
        st.write("")

        st.markdown("### I am a...")
        gender = st.radio("Gender", ["Boy", "Girl"], label_visibility="collapsed", horizontal=True)
        st.write("")

        st.markdown("### What do you like? (Choose up to 3)")
        likes = {
            "Minecraft": st.checkbox("Minecraft", key="interest_minecraft"),
            "Soccer": st.checkbox("Soccer", key="interest_soccer"),
            "Chess": st.checkbox("Chess", key="interest_chess"),
            "Space Travel": st.checkbox("Space Travel", key="interest_space_travel"),
            "Animals": st.checkbox("Animals", key="interest_animals"),
            "Gaming": st.checkbox("Gaming", key="interest_gaming"),
        }
        st.write("")
        start_pressed = st.form_submit_button("Next →", use_container_width=True)

    if start_pressed:
        selected = [name for name, value in likes.items() if value]

        if not student_name_input or student_name_input.strip() == "":
            st.error("Please enter your name!")
            st.stop()
        if not selected:
            st.error("Please select at least one interest!")
            st.stop()
        if len(selected) > 3:
            st.warning("⚠️ Please choose maximum 3 interests!")
            st.stop()

        st.session_state.student_name = student_name_input.strip()
        st.session_state.pronoun = "he/him" if gender == "Boy" else "she/her"
        st.session_state.interests = selected
        reset_session_state(keep_profile=True)
        st.rerun()

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    st.stop()

# --- ADAPTIVE ENGINE ---
def update_difficulty(correct, subject=None):
    if correct:
        st.session_state.difficulty = min(7, st.session_state.difficulty + 1)
    else:
        st.session_state.difficulty = max(3, st.session_state.difficulty - 1)

    if subject:
        current_diff = st.session_state.difficulty
        if subject == "ELA":
            st.session_state.max_difficulty_ela = max(
                st.session_state.max_difficulty_ela, current_diff
            )
        elif subject == "Math":
            st.session_state.max_difficulty_math = max(
                st.session_state.max_difficulty_math, current_diff
            )

# --- REPORT RENDERER ---
def render_report():
    score = st.session_state.correct
    total_answered = st.session_state.total
    is_partial = st.session_state.question_count < TOTAL_QUESTIONS

    score_pct = score / total_answered if total_answered > 0 else 0
    if score_pct >= 0.9:
        stars = 5
    elif score_pct >= 0.8:
        stars = 4
    elif score_pct >= 0.65:
        stars = 3
    elif score_pct >= 0.5:
        stars = 2
    else:
        stars = 1

    difficulty = st.session_state.difficulty
    if difficulty <= 2:
        grade_level = "2nd-3rd Grade"
        grade_emoji = "📗"
    elif difficulty <= 4:
        grade_level = "4th Grade"
        grade_emoji = "📘"
    elif difficulty <= 6:
        grade_level = "5th-6th Grade"
        grade_emoji = "📙"
    elif difficulty <= 8:
        grade_level = "7th Grade"
        grade_emoji = "📕"
    else:
        grade_level = "8th Grade"
        grade_emoji = "📚"

    student_name = st.session_state.get("student_name", "")
    session_mode = st.session_state.get("session_mode", "")

    if is_partial:
        if student_name:
            st.markdown(f"### 📊 {student_name}'s Progress Report")
        else:
            st.markdown("### 📊 Progress Report")
        st.markdown(f"*Session in progress — {st.session_state.question_count}/{TOTAL_QUESTIONS} questions completed*")
    else:
        if student_name:
            st.markdown(f"### Great job, {student_name}! Session Complete!")
        else:
            st.markdown("### Session Complete!")

    if st.session_state.session_start_time:
        total_elapsed = int(time.time() - st.session_state.session_start_time)
        mins, secs = divmod(total_elapsed, 60)
        st.markdown(f"**Time: {mins:02d}:{secs:02d}**")

    st.markdown(f"**Score: {score} / {total_answered}** ({score_pct*100:.0f}%)")
    st.write("")

    st.markdown(f"## {grade_emoji} Level: **{grade_level}**")
    st.markdown(f"*(Difficulty reached: Level {difficulty}/10)*")
    st.write("")
    st.markdown("**Rating:** " + "⭐" * stars)
    st.write("---")

    domain_correct = st.session_state.get("domain_correct", {})
    domain_total = st.session_state.get("domain_total", {})

    ela_correct = st.session_state.correct_ela
    ela_total = st.session_state.total_ela
    math_correct = st.session_state.correct_math
    math_total = st.session_state.total_math

    all_results = []

    if session_mode != "Math":
        ela_pct = f"{ela_correct/ela_total*100:.0f}%" if ela_total > 0 else "—"
        st.markdown(f"### 📚 ELA — {ela_correct}/{ela_total} ({ela_pct})")
        st.write("")
        for domain in ELA_DOMAINS:
            d_total = domain_total.get(domain, 0)
            d_correct = domain_correct.get(domain, 0)
            if d_total > 0:
                pct = d_correct / d_total
                label = "Needs Work" if pct < 0.5 else "Getting There" if pct < 0.75 else "Strong"
                st.markdown(f"**{domain}** — {d_correct}/{d_total} ({pct*100:.0f}%) _{label}_")
                st.progress(pct)
                all_results.append((domain, pct))
            else:
                st.markdown(f"**{domain}** — 0/0")
        st.write("")

    if session_mode != "ELA":
        math_pct = f"{math_correct/math_total*100:.0f}%" if math_total > 0 else "—"
        st.markdown(f"### 🔢 Math — {math_correct}/{math_total} ({math_pct})")
        st.write("")
        for domain in MATH_DOMAINS:
            d_total = domain_total.get(domain, 0)
            d_correct = domain_correct.get(domain, 0)
            if d_total > 0:
                pct = d_correct / d_total
                label = "Needs Work" if pct < 0.5 else "Getting There" if pct < 0.75 else "Strong"
                st.markdown(f"**{domain}** — {d_correct}/{d_total} ({pct*100:.0f}%) _{label}_")
                st.progress(pct)
                all_results.append((domain, pct))
            else:
                st.markdown(f"**{domain}** — 0/0")
        st.write("")

    if all_results:
        weakest = min(all_results, key=lambda x: x[1])
        if weakest[1] < 0.75:
            st.info(f"💪 **Focus Area:** {weakest[0]} ({weakest[1]*100:.0f}%)")

    st.write("")

    if is_partial:
        col_resume, col_new = st.columns(2)
        with col_resume:
            if st.button("▶️ Continue Session", use_container_width=True):
                st.session_state.show_results = False
                st.rerun()
        with col_new:
            if st.button("🆕 New Session", use_container_width=True):
                reset_session_state()
                st.rerun()
    else:
        if st.button("Play Again", use_container_width=True):
            reset_session_state(keep_profile=True)
            # session_mode cleared so mode selector shows (name/interests kept)
            st.session_state.session_mode = ""
            st.rerun()


# --- UI ---
st.markdown("# ⭐ FUN ED")
student_name = st.session_state.get("student_name", "")
session_mode = st.session_state.get("session_mode", "")
mode_label = "📚 Reading" if session_mode == "ELA" else "🔢 Math" if session_mode == "Math" else ""
if student_name:
    st.markdown(f"*{student_name}'s {mode_label} session*")
else:
    st.markdown(f"*{mode_label} session*")
st.write("---")

col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown("### Progress")
    st.write("")

    q_count = st.session_state.question_count
    st.markdown(f"**{q_count} / {TOTAL_QUESTIONS} questions**")
    st.progress(q_count / TOTAL_QUESTIONS if TOTAL_QUESTIONS > 0 else 0)
    st.write("")

    if st.session_state.session_start_time:
        elapsed = int(time.time() - st.session_state.session_start_time)
        mins, secs = divmod(elapsed, 60)
        st.markdown(f"**Time: {mins:02d}:{secs:02d}**")
        st.write("")

    st.markdown("<div class='diff-label'>Difficulty Level</div>", unsafe_allow_html=True)
    st.progress(st.session_state.difficulty / 10)
    st.markdown(f"**Level {st.session_state.difficulty}/10**")
    st.write("")
    st.markdown(f"**Score:** {st.session_state.correct} / {st.session_state.total}")
    st.write("")

    if not st.session_state.show_results:
        if st.session_state.total > 0:
            if st.button("📊 View Report", use_container_width=True):
                st.session_state.show_results = True
                st.session_state.question_data = None
                st.session_state.answered = False
                st.session_state.last_result = None
                st.rerun()
        if st.button("🔄 Reset Session", use_container_width=True):
            reset_session_state()
            st.rerun()

with col2:
    if st.session_state.show_results:
        render_report()
    elif st.session_state.question_data:
        q = st.session_state.question_data

        subject = st.session_state.current_subject or ""
        domain = st.session_state.current_domain or ""
        type_icon = "📚" if subject == "ELA" else "🔢"
        st.markdown(f"**{type_icon} {domain}** — Question {st.session_state.question_count}/{TOTAL_QUESTIONS}")
        st.write("")
        st.markdown(f"<div class='passage-box'>{q['passage']}</div>", unsafe_allow_html=True)

        if "vocabulary" in q and q["vocabulary"]:
            st.write("")
            with st.expander("📖 Vocabulary", expanded=False):
                for vocab_item in q["vocabulary"]:
                    if isinstance(vocab_item, dict):
                        word = vocab_item.get("word", "")
                        definition = vocab_item.get("definition", "")
                    else:
                        word = str(vocab_item)
                        definition = ""
                    if word and definition:
                        st.markdown(f"**{word}:** {definition}")

        st.write("")
        st.markdown(f"**{q['question']}**")
        st.write("")

        for letter in ["A", "B", "C", "D"]:
            label = f"{letter}. {q['choices'][letter]}"
            if not st.session_state.answered:
                if st.button(label, key=f"choice_{letter}", use_container_width=True):
                    st.session_state.answered = True
                    st.session_state.total += 1

                    elapsed_time = 0.0
                    if st.session_state.question_start_time:
                        elapsed_time = time.time() - st.session_state.question_start_time

                    subj = st.session_state.current_subject
                    dom = st.session_state.current_domain
                    is_correct = (letter == q["answer"])

                    if subj == "ELA":
                        st.session_state.total_ela += 1
                        st.session_state.time_ela += elapsed_time
                        if is_correct:
                            st.session_state.correct_ela += 1
                    elif subj == "Math":
                        st.session_state.total_math += 1
                        st.session_state.time_math += elapsed_time
                        if is_correct:
                            st.session_state.correct_math += 1

                    if dom and dom in st.session_state.domain_total:
                        st.session_state.domain_total[dom] += 1
                        if is_correct:
                            st.session_state.domain_correct[dom] += 1

                    if is_correct:
                        st.session_state.correct += 1
                        update_difficulty(True, subj)
                        st.session_state.last_result = ("correct", letter, q)
                    else:
                        update_difficulty(False, subj)
                        st.session_state.last_result = ("wrong", letter, q)

                    # Save progress after every answer
                    save_progress_snapshot()
                    st.rerun()

        if st.session_state.answered:
            if st.button("Next Question", use_container_width=True):
                if st.session_state.question_count >= TOTAL_QUESTIONS:
                    st.session_state.show_results = True
                    st.session_state.question_data = None
                    st.session_state.answered = False
                    st.session_state.last_result = None
                    st.rerun()
                else:
                    with st.spinner("Loading the next question..."):
                        selected_interest = random.choice(st.session_state.interests)
                        if load_new_question(selected_interest):
                            st.session_state.answered = False
                            st.session_state.last_result = None
                            st.rerun()
                        else:
                            st.error("Could not generate question. Please try again.")

        if st.session_state.last_result:
            result, chosen, q = st.session_state.last_result
            if result == "correct":
                st.markdown(f"<div class='correct-box'>✅ Correct! {q['explanation']}</div>", unsafe_allow_html=True)
            else:
                STRATEGY_TIPS = {
                    "Reading Comprehension":    "Check the first and last sentences of the passage.",
                    "Main Idea / Central Theme": "Check the first and last sentences of the passage.",
                    "Vocabulary in Context":    "Find the word in the passage and read the sentences around it.",
                    "Literary Analysis":        "Look for what the character does or says, not just thinks.",
                    "Text Structure":           "Look for signal words like 'because', 'however', 'first', 'finally'.",
                    "Argument & Evidence":      "Find the author's main claim first, then look for supporting details.",
                    "Ratios & Proportions":     "Read the problem twice before calculating.",
                    "Fractions & Decimals":     "Read the problem twice before calculating.",
                    "Expressions & Equations":  "Read the problem twice before calculating.",
                    "Geometry":                 "Read the problem twice before calculating.",
                    "Statistics & Data":        "Read the problem twice before calculating.",
                }
                current_domain = st.session_state.get("current_domain", "")
                tip = STRATEGY_TIPS.get(current_domain, "Read the question carefully before choosing an answer.")
                st.markdown(f"<div class='wrong-box'>❌ Not quite. Correct answer: {q['answer']}. {q['explanation']}<br><br>📌 <strong>Strategy tip:</strong> {tip}</div>", unsafe_allow_html=True)
    else:
        st.markdown("### 👈 Pick your interests and click Start Session to begin")
        st.markdown("Passages will be written around your interests at the right difficulty level.")

import os
import random
import streamlit as st
from anthropic import Anthropic
import time
import json
import traceback

# --- VERSION ---
VERSION = "1.6"  # April 26, 2026 - Replace emoji icons in onboarding form (Windows fix)

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
if not API_KEY:
    st.error("DEBUG: API_KEY is None or empty")
else:
    st.success(f"DEBUG: API_KEY found, length={len(API_KEY)}")

# --- CONFIG ---
INTERESTS = ["Minecraft", "Soccer", "Chess", "Space Travel"]

# Florida B.E.S.T. Standards for 6th Grade ELA
FLORIDA_BEST_STANDARDS = {
    "ELA.6.R.1.1": "Character Development & Plot - Analyze how characters develop and advance the plot",
    "ELA.6.R.1.2": "Thematic Development - Identify and analyze themes and central ideas",
    "ELA.6.R.2.1": "Text Structures - Analyze text structures and their effects on meaning",
    "ELA.6.R.2.4": "Argument Development - Evaluate arguments and claims in text",
    "ELA.6.R.3.1": "Figurative Language - Interpret and analyze figurative language and literary devices"
}

SKILLS = list(FLORIDA_BEST_STANDARDS.keys())
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
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "pronoun" not in st.session_state:
    st.session_state.pronoun = ""
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

# Question types
QUESTION_TYPES = ["STAR Reading", "Star Renaissance", "FunEd"]

# Stats by question type
if "correct_star_reading" not in st.session_state:
    st.session_state.correct_star_reading = 0
if "total_star_reading" not in st.session_state:
    st.session_state.total_star_reading = 0
if "time_star_reading" not in st.session_state:
    st.session_state.time_star_reading = 0.0

if "correct_star_renaissance" not in st.session_state:
    st.session_state.correct_star_renaissance = 0
if "total_star_renaissance" not in st.session_state:
    st.session_state.total_star_renaissance = 0
if "time_star_renaissance" not in st.session_state:
    st.session_state.time_star_renaissance = 0.0

if "correct_funed" not in st.session_state:
    st.session_state.correct_funed = 0
if "total_funed" not in st.session_state:
    st.session_state.total_funed = 0
if "time_funed" not in st.session_state:
    st.session_state.time_funed = 0.0

# Current question timing and type
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None
if "current_question_type" not in st.session_state:
    st.session_state.current_question_type = None

# Max difficulty reached per question type
if "max_difficulty_star_reading" not in st.session_state:
    st.session_state.max_difficulty_star_reading = 5
if "max_difficulty_star_renaissance" not in st.session_state:
    st.session_state.max_difficulty_star_renaissance = 5
if "max_difficulty_funed" not in st.session_state:
    st.session_state.max_difficulty_funed = 5

# Track used topics to avoid repetition
if "used_topics" not in st.session_state:
    st.session_state.used_topics = []

# Skill tracking — correct/total per skill
SKILL_NAMES = {
    "ELA.6.R.1.1": "Character Development",
    "ELA.6.R.1.2": "Central Theme",
    "ELA.6.R.2.1": "Text Structure",
    "ELA.6.R.2.4": "Argument & Evidence",
    "ELA.6.R.3.1": "Figurative Language",
}
if "skill_correct" not in st.session_state:
    st.session_state.skill_correct = {s: 0 for s in SKILL_NAMES}
if "skill_total" not in st.session_state:
    st.session_state.skill_total = {s: 0 for s in SKILL_NAMES}

# Focus skill for next session (weakest skill from previous session)
if "focus_skill" not in st.session_state:
    st.session_state.focus_skill = None

# --- PROMPT ENGINE ---
def build_prompt(interest, skill, difficulty, question_number, question_type="Star Renaissance", student_name="", pronoun=""):
    level_desc = DIFFICULTY_MAP[difficulty]
    standard_description = FLORIDA_BEST_STANDARDS[skill]

    # Passage length based on difficulty
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
    else:  # 9-10
        word_count = "160 to 200 words"
        sentence_complexity = "Use sophisticated sentence structures with embedded clauses, appositives, and varied syntax."

    # Determine prompt style based on question type
    if question_type == "STAR Reading":
        topic_instruction = "Write in a formal academic STAR test style with a dry, objective tone. Use real-world topics from science, history, nature, or social studies. No pop culture or student interests."
        topic_description = "Interest theme: formal academic real-world topic"
    elif question_type == "FunEd":
        topic_instruction = f"Always use the student's interest ({interest}) as the passage topic. Make it engaging, fun, and relevant to their interests while maintaining educational value."
        topic_description = f"Interest theme: {interest}"
    else:  # Star Renaissance (default)
        if question_number in [1, 4, 7, 10]:
            topic_instruction = f"Use the student's interest ({interest}) as the passage topic."
            topic_description = f"Interest theme: {interest}"
        elif question_number in [2, 5, 8]:
            topic_instruction = "Use a neutral real-world topic such as science, nature, or history. No pop culture."
            topic_description = "Interest theme: neutral real-world topic"
        else:
            topic_instruction = "Write in a formal academic style with an objective tone."
            topic_description = "Interest theme: formal academic topic"

    # Determine correct answer distribution to ensure balance
    # Pattern: A, B, C, D repeating (slightly more A and B to reach 10)
    answer_pattern = {
        1: "A", 2: "B", 3: "C", 4: "D",
        5: "A", 6: "B", 7: "C", 8: "D",
        9: "A", 10: "B"
    }
    correct_answer = answer_pattern.get(question_number, "A")

    # Get used topics to avoid repetition
    used_topics = st.session_state.get("used_topics", [])
    if used_topics:
        topic_restriction = f"\n\n**IMPORTANT - TOPIC RESTRICTION:**\nDo NOT use these topics that have already been used in this session:\n" + "\n".join([f"- {topic}" for topic in used_topics]) + "\n\nChoose a COMPLETELY DIFFERENT topic/subject/scenario. Be creative and vary the content significantly."
    else:
        topic_restriction = ""

    # Skill-specific guidance based on Florida B.E.S.T. Standards
    if skill == "ELA.6.R.1.1":
        skill_guidance = """
- Create a narrative passage with clear character(s) and plot events
- Show character development through actions, dialogue, thoughts, or interactions
- Question should ask about HOW characters develop or HOW they advance the plot
- Example stems: 'How does the character\'s action reveal their development?' 'What effect does [event] have on the plot?'"""
    elif skill == "ELA.6.R.1.2":
        skill_guidance = """
- Write a passage with a clear theme or central idea (e.g., perseverance, friendship, courage, discovery)
- Include evidence that develops this theme throughout
- Question should ask about the theme or central idea and how it develops
- Example stems: 'What is the central theme?' 'How does the author develop the theme of [X]?'"""
    elif skill == "ELA.6.R.2.1":
        skill_guidance = """
- Use a clear text structure (chronological, cause-effect, problem-solution, compare-contrast, descriptive)
- Make the structure purposeful and integral to meaning
- Question should ask about the structure and its effect
- Example stems: 'How does the author organize the information?' 'What is the effect of the [chronological/cause-effect] structure?'"""
    elif skill == "ELA.6.R.2.4":
        skill_guidance = """
- Present an argument or claim with supporting evidence
- Include reasoning that connects evidence to claim
- Question should evaluate the argument's strength, evidence quality, or reasoning
- Example stems: 'Which evidence best supports the author\'s claim?' 'What weakens the author\'s argument?'"""
    else:  # ELA.6.R.3.1
        skill_guidance = """
- Include figurative language (metaphor, simile, personification, hyperbole, idiom, symbolism, or allusion)
- Use it purposefully to enhance meaning, mood, or tone
- Question should ask about interpretation or effect of the figurative language
- Example stems: 'What does the metaphor [X] reveal?' 'The phrase \'[X]\' suggests that...' 'What effect does the personification create?'"""

    # FunEd questions require special advanced requirements
    if question_type == "FunEd":
        return f"""You are generating a FunEd reading comprehension question about {interest} for a 6th grade student.

**Florida B.E.S.T. Standard:** {skill}
**Standard Description:** {standard_description}

**PASSAGE REQUIREMENTS:**
- Length: {word_count}
- Reading level: {level_desc}
- {sentence_complexity}
- Topic: **{interest}** (Make it engaging, fun, and relevant to this interest){topic_restriction}
- **IMPORTANT: The protagonist must be named {student_name} and use {pronoun} pronouns throughout the passage.**
- **Character must face conflicting motivations** (not just one obstacle - internal conflict, tough choices, competing desires)
- **Answer cannot be found in a single sentence** — requires inference across multiple parts of the passage
- **No sentence should directly state the theme** — theme should emerge through events and character actions

**QUESTION REQUIREMENTS:**
{skill_guidance}
- **Use inference stems:** 'most likely', 'primarily serves to', 'best supported by', 'most strongly implies', 'suggests that'
- Ask **WHY** or **WHAT IT IMPLIES** — never ask what is explicitly stated
- Require students to connect multiple details to form conclusion

**ANSWER CHOICE REQUIREMENTS - CRITICAL:**
- Provide exactly 4 answer choices labeled A, B, C, D
- **The correct answer MUST be choice {correct_answer}** - Structure your choices so that {correct_answer} is the correct answer
- Only ONE choice is correct

**CORRECT ANSWER:**
- **Paraphrases the inference** using different words than the passage
- Never copies passage wording
- Demonstrates deep comprehension, not surface reading

**WRONG ANSWERS - Sophisticated Distractors:**
- **Wrong Answer Type 1:** Reverses the passage's logic but sounds plausible (opposite conclusion from same evidence)
- **Wrong Answer Type 2:** Uses passage vocabulary in the wrong context (familiar words, wrong meaning)
- **Wrong Answer Type 3:** Partially true but misses the central point (gets one detail right, but overall wrong)
- ALL wrong answers must be defensible at first glance but clearly wrong upon careful analysis
- Use actual details from the passage but with wrong interpretation

**Example for Understanding:**
Passage concept: "Alex loved coding but felt pressure from friends to play sports. He started skipping robotics club to practice with the team, but felt empty after each game."

GOOD QUESTION (inference, not explicit):
✓ "Alex's behavior most strongly implies that he..."

GOOD CORRECT ANSWER (inference + paraphrase):
✓ "...is sacrificing personal fulfillment for social acceptance"
  (Passage never says this directly - requires inference from "loved coding", "pressure from friends", "felt empty")

GOOD WRONG ANSWERS:
✓ Type 1 (reverses logic): "...discovered his true passion through his friends' encouragement"
✓ Type 2 (vocabulary misuse): "...became skilled at balancing his interests with team commitments"
✓ Type 3 (partial truth): "...enjoys spending time with his friends during practice"

**Vocabulary Requirements:**
- Identify 3-5 challenging vocabulary words from the passage
- Choose words that are:
  * Important for understanding the passage
  * Appropriate for 6th grade level (not too easy, not too hard)
  * Academic or literary terms that students should learn
- Provide student-friendly definitions (clear, concise, age-appropriate)

**Output Format:**
Respond ONLY in this exact JSON format, no markdown, no extra text:
{{
  "passage": "...",
  "question": "...",
  "choices": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "answer": "{correct_answer}",
  "explanation": "...",
  "skill": "{skill}",
  "topic": "brief 2-4 word description of passage topic (e.g., 'soccer tournament', 'minecraft adventure', 'chess competition')",
  "vocabulary": [
    {{"word": "hesitated", "definition": "paused before doing something because of nervousness or uncertainty"}},
    {{"word": "confident", "definition": "feeling sure about your abilities or that something will happen"}}
  ]
}}

IMPORTANT:
1. Make sure the correct answer is in choice {correct_answer}. The "answer" field in JSON must be "{correct_answer}".
2. Include a "topic" field with a brief description of the passage topic.
3. Include a "vocabulary" array with 3-5 words and their student-friendly definitions.
4. Passage must require inference - no single sentence should contain the full answer."""

    # Standard prompt for STAR Reading and Star Renaissance
    return f"""You are generating a Florida B.E.S.T. Standards-aligned reading comprehension question for a 6th grade student.

**Florida B.E.S.T. Standard:** {skill}
**Standard Description:** {standard_description}

**Passage Requirements:**
- Length: {word_count}
- Reading level: {level_desc}
- {sentence_complexity}
- {topic_instruction}{topic_restriction}
- **IMPORTANT: The protagonist must be named {student_name} and use {pronoun} pronouns throughout the passage.**

**Question Requirements:**
{skill_guidance}

**Answer Choice Requirements - CRITICAL:**
- Provide exactly 4 answer choices labeled A, B, C, D
- **The correct answer MUST be choice {correct_answer}** - Structure your choices so that {correct_answer} is the correct answer
- Only ONE choice is correct

**CORRECT ANSWER Requirements:**
- **DO NOT copy phrases word-for-word from the passage**
- **MUST paraphrase** - use different words/synonyms to express the same meaning
- Should demonstrate understanding, not just text matching
- Example: If passage says "The bird soared high above the clouds", correct answer could be "The bird flew at a great altitude" (NOT "The bird soared high above the clouds")

**WRONG ANSWERS Requirements:**
- ALL wrong answers must be:
  * Plausible and sophisticated - not obviously wrong
  * **Use actual details/facts FROM the passage** but in wrong context or with wrong interpretation
  * Similar in length and complexity to the correct answer
  * Defensible at first glance but wrong upon careful analysis
  * Based on misreading, partial understanding, or incorrect connections
- Avoid clearly silly, extreme, or absurd wrong answers
- Wrong answers should include passage vocabulary but with incorrect meaning
- Make students think critically to identify the correct answer

**Example Scenario:**
Passage: "Maya hesitated at the edge of the diving board, her hands trembling. She took a deep breath, remembered her coach's advice, and dove into the pool with confidence."

GOOD CORRECT ANSWER (paraphrased):
✓ "Maya overcame her initial fear and performed the dive successfully"
  (Does NOT copy "hesitated", "trembling", "dove" - uses "overcame initial fear" and "performed successfully")

GOOD WRONG ANSWERS (use passage details but wrong):
✓ "Maya decided not to dive because she was too nervous"
  (Uses "nervous" related to "trembling" but wrong outcome)
✓ "Maya's coach had to convince her to attempt the dive"
  (Mentions coach from passage but wrong - she remembered advice, not convinced)
✓ "Maya jumped without thinking about her technique"
  (Opposite of what happened - she DID think, "remembered coach's advice")

BAD WRONG ANSWERS (too obvious or silly):
✗ "Maya turned into a mermaid" (absurd)
✗ "There is no pool in the passage" (obviously false)
✗ "Maya is afraid of water forever" (extreme, unsupported)

**Vocabulary Requirements:**
- Identify 3-5 challenging vocabulary words from the passage
- Choose words that are:
  * Important for understanding the passage
  * Appropriate for 6th grade level (not too easy, not too hard)
  * Academic or literary terms that students should learn
- Provide student-friendly definitions (clear, concise, age-appropriate)

**Output Format:**
Respond ONLY in this exact JSON format, no markdown, no extra text:
{{
  "passage": "...",
  "question": "...",
  "choices": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "answer": "{correct_answer}",
  "explanation": "...",
  "skill": "{skill}",
  "topic": "brief 2-4 word description of passage topic (e.g., 'soccer tournament', 'space exploration', 'coral reefs')",
  "vocabulary": [
    {{"word": "example_word", "definition": "student-friendly definition here"}},
    {{"word": "another_word", "definition": "another clear definition"}}
  ]
}}

IMPORTANT:
1. Make sure the correct answer is in choice {correct_answer}. The "answer" field in JSON must be "{correct_answer}".
2. Include a "topic" field with a brief description of the main subject/topic of your passage.
3. Include a "vocabulary" array with 3-5 words and their student-friendly definitions."""

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


def generate_question(interest, skill, difficulty, question_number, question_type="Star Renaissance"):
    if client is None:
        st.write("ERROR: Anthropic client is None — API key missing or not loaded")
        return None

    # Get student name and pronoun from session state
    student_name = st.session_state.get("student_name", "")
    pronoun = st.session_state.get("pronoun", "")

    prompt = build_prompt(interest, skill, difficulty, question_number, question_type, student_name, pronoun)
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
                st.write(f"ERROR: JSON parse failed for model={model_name} attempt={attempt+1}, raw={raw[:200]}")
            except json.JSONDecodeError as e:
                st.write(f"FULL ERROR: {traceback.format_exc()}")
                return None
            except Exception as e:
                st.write(f"FULL ERROR: {traceback.format_exc()}")
                time.sleep((attempt + 1) * 2)
    st.write(f"ERROR: All models and attempts exhausted for question_type={question_type} difficulty={difficulty}")
    return None


def load_new_question(interest, skill):
    import traceback
    if st.session_state.question_count >= 10:
        return False
    question_number = st.session_state.question_count + 1

    # Determine question type based on question number AND difficulty level
    # If difficulty >= 7 (advanced): More FunEd questions (5 out of 10)
    # If difficulty < 7 (beginner/intermediate): Original pattern (4 FunEd, 3 STAR, 3 Renaissance)

    current_difficulty = st.session_state.difficulty

    if current_difficulty >= 7:
        # Advanced level: FunEd = 1,3,5,7,9 / STAR = 2,8 / Renaissance = 4,6,10
        if question_number in [1, 3, 5, 7, 9]:
            question_type = "FunEd"
        elif question_number in [2, 8]:
            question_type = "STAR Reading"
        else:  # 4, 6, 10
            question_type = "Star Renaissance"
    else:
        # Beginner/Intermediate: Original pattern FunEd = 1,4,7,10 / STAR = 2,5,8 / Renaissance = 3,6,9
        if question_number in [1, 4, 7, 10]:
            question_type = "FunEd"
        elif question_number in [2, 5, 8]:
            question_type = "STAR Reading"
        else:  # 3, 6, 9
            question_type = "Star Renaissance"

    # Weighted skill system: if focus_skill exists, use it for questions 2, 4, 6, 8
    selected_skill = skill
    if st.session_state.focus_skill and question_number in [2, 4, 6, 8]:
        selected_skill = st.session_state.focus_skill

    try:
        data = generate_question(interest, selected_skill, st.session_state.difficulty, question_number, question_type)
    except Exception as e:
        st.error(f"DEBUG ERROR: {str(e)}")
        return False
    if data:
        st.session_state.question_data = data
        st.session_state.question_count += 1
        st.session_state.current_question_type = question_type
        st.session_state.question_start_time = time.time()  # Start timing
        st.session_state.skill_index = (st.session_state.skill_index + 1) % len(SKILLS)

        # Track topic to avoid repetition
        if "topic" in data and data["topic"]:
            if "used_topics" not in st.session_state:
                st.session_state.used_topics = []
            st.session_state.used_topics.append(data["topic"])

        return True
    return False

if not st.session_state.started:
    st.markdown("# ⭐ FUN ED")
    st.markdown("*Your adventure-filled learning world*")
    st.write("---")

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
        start_pressed = st.form_submit_button("Let's Go!", use_container_width=True)

    if start_pressed:
        selected = [name for name, value in likes.items() if value]

        # Validation: Check if name is provided
        if not student_name_input or student_name_input.strip() == "":
            st.error("Please enter your name!")
            st.stop()

        # Validation: Check if interests are selected and not more than 3
        if not selected:
            st.error("Please select at least one interest!")
            st.stop()
        if len(selected) > 3:
            st.warning("⚠️ Please choose maximum 3 interests!")
            st.stop()

        # Store student name and pronoun
        st.session_state.student_name = student_name_input.strip()
        if gender == "Boy":
            st.session_state.pronoun = "he/him"
        else:  # Girl
            st.session_state.pronoun = "she/her"

        # Store interests
        if selected:
            st.session_state.interests = selected
            st.session_state.skill_index = 0
            st.session_state.question_data = None
            st.session_state.answered = False
            st.session_state.last_result = None
            st.session_state.show_results = False
            st.session_state.question_count = 0
            st.session_state.error_message = ""
            # Reset question type stats
            st.session_state.correct_star_reading = 0
            st.session_state.total_star_reading = 0
            st.session_state.time_star_reading = 0.0
            st.session_state.correct_star_renaissance = 0
            st.session_state.total_star_renaissance = 0
            st.session_state.time_star_renaissance = 0.0
            st.session_state.correct_funed = 0
            st.session_state.total_funed = 0
            st.session_state.time_funed = 0.0
            st.session_state.question_start_time = None
            st.session_state.current_question_type = None
            # Reset max difficulty per type
            st.session_state.max_difficulty_star_reading = 5
            st.session_state.max_difficulty_star_renaissance = 5
            st.session_state.max_difficulty_funed = 5
            # Reset used topics
            st.session_state.used_topics = []
            # Reset skill tracking
            st.session_state.skill_correct = {s: 0 for s in SKILL_NAMES}
            st.session_state.skill_total = {s: 0 for s in SKILL_NAMES}
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
def update_difficulty(correct, question_type=None):
    if correct:
        st.session_state.difficulty = min(10, st.session_state.difficulty + 1)
    else:
        st.session_state.difficulty = max(1, st.session_state.difficulty - 1)

    # Track max difficulty per question type
    if question_type:
        current_diff = st.session_state.difficulty
        if question_type == "STAR Reading":
            st.session_state.max_difficulty_star_reading = max(
                st.session_state.max_difficulty_star_reading, current_diff
            )
        elif question_type == "Star Renaissance":
            st.session_state.max_difficulty_star_renaissance = max(
                st.session_state.max_difficulty_star_renaissance, current_diff
            )
        elif question_type == "FunEd":
            st.session_state.max_difficulty_funed = max(
                st.session_state.max_difficulty_funed, current_diff
            )

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

    # Only show Reset Session button when NOT on results screen
    if not st.session_state.show_results:
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
            # Reset question type stats
            st.session_state.correct_star_reading = 0
            st.session_state.total_star_reading = 0
            st.session_state.time_star_reading = 0.0
            st.session_state.correct_star_renaissance = 0
            st.session_state.total_star_renaissance = 0
            st.session_state.time_star_renaissance = 0.0
            st.session_state.correct_funed = 0
            st.session_state.total_funed = 0
            st.session_state.time_funed = 0.0
            st.session_state.question_start_time = None
            st.session_state.current_question_type = None
            # Reset max difficulty per type
            st.session_state.max_difficulty_star_reading = 5
            st.session_state.max_difficulty_star_renaissance = 5
            st.session_state.max_difficulty_funed = 5
            # Reset used topics
            st.session_state.used_topics = []
            # Reset skill tracking
            st.session_state.skill_correct = {s: 0 for s in SKILL_NAMES}
            st.session_state.skill_total = {s: 0 for s in SKILL_NAMES}
            st.rerun()

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

        # Convert difficulty level to grade level
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
        else:  # 9-10
            grade_level = "8th Grade"
            grade_emoji = "📚"

        # Personalized greeting with student name
        student_name = st.session_state.get("student_name", "")
        if student_name:
            st.markdown(f"### Great job, {student_name}! You completed 10 questions!")
        else:
            st.markdown("### Great job! You completed 10 questions!")
        st.markdown(f"**Overall Score: {score} out of 10!**")
        st.write("")

        # Display reading level prominently
        st.markdown(f"## {grade_emoji} Your Reading Level: **{grade_level}**")
        st.markdown(f"*(Difficulty Level {difficulty}/10)*")
        st.write("")

        st.markdown("**Rating:** " + "⭐" * stars)

        # Display if this session focused on a specific skill
        if st.session_state.focus_skill:
            focus_skill_name = SKILL_NAMES.get(st.session_state.focus_skill, "Unknown")
            st.info(f"📌 **This session focused on:** {focus_skill_name}")

        st.write("---")

        # Calculate weakest skill for next session
        skill_correct = st.session_state.get("skill_correct", {})
        skill_total = st.session_state.get("skill_total", {})
        weakest_skill = None
        lowest_accuracy = 1.0  # Start at 100%

        for skill_code in SKILL_NAMES:
            total = skill_total.get(skill_code, 0)
            correct = skill_correct.get(skill_code, 0)
            if total > 0:
                accuracy = correct / total
                if accuracy < lowest_accuracy:
                    lowest_accuracy = accuracy
                    weakest_skill = skill_code

        # Set focus_skill for next session
        if weakest_skill:
            st.session_state.focus_skill = weakest_skill

        # Detailed stats by question type
        st.markdown("### Results by Question Type")
        st.write("")

        # FunEd stats
        # Determine which questions were FunEd based on difficulty
        if difficulty >= 7:
            funed_questions = "1, 3, 5, 7, 9"
            star_questions = "2, 8"
            renaissance_questions = "4, 6, 10"
        else:
            funed_questions = "1, 4, 7, 10"
            star_questions = "2, 5, 8"
            renaissance_questions = "3, 6, 9"

        st.markdown(f"**🎮 FunEd (Questions {funed_questions})**")
        funed_correct = st.session_state.correct_funed
        funed_total = st.session_state.total_funed
        funed_time = st.session_state.time_funed
        funed_max_diff = st.session_state.max_difficulty_funed
        if funed_total > 0:
            st.markdown(f"- Correct: {funed_correct} / {funed_total}")
            st.markdown(f"- Wrong: {funed_total - funed_correct}")
            st.markdown(f"- Total Time: {funed_time:.1f} seconds (Avg: {funed_time/funed_total:.1f}s per question)")
            st.markdown(f"- Max Difficulty Reached: Level {funed_max_diff}/10")
        else:
            st.markdown("- No questions answered")
        st.write("")

        # STAR Reading stats
        st.markdown(f"**📚 STAR Reading (Questions {star_questions})**")
        star_reading_correct = st.session_state.correct_star_reading
        star_reading_total = st.session_state.total_star_reading
        star_reading_time = st.session_state.time_star_reading
        star_reading_max_diff = st.session_state.max_difficulty_star_reading
        if star_reading_total > 0:
            st.markdown(f"- Correct: {star_reading_correct} / {star_reading_total}")
            st.markdown(f"- Wrong: {star_reading_total - star_reading_correct}")
            st.markdown(f"- Total Time: {star_reading_time:.1f} seconds (Avg: {star_reading_time/star_reading_total:.1f}s per question)")
            st.markdown(f"- Max Difficulty Reached: Level {star_reading_max_diff}/10")
        else:
            st.markdown("- No questions answered")
        st.write("")

        # Star Renaissance stats
        st.markdown(f"**🌟 Star Renaissance (Questions {renaissance_questions})**")
        star_renaissance_correct = st.session_state.correct_star_renaissance
        star_renaissance_total = st.session_state.total_star_renaissance
        star_renaissance_time = st.session_state.time_star_renaissance
        star_renaissance_max_diff = st.session_state.max_difficulty_star_renaissance
        if star_renaissance_total > 0:
            st.markdown(f"- Correct: {star_renaissance_correct} / {star_renaissance_total}")
            st.markdown(f"- Wrong: {star_renaissance_total - star_renaissance_correct}")
            st.markdown(f"- Total Time: {star_renaissance_time:.1f} seconds (Avg: {star_renaissance_time/star_renaissance_total:.1f}s per question)")
            st.markdown(f"- Max Difficulty Reached: Level {star_renaissance_max_diff}/10")
        else:
            st.markdown("- No questions answered")
        st.write("")

        # Comparative Analysis
        st.write("---")
        st.markdown("### 📊 Your Performance Analysis")
        st.write("")

        # Collect data for comparison
        types_data = []
        if star_reading_total > 0:
            types_data.append({
                "name": "STAR Reading",
                "icon": "📚",
                "accuracy": star_reading_correct / star_reading_total,
                "avg_time": star_reading_time / star_reading_total,
                "max_diff": star_reading_max_diff
            })
        if star_renaissance_total > 0:
            types_data.append({
                "name": "Star Renaissance",
                "icon": "🌟",
                "accuracy": star_renaissance_correct / star_renaissance_total,
                "avg_time": star_renaissance_time / star_renaissance_total,
                "max_diff": star_renaissance_max_diff
            })
        if funed_total > 0:
            types_data.append({
                "name": "FunEd",
                "icon": "🎮",
                "accuracy": funed_correct / funed_total,
                "avg_time": funed_time / funed_total,
                "max_diff": funed_max_diff
            })

        if len(types_data) >= 2:
            # Speed comparison
            fastest = min(types_data, key=lambda x: x["avg_time"])
            slowest = max(types_data, key=lambda x: x["avg_time"])
            if fastest != slowest:
                st.markdown(f"**⚡ Speed:** You're fastest at {fastest['icon']} **{fastest['name']}** questions! "
                           f"(Avg: {fastest['avg_time']:.1f}s vs {slowest['avg_time']:.1f}s for {slowest['icon']} {slowest['name']})")

            # Accuracy comparison
            most_accurate = max(types_data, key=lambda x: x["accuracy"])
            least_accurate = min(types_data, key=lambda x: x["accuracy"])
            if most_accurate != least_accurate:
                st.markdown(f"**🎯 Accuracy:** You have the highest accuracy in {most_accurate['icon']} **{most_accurate['name']}** questions! "
                           f"({most_accurate['accuracy']*100:.0f}% vs {least_accurate['accuracy']*100:.0f}% for {least_accurate['icon']} {least_accurate['name']})")

            # Difficulty comparison
            highest_diff = max(types_data, key=lambda x: x["max_diff"])
            lowest_diff = min(types_data, key=lambda x: x["max_diff"])
            if highest_diff != lowest_diff:
                st.markdown(f"**📈 Challenge Level:** You reached the highest difficulty level in {highest_diff['icon']} **{highest_diff['name']}** questions! "
                           f"(Level {highest_diff['max_diff']} vs Level {lowest_diff['max_diff']} for {lowest_diff['icon']} {lowest_diff['name']})")

            # Overall insights
            st.write("")
            if fastest == most_accurate:
                st.markdown(f"💡 **Insight:** You excel at {fastest['icon']} **{fastest['name']}** - both fast AND accurate! Keep it up!")
            elif slowest == most_accurate:
                st.markdown(f"💡 **Insight:** You take your time with {slowest['icon']} **{slowest['name']}**, and it pays off with great accuracy!")
            else:
                st.markdown(f"💡 **Insight:** You have a balanced approach - fast at {fastest['icon']} **{fastest['name']}** and accurate at {most_accurate['icon']} **{most_accurate['name']}**!")

        # --- SKILL BREAKDOWN ---
        st.write("---")
        st.markdown("### 🎯 Skills Breakdown")
        skill_correct = st.session_state.get("skill_correct", {})
        skill_total = st.session_state.get("skill_total", {})
        skill_results = []
        for code, name in SKILL_NAMES.items():
            total = skill_total.get(code, 0)
            correct = skill_correct.get(code, 0)
            if total > 0:
                pct = correct / total
                skill_results.append((name, correct, total, pct))

        if skill_results:
            skill_results.sort(key=lambda x: x[3])  # sort weakest first
            for name, correct, total, pct in skill_results:
                bar_color = "#e74c3c" if pct < 0.5 else "#f39c12" if pct < 0.75 else "#27ae60"
                label = "⚠️ Needs Work" if pct < 0.5 else "📈 Getting There" if pct < 0.75 else "✅ Strong"
                st.markdown(f"**{name}** — {correct}/{total} ({pct*100:.0f}%) {label}")
                st.progress(pct)

            # Weakest skill callout
            weakest = skill_results[0]
            if weakest[3] < 0.75:
                st.info(f"💪 **Focus Area:** Practice more **{weakest[0]}** questions next session!")

        st.write("")
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
            # Reset question type stats
            st.session_state.correct_star_reading = 0
            st.session_state.total_star_reading = 0
            st.session_state.time_star_reading = 0.0
            st.session_state.correct_star_renaissance = 0
            st.session_state.total_star_renaissance = 0
            st.session_state.time_star_renaissance = 0.0
            st.session_state.correct_funed = 0
            st.session_state.total_funed = 0
            st.session_state.time_funed = 0.0
            st.session_state.question_start_time = None
            st.session_state.current_question_type = None
            # Reset max difficulty per type
            st.session_state.max_difficulty_star_reading = 5
            st.session_state.max_difficulty_star_renaissance = 5
            st.session_state.max_difficulty_funed = 5
            # Reset used topics
            st.session_state.used_topics = []
            # Reset skill tracking
            st.session_state.skill_correct = {s: 0 for s in SKILL_NAMES}
            st.session_state.skill_total = {s: 0 for s in SKILL_NAMES}
            selected_interest = random.choice(st.session_state.interests)
            selected_skill = SKILLS[st.session_state.skill_index]
            if load_new_question(selected_interest, selected_skill):
                st.rerun()
            else:
                st.error("Could not generate question. Try again.")
    elif st.session_state.question_data:
        q = st.session_state.question_data

        # Show current question type
        qtype = st.session_state.current_question_type
        if qtype == "STAR Reading":
            type_icon = "📚"
        elif qtype == "Star Renaissance":
            type_icon = "🌟"
        else:  # FunEd
            type_icon = "🎮"

        st.markdown(f"**{type_icon} {qtype}** - Question {st.session_state.question_count}/10")
        st.write("")
        st.markdown(f"<div class='passage-box'>{q['passage']}</div>", unsafe_allow_html=True)

        # Display vocabulary if available
        if "vocabulary" in q and q["vocabulary"]:
            st.write("")
            with st.expander("📖 Vocabulary", expanded=False):
                for vocab_item in q["vocabulary"]:
                    word = vocab_item.get("word", "")
                    definition = vocab_item.get("definition", "")
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

                    # Calculate time spent on this question
                    elapsed_time = 0.0
                    if st.session_state.question_start_time:
                        elapsed_time = time.time() - st.session_state.question_start_time

                    # Update stats based on question type
                    qtype = st.session_state.current_question_type
                    is_correct = (letter == q["answer"])

                    if qtype == "STAR Reading":
                        st.session_state.total_star_reading += 1
                        st.session_state.time_star_reading += elapsed_time
                        if is_correct:
                            st.session_state.correct_star_reading += 1
                    elif qtype == "Star Renaissance":
                        st.session_state.total_star_renaissance += 1
                        st.session_state.time_star_renaissance += elapsed_time
                        if is_correct:
                            st.session_state.correct_star_renaissance += 1
                    elif qtype == "FunEd":
                        st.session_state.total_funed += 1
                        st.session_state.time_funed += elapsed_time
                        if is_correct:
                            st.session_state.correct_funed += 1

                    # Track skill performance
                    q_skill = q.get("skill", "")
                    if q_skill in st.session_state.skill_total:
                        st.session_state.skill_total[q_skill] += 1
                        if is_correct:
                            st.session_state.skill_correct[q_skill] += 1

                    if is_correct:
                        st.session_state.correct += 1
                        update_difficulty(True, qtype)
                        st.session_state.last_result = ("correct", letter, q)
                    else:
                        update_difficulty(False, qtype)
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
                    # Load new question FIRST, then clear state if successful
                    with st.spinner("Loading the next question..."):
                        selected_interest = random.choice(st.session_state.interests)
                        selected_skill = SKILLS[st.session_state.skill_index]
                        if load_new_question(selected_interest, selected_skill):
                            # Only clear state after successful load
                            st.session_state.answered = False
                            st.session_state.last_result = None
                            st.rerun()
                        else:
                            st.error("Could not generate question. Please try again.")
                            # Keep current question_data so user doesn't see onboarding

        if st.session_state.last_result:
            result, chosen, q = st.session_state.last_result
            if result == "correct":
                st.markdown(f"<div class='correct-box'>✅ Correct! {q['explanation']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='wrong-box'>❌ Not quite. Correct answer: {q['answer']}. {q['explanation']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("### 👈 Pick your interests and click Let's Go to start")
        st.markdown("Passages will be written around Ediz's interests at the right difficulty level.")

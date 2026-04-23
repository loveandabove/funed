# CLAUDE.md - Project Rules & Guidelines

## VERSIONING RULES

### Backup Protocol
- **NEVER modify app.py without creating a backup first**
- Backup format: `app_v[version].py`
- Always announce current version before starting work

### Version Numbering System
```
Minor change:    v1.0 → v1.1 → v1.2
Major feature:   v1.9 → v2.0
Hotfix:          v1.0 → v1.0.1
```

**Examples:**
- Adding a new session state variable: v1.0 → v1.1
- Completely new question type: v1.9 → v2.0
- Fixing a bug without new features: v1.0 → v1.0.1

### Backup Workflow
1. Announce current version: "Current version: v1.0"
2. Create backup: `cp app.py app_v1.0.py`
3. Update VERSION in app.py: `VERSION = "1.1"`
4. Make changes to app.py
5. Test and verify
6. Document changes in version history

---

## CURRENT STATE

**Main File:** `app.py`
**Version:** `1.0`
**Last Change:** April 20, 2026
**Status:** ✅ Production Ready

---

## VERSION HISTORY

### v1.0 - April 20, 2026
**Features Added:**
- Topic tracking system (prevents topic repetition in sessions)
- Advanced FunEd prompt requirements
- Conflicting motivations in passages
- Multi-layered inference questions
- Sophisticated distractor types (3 types)
- Topic restriction logic in prompt
- `used_topics` session state management

**Files:**
- app.py (main)
- app_v1.0.py (backup)

**Key Changes:**
- Added `VERSION = "1.0"` variable (line 9)
- Added `used_topics` session state (line 168-169)
- Modified `build_prompt()` with dual-path logic (lines 259-402)
- Modified `load_new_question()` for topic capture (lines 410-414)
- Updated 3 reset functions to clear used_topics (lines 463, 548, 736)

**Lines Modified:** ~100 lines

---

## PROJECT STRUCTURE

```
/Users/gadimitrani/Documents/PROJECTS AI/FUN_ED/
├── app.py                          # Main application (v1.0)
├── app_v1.0.py                     # Backup
├── CLAUDE.md                       # This file - project rules
├── Summary April 20 MSTR.md        # Documentation
├── Fun Ed April 17.md              # Historical docs
├── Fun Ed April 18.md              # Historical docs
├── .env                            # API keys (not tracked)
├── .gitignore                      # Git ignore rules
└── venv/                           # Virtual environment
```

---

## CODING STANDARDS

### Language Standards
- **Code:** English (variables, functions, comments)
- **User-facing text:** English
- **Documentation:** English

### Code Quality
- Use descriptive variable names
- Add comments for complex logic
- Keep functions focused and modular
- Follow existing code style

### Session State Management
- Always check if session state key exists before using
- Initialize all session state variables at startup
- Clear session state in all reset functions

### Prompt Engineering
- Provide explicit instructions to AI
- Include concrete examples
- Use structured checklists
- Specify output format precisely

---

## TESTING CHECKLIST

Before marking any version as complete:

**Functionality:**
- [ ] Application starts without errors
- [ ] All 10 questions generate successfully
- [ ] Topic tracking works (no repeats in session)
- [ ] All 3 reset functions clear session state properly
- [ ] Report screen displays correctly

**Question Types:**
- [ ] FunEd questions use student interests
- [ ] STAR Reading questions are formal
- [ ] Star Renaissance questions are mixed
- [ ] All questions align with Florida B.E.S.T. standards

**Data Integrity:**
- [ ] Time tracking accurate per question type
- [ ] Correct/wrong counts accurate
- [ ] Max difficulty tracking correct
- [ ] Topics properly captured and restricted

**UI/UX:**
- [ ] Onboarding screen works
- [ ] Questions display properly
- [ ] Answer buttons functional
- [ ] Next Question button works
- [ ] Report screen shows all stats

---

## DEPLOYMENT

**Local Testing:**
```bash
source venv/bin/activate
streamlit run app.py
```

**URLs:**
- Local: http://localhost:8505
- Network: http://192.168.5.208:8505

**Environment:**
- Python 3.x
- Streamlit
- Anthropic API (Claude)

---

## DOCUMENTATION STANDARDS

### When Creating Documentation
- Use markdown format
- Include code examples with line numbers
- Show before/after comparisons
- List benefits for all stakeholders
- Provide testing guidelines

### File Naming
- Documentation: `[Topic] [Date] [Type].md`
- Example: `Summary April 20 MSTR.md`
- Backups: `app_v[version].py`

---

## FLORIDA B.E.S.T. STANDARDS

The application tests these 6th grade ELA standards:

1. **ELA.6.R.1.1** - Character Development & Plot
2. **ELA.6.R.1.2** - Thematic Development
3. **ELA.6.R.2.1** - Text Structures
4. **ELA.6.R.2.4** - Argument Development
5. **ELA.6.R.3.1** - Figurative Language

---

## QUESTION TYPE STRUCTURE

**Distribution (10 questions):**
- Questions 1, 4, 7, 10: 🎮 FunEd (Advanced)
- Questions 2, 5, 8: 📚 STAR Reading (Standard)
- Questions 3, 6, 9: 🌟 Star Renaissance (Standard)

**FunEd Special Requirements:**
- Conflicting motivations
- Multi-layered inference
- No explicit theme
- 3 types of sophisticated distractors

---

## API CONFIGURATION

**Primary Model:** claude-sonnet-4-6
**Fallbacks:**
- claude-opus-4-6
- claude-sonnet-4-5-20250929
- claude-haiku-4-5-20251001

**API Keys:**
- Stored in `.env` file (not tracked in git)
- Variables: `ANTHROPIC_API_KEY` or `CLAUDE_API_KEY`

---

## SESSION STATE VARIABLES

### Core Variables
```python
difficulty: int               # Current difficulty (1-10)
correct: int                  # Total correct answers
total: int                    # Total questions answered
question_count: int           # Questions completed (0-10)
show_results: bool            # Show report screen
started: bool                 # Session started
interests: list               # Selected student interests
```

### Question Type Stats
```python
# Per type: star_reading, star_renaissance, funed
correct_[type]: int           # Correct count
total_[type]: int             # Total count
time_[type]: float            # Total time (seconds)
max_difficulty_[type]: int    # Max difficulty reached
```

### Tracking Variables
```python
used_topics: list             # Topics used in session
question_data: dict           # Current question data
answered: bool                # Current question answered
current_question_type: str    # Current type
question_start_time: float    # Timestamp
```

---

## COMMON TASKS

### Adding a New Feature
1. Check current version
2. Create backup
3. Increment version
4. Implement feature
5. Test thoroughly
6. Update CLAUDE.md
7. Create documentation

### Fixing a Bug
1. Check current version
2. Create backup
3. Increment patch version (v1.0 → v1.0.1)
4. Fix bug
5. Test fix
6. Update CLAUDE.md

### Modifying Prompts
1. Backup current version
2. Locate prompt in `build_prompt()` function
3. Test with multiple question types
4. Verify JSON output format
5. Check distractor quality

---

## IMPORTANT NOTES

### Do NOT modify without backup:
- ❌ app.py
- ❌ Any production file

### Always test:
- ✅ All 3 question types
- ✅ All 3 reset functions
- ✅ Topic tracking
- ✅ Report generation

### Keep consistent:
- ✅ Florida B.E.S.T. standards alignment
- ✅ Answer distribution pattern (A, B, C, D)
- ✅ Difficulty progression (1-10)
- ✅ Time tracking per type

---

## CONTACT & SUPPORT

**Project:** Fun Ed - Reading Comprehension App
**Student:** Ediz (6th Grade)
**Standards:** Florida B.E.S.T. ELA 6th Grade
**Created:** April 2026
**Current Version:** v1.0

---

*Last updated: April 20, 2026*
*By: Claude (Anthropic)*

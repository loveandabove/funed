# Fun Ed - Version History

This document tracks all versions of the Fun Ed reading comprehension application.

---

## v1.5 - English Dictionary/Vocabulary Feature
**Date:** April 23, 2026
**Git Commit:** 0af7f6a

### Changes:
- **Vocabulary Definitions:**
  - AI now identifies 3-5 challenging vocabulary words from each passage
  - Words selected are appropriate for 6th grade level
  - Student-friendly definitions provided for each word
  - Applied to ALL question types (FunEd, STAR Reading, Star Renaissance)
- **UI Enhancement:**
  - Added "📖 Vocabulary" expandable section below each passage
  - Collapsible expander (starts closed to not distract from question)
  - Clear word + definition format: "**word:** definition"
- **JSON Output Updated:**
  - Added "vocabulary" array to JSON format
  - Each entry contains "word" and "definition" fields
  - AI instructed to choose important, grade-appropriate academic terms

### Why:
- Build vocabulary while reading
- Help students understand challenging words in context
- Support comprehension by clarifying unfamiliar terms
- Teach academic vocabulary naturally through exposure
- Optional (expandable) so doesn't interfere with question flow

---

## v1.4 - Personalization Update
**Date:** April 23, 2026
**Git Commit:** fc6fddc

### Changes:
- **Onboarding Personalization:**
  - Added "What's your name?" text input field
  - Added gender selection with "Boy 👦" / "Girl 👧" radio buttons
  - Determines pronouns automatically (he/him or she/her)
  - Limited interest selection to maximum 3 with validation warning
- **Personalized Story Generation:**
  - All passage protagonists now named after the student
  - Correct pronouns used throughout all passages (he/him or she/her)
  - Applied to ALL question types: FunEd, STAR Reading, and Star Renaissance
- **Report Screen Enhancement:**
  - Personalized greeting: "Great job, {student_name}!" on completion
- **Session State Updates:**
  - Added student_name and pronoun storage
  - Passed to all prompt generation functions

### Why:
- Increase engagement through personalized content
- Students see themselves as the protagonist in every story
- Gender-affirming language throughout the experience
- Limit interest selection to prevent decision fatigue and improve story quality

---

## v1.3 - Difficulty-Based Question Distribution
**Date:** April 22, 2026
**Git Commit:** 14bbde2

### Changes:
- **Dynamic Question Type Distribution Based on Difficulty:**
  - When difficulty >= 7 (Advanced):
    - FunEd questions: 1, 3, 5, 7, 9 (5 questions - 50%)
    - STAR Reading: 2, 8 (2 questions - 20%)
    - Star Renaissance: 4, 6, 10 (3 questions - 30%)
  - When difficulty < 7 (Beginner/Intermediate):
    - FunEd questions: 1, 4, 7, 10 (4 questions - 40%)
    - STAR Reading: 2, 5, 8 (3 questions - 30%)
    - Star Renaissance: 3, 6, 9 (3 questions - 30%)
- **Report Screen Enhancement:** Dynamically displays which question numbers were which type based on difficulty level used

### Why:
- Increase student engagement during challenging content by providing more FunEd (engaging) questions
- Maintain balanced distribution at lower difficulty levels

---

## v1.2 - Weighted Skill System
**Date:** April 21, 2026

### Changes:
- **Adaptive Learning Algorithm:**
  - After each session ends, system analyzes skill_correct and skill_total data
  - Identifies weakest skill (lowest accuracy rate)
  - Stores weakest skill as "focus_skill" in session state
- **Automatic Skill Targeting:**
  - Questions 2, 4, 6, 8 automatically assigned to focus_skill (4 out of 10 questions = 40%)
  - Remaining questions rotate through other skills normally
- **Report Screen Enhancement:**
  - Displays "This session focused on: [skill name]" when focus_skill was active
  - Shows which skill will be targeted in next session

### Why:
- Personalized learning targeting student's weak areas
- Automatic remediation without manual intervention
- 40% focus on weak skill while maintaining 60% balanced practice

---

## v1.1 - Skill Tracking System
**Date:** April 21, 2026

### Changes:
- **Per-Skill Performance Tracking:**
  - Added skill_correct and skill_total dictionaries to session state
  - Tracks accuracy for each of 5 Florida B.E.S.T. standards independently
- **Enhanced Report Screen:**
  - Added "Skill Breakdown" section showing performance by skill
  - Displays correct/total and accuracy percentage for each skill
  - Color-coded skill names matching sidebar legend
- **Data Structure:**
  - skill_correct: {skill_code: correct_count}
  - skill_total: {skill_code: total_count}

### Why:
- Identify specific areas of strength and weakness
- Provide detailed feedback beyond overall score
- Foundation for adaptive learning features

---

## v1.0 - Topic Tracking & Advanced FunEd Prompts
**Date:** April 20, 2026

### Changes:
- **Topic Tracking System:**
  - Added used_topics list to session state
  - Prevents topic repetition within a single session
  - Ensures variety across all 10 questions
- **Advanced FunEd Question Prompts:**
  - Redesigned FunEd questions for maximum engagement
  - Added specific examples: gamer slang, Roblox references, TikTok trends
  - Maintained educational rigor while increasing relatability
- **Enhanced Question Generation:**
  - More specific instructions to Claude API
  - Better balance between fun and educational value

### Why:
- Increase student engagement through relevant, modern content
- Prevent boredom from repeated topics
- Improve learning outcomes through relatable examples

---

## Version Numbering System

**Format:** MAJOR.MINOR.PATCH

- **Major Version (X.0.0):** Complete rewrites, fundamental architecture changes
- **Minor Version (1.X.0):** New features, significant functionality additions
- **Patch Version (1.0.X):** Bug fixes, small tweaks, hotfixes

**Examples:**
- v1.0 → v1.1 (new feature: skill tracking)
- v1.9 → v2.0 (major overhaul)
- v1.0 → v1.0.1 (bug fix)

---

## Update Protocol

Before each version update:
1. Create backup: `cp app.py app_v[current_version].py`
2. Create git commit with current version number
3. Update VERSION variable in app.py
4. Make changes
5. Test thoroughly
6. Update this VERSIONS.md file
7. Create git commit with new version number

---

**Current Version:** v1.5
**Last Updated:** April 23, 2026

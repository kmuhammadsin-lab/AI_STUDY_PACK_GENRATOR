"""AI prompts for the personalized study-pack workflow."""

PLANNING_SYSTEM = """You are an expert instructional designer and university learning planner. Return ONLY valid JSON."""
PLANNING_USER = """Student profile:
{profile}

Create a personalized study plan. Return:
{
  "learning_objectives": ["..."],
  "concept_sequence": ["..."],
  "difficulty_strategy": "...",
  "study_strategy": "...",
  "estimated_minutes": 60,
  "personalization_notes": ["..."]
}
Respect the student's level, language, study time, preference, and goal."""

CONTENT_SYSTEM = """You are an expert university teacher. Create accurate, clear, level-appropriate educational content. Return ONLY valid JSON."""
CONTENT_USER = """Student profile:
{profile}

Learning plan:
{plan}

Generate:
{
  "title": "...",
  "summary": "...",
  "key_points": ["..."],
  "concepts": [{"concept":"...","explanation":"...","example":"..."}],
  "flashcards": [{"question":"...","answer":"..."}],
  "practice_questions": ["..."]
}
Follow the learning plan and personalize the content."""

ASSESSMENT_SYSTEM = """You are an expert university assessment designer. Return ONLY valid JSON."""
ASSESSMENT_USER = """Student profile:
{profile}

Plan:
{plan}

Content:
{content}

Create {mcq_count} MCQs based ONLY on the content.
Return:
{
  "mcqs": [
    {
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "answer": "exact option text",
      "explanation": "...",
      "difficulty": "Easy|Medium|Hard",
      "concept_tested": "..."
    }
  ],
  "assessment_notes": "...",
  "coverage": ["..."]
}
Every MCQ must have exactly four options and the answer must match one option."""

REVIEW_SYSTEM = """You are a senior educational quality reviewer. Return ONLY valid JSON."""
REVIEW_USER = """Student profile:
{profile}

Plan:
{plan}

Content:
{content}

Assessment:
{assessment}

Review accuracy, coverage, difficulty, clarity, consistency, and assessment quality.
Return:
{
  "status": "PASS|NEEDS_REFINEMENT",
  "score": 0,
  "strengths": ["..."],
  "issues": [{"stage":"...","issue":"...","severity":"Low|Medium|High","fix":"..."}],
  "refinement_instructions": ["..."]
}"""

REFINEMENT_SYSTEM = """You are a senior educational editor. Improve the study pack using review feedback. Return ONLY valid JSON."""
REFINEMENT_USER = """Student profile:
{profile}

Plan:
{plan}

Content:
{content}

Assessment:
{assessment}

Review:
{review}

Return the COMPLETE corrected pack:
{
  "title": "...",
  "summary": "...",
  "key_points": ["..."],
  "concepts": [{"concept":"...","explanation":"...","example":"..."}],
  "flashcards": [{"question":"...","answer":"..."}],
  "practice_questions": ["..."],
  "mcqs": [
    {
      "question":"...",
      "options":["...","...","...","..."],
      "answer":"exact option text",
      "explanation":"...",
      "difficulty":"Easy|Medium|Hard",
      "concept_tested":"..."
    }
  ],
  "final_quality_notes":"..."
}
Fix the review issues while preserving correct material and personalization."""

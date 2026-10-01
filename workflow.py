"""AI workflow: Planning -> Content -> Assessment -> Review -> Refinement."""

import json
import re
import time
from typing import Any, Callable, Dict, Optional

from groq import Groq

from prompts import (
    PLANNING_SYSTEM, PLANNING_USER,
    CONTENT_SYSTEM, CONTENT_USER,
    ASSESSMENT_SYSTEM, ASSESSMENT_USER,
    REVIEW_SYSTEM, REVIEW_USER,
    REFINEMENT_SYSTEM, REFINEMENT_USER,
)

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3


class WorkflowError(Exception):
    pass


def _parse_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.I)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("AI did not return valid JSON.")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("AI response is not a JSON object.")
    return data


def _call_ai(client, system, user, model, temperature=0.3, max_tokens=7000):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return _parse_json(response.choices[0].message.content)
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(attempt)
    raise WorkflowError(f"AI call failed after {MAX_RETRIES} attempts: {last_error}")


def _list(data, key):
    value = data.get(key)
    if not isinstance(value, list):
        raise WorkflowError(f"Validation failed: '{key}' must be a list.")
    return value


def planning_stage(client, profile, model):
    result = _call_ai(client, PLANNING_SYSTEM, PLANNING_USER.format(
        profile=json.dumps(profile, indent=2, ensure_ascii=False)), model, 0.2)
    _list(result, "learning_objectives")
    _list(result, "concept_sequence")
    return result


def content_stage(client, profile, plan, model):
    result = _call_ai(client, CONTENT_SYSTEM, CONTENT_USER.format(
        profile=json.dumps(profile, indent=2, ensure_ascii=False),
        plan=json.dumps(plan, indent=2, ensure_ascii=False)), model, 0.4)
    for key in ("key_points", "concepts", "flashcards", "practice_questions"):
        _list(result, key)
    return result


def assessment_stage(client, profile, plan, content, mcq_count, model):
    result = _call_ai(client, ASSESSMENT_SYSTEM, ASSESSMENT_USER.format(
        profile=json.dumps(profile, indent=2, ensure_ascii=False),
        plan=json.dumps(plan, indent=2, ensure_ascii=False),
        content=json.dumps(content, indent=2, ensure_ascii=False),
        mcq_count=mcq_count), model, 0.2)
    mcqs = _list(result, "mcqs")
    if len(mcqs) < mcq_count:
        raise WorkflowError(f"Expected {mcq_count} MCQs, received {len(mcqs)}.")
    for i, mcq in enumerate(mcqs[:mcq_count], 1):
        if not isinstance(mcq.get("options"), list) or len(mcq["options"]) != 4:
            raise WorkflowError(f"MCQ {i} must have exactly four options.")
        if mcq.get("answer") not in mcq["options"]:
            raise WorkflowError(f"MCQ {i} answer does not match an option.")
    return result


def review_stage(client, profile, plan, content, assessment, model):
    return _call_ai(client, REVIEW_SYSTEM, REVIEW_USER.format(
        profile=json.dumps(profile, indent=2, ensure_ascii=False),
        plan=json.dumps(plan, indent=2, ensure_ascii=False),
        content=json.dumps(content, indent=2, ensure_ascii=False),
        assessment=json.dumps(assessment, indent=2, ensure_ascii=False)), model, 0.1)


def refinement_stage(client, profile, plan, content, assessment, review, model):
    result = _call_ai(client, REFINEMENT_SYSTEM, REFINEMENT_USER.format(
        profile=json.dumps(profile, indent=2, ensure_ascii=False),
        plan=json.dumps(plan, indent=2, ensure_ascii=False),
        content=json.dumps(content, indent=2, ensure_ascii=False),
        assessment=json.dumps(assessment, indent=2, ensure_ascii=False),
        review=json.dumps(review, indent=2, ensure_ascii=False)), model, 0.2, 9000)
    for key in ("key_points", "concepts", "flashcards", "practice_questions", "mcqs"):
        _list(result, key)
    return result


def run_workflow(client, profile, mcq_count, model=DEFAULT_MODEL,
                 progress_callback: Optional[Callable[[int, str], None]] = None):
    def update(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    update(10, "1/5 Planning personalized learning path...")
    plan = planning_stage(client, profile, model)

    update(30, "2/5 Generating personalized content...")
    content = content_stage(client, profile, plan, model)

    update(50, "3/5 Creating assessment...")
    assessment = assessment_stage(client, profile, plan, content, mcq_count, model)

    update(70, "4/5 Reviewing quality...")
    review = review_stage(client, profile, plan, content, assessment, model)

    update(85, "5/5 Refining using review feedback...")
    final_pack = refinement_stage(client, profile, plan, content, assessment, review, model)

    update(100, "Workflow completed.")
    return {
        "profile": profile,
        "plan": plan,
        "content": content,
        "assessment": assessment,
        "review": review,
        "final_pack": final_pack,
    }

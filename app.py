"""Main Streamlit application for the AI Personalized Study Pack Generator."""

import json
import streamlit as st
from groq import Groq

from workflow import run_workflow, WorkflowError, DEFAULT_MODEL


st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)


def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None


st.title("📚 AI Personalized Study Pack Generator")
st.caption("Planning → Content → Assessment → Review → Refinement")

with st.sidebar:
    st.header("👤 Student Profile")

    level = st.selectbox(
        "Academic Level",
        ["Beginner", "Intermediate", "University Student", "Advanced"],
        index=2,
    )

    preference = st.selectbox(
        "Learning Preference",
        [
            "Simple explanations",
            "Examples and practical learning",
            "Exam-focused learning",
            "Conceptual/deep learning",
        ],
    )

    study_time = st.slider("Study Time (minutes)", 15, 240, 60, 15)
    language = st.selectbox("Language", ["Simple English", "English", "Urdu"])
    goal = st.text_area(
        "Learning Goal",
        "Understand the topic and prepare for my university exam.",
    )
    mcq_count = st.slider("Number of MCQs", 3, 15, 5)
    model = st.text_input("Groq Model", DEFAULT_MODEL)

topic = st.text_input(
    "📌 Topic",
    placeholder="Example: Object Oriented Programming - Inheritance",
)

extra = st.text_area(
    "Additional Instructions",
    placeholder="Example: Use C++ examples and focus on exam-important concepts.",
)

st.markdown(
    "**Workflow:** Student Profile → Planning → Content → Assessment → Review → Refinement"
)

if st.button("🚀 Generate Personalized Study Pack", type="primary",
             use_container_width=True):

    api_key = get_api_key()

    if not api_key:
        st.error("GROQ_API_KEY is missing. Add it in Streamlit Secrets.")
        st.stop()

    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    profile = {
        "topic": topic.strip(),
        "academic_level": level,
        "learning_preference": preference,
        "study_time_minutes": study_time,
        "language": language,
        "learning_goal": goal,
        "extra_instructions": extra,
    }

    client = Groq(api_key=api_key)
    progress = st.progress(0)
    status = st.empty()

    def update(percent, message):
        progress.progress(percent)
        status.info(message)

    try:
        result = run_workflow(
            client=client,
            profile=profile,
            mcq_count=mcq_count,
            model=model.strip() or DEFAULT_MODEL,
            progress_callback=update,
        )
        st.session_state["result"] = result
        status.success("✅ Study pack generated successfully.")

    except WorkflowError as exc:
        status.error("Workflow failed.")
        st.error(str(exc))
    except Exception as exc:
        status.error("Unexpected error.")
        st.error("Check your API key, model name, and Streamlit logs.")
        st.exception(exc)


if "result" in st.session_state:
    result = st.session_state["result"]
    pack = result["final_pack"]
    review = result["review"]

    st.divider()
    st.header("🎓 Final Personalized Study Pack")

    c1, c2, c3 = st.columns(3)
    c1.metric("Review Score", f'{review.get("score", "N/A")}/100')
    c2.metric("Status", review.get("status", "N/A"))
    c3.metric("MCQs", len(pack.get("mcqs", [])))

    st.subheader(pack.get("title", topic))

    tabs = st.tabs([
        "📖 Summary", "💡 Key Points", "🧠 Concepts",
        "🗂️ Flashcards", "❓ MCQs", "✍️ Practice",
        "🔍 Review", "⚙️ Workflow"
    ])

    with tabs[0]:
        st.write(pack.get("summary", ""))

    with tabs[1]:
        for i, point in enumerate(pack.get("key_points", []), 1):
            st.markdown(f"**{i}.** {point}")

    with tabs[2]:
        for item in pack.get("concepts", []):
            st.markdown(f"### {item.get('concept', '')}")
            st.write(item.get("explanation", ""))
            if item.get("example"):
                st.info(f"Example: {item['example']}")

    with tabs[3]:
        for i, card in enumerate(pack.get("flashcards", []), 1):
            with st.expander(f"Card {i}: {card.get('question', '')}"):
                st.write(card.get("answer", ""))

    with tabs[4]:
        for i, mcq in enumerate(pack.get("mcqs", []), 1):
            st.markdown(f"### MCQ {i}")
            st.write(mcq.get("question", ""))
            options = mcq.get("options", [])

            if len(options) == 4:
                selected = st.radio(
                    "Choose an answer:",
                    options,
                    key=f"answer_{i}",
                )
                if st.button("Check Answer", key=f"check_{i}"):
                    if selected == mcq.get("answer"):
                        st.success("Correct! 🎉")
                    else:
                        st.error(f'Correct answer: {mcq.get("answer")}')
                    st.info(mcq.get("explanation", ""))

            st.caption(
                f'Difficulty: {mcq.get("difficulty", "N/A")} | '
                f'Concept: {mcq.get("concept_tested", "N/A")}'
            )

    with tabs[5]:
        for i, question in enumerate(pack.get("practice_questions", []), 1):
            st.markdown(f"**{i}. {question}**")

    with tabs[6]:
        st.write(f'**Status:** {review.get("status", "N/A")}')
        st.write(f'**Score:** {review.get("score", "N/A")}/100')

        for strength in review.get("strengths", []):
            st.success(strength)

        for issue in review.get("issues", []):
            st.warning(
                f'{issue.get("severity", "N/A")} — '
                f'{issue.get("stage", "N/A")}: {issue.get("issue", "")}'
            )
            st.caption(f'Fix: {issue.get("fix", "")}')

    with tabs[7]:
        st.markdown("### Planning")
        st.json(result["plan"])
        st.markdown("### Content")
        st.json(result["content"])
        st.markdown("### Assessment")
        st.json(result["assessment"])
        st.markdown("### Review")
        st.json(result["review"])

    st.download_button(
        "⬇️ Download Study Pack JSON",
        data=json.dumps(pack, indent=2, ensure_ascii=False),
        file_name="personalized_study_pack.json",
        mime="application/json",
        use_container_width=True,
    )

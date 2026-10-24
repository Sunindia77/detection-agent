
import asyncio
import json

import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.discovery.adapters.adk.agent import root_agent
from src.discovery.application.evaluation_service import (
    validate_discovery_output,
)

APP_NAME = "detection-agent"
USER_ID = "poc-user"


async def run_discovery(transcript: str) -> str:
    """Run the existing Google ADK discovery agent."""
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Analyze the following meeting transcript and return "
                    "the discovery output in JSON.\n\n"
                    f"TRANSCRIPT:\n{transcript}"
                )
            )
        ],
    )

    final_response = None

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content:
            final_response = "".join(
                part.text or ""
                for part in event.content.parts
                if part.text
            )

    if not final_response:
        raise RuntimeError("The agent did not return a final response.")

    return final_response


def render_discovery_ui() -> None:
    """Render the Streamlit UI for meeting discovery."""
    st.set_page_config(
        page_title="Detection Agent",
        page_icon="🔎",
        layout="wide",
    )

    st.title("🔎 Detection Agent")
    st.caption(
        "Powered by Google ADK and your configured OpenAI model"
    )

    st.sidebar.header("Meeting Analysis")
    st.sidebar.write(
        "Convert meeting discussions into structured requirements, "
        "user stories, risks, and open questions."
    )

    uploaded_file = st.file_uploader(
        "Upload a meeting transcript",
        type=["txt", "md"],
    )

    uploaded_text = ""
    if uploaded_file is not None:
        uploaded_text = uploaded_file.getvalue().decode(
            "utf-8-sig",
            errors="replace",
        )

    transcript = st.text_area(
        "Meeting transcript",
        value=uploaded_text,
        height=250,
        placeholder=(
            "Paste the meeting transcript here...\n\n"
            "Product owner: Customers need to reset their password "
            "using their registered email address.\n"
            "Developer: The reset link should expire after 15 minutes."
        ),
    )

    if st.button(
        "Analyze Meeting",
        type="primary",
        use_container_width=True,
    ):
        if not transcript.strip():
            st.warning("Please paste or upload a meeting transcript.")
            return

        try:
            with st.spinner("Analyzing meeting with Google ADK..."):
                raw_result = asyncio.run(run_discovery(transcript))

            cleaned_result = raw_result.strip()

            if cleaned_result.startswith("```"):
                lines = cleaned_result.splitlines()
                if lines[-1].strip().startswith("```"):
                    lines = lines[1:-1]
                    cleaned_result = "\n".join(lines)

            try:
                result = json.loads(cleaned_result)
            except json.JSONDecodeError:
                st.error(
                    "The agent returned a response that is not valid JSON. "
                    "Showing the raw response instead."
                )
                st.text_area(
                    "Raw agent response",
                    value=raw_result,
                    height=300,
                )
                return

            st.session_state["discovery_result"] = result
            st.session_state["discovery_raw"] = raw_result

        except Exception as exc:
            st.error(
                f"Analysis failed: {exc}. "
                "Check your API configuration and terminal logs."
            )

    result = st.session_state.get("discovery_result")

    
result = st.session_state.get("discovery_result")

if result:
    validation = validate_discovery_output(result)

    st.subheader("Output Quality Checks")

    if validation["valid"]:
        st.success("Required output structure is valid.")
    else:
        st.error("Output structure needs attention.")

    if validation["errors"]:
        for error in validation["errors"]:
            st.write(f"- {error}")

    if validation["warnings"]:
        for warning in validation["warnings"]:
            st.warning(warning)


    if result:
        st.divider()
        st.subheader("Discovery Results")

        summary = result.get("meeting_summary", "")
        if isinstance(summary, str):
            st.info(summary)
        else:
            st.write(summary)

        sections = [
            ("Functional Requirements", "functional_requirements"),
            (
                "Non-Functional Requirements",
                "non_functional_requirements",
            ),
            ("User Stories", "user_stories"),
            ("Open Questions", "open_questions"),
            ("Dependencies", "dependencies"),
            ("Risks", "risks"),
        ]

        tabs = st.tabs([label for label, _ in sections])

        for tab, (label, key) in zip(tabs, sections):
            with tab:
                st.subheader(label)
                items = result.get(key, [])
                if items:
                    st.json(items)
                else:
                    st.write("No items returned for this section.")

        st.download_button(
            "Download discovery results (JSON)",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="discovery-results.json",
            mime="application/json",
            use_container_width=True,
        )


if __name__ == "__main__":
    # Streamlit imports this module when running the UI.
    # Plain Python execution retains the command-line smoke test.
    if "streamlit" in __import__("sys").modules:
        render_discovery_ui()
    else:
        sample_transcript = """
        Product owner: Customers need to reset their password using their
        registered email address.
        Developer: The reset link should expire after 15 minutes.
        Product owner: We also need to prevent reuse of an expired reset link.
        Developer: We have not decided the maximum number of reset attempts.
        """
        print(asyncio.run(run_discovery(sample_transcript)))

import os
import re
import uuid

import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEndpoint,
)

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
)

# ============================================================
# CUSTOM FILE MODULES
# ============================================================

from file_processor import (
    process_documents,
    build_document_context,
    get_file_extension,
)

from vision_service import (
    analyze_image,
    analyze_images,
    is_supported_image,
    prepare_image_for_history,
)


# ============================================================
# 1. ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

HF_TOKEN = os.getenv(
    "HUGGINGFACEHUB_API_TOKEN"
)


# ============================================================
# 2. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="centered",
)


# ============================================================
# 3. CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    [data-testid="stChatInput"] textarea {
        color: #000000 !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #333333 !important;
        opacity: 1 !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] button {
        text-align: left !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatInput"] button {
position: relative;
}
    
    
    [data-testid="stChatInput"] button:hover::after {
    
    content: "Add files and more";
    
    position: absolute;
    
    bottom: 48px;
    left: 0px;
    
    background-color: #1f1f1f;
    color: #ffffff;
    
    padding: 7px 10px;
    
    border-radius: 7px;
    
    font-size: 13px;
    font-weight: 500;
    
    white-space: nowrap;
    
    z-index: 9999;
    
    box-shadow:
    0px 4px 12px rgba(0, 0, 0, 0.25);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. CHECK TOKEN
# ============================================================

if not HF_TOKEN:

    st.error(
        "Hugging Face API token nahi mila. "
        ".env file me HUGGINGFACEHUB_API_TOKEN add karo."
    )

    st.stop()


# ============================================================
# 5. TEXT MODEL
# ============================================================

@st.cache_resource
def load_text_model():

    llm = HuggingFaceEndpoint(
        repo_id="meta-llama/Llama-3.1-8B-Instruct",
        task="text-generation",
        max_new_tokens=1024,
        do_sample=False,
        provider="auto",
        huggingfacehub_api_token=HF_TOKEN,
    )

    return ChatHuggingFace(
        llm=llm
    )


text_model = load_text_model()


# ============================================================
# 6. IMAGE GENERATION CLIENT
# ============================================================

@st.cache_resource
def load_image_client():

    return InferenceClient(
        api_key=HF_TOKEN 
    )


image_client = load_image_client()


# ============================================================
# 7. IMAGE GENERATOR
# ============================================================

def generate_image(prompt):

    return image_client.text_to_image(
        prompt,
        model="black-forest-labs/FLUX.1-schnell",
    )


# ============================================================
# 8. DETECT IMAGE GENERATION REQUEST
# ============================================================

def is_image_generation_request(prompt):

    if not prompt:
        return False

    text = prompt.lower().strip()

    keywords = [
        "generate an image",
        "generate image",
        "create an image",
        "create image",
        "make an image",
        "make image",
        "draw an image",
        "draw image",
        "generate a picture",
        "create a picture",
        "generate a photo",
        "create a photo",
        "image bana",
        "image banao",
        "photo bana",
        "photo banao",
        "picture bana",
        "picture banao",
        "tasveer bana",
        "tasveer banao",
    ]

    return any(
        keyword in text
        for keyword in keywords
    )


# ============================================================
# 9. BULK REQUEST COUNT
# ============================================================

def extract_requested_count(prompt):

    if not prompt:
        return None

    matches = re.findall(
        r"\b(\d{1,3})\b",
        prompt
    )

    if not matches:
        return None


    for match in matches:

        count = int(match)

        if 2 <= count <= 200:
            return count


    return None


# ============================================================
# 10. BULK REQUEST DETECTION
# ============================================================

def is_bulk_list_request(
    prompt,
    requested_count,
):

    if not prompt:
        return False

    if requested_count is None:
        return False

    if requested_count < 15:
        return False


    text = prompt.lower()


    keywords = [
        "question",
        "questions",
        "interview questions",
        "examples",
        "example",
        "problems",
        "problem",
        "ideas",
        "idea",
        "tips",
        "tip",
        "points",
        "point",
        "mcq",
        "mcqs",
        "exercises",
        "exercise",
        "solutions",
        "solution",
        "answers",
        "answer",
        "list",
        "most asked",
        "most important",
        "top",
    ]


    return any(
        keyword in text
        for keyword in keywords
    )


# ============================================================
# 11. ANSWER / SOLUTION REQUEST
# ============================================================

def wants_solutions(prompt):

    if not prompt:
        return False

    text = prompt.lower()


    keywords = [
        "with answer",
        "with answers",
        "with solution",
        "with solutions",
        "provide answer",
        "provide answers",
        "provide solution",
        "provide solutions",
        "along with answer",
        "along with answers",
        "answer bhi",
        "answers bhi",
        "solution bhi",
        "solutions bhi",
    ]


    return any(
        keyword in text
        for keyword in keywords
    )


# ============================================================
# 12. BULK RESPONSE GENERATION
# ============================================================

def generate_bulk_response(
    original_prompt,
    total_items,
):

    batch_size = 10

    include_solutions = wants_solutions(
        original_prompt
    )


    all_batches = []

    start_number = 1


    total_batches = (
        total_items + batch_size - 1
    ) // batch_size


    progress_bar = st.progress(
        0,
        text="Preparing response..."
    )


    batch_number = 0


    while start_number <= total_items:

        batch_number += 1


        end_number = min(
            start_number + batch_size - 1,
            total_items,
        )


        if include_solutions:

            answer_instruction = """
For EVERY item:
- Write the question clearly.
- Immediately provide its answer or solution.
- Do not leave any question unanswered.
- Keep each solution useful and concise.
"""

        else:

            answer_instruction = """
Follow the user's requested format exactly.
Do not add unnecessarily long solutions unless requested.
"""


        batch_prompt = f"""
The user requested:

{original_prompt}

Generate PART {batch_number} of {total_batches}.

Generate EXACTLY item numbers:

{start_number} through {end_number}

STRICT RULES:

1. Start numbering from {start_number}.
2. End numbering at {end_number}.
3. Generate every number.
4. Do not restart numbering from 1.
5. Do not skip numbers.
6. Do not say "and so on".
7. Do not replace items with "etc".
8. Do not stop before {end_number}.
9. Avoid duplicates.
10. Do not write an introduction.
11. Do not write a conclusion.
12. Follow the original user's topic.
13. Keep individual items concise enough to fit.

{answer_instruction}

Generate only items {start_number} to {end_number}.
"""


        response = text_model.invoke(
            [
                HumanMessage(
                    content=batch_prompt
                )
            ]
        )


        batch_text = str(
            response.content
        ).strip()


        all_batches.append(
            batch_text
        )


        progress_value = (
            batch_number / total_batches
        )


        progress_bar.progress(
            progress_value,
            text=(
                f"Generating "
                f"{start_number}-{end_number} "
                f"of {total_items}..."
            ),
        )


        start_number = (
            end_number + 1
        )


    progress_bar.progress(
        1.0,
        text=f"Completed {total_items} items.",
    )


    return "\n\n".join(
        all_batches
    )


# ============================================================
# 13. SESSION STATE
# ============================================================

if "chat_sessions" not in st.session_state:

    st.session_state.chat_sessions = {}


if "current_session_id" not in st.session_state:

    st.session_state.current_session_id = None


if "force_new_chat" not in st.session_state:

    st.session_state.force_new_chat = False


# ============================================================
# 14. CLEAN LLM TEXT
# ============================================================

def clean_llm_text(text):

    text = str(text).strip()

    if not text:
        return ""

    text = text.splitlines()[0].strip()


    text = re.sub(
        r"^(topic|subject|category|answer|result)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )


    return text.strip(
        "\"'` "
    )


# ============================================================
# 15. SESSION TITLE
# ============================================================

def create_session_title(
    first_question,
    uploaded_files=None,
):

    title = (
        first_question.strip()
        if first_question
        else ""
    )


    # User ne question nahi likha,
    # sirf file upload ki
    if not title and uploaded_files:

        if len(uploaded_files) == 1:

            title = (
                f"Analyze {uploaded_files[0].name}"
            )

        else:

            title = (
                f"Analyze {len(uploaded_files)} files"
            )


    if not title:

        title = "New Conversation"


    if len(title) > 45:

        title = (
            title[:45].strip()
            + "..."
        )


    return title


# ============================================================
# 16. DETECT TOPIC
# ============================================================

def detect_topic(question):

    if not question:

        return "File Analysis"


    prompt = f"""
You are a conversation topic classifier.

Identify the main subject of the user's message.

Rules:

1. Return ONLY the topic.
2. Use 1 to 5 words.
3. Do not answer the question.
4. Do not explain.
5. User may ask about ANY subject.
6. Prefer a broad meaningful subject.

User message:

{question}

Return only the topic:
"""


    try:

        response = text_model.invoke(
            [
                HumanMessage(
                    content=prompt
                )
            ]
        )


        topic = clean_llm_text(
            response.content
        )


        if not topic:

            return question[:50]


        return topic[:60]


    except Exception:

        return question[:50]


# ============================================================
# 17. SESSION SUMMARY
# ============================================================

def get_session_summary(session):

    user_questions = [
        message.get("content", "")
        for message in session["messages"]
        if (
            message["role"] == "user"
            and message.get("content")
        )
    ]


    recent_questions = (
        user_questions[-6:]
    )


    if not recent_questions:

        return "No previous questions."


    return "\n".join(
        f"- {question}"
        for question in recent_questions
    )


# ============================================================
# 18. SESSION MATCHING
# ============================================================

def question_belongs_to_session(
    question,
    detected_topic,
    session,
):

    session_title = session["title"]

    session_topic = session["topic"]

    session_summary = get_session_summary(
        session
    )


    prompt = f"""
You are a conversation routing system.

Existing conversation:
{session_title}

Internal topic:
{session_topic}

Recent questions:
{session_summary}

New message:
{question}

Detected topic:
{detected_topic}

Rules:

- Same general subject = YES
- Follow-up question = YES
- Related subtopic = YES
- Asking for details/solutions/examples = YES
- Asking questions about previously uploaded files = YES
- Clearly different subject = NO

Return ONLY YES or NO.
"""


    try:

        response = text_model.invoke(
            [
                HumanMessage(
                    content=prompt
                )
            ]
        )


        decision = clean_llm_text(
            response.content
        ).upper()


        return decision.startswith(
            "YES"
        )


    except Exception:

        return False


# ============================================================
# 19. FIND EXISTING SESSION
# ============================================================

def find_matching_session(
    question,
    detected_topic,
):

    current_id = (
        st.session_state.current_session_id
    )


    if (
        current_id
        and current_id
        in st.session_state.chat_sessions
    ):

        session = (
            st.session_state.chat_sessions[
                current_id
            ]
        )


        if question_belongs_to_session(
            question,
            detected_topic,
            session,
        ):

            return current_id


    sessions = list(
        st.session_state.chat_sessions.items()
    )

    sessions.reverse()


    for session_id, session in sessions:

        if session_id == current_id:
            continue


        if question_belongs_to_session(
            question,
            detected_topic,
            session,
        ):

            return session_id


    return None


# ============================================================
# 20. CREATE SESSION
# ============================================================

def create_session(
    topic,
    first_question,
    uploaded_files=None,
):

    session_id = str(
        uuid.uuid4()
    )


    title = create_session_title(
        first_question,
        uploaded_files,
    )


    st.session_state.chat_sessions[
        session_id
    ] = {

        "title": title,

        "topic": topic,

        "messages": [],

        # Processed document context
        "document_context": "",

        # Attached document names
        "document_names": [],
    }


    return session_id


# ============================================================
# 21. ROUTE QUESTION
# ============================================================

def route_question(
    question,
    uploaded_files=None,
):

    detected_topic = detect_topic(
        question
    )


    # ========================================================
    # FILE UPLOAD SHOULD STAY IN CURRENT CHAT WHEN POSSIBLE
    # ========================================================

    if (
        uploaded_files
        and st.session_state.current_session_id
        and not st.session_state.force_new_chat
    ):

        return (
            st.session_state.current_session_id
        )


    # ========================================================
    # FORCED NEW CHAT
    # ========================================================

    if st.session_state.force_new_chat:

        session_id = create_session(
            detected_topic,
            question,
            uploaded_files,
        )


        st.session_state.force_new_chat = (
            False
        )


        return session_id


    # ========================================================
    # FIRST CHAT
    # ========================================================

    if not st.session_state.chat_sessions:

        return create_session(
            detected_topic,
            question,
            uploaded_files,
        )


    matching_session = (
        find_matching_session(
            question,
            detected_topic,
        )
    )


    if matching_session:

        return matching_session


    return create_session(
        detected_topic,
        question,
        uploaded_files,
    )


# ============================================================
# 22. DISPLAY MESSAGE
# ============================================================

def display_message(message):

    role = message["role"]

    message_type = message.get(
        "type",
        "text",
    )


    # ========================================================
    # USER WITH ATTACHMENTS
    # ========================================================

    if (
        role == "user"
        and message_type == "attachment"
    ):

        with st.chat_message(
            "user"
        ):


            # Images
            images = message.get(
                "images",
                []
            )


            for image in images:

                st.image(
                    image["bytes"],
                    caption=image["name"],
                    width=350,
                )


            # Documents
            documents = message.get(
                "documents",
                []
            )


            for document_name in documents:

                st.markdown(
                    f"📎 **{document_name}**"
                )


            # User question
            if message.get("content"):

                st.markdown(
                    message["content"]
                )


    # ========================================================
    # NORMAL USER
    # ========================================================

    elif role == "user":

        with st.chat_message(
            "user"
        ):

            st.markdown(
                message["content"]
            )


    # ========================================================
    # ASSISTANT TEXT
    # ========================================================

    elif (
        role == "assistant"
        and message_type == "text"
    ):

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                message["content"]
            )


    # ========================================================
    # GENERATED IMAGE
    # ========================================================

    elif (
        role == "assistant"
        and message_type == "image"
    ):

        with st.chat_message(
            "assistant"
        ):

            st.image(
                message["content"],
                caption="🎨 AI Generated Image",
                use_container_width=True,
            )


# ============================================================
# 23. SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "💬 Recent Conversations"
    )


    st.caption(
        "Start fresh anytime or continue "
        "one of your previous conversations."
    )


    st.divider()


    # ========================================================
    # NEW CHAT
    # ========================================================

    if st.button(
        "➕ New Chat",
        use_container_width=True,
    ):

        st.session_state.current_session_id = (
            None
        )

        st.session_state.force_new_chat = (
            True
        )

        st.rerun()


    st.divider()


    # ========================================================
    # EXISTING CHATS
    # ========================================================

    session_items = list(
        st.session_state.chat_sessions.items()
    )

    session_items.reverse()


    if not session_items:

        st.caption(
            "No conversations yet."
        )

        st.caption(
            "Ask something to get started ✨"
        )


    else:

        for session_id, session in session_items:

            title = session["title"]


            if (
                session_id
                == st.session_state.current_session_id
            ):

                label = f"🟢 {title}"


            else:

                label = f"💬 {title}"


            if st.button(
                label,
                key=f"session_{session_id}",
                use_container_width=True,
            ):

                st.session_state.current_session_id = (
                    session_id
                )

                st.session_state.force_new_chat = (
                    False
                )

                st.rerun()


    # ========================================================
    # CLEAR ALL
    # ========================================================

    if st.session_state.chat_sessions:

        st.divider()


        if st.button(
            "🗑️ Clear All Conversations",
            use_container_width=True,
        ):

            st.session_state.chat_sessions = {}

            st.session_state.current_session_id = (
                None
            )

            st.session_state.force_new_chat = (
                False
            )

            st.rerun()


# ============================================================
# 24. MAIN PAGE
# ============================================================

st.title(
    "🤖 AI Chatbot"
)


st.write(
    "One conversation. Endless possibilities. 🚀 "
    "Ask questions, upload files, analyze images, "
    "generate creative visuals, and explore ideas with AI."
)


# ============================================================
# 25. DISPLAY CURRENT SESSION
# ============================================================

current_session_id = (
    st.session_state.current_session_id
)


if (
    current_session_id
    and current_session_id
    in st.session_state.chat_sessions
):


    current_session = (
        st.session_state.chat_sessions[
            current_session_id
        ]
    )


    st.caption(
        f"💬 {current_session['title']}"
    )


    for message in current_session[
        "messages"
    ]:

        display_message(
            message
        )


# ============================================================
# 26. NEW CHAT SCREEN
# ============================================================

elif st.session_state.force_new_chat:

    st.markdown(
        "### ✨ Start a new conversation"
    )


    st.caption(
        "Ask anything or attach a file below "
        "to begin a fresh chat."
    )


# ============================================================
# 27. CHAT INPUT + FILE ATTACHMENTS
# ============================================================

chat_submission = st.chat_input(

    "Ask me anything...",

    accept_file="multiple",

    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "pdf",
        "docx",
        "txt",
        "csv",
    ],
)


# ============================================================
# 28. PROCESS SUBMISSION
# ============================================================

if chat_submission:


    # ========================================================
    # EXTRACT TEXT
    # ========================================================

    user_input = ""

    if hasattr(
        chat_submission,
        "text"
    ):

        if chat_submission.text:

            user_input = (
                chat_submission.text.strip()
            )


    # ========================================================
    # EXTRACT FILES
    # ========================================================

    uploaded_files = []

    if hasattr(
        chat_submission,
        "files"
    ):

        uploaded_files = list(
            chat_submission.files
        )


    # Nothing submitted
    if (
        not user_input
        and not uploaded_files
    ):

        st.stop()


    # ========================================================
    # SPLIT FILES BY TYPE
    # ========================================================

    image_files = []

    document_files = []


    for uploaded_file in uploaded_files:

        extension = get_file_extension(
            uploaded_file
        )


        if extension in {
            "jpg",
            "jpeg",
            "png",
            "webp",
        }:

            image_files.append(
                uploaded_file
            )


        elif extension in {
            "pdf",
            "docx",
            "txt",
            "csv",
        }:

            document_files.append(
                uploaded_file
            )


    # ========================================================
    # FIND / CREATE SESSION
    # ========================================================

    routing_text = (
        user_input
        if user_input
        else "Analyze uploaded files"
    )


    with st.spinner(
        "Understanding your conversation..."
    ):

        session_id = route_question(
            routing_text,
            uploaded_files,
        )


    st.session_state.current_session_id = (
        session_id
    )


    current_session = (
        st.session_state.chat_sessions[
            session_id
        ]
    )


    # ========================================================
    # PREPARE IMAGE HISTORY
    # ========================================================

    history_images = []


    for image_file in image_files:

        try:

            history_images.append(
                prepare_image_for_history(
                    image_file
                )
            )

        except Exception:

            pass


    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    if uploaded_files:

        current_session[
            "messages"
        ].append(
            {
                "role": "user",

                "type": "attachment",

                "content": user_input,

                "images": history_images,

                "documents": [
                    file.name
                    for file in document_files
                ],
            }
        )


    else:

        current_session[
            "messages"
        ].append(
            {
                "role": "user",
                "type": "text",
                "content": user_input,
            }
        )


    # ========================================================
    # DISPLAY USER MESSAGE
    # ========================================================

    with st.chat_message(
        "user"
    ):


        for image in history_images:

            st.image(
                image["bytes"],
                caption=image["name"],
                width=350,
            )


        for document_file in document_files:

            st.markdown(
                f"📎 **{document_file.name}**"
            )


        if user_input:

            st.markdown(
                user_input
            )


       # ========================================================
    # 29. PROCESS DOCUMENTS
    # ========================================================

    if document_files:

        try:

            with st.spinner(
                "📄 Reading uploaded files..."
            ):

                processed_documents = process_documents(
                    document_files
                )

                new_document_context = build_document_context(
                    processed_documents
                )


            # ------------------------------------------------
            # Store document context in current conversation
            # ------------------------------------------------

            if new_document_context:

                previous_context = current_session.get(
                    "document_context",
                    ""
                )


                if previous_context:

                    current_session["document_context"] = (
                        previous_context
                        + "\n\n"
                        + new_document_context
                    )

                else:

                    current_session["document_context"] = (
                        new_document_context
                    )


            # ------------------------------------------------
            # Make sure document_names exists
            # ------------------------------------------------

            if "document_names" not in current_session:

                current_session["document_names"] = []


            # ------------------------------------------------
            # Store uploaded document names
            # ------------------------------------------------

            for document_file in document_files:

                if (
                    document_file.name
                    not in current_session["document_names"]
                ):

                    current_session["document_names"].append(
                        document_file.name
                    )


        except Exception as e:

            error_message = (
                "File process nahi ho payi: "
                f"{str(e)}"
            )

            with st.chat_message(
                "assistant"
            ):

                st.error(
                    error_message
                )


    # ========================================================
    # 30. IMAGE ANALYSIS
    # ========================================================

    if image_files:

        try:

            image_question = (
                user_input
                if user_input
                else
                "Analyze this image in detail and explain "
                "the important information visible in it."
            )


            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🖼️ Analyzing image..."
                ):

                    # =========================================
                    # SINGLE IMAGE
                    # =========================================

                    if len(image_files) == 1:

                        ai_response = analyze_image(
                            image_files[0],
                            image_question,
                        )


                    # =========================================
                    # MULTIPLE IMAGES
                    # =========================================

                    else:

                        ai_response = analyze_images(
                            image_files,
                            image_question,
                        )


                st.markdown(
                    ai_response
                )


            # ------------------------------------------------
            # Save AI response
            # ------------------------------------------------

            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": ai_response,
                }
            )


            st.rerun()


        except Exception as e:

            error_message = (
                "Image analyze nahi ho payi: "
                f"{str(e)}"
            )


            with st.chat_message(
                "assistant"
            ):

                st.error(
                    error_message
                )


            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": error_message,
                }
            )


    # ========================================================
    # 31. DOCUMENT QUESTION / DOCUMENT ANALYSIS
    # ========================================================

    elif document_files:

        try:

            document_context = current_session.get(
                "document_context",
                ""
            )


            # ------------------------------------------------
            # User ne question nahi diya
            # ------------------------------------------------

            if user_input:

                document_question = user_input

            else:

                document_question = (
                    "Analyze the uploaded files and provide "
                    "a clear summary of the important information."
                )


            document_prompt = f"""
You are an AI assistant analyzing files uploaded by the user.

Use the uploaded file content below as the primary source
for your answer.

UPLOADED FILE CONTENT:

{document_context}


USER QUESTION:

{document_question}


IMPORTANT INSTRUCTIONS:

1. Answer the user's question clearly.

2. Use information from the uploaded files.

3. Do not invent information that is not available
   in the uploaded files.

4. If the requested information cannot be found in
   the uploaded files, clearly say that.

5. If multiple uploaded files are available, use information
   from all relevant files.

6. Structure the answer properly using headings, bullet points,
   or numbered lists when useful.

7. If the user asks for a summary, provide a useful summary.

8. If the user asks for specific information, focus on that
   information instead of unnecessarily summarizing everything.

Answer:
"""


            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "📄 Analyzing uploaded files..."
                ):

                    response = text_model.invoke(
                        [
                            HumanMessage(
                                content=document_prompt
                            )
                        ]
                    )


                ai_response = str(
                    response.content
                )


                st.markdown(
                    ai_response
                )


            # ------------------------------------------------
            # Save assistant response
            # ------------------------------------------------

            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": ai_response,
                }
            )


            st.rerun()


        except Exception as e:

            error_message = (
                "Document analyze nahi ho paya: "
                f"{str(e)}"
            )


            with st.chat_message(
                "assistant"
            ):

                st.error(
                    error_message
                )


            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": error_message,
                }
            )


    # ========================================================
    # 32. PREVIOUSLY UPLOADED DOCUMENT QUESTION
    #
    # Example:
    #
    # Message 1:
    # User uploads Java.pdf
    #
    # Message 2:
    # User asks:
    # "Isme multithreading ke baare me kya likha hai?"
    #
    # User ko PDF dobara upload nahi karni padegi.
    # ========================================================

    elif (
        current_session.get(
            "document_context",
            ""
        )
        and user_input
    ):

        try:

            document_context = current_session.get(
                "document_context",
                ""
            )


            document_prompt = f"""
The user has previously uploaded documents in this conversation.

Use the uploaded document content below when answering the
user's question.

UPLOADED DOCUMENT CONTENT:

{document_context}


USER QUESTION:

{user_input}


IMPORTANT RULES:

1. Use the uploaded documents as the primary source.

2. If the answer exists in the uploaded document,
   answer from the document.

3. If the answer cannot be found in the uploaded document,
   clearly say that the information was not found.

4. Do not invent document content.

5. Give a clear and useful answer.

Answer:
"""


            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🔎 Searching uploaded files..."
                ):

                    response = text_model.invoke(
                        [
                            HumanMessage(
                                content=document_prompt
                            )
                        ]
                    )


                ai_response = str(
                    response.content
                )


                st.markdown(
                    ai_response
                )


            # ------------------------------------------------
            # Store answer
            # ------------------------------------------------

            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": ai_response,
                }
            )


            st.rerun()


        except Exception as e:

            error_message = (
                "Uploaded file context se answer generate "
                f"nahi ho paya: {str(e)}"
            )


            with st.chat_message(
                "assistant"
            ):

                st.error(
                    error_message
                )


            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": error_message,
                }
            )


    # ========================================================
    # 33. IMAGE GENERATION
    #
    # Only when user has NOT uploaded an image/document.
    # ========================================================

    elif (
        user_input
        and is_image_generation_request(
            user_input
        )
    ):

        try:

            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🎨 Creating your image..."
                ):

                    generated_image = generate_image(
                        user_input
                    )


                st.image(
                    generated_image,
                    caption="🎨 AI Generated Image",
                    use_container_width=True,
                )


            # ------------------------------------------------
            # Save generated image in history
            # ------------------------------------------------

            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "image",
                    "content": generated_image,
                }
            )


            st.rerun()


        except Exception as e:

            error_message = (
                "Image generate nahi ho payi: "
                f"{str(e)}"
            )


            with st.chat_message(
                "assistant"
            ):

                st.error(
                    error_message
                )


            current_session["messages"].append(
                {
                    "role": "assistant",
                    "type": "text",
                    "content": error_message,
                }
            )


    # ========================================================
    # 34. BULK REQUEST OR NORMAL TEXT CHAT
    # ========================================================

    elif user_input:

        requested_count = extract_requested_count(
            user_input
        )


        bulk_request = is_bulk_list_request(
            user_input,
            requested_count,
        )


        # ====================================================
        # 34A. BULK RESPONSE
        #
        # Example:
        # "Give me 100 Java interview questions with answers"
        # ====================================================

        if bulk_request:

            try:

                with st.chat_message(
                    "assistant"
                ):

                    st.info(
                        f"📚 You requested "
                        f"{requested_count} items. "
                        "Generating the complete response "
                        "in multiple batches..."
                    )


                    ai_response = generate_bulk_response(
                        original_prompt=user_input,
                        total_items=requested_count,
                    )


                    st.markdown(
                        ai_response
                    )


                # --------------------------------------------
                # Save complete response
                # --------------------------------------------

                current_session["messages"].append(
                    {
                        "role": "assistant",
                        "type": "text",
                        "content": ai_response,
                    }
                )


                st.rerun()


            except Exception as e:

                error_message = (
                    "Complete response generate nahi ho paya: "
                    f"{str(e)}"
                )


                with st.chat_message(
                    "assistant"
                ):

                    st.error(
                        error_message
                    )


                current_session["messages"].append(
                    {
                        "role": "assistant",
                        "type": "text",
                        "content": error_message,
                    }
                )


        # ====================================================
        # 34B. NORMAL TEXT CHAT
        # ====================================================

        else:

            langchain_messages = []


            # ------------------------------------------------
            # Build current conversation history
            # ------------------------------------------------

            for message in current_session["messages"]:

                message_type = message.get(
                    "type",
                    "text",
                )


                # --------------------------------------------
                # Only normal text messages go into
                # ChatHuggingFace history.
                #
                # Attachment messages are handled separately.
                # --------------------------------------------

                if message_type != "text":

                    continue


                # --------------------------------------------
                # USER
                # --------------------------------------------

                if message["role"] == "user":

                    content = message.get(
                        "content",
                        ""
                    )


                    if content:

                        langchain_messages.append(
                            HumanMessage(
                                content=content
                            )
                        )


                # --------------------------------------------
                # ASSISTANT
                # --------------------------------------------

                elif message["role"] == "assistant":

                    content = message.get(
                        "content",
                        ""
                    )
 

                    if content:

                        langchain_messages.append(
                            AIMessage(
                                content=content
                            )
                        )


            # ------------------------------------------------
            # Safety fallback
            # ------------------------------------------------

            if not langchain_messages:

                langchain_messages.append(
                    HumanMessage(
                        content=user_input
                    )
                )


            # =================================================
            # GENERATE NORMAL RESPONSE
            # =================================================

            try:

                with st.chat_message(
                    "assistant"
                ):

                    with st.spinner(
                        "Thinking..."
                    ):

                        response = text_model.invoke(
                            langchain_messages
                        )


                    ai_response = str(
                        response.content
                    )


                    st.markdown(
                        ai_response
                    )


                # --------------------------------------------
                # Save answer
                # --------------------------------------------

                current_session["messages"].append(
                    {
                        "role": "assistant",
                        "type": "text",
                        "content": ai_response,
                    }
                )


                st.rerun()


            except Exception as e:

                error_message = (
                    "AI response generate nahi ho paya: "
                    f"{str(e)}"
                )


                with st.chat_message(
                    "assistant"
                ):

                    st.error(
                        error_message
                    )


                current_session["messages"].append(
                    {
                        "role": "assistant",
                        "type": "text",
                        "content": error_message,
                    }
                )
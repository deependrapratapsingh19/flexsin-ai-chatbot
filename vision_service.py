import base64
import os

from huggingface_hub import InferenceClient


# ============================================================
# CONFIGURATION
# ============================================================

SUPPORTED_IMAGE_TYPES = {
    "jpg",
    "jpeg",
    "png",
    "webp",
}


# Vision model
VISION_MODEL = (
    "meta-llama/Llama-4-Scout-17B-16E-Instruct"
)


# ============================================================
# GET FILE EXTENSION
# ============================================================

def get_image_extension(uploaded_file):

    if uploaded_file is None:

        return ""


    filename = getattr(
        uploaded_file,
        "name",
        ""
    )


    if "." not in filename:

        return ""


    return filename.rsplit(
        ".",
        1
    )[-1].lower().strip()


# ============================================================
# CHECK IF FILE IS IMAGE
# ============================================================

def is_supported_image(uploaded_file):

    extension = get_image_extension(
        uploaded_file
    )


    return extension in SUPPORTED_IMAGE_TYPES


# ============================================================
# CREATE VISION CLIENT
# ============================================================

def create_vision_client():

    token = os.getenv(
        "HUGGINGFACEHUB_API_TOKEN"
    )


    if not token:

        raise ValueError(
            "HUGGINGFACEHUB_API_TOKEN "
            "environment variable nahi mila."
        )


    return InferenceClient(
        provider="auto",
        api_key=token,
    )


# ============================================================
# IMAGE → DATA URL
# ============================================================

def image_to_data_url(uploaded_file):

    if uploaded_file is None:

        raise ValueError(
            "No image was provided."
        )


    if not is_supported_image(
        uploaded_file
    ):

        raise ValueError(
            "Unsupported image format. "
            "Use JPG, JPEG, PNG or WEBP."
        )


    image_bytes = uploaded_file.getvalue()


    if not image_bytes:

        raise ValueError(
            "Uploaded image is empty."
        )


    # Mime type Streamlit generally provide karta hai.
    mime_type = getattr(
        uploaded_file,
        "type",
        None
    )


    # Fallback MIME
    if not mime_type:

        extension = get_image_extension(
            uploaded_file
        )


        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }


        mime_type = mime_map.get(
            extension,
            "image/jpeg",
        )


    base64_image = base64.b64encode(
        image_bytes
    ).decode(
        "utf-8"
    )


    return (
        f"data:{mime_type};base64,"
        f"{base64_image}"
    )


# ============================================================
# ANALYZE SINGLE IMAGE
# ============================================================

def analyze_image(
    uploaded_file,
    question,
):

    client = create_vision_client()


    image_data_url = image_to_data_url(
        uploaded_file
    )


    question = (
        question.strip()
        if question
        else "Describe and analyze this image in detail."
    )


    messages = [
        {
            "role": "user",

            "content": [
                {
                    "type": "text",
                    "text": question,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    },
                },
            ],
        }
    ]


    response = (
        client.chat.completions.create(
            model=VISION_MODEL,
            messages=messages,
            max_tokens=1200,
        )
    )


    if not response.choices:

        raise ValueError(
            "Vision model ne koi response return nahi kiya."
        )


    content = (
        response
        .choices[0]
        .message
        .content
    )


    if not content:

        raise ValueError(
            "Vision model ka response empty tha."
        )


    return str(content)


# ============================================================
# ANALYZE MULTIPLE IMAGES
# ============================================================

def analyze_images(
    uploaded_files,
    question,
):

    if not uploaded_files:

        raise ValueError(
            "No images were provided."
        )


    client = create_vision_client()


    content = []


    # ========================================================
    # TEXT PART
    # ========================================================

    user_question = (
        question.strip()
        if question
        else (
            "Analyze these images. "
            "Describe the important information "
            "and explain similarities or differences "
            "when relevant."
        )
    )


    content.append(
        {
            "type": "text",
            "text": user_question,
        }
    )


    # ========================================================
    # IMAGE PARTS
    # ========================================================

    valid_image_count = 0


    for uploaded_file in uploaded_files:

        if not is_supported_image(
            uploaded_file
        ):

            continue


        image_data_url = image_to_data_url(
            uploaded_file
        )


        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url
                },
            }
        )


        valid_image_count += 1


    if valid_image_count == 0:

        raise ValueError(
            "No supported images were found."
        )


    messages = [
        {
            "role": "user",
            "content": content,
        }
    ]


    response = (
        client.chat.completions.create(
            model=VISION_MODEL,
            messages=messages,
            max_tokens=1500,
        )
    )


    if not response.choices:

        raise ValueError(
            "Vision model ne koi response return nahi kiya."
        )


    answer = (
        response
        .choices[0]
        .message
        .content
    )


    if not answer:

        raise ValueError(
            "Vision model response empty tha."
        )


    return str(answer)


# ============================================================
# PREPARE IMAGE DATA FOR SESSION HISTORY
# ============================================================

def prepare_image_for_history(
    uploaded_file
):

    if not is_supported_image(
        uploaded_file
    ):

        raise ValueError(
            "Unsupported image."
        )


    return {
        "name": uploaded_file.name,

        "mime_type": getattr(
            uploaded_file,
            "type",
            "image/jpeg",
        ),

        "bytes": uploaded_file.getvalue(),
    }


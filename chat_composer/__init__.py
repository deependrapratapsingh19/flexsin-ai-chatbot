from pathlib import Path

import streamlit as st


# ============================================================
# COMPONENT PATHS
# ============================================================

_COMPONENT_ROOT = Path(
    __file__
).resolve().parent


_FRONTEND_BUILD = (
    _COMPONENT_ROOT
    / "frontend"
    / "dist"
)


_JS_FILES = list(
    _FRONTEND_BUILD.glob(
        "assets/*.js"
    )
)


_CSS_FILES = list(
    _FRONTEND_BUILD.glob(
        "assets/*.css"
    )
)


# ============================================================
# LOAD BUILT ASSETS
# ============================================================

def _load_asset(files):

    if not files:

        return ""

    return files[0].read_text(
        encoding="utf-8"
    )


# ============================================================
# REGISTER COMPONENT
# ============================================================

def _get_component():

    if not _FRONTEND_BUILD.exists():

        raise RuntimeError(
            "Chat composer frontend build nahi mila. "
            "Run: cd chat_composer/frontend && "
            "npm install && npm run build"
        )


    js = _load_asset(
        _JS_FILES
    )


    css = _load_asset(
        _CSS_FILES
    )


    if not js:

        raise RuntimeError(
            "Chat composer JavaScript build file nahi mila."
        )


    component = st.components.v2.component(
        "deependra.chat_composer",

        html=(
            '<div id="chat-composer-root"></div>'
        ),

        js=js,

        css=css,
    )


    return component


# ============================================================
# PYTHON WRAPPER
# ============================================================

def chat_composer(
    placeholder="Ask me anything...",
    disabled=False,
    key="main_chat_composer",
):

    component = _get_component()


    result = component(
        data={
            "placeholder": placeholder,
            "disabled": disabled,

            "allowedExtensions": [
                "jpg",
                "jpeg",
                "png",
                "webp",
                "pdf",
                "docx",
                "txt",
                "csv",
            ],
        },

        key=key,
    )


    return result
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Optional


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIRECTORY = Path(
    __file__
).resolve().parent


LIBRARY_DIRECTORY = (
    BASE_DIRECTORY
    / "library_files"
)


METADATA_FILE = (
    LIBRARY_DIRECTORY
    / "library_metadata.json"
)


SUPPORTED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "pdf",
    "docx",
    "txt",
    "csv",
}


MAX_LIBRARY_FILE_SIZE = (
    50 * 1024 * 1024
)


# ============================================================
# INITIALIZE LIBRARY
# ============================================================

def initialize_library():

    LIBRARY_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


    if not METADATA_FILE.exists():

        METADATA_FILE.write_text(
            "{}",
            encoding="utf-8",
        )


# ============================================================
# SAFE FILE NAME
# ============================================================

def sanitize_filename(
    filename
):

    filename = os.path.basename(
        filename
    )


    filename = re.sub(
        r"[^A-Za-z0-9._ -]",
        "_",
        filename,
    )


    filename = filename.strip(
        ". "
    )


    if not filename:

        filename = "uploaded_file"


    return filename


# ============================================================
# FILE EXTENSION
# ============================================================

def get_extension(
    filename
):

    if "." not in filename:

        return
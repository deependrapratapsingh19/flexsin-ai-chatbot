import base64
import os
import re
from urllib.parse import urlparse

import requests


# ============================================================
# CONFIGURATION
# ============================================================

GITHUB_API_BASE = (
    "https://api.github.com"
)

REQUEST_TIMEOUT = 20

MAX_FILE_CHARACTERS = 15000

MAX_REPOSITORY_CHARACTERS = 60000

MAX_FILES = 30


# ============================================================
# SUPPORTED CODE/TEXT FILE EXTENSIONS
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".html",
    ".css",
    ".scss",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".md",
    ".txt",
    ".sql",
    ".sh",
}


# ============================================================
# IMPORTANT FILE NAMES
# ============================================================

IMPORTANT_FILENAMES = {
    "readme",
    "readme.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".gitignore",
}


# ============================================================
# GITHUB HEADERS
# ============================================================

def get_github_headers():

    headers = {
        "Accept": (
            "application/vnd.github+json"
        ),
        "X-GitHub-Api-Version": (
            "2022-11-28"
        ),
        "User-Agent": (
            "Deependra-AI-Chatbot"
        ),
    }


    github_token = os.getenv(
        "GITHUB_TOKEN"
    )


    if github_token:

        headers[
            "Authorization"
        ] = (
            f"Bearer {github_token}"
        )


    return headers


# ============================================================
# PARSE GITHUB REPOSITORY URL
# ============================================================

def parse_github_repo_url(
    repo_url
):

    if not repo_url:

        raise ValueError(
            "GitHub repository URL empty hai."
        )


    repo_url = repo_url.strip()


    # Allow owner/repository
    if (
        "/" in repo_url
        and not repo_url.startswith(
            ("http://", "https://")
        )
    ):

        parts = repo_url.strip(
            "/"
        ).split("/")


        if len(parts) == 2:

            owner = parts[0]

            repo = parts[1]


            if repo.endswith(
                ".git"
            ):

                repo = repo[:-4]


            return owner, repo


    parsed_url = urlparse(
        repo_url
    )


    hostname = (
        parsed_url.hostname
        or ""
    ).lower()


    if hostname not in {
        "github.com",
        "www.github.com",
    }:

        raise ValueError(
            "Please provide a valid github.com "
            "repository URL."
        )


    path_parts = [
        part
        for part
        in parsed_url.path.split("/")
        if part
    ]


    if len(path_parts) < 2:

        raise ValueError(
            "Invalid GitHub repository URL."
        )


    owner = path_parts[0]

    repo = path_parts[1]


    if repo.endswith(
        ".git"
    ):

        repo = repo[:-4]


    return owner, repo


# ============================================================
# GITHUB GET REQUEST
# ============================================================

def github_get(
    url,
    params=None,
):

    try:

        response = requests.get(
            url,
            headers=get_github_headers(),
            params=params,
            timeout=REQUEST_TIMEOUT,
        )


        if response.status_code == 404:

            raise ValueError(
                "GitHub repository/resource nahi mila. "
                "Repository private ho sakta hai ya URL galat hai."
            )


        if response.status_code == 403:

            raise ValueError(
                "GitHub API access/rate limit issue. "
                "GITHUB_TOKEN configure karo."
            )


        response.raise_for_status()


        return response.json()


    except requests.Timeout as error:

        raise RuntimeError(
            "GitHub request timeout ho gaya."
        ) from error


    except requests.RequestException as error:

        raise RuntimeError(
            f"GitHub API request failed: {error}"
        ) from error


# ============================================================
# GET REPOSITORY INFORMATION
# ============================================================

def get_repository_info(
    repo_url
):

    owner, repo = (
        parse_github_repo_url(
            repo_url
        )
    )


    api_url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}"
    )


    data = github_get(
        api_url
    )


    return {
        "owner": owner,
        "name": repo,
        "full_name": data.get(
            "full_name",
            f"{owner}/{repo}"
        ),
        "description": (
            data.get("description")
            or ""
        ),
        "default_branch": data.get(
            "default_branch",
            "main"
        ),
        "language": (
            data.get("language")
            or ""
        ),
        "stars": data.get(
            "stargazers_count",
            0
        ),
        "forks": data.get(
            "forks_count",
            0
        ),
        "open_issues": data.get(
            "open_issues_count",
            0
        ),
        "html_url": data.get(
            "html_url",
            repo_url
        ),
        "private": data.get(
            "private",
            False
        ),
    }


# ============================================================
# CHECK SUPPORTED CODE FILE
# ============================================================

def is_supported_repository_file(
    path
):

    filename = os.path.basename(
        path
    ).lower()


    if filename in IMPORTANT_FILENAMES:

        return True


    _, extension = os.path.splitext(
        filename
    )


    return (
        extension
        in SUPPORTED_EXTENSIONS
    )


# ============================================================
# GET REPOSITORY TREE
# ============================================================

def get_repository_tree(
    repo_url
):

    info = get_repository_info(
        repo_url
    )


    owner = info["owner"]

    repo = info["name"]

    branch = info[
        "default_branch"
    ]


    api_url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}/git/"
        f"trees/{branch}"
    )


    data = github_get(
        api_url,
        params={
            "recursive": "1"
        },
    )


    tree = data.get(
        "tree",
        []
    )


    files = []


    for item in tree:

        if item.get(
            "type"
        ) != "blob":

            continue


        path = item.get(
            "path",
            ""
        )


        if not path:

            continue


        if not is_supported_repository_file(
            path
        ):

            continue


        files.append(
            {
                "path": path,
                "size": item.get(
                    "size",
                    0
                ),
                "sha": item.get(
                    "sha",
                    ""
                ),
            }
        )


    return info, files


# ============================================================
# GET FILE CONTENT
# ============================================================

def get_repository_file(
    owner,
    repo,
    path,
):

    api_url = (
        f"{GITHUB_API_BASE}/repos/"
        f"{owner}/{repo}/contents/"
        f"{path}"
    )


    data = github_get(
        api_url
    )


    if isinstance(
        data,
        list
    ):

        return ""


    if data.get(
        "type"
    ) != "file":

        return ""


    encoded_content = data.get(
        "content"
    )


    encoding = data.get(
        "encoding"
    )


    if not encoded_content:

        return ""


    if encoding != "base64":

        return ""


    try:

        decoded = base64.b64decode(
            encoded_content
        )


        text = decoded.decode(
            "utf-8",
            errors="replace"
        )


    except Exception:

        return ""


    if len(text) > MAX_FILE_CHARACTERS:

        text = (
            text[:MAX_FILE_CHARACTERS]
            + "\n\n[File truncated]"
        )


    return text


# ============================================================
# FILE PRIORITY
# ============================================================

def repository_file_priority(
    file_info
):

    path = file_info[
        "path"
    ]


    filename = os.path.basename(
        path
    ).lower()


    if filename == "readme.md":

        return 0


    if filename in {
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "dockerfile",
    }:

        return 1


    # Source code
    return 2


# ============================================================
# BUILD REPOSITORY CONTEXT
# ============================================================

def build_repository_context(
    repo_url,
):

    info, files = get_repository_tree(
        repo_url
    )


    files = sorted(
        files,
        key=repository_file_priority,
    )


    files = files[
        :MAX_FILES
    ]


    context_parts = []


    total_characters = 0


    for file_info in files:

        path = file_info[
            "path"
        ]


        text = get_repository_file(
            info["owner"],
            info["name"],
            path,
        )


        if not text:

            continue


        file_context = f"""
========================================
FILE: {path}
========================================

{text}
""".strip()


        remaining = (
            MAX_REPOSITORY_CHARACTERS
            - total_characters
        )


        if remaining <= 0:

            break


        if len(
            file_context
        ) > remaining:

            file_context = (
                file_context[
                    :remaining
                ]
                + "\n\n"
                + "[Repository context truncated]"
            )


        context_parts.append(
            file_context
        )


        total_characters += len(
            file_context
        )


        if (
            total_characters
            >= MAX_REPOSITORY_CHARACTERS
        ):

            break


    repository_header = f"""
GITHUB REPOSITORY

Repository:
{info["full_name"]}

Description:
{info["description"]}

Primary language:
{info["language"]}

Default branch:
{info["default_branch"]}

GitHub URL:
{info["html_url"]}

FILES:
""".strip()


    repository_context = (
        repository_header
        + "\n\n"
        + "\n\n".join(
            context_parts
        )
    )


    return {
        "info": info,
        "files": files,
        "context": repository_context,
    }
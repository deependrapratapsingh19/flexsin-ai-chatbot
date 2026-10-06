import os
from typing import Any

import requests


# ============================================================
# CONFIGURATION
# ============================================================

BRAVE_SEARCH_URL = (
    "https://api.search.brave.com/res/v1/web/search"
)

DEFAULT_RESULT_COUNT = 8

MAX_RESULT_COUNT = 20

REQUEST_TIMEOUT = 20


# ============================================================
# GET API KEY
# ============================================================

def get_brave_api_key():

    api_key = os.getenv(
        "BRAVE_SEARCH_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "BRAVE_SEARCH_API_KEY nahi mila. "
            ".env file me Brave Search API key add karo."
        )

    return api_key


# ============================================================
# CLEAN VALUE
# ============================================================

def clean_value(value):

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# SEARCH WEB
# ============================================================

def search_web(
    query,
    count=DEFAULT_RESULT_COUNT,
    country="IN",
    search_lang="en",
    freshness=None,
):

    if not query:

        raise ValueError(
            "Search query empty hai."
        )


    query = query.strip()


    if not query:

        raise ValueError(
            "Search query empty hai."
        )


    api_key = get_brave_api_key()


    # --------------------------------------------------------
    # Keep count inside safe range
    # --------------------------------------------------------

    count = max(
        1,
        min(
            int(count),
            MAX_RESULT_COUNT,
        )
    )


    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }


    params = {
        "q": query,
        "count": count,
        "country": country,
        "search_lang": search_lang,
        "safesearch": "moderate",
    }


    # --------------------------------------------------------
    # Optional freshness
    #
    # pd = past day
    # pw = past week
    # pm = past month
    # py = past year
    # --------------------------------------------------------

    if freshness:

        params["freshness"] = freshness


    try:

        response = requests.get(
            BRAVE_SEARCH_URL,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )


        response.raise_for_status()


        payload = response.json()


    except requests.Timeout as error:

        raise RuntimeError(
            "Web search timeout ho gaya. "
            "Please try again."
        ) from error


    except requests.RequestException as error:

        raise RuntimeError(
            f"Web search request failed: {error}"
        ) from error


    except ValueError as error:

        raise RuntimeError(
            "Search API ne invalid JSON response diya."
        ) from error


    # ========================================================
    # EXTRACT WEB RESULTS
    # ========================================================

    web_section = payload.get(
        "web",
        {}
    )


    raw_results = web_section.get(
        "results",
        []
    )


    results = []


    for index, result in enumerate(
        raw_results,
        start=1
    ):

        title = clean_value(
            result.get("title")
        )

        url = clean_value(
            result.get("url")
        )

        description = clean_value(
            result.get("description")
        )


        # Extra snippets can provide additional context
        extra_snippets = result.get(
            "extra_snippets",
            []
        )


        if not isinstance(
            extra_snippets,
            list
        ):

            extra_snippets = []


        results.append(
            {
                "position": index,
                "title": title,
                "url": url,
                "description": description,
                "extra_snippets": [
                    clean_value(snippet)
                    for snippet in extra_snippets
                    if clean_value(snippet)
                ],
            }
        )


    return {
        "query": query,
        "count": len(results),
        "results": results,
    }


# ============================================================
# FORMAT RESULTS FOR LLM
# ============================================================

def build_web_context(
    search_result
):

    results = search_result.get(
        "results",
        []
    )


    if not results:

        return (
            "No relevant web search results were found."
        )


    context_parts = []


    for result in results:

        position = result.get(
            "position",
            ""
        )

        title = result.get(
            "title",
            ""
        )

        url = result.get(
            "url",
            ""
        )

        description = result.get(
            "description",
            ""
        )


        context = f"""
SOURCE {position}

TITLE:
{title}

URL:
{url}

SNIPPET:
{description}
""".strip()


        extra_snippets = result.get(
            "extra_snippets",
            []
        )


        if extra_snippets:

            context += "\n\nADDITIONAL CONTEXT:\n"

            context += "\n".join(
                f"- {snippet}"
                for snippet
                in extra_snippets[:3]
            )


        context_parts.append(
            context
        )


    return "\n\n".join(
        context_parts
    )


# ============================================================
# FORMAT SOURCES FOR STREAMLIT
# ============================================================

def get_web_sources(
    search_result
):

    sources = []


    for result in search_result.get(
        "results",
        []
    ):

        url = result.get(
            "url"
        )

        title = result.get(
            "title"
        )


        if not url:
            continue


        sources.append(
            {
                "title": (
                    title
                    or url
                ),
                "url": url,
            }
        )


    return
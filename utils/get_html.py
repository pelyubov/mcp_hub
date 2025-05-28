import random
import time

import requests


def get_html_from_url(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    time.sleep(random.uniform(1, 3))

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return ""


def get_title_n_content_from_html(html_content: str) -> tuple[str | None, str]:
    """
    Extract paragraphs from HTML content.

    Args:
        html_content (str): The HTML content as a string.

    Returns:
        list: A list of paragraphs extracted from the HTML.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(
        markup=html_content, features="html.parser", from_encoding="utf8"
    )

    title = soup.title.string if soup.title else None

    return title, soup.get_text()

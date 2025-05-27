from typing import Callable

from pydantic import BaseModel


def get_html_from_url(url: str) -> str:
    """
    Fetch HTML content from a given URL.

    Args:
        url (str): The URL to fetch HTML content from.

    Returns:
        str: The HTML content as a string.
    """
    import requests

    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    return response.text

def paragraph_filter_fn(paragraph: str) -> bool:
    """
    Filter function to determine if a paragraph should be included.

    Args:
        paragraph (str): The paragraph to check.

    Returns:
        bool: True if the paragraph is not empty, False otherwise.
    """
    return paragraph.strip().split().__len__() > 20



def get_title_n_paragraphs_from_html(html_content: str, paragraphs_filter_fn: Callable[[str], bool] = paragraph_filter_fn) -> tuple[str, list[str]]:
    """
    Extract paragraphs from HTML content.

    Args:
        html_content (str): The HTML content as a string.

    Returns:
        list: A list of paragraphs extracted from the HTML.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(markup=html_content, features="html.parser", from_encoding='utf-8')

    title = soup.title.string if soup.title else None
    # Find all paragraph tags
    ps = soup.find_all('p')
    
    return title, [p.get_text().strip() for p in ps if paragraphs_filter_fn(p.get_text())]



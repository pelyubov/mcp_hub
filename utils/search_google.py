from typing import Callable

from googlesearch import search


def default_link_filter_fn(url: str, keywords: set[str] = set(["google", "youtube", "image", "img", "maps", "map"])) -> bool:
    for keyword in keywords:
        if keyword in url:
            return False
    return True


def search_google(query: str, num_results: int = 10, region: str = "vn", start_num: int = 0, link_filter_fn: Callable[[str], bool] = default_link_filter_fn) -> tuple[list, int]:
    """Search Google and return the results."""
    results = []
    while len(results) < num_results:
        for result in search(query, num=num_results, country=region, start=start_num):
            if link_filter_fn is None or link_filter_fn(result):
                if len(results) >= num_results:
                    break
                results.append(result)
        start_num += num_results
    return results, start_num
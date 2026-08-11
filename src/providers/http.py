from typing import Any

import requests


class PublicProviderError(Exception):
    """A public provider returned unusable data or could not be reached."""


def get_json(url: str, params: dict[str, str | int] | None = None) -> Any:
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise PublicProviderError(f"public data request failed: {url}") from exc

"""Utilities for LaCrosse View."""

import aiohttp
from typing import Any
import logging

_LOGGER = logging.getLogger(__name__)


async def request(
    url: str, method: str, websession: aiohttp.ClientSession | None, **kwargs: Any
) -> tuple[aiohttp.ClientResponse, dict[str, Any]]:
    kwargs.setdefault("headers", {})["User-Agent"] = "okhttp/5.0.0-alpha.11"
    if not websession:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
                _LOGGER.debug("Request: %s %s", method, url)
                _LOGGER.debug("Response: %s", await response.text())
                data = await response.json()
    else:
        async with websession.request(method, url, **kwargs) as response:
            _LOGGER.debug("Request: %s %s", method, url)
            _LOGGER.debug("Response: %s", await response.text())
            data = await response.json()

    return response, data

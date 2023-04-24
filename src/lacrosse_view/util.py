"""Utilities for LaCrosse View."""

import aiohttp
from typing import Any


async def request(
    url: str, method: str, websession: aiohttp.ClientSession | None, **kwargs: Any
) -> tuple[aiohttp.ClientResponse, dict[str, Any]]:
    if not websession:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
                data = await response.json()
    else:
        async with websession.request(method, url, **kwargs) as response:
            data = await response.json()

    return response, data

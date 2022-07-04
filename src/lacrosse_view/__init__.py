"""LaCrosse View library."""
# Thanks to Keith Prickett for the original code: https://github.com/keithprickett/lacrosse_weather

from __future__ import annotations
from typing import Any
import aiohttp
from pydantic import BaseModel
from pytz import timezone
import datetime
import asyncio
from collections.abc import Awaitable, Callable


def _retry(
    func: Callable[..., Awaitable[list[Sensor]]]
) -> Callable[..., Awaitable[list[Sensor]]]:
    """Handle query retries."""

    async def wrapper(obj, *args, **kwargs) -> list[Sensor]:
        """Wrap all query functions."""
        update_retries = 5
        while update_retries > 0:
            try:
                result = await func(obj, *args, **kwargs)
                break
            except HTTPError as error:
                update_retries -= 1
                if update_retries == 0:
                    raise error
                await asyncio.sleep(1)

        return result

    return wrapper


class LaCrosse:
    """Basic class to hold the LaCrosse data."""

    token: str = ""
    websession: aiohttp.ClientSession | None = None

    def __init__(self, websession: aiohttp.ClientSession | None = None):
        self.websession = websession

    @_retry
    async def login(self, email: str, password: str) -> bool:
        """Login to the LaCrosse API."""
        login_url = (
            "https://www.googleapis.com/"
            "identitytoolkit/v3/relyingparty/verifyPassword?"
            "key=AIzaSyD-Uo0hkRIeDYJhyyIg-TvAv8HhExARIO4"
        )

        payload = {"email": email, "password": password, "returnSecureToken": True}

        data: dict[str, Any]

        if not self.websession:
            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, json=payload) as response:
                    data = await response.json()
                    try:
                        self.token: str = data["idToken"]
                    except KeyError:
                        raise LoginError("Invalid credentials.")
        else:
            async with self.websession.post(login_url, json=payload) as response:
                data = await response.json()
                try:
                    self.token: str = data["idToken"]
                except KeyError:
                    raise LoginError("Invalid credentials.")

        if self.token is None:
            raise LoginError("Login failed. Check credentials and try again.")

        return True

    @_retry
    async def get_locations(self) -> list[Location]:
        """Get all locations."""
        if self.token == "":
            raise LoginError("Login first.")

        locations_url = (
            "https://lax-gateway.appspot.com/"
            "_ah/api/lacrosseClient/v1.1/active-user/locations"
        )
        headers = {"Authorization": "Bearer " + self.token}

        data: dict[str, Any]

        if not self.websession:
            async with aiohttp.ClientSession() as session:
                async with session.get(locations_url, headers=headers) as response:
                    if response.status != 200:
                        raise HTTPError(
                            "Failed to get locations, status code: "
                            + str(response.status)
                        )
                    data = await response.json()
        else:
            async with self.websession.get(locations_url, headers=headers) as response:
                if response.status != 200:
                    raise HTTPError(
                        "Failed to get locations, status code: " + str(response.status)
                    )
                data = await response.json()

        return [
            Location(id=location["id"], name=location["name"])
            for location in data["items"]
        ]

    @_retry
    async def get_sensors(
        self,
        location: Location,
        tz: str = "America/New_York",
        start: str = "",
        end: str = "",
    ) -> list[dict[str, Any]]:
        """Get all sensors."""

        if self.token == "":
            raise LoginError("Login first.")

        # Validate the timezone
        timezone(tz)

        # Check if the start and end times are valid
        if start != "" and end != "":
            # Check if it is a valid Unix timestamp
            try:
                datetime.datetime.fromtimestamp(int(start))
                datetime.datetime.fromtimestamp(int(end))
            except ValueError:
                raise ValueError("Invalid start or end time.")
            if start > end:
                raise ValueError("Start time cannot be after end time.")

        devices = list()
        headers = {"Authorization": "Bearer " + self.token}

        sensors_url = (
            "https://lax-gateway.appspot.com/"
            "_ah/api/lacrosseClient/v1.1/active-user/location/"
            + str(location.id)
            + "/sensorAssociations?prettyPrint=false"
        )
        if not self.websession:
            async with aiohttp.ClientSession() as session:
                async with session.get(sensors_url, headers=headers) as response:
                    if response.status != 200:
                        raise HTTPError(
                            "Failed to get location, status code: "
                            + str(response.status)
                        )
                    data = await response.json()
        else:
            async with self.websession.get(sensors_url, headers=headers) as response:
                if response.status != 200:
                    raise HTTPError(
                        "Failed to get location, status code: " + str(response.status)
                    )
                data = await response.json()

        for device in data.get("items"):
            sensor = device.get("sensor")
            device = {
                "name": device.get("name"),
                "device_id": device.get("id"),
                "type": sensor.get("type").get("name"),
                "sensor_id": sensor.get("id"),
                "sensor_field_names": [
                    x for x in sensor.get("fields") if x.lower() != "notsupported"
                ],
                "location": location,
                "permissions": sensor.get("permissions"),
                "model": sensor.get("type").get("name"),
            }

            fields_str = (
                ",".join(device["sensor_field_names"])
                if device["sensor_field_names"]
                else None
            )

            aggregates = "ai.ticks.1"

            url = (
                "https://ingv2.lacrossetechnology.com/"
                "api/v1.1/active-user/device-association/ref.user-device.{id}/"
                "feed?fields={fields}&"
                "tz={tz}&"
                "from={_from}&"
                "to={_to}&"
                "aggregates={agg}&"
                "types=spot".format(
                    id=device["device_id"],
                    fields=fields_str,
                    tz=tz,
                    _from=start,
                    _to=end,
                    agg=aggregates,
                )
            )

            headers = {"Authorization": "Bearer " + self.token}

            if not self.websession:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            raise HTTPError(
                                "Failed to get sensor, status code: "
                                + str(response.status)
                            )
                        data = await response.json()
            else:
                async with self.websession.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise HTTPError(
                            "Failed to get sensor, status code: " + str(response.status)
                        )
                    data = await response.json()

            device["data"] = data.get("ref.user-device." + device["device_id"])[
                "ai.ticks.1"
            ]["fields"]

            device = Sensor(**device)

            devices.append(device)

        return devices

    @_retry
    async def logout(self) -> bool:
        """Logout from the LaCrosse API."""
        url = (
            "https://lax-gateway.appspot.com/"
            "_ah/api/lacrosseClient/v1.1/user/devices"
            "?prettyPrint=false"
        )
        headers = {"Authorization": "Bearer " + self.token}
        body = {
            "firebaseRegistrationToken": "fpxASxqXfE_rvyNdMGe2Bd:APA91bH53k_fq0pWNpIwTla9CiOQgx8G1PLrKpp74AfdTHPgwh3g0RZNopQQ-POqmNVyaW_2vT9I7nYz0RdWqY1DU4uNIx4vOzZPQwn7mHD6uvtYH8qxwedB3cLOBmSpOdAOkH2jTN4c"
        }
        if not self.websession:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, json=body, headers=headers) as response:
                    if response.status != 200:
                        raise HTTPError(
                            "Failed to logout, status code: " + str(response.status)
                        )
                    data = await response.json()
                    if data["message"] != "Operation Successful":
                        raise HTTPError("Failed to logout, message: " + data["message"])
                    self.token = ""
                    return True
        else:
            async with self.websession.delete(
                url, json=body, headers=headers
            ) as response:
                if response.status != 200:
                    raise HTTPError(
                        "Failed to logout, status code: " + str(response.status)
                    )
                data = await response.json()
                if data["message"] != "Operation Successful":
                    raise HTTPError("Failed to logout, message: " + data["message"])
                self.token = ""
                return True


class Location(BaseModel):
    """Location."""

    id: str
    name: str


class Sensor(BaseModel):
    """Results from get_sensors."""

    name: str
    device_id: str
    type: str
    sensor_id: str
    sensor_field_names: list[str]
    location: Location
    permissions: dict[str, bool]
    model: str
    data: dict[str, Any]


class LaCrosseError(Exception):
    """Basic exception class for LaCrosse errors."""


class LoginError(LaCrosseError):
    """Exception for login errors."""


class HTTPError(LaCrosseError):
    """Exception for HTTP errors."""

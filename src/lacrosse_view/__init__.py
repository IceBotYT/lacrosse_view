"""LaCrosse View library."""
# Thanks to Keith Prickett for the original code: https://github.com/keithprickett/lacrosse_weather

from __future__ import annotations
from typing import Any
import aiohttp
from pydantic import BaseModel
from aiozoneinfo import async_get_time_zone
import datetime

from .const import DEVICE_URL, LOGIN_URL, SENSORS_URL, LOCATIONS_URL
from .util import request


class LaCrosse:
    """Basic class to hold the LaCrosse data."""

    token: str = ""
    websession: aiohttp.ClientSession | None = None

    def __init__(self, websession: aiohttp.ClientSession | None = None):
        self.websession = websession

    async def login(self, email: str, password: str) -> bool:
        """Login to the LaCrosse API."""

        payload = {"email": email, "password": password, "returnSecureToken": True}

        response, data = await request(LOGIN_URL, "POST", self.websession, json=payload)

        try:
            self.token: str = data["idToken"]
        except KeyError as e:
            raise LoginError("Invalid credentials.", data) from e

        if self.token is None:
            raise LoginError("Login failed. Check credentials and try again.")

        return True

    async def get_locations(self) -> list[Location]:
        """Get all locations."""
        if self.token == "":
            raise LoginError("Login first.")

        headers = {"Authorization": f"Bearer {self.token}"}

        response, data = await request(
            LOCATIONS_URL, "GET", self.websession, headers=headers
        )

        if response.status != 200:
            raise HTTPError(
                f"Failed to get locations, status code: {str(response.status)}",
                data,
            )

        return [
            Location(id=location["id"], name=location["name"])
            for location in data["items"]
        ]

    async def get_sensors(
        self,
        location: Location,
        tz: str = "America/New_York",
        start: str = "",
        end: str = "",
    ) -> list[Sensor]:
        """Get all sensors."""

        if self.token == "":
            raise LoginError("Login first.")

        # Validate the timezone
        await async_get_time_zone(tz)

        # Check if the start and end times are valid
        if start != "" and end != "":
            # Check if it is a valid Unix timestamp
            try:
                datetime.datetime.fromtimestamp(int(start))
                datetime.datetime.fromtimestamp(int(end))
            except ValueError as e:
                raise ValueError("Invalid start or end time.") from e
            if start > end:
                raise ValueError("Start time cannot be after end time.")

        headers = {"Authorization": f"Bearer {self.token}"}

        sensors_url = SENSORS_URL.format(location_id=str(location.id))

        response, data = await request(
            sensors_url, "GET", self.websession, headers=headers
        )

        if response.status != 200:
            raise HTTPError(
                f"Failed to get location, status code: {str(response.status)}",
                data,
            )

        aggregates = "ai.ticks.1"

        devices = []
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

            url = DEVICE_URL.format(
                id=device["device_id"],
                fields=fields_str,
                tz=tz,
                _from=start,
                _to=end,
                agg=aggregates,
            )

            headers = {"Authorization": f"Bearer {self.token}"}

            response, data = await request(url, "GET", self.websession, headers=headers)

            if response.status != 200:
                raise HTTPError(
                    f"Failed to get sensor, status code: {str(response.status)}", data
                )

            device["data"] = data.get("ref.user-device." + device["device_id"])[
                "ai.ticks.1"
            ]["fields"]

            device = Sensor(**device)

            devices.append(device)

        return devices

    async def logout(self) -> bool:
        """Logout from the LaCrosse API."""
        url = (
            "https://lax-gateway.appspot.com/"
            "_ah/api/lacrosseClient/v1.1/user/devices"
            "?prettyPrint=false"
        )
        headers = {"Authorization": f"Bearer {self.token}"}
        body = {
            "firebaseRegistrationToken": "fpxASxqXfE_rvyNdMGe2Bd:APA91bH53k_fq0pWNpIwTla9CiOQgx8G1PLrKpp74AfdTHPgwh3g0RZNopQQ-POqmNVyaW_2vT9I7nYz0RdWqY1DU4uNIx4vOzZPQwn7mHD6uvtYH8qxwedB3cLOBmSpOdAOkH2jTN4c"
        }

        response, data = await request(
            url, "DELETE", self.websession, json=body, headers=headers
        )

        if response.status != 200:
            raise HTTPError(f"Failed to logout, status code: {str(response.status)}")
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

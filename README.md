> [!IMPORTANT]
> This project is no longer being updated. I no longer own a LaCrosse View device and I have moved on to other projects.
> I will only do general fixes required by Home Assistant. If you would like to to take over this repo and maintain it, please let me know.

# La Crosse View

A library for retrieving data from [La Crosse View-connected sensors](https://www.lacrossetechnology.com/collections/lacrosse-view-connected).

## Disclaimer

This library is **NOT** for the Jeelink LaCrosse sensors. You can find that library [here](https://pypi.org/project/pylacrosse/).
There is also a [Home Assistant integration](https://home-assistant.io/integrations/lacrosse) for the Jeelink LaCrosse sensors.

## Installation

Run this in your terminal:
```
pip install lacrosse_view
```

## Usage

This example shows how to get the latest data from every sensor connected to the first location on your account.
```python

from lacrosse_view import LaCrosse
import asyncio
from datetime import datetime, timedelta
import time

async def get_data():
    api = LaCrosse()
    # Log in to your LaCrosse View account
    await api.login('username', 'password')
    # Get the sensors from the first location on the account
    locations = await api.get_locations()
    startTime = datetime.now() - timedelta(minutes=1)
    endTime = datetime.now()
    startTimeUnix = time.mktime(startTime.timetuple())
    endTimeUnix = time.mktime(endTime.timetuple())
    sensors = await api.get_sensors(locations[0], tz="America/Vancouver", start=startTimeUnix, end=endTimeUnix)
 
    for sensor in sensors:
        for field in sensor.sensor_field_names:
            # Each value is a dictionary with keys "s" and "u". "s" is the value and "u" is the Unix timestamp for it.
            value = sensor.data[field]["values"][-1]["s"]
            print(
                f"{sensor.name} {field}: {value}"
            )
    
    await api.logout()

asyncio.run(get_data())


```

## Questions?
If you have any questions, please, don't hesitate to [open an issue](https://github.com/IceBotYT/lacrosse_view/issues/new).

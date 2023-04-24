"""Constants for LaCrosse View."""

DEVICE_URL = (
    "https://ingv2.lacrossetechnology.com/"
    "api/v1.1/active-user/device-association/ref.user-device.{id}/"
    "feed?fields={fields}&"
    "tz={tz}&"
    "from={_from}&"
    "to={_to}&"
    "aggregates={agg}&"
    "types=spot"
)
SENSORS_URL = "https://lax-gateway.appspot.com/_ah/api/lacrosseClient/v1.1/active-user/location/{location_id}/sensorAssociations?prettyPrint=false"
LOCATIONS_URL = (
    "https://lax-gateway.appspot.com/"
    "_ah/api/lacrosseClient/v1.1/active-user/locations"
)
LOGIN_URL = (
    "https://www.googleapis.com/"
    "identitytoolkit/v3/relyingparty/verifyPassword?"
    "key=AIzaSyD-Uo0hkRIeDYJhyyIg-TvAv8HhExARIO4"
)

"""Load API v1 resources so their routes are attached to their namespaces.

The namespaces are created in ``nsmodels`` modules and registered with the
Flask-RESTX API before it is initialized on the Flask application.
"""

from app.api.v1.alert_settings import AlertSettingsApi
from app.api.v1.devices import DevicesApi
from app.api.v1.earthquakes import EarthquakesApi
from app.api.v1.felt_reports import FeltReportsApi
from app.api.v1.location_settings import LocationSettingsApi
from app.api.v1.notifications import (
    NotificationAttemptsApi,
    NotificationStatsApi,
    NotificationsApi,
)

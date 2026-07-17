from typing import Literal

AlertSeverity = Literal["warning", "error"]

# --- Configuration ---
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
REVERSE_GEOCODING_API_URL = "https://nominatim.openstreetmap.org/reverse"
REVERSE_GEOCODING_USER_AGENT = "WeatherAppStreamlit/1.0 (+https://github.com/Anton-Georgiev1/Weather-app)"
SKYWATCH_URL = "https://skywatchbg.vercel.app/"
LAST_CITY_STORAGE_KEY = "last_city"
LAST_COUNTRY_STORAGE_KEY = "last_country"
LAST_LANG_STORAGE_KEY = "last_lang"

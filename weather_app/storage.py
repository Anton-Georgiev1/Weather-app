from streamlit_local_storage import LocalStorage  # pyright: ignore[reportMissingTypeStubs]

from weather_app.config import LAST_CITY_STORAGE_KEY, LAST_COUNTRY_STORAGE_KEY, LAST_LANG_STORAGE_KEY


def load_last_location(local_storage: LocalStorage) -> dict[str, str]:
    """Read the last used city/country from the browser's local storage so the search
    fields can be pre-filled on startup. Local storage (not a server-side file) is used
    because this app is hosted for multiple visitors, and each browser must only see its
    own last-used location, not one shared across every visitor."""
    city = local_storage.getItem(LAST_CITY_STORAGE_KEY)
    country = local_storage.getItem(LAST_COUNTRY_STORAGE_KEY)
    return {"city": city or "", "country": country or ""}

def save_last_location(local_storage: LocalStorage, city: str, country: str) -> None:
    """Persist the last used city/country to the browser's local storage so it survives
    app restarts and reloads. Empty values are left untouched rather than overwriting a
    previously remembered location."""
    if city:
        local_storage.setItem(LAST_CITY_STORAGE_KEY, city, key="set_last_city")
    if country:
        local_storage.setItem(LAST_COUNTRY_STORAGE_KEY, country, key="set_last_country")

def load_last_language(local_storage: LocalStorage) -> str | None:
    """Read the last selected UI language from the browser's local storage."""
    return local_storage.getItem(LAST_LANG_STORAGE_KEY)

def save_last_language(local_storage: LocalStorage, lang: str) -> None:
    """Persist the selected UI language to the browser's local storage so it's restored
    on the next visit instead of resetting to English."""
    local_storage.setItem(LAST_LANG_STORAGE_KEY, lang, key="set_last_lang")

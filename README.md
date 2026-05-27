# 🌤️ Weather Pro Dashboard

A high-performance, professional-grade weather application built with **Python**, **Streamlit**, and the **Open-Meteo API**. This dashboard provides a sleek, "AccuWeather-inspired" experience, featuring real-time data, high-resolution hourly tracks, and interactive global radar—all without requiring an API key.

---

## Key Features

- **Intelligent Search:** Auto-locate any city and country globally with smart geocoding.
- **24-Hour Precise Track:** Get a detailed hourly breakdown of temperature, wind speed, humidity, and rain probability.
- **Comprehensive Forecasts:**
  - **7-Day Quick View:** High-impact visual cards for your immediate week.
  - **14-Day Outlook:** A two-week grid for extended planning.
  - **30-Day Trends:** Long-range seasonal ensemble data to predict upcoming weather patterns.
- **Live Interactive Radar:** High-accuracy global radar powered by **Windy**, perfectly synced to your searched location.
- **Rain Intuition:** Smart UI highlighting for days with significant precipitation risk.
- **Adaptive Theme:** Exclusive support for professional **Light** and **Dark** modes (system overrides disabled for consistency).

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- `pip` (Python package manager)

### Installation

1. **Clone the repository:**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Dashboard:**
   ```bash
   streamlit run Weather_app.py
   ```

---

## Technical Overview

### Tech Stack
- **Frontend:** Streamlit (Custom CSS & HTML components)
- **Data Engine:** Open-Meteo API (Forecast & Seasonal endpoints)
- **Visuals:** Windy.com Interactive Embeds
- **Data Processing:** Pandas & Httpx

### Testing
The project includes a robust suite of unit tests powered by `pytest` and `pytest-httpx`.
To run the tests:
```bash
pytest test_weather_app.py
```

---

## Reliability & Robustness

- **Defensive Design:** Handles partial API responses and malformed data without crashing.
- **Edge-Case Handling:** Graceful fallbacks for seasonal trend data and extreme coordinate values.
- **Privacy First:** No API keys, no tracking, just pure weather data.

---

*Weather data provided by [Open-Meteo](https://open-meteo.com/). Radar visuals by [Windy.com](https://www.windy.com/).*

# Weather App Dashboard

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-18%20passed-success)](test_weather_app.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **"Weather is more than just data; it's the backdrop to our lives."**  
> This dashboard is a professional-grade meteorological companion designed to bridge the gap between cold, raw data and meaningful, human-centric planning.

---

## The Vision

Most weather apps overwhelm users with cluttered grids and obscure metrics. This project was born from the belief that **clarity builds confidence**. We've stripped away the noise to focus on what matters:
- **How it feels:** Beyond degrees, we prioritize "Real Feel" and humidity trends.
- **When it matters:** Surgical 24-hour views for immediate planning.
- **Where you are:** Instant, intelligent geocoding that understands you.

## Key Features

### Confidence in Every Plan
- **Smart Global Search:** A sophisticated geocoding engine that finds your location instantly, handling the "heavy lifting" so you don't have to.
- **Precision 24-Hour Track:** A high-fidelity, hour-by-hour view designed to help you navigate your day with absolute certainty.
- **Multi-Horizon Forecasts:** 
  - **7-Day Insight:** Large, readable cards for immediate tactical decisions.
  - **14-Day Outlook:** A comprehensive grid for long-term strategic visibility.
- **Deep-Dive Drilldown:** Click any day to reveal a specific 24-hour breakdown. Because sometimes, you need the details.

### Safety & Awareness
- **Intelligent Alerts:** Proactive, color-coded warnings for severe storms, heavy snow, and high-wind advisories. We watch the skies so you can stay safe.
- **Live Radar Nowcast:** A high-definition, interactive global radar powered by **Windy**, centered precisely on your world.
- **Trend Metrics:** Deep-dive into real-feel temperatures, humidity averages, and wind gusts.

###  Global by Design
- **Full Bilingual Support:** Seamlessly switch between **English** and **Bulgarian**. Localized date formatting and condition descriptions make it feel like home, no matter where you are.
- **Open-Source Integrity:** Powered by the **Open-Meteo API**. High-fidelity insights, zero API keys required.

---

## Technical Excellence

As a senior-led project, the architecture is as polished as the UI:
- **Clean Architecture (SRP):** Logic is strictly decoupled. Geocoding, weather processing, and UI rendering live in their own testable domains.
- **Defensive Engineering:** We use "safe-fetch" patterns and robust error handling to ensure the app remains stable, even when external APIs don't.
- **Modern Tech Stack:**
  - **Frontend:** Streamlit with custom CSS/HTML injection for a bespoke, premium feel.
  - **Performance:** `httpx` for high-performance, asynchronous-ready requests.
  - **Data Integrity:** `pandas` for advanced time-series manipulation.

### Reliability as a Standard
We don't guess—we verify. The core business logic is protected by a **18-test suite**, ensuring that every calculation and translation is accurate.

```bash
# Run the verification suite
pytest test_weather_app.py
```

---

##  Getting Started

### Prerequisites
- **Python 3.12** or higher (utilizing the latest language features).

### Installation

1. **Clone the repository:**
2. **Set up your environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Launch the Experience:**
   ```bash
   streamlit run Weather_app.py
   ```

---

## Contributing

This is a community-driven project. Whether you're fixing a typo or adding a new translation, your contribution is valued.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

Distributed under the MIT License. Crafted with for the open-source community.

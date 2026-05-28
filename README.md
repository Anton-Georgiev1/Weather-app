# Weather App Dashboard

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-18%20passed-success)](test_weather_app.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A sophisticated, professional-grade weather application that balances technical precision with a human-centric user experience. Built with **Python**, **Streamlit**, and the **Open-Meteo API**, this dashboard delivers high-fidelity weather insights without the complexity of API keys or cluttered interfaces.

---

## The Vision

Weather data is often cold and overwhelming. This dashboard is designed to be **intuitive and supportive**. Whether you are planning a weekend hike or just checking if you need an umbrella for your commute, the Weather App Dashboard provides the right information at the right time, with visual cues that "speak" weather intuitively.

## Key Features

- **Smart Global Search:** Instantly locate any city in the world. Our geocoding engine handles the heavy lifting, even with minimal input.
- **Precision 24-Hour Track:** A surgical view of the next 24 hours, helping you navigate your day with confidence.
- **Dynamic Outlooks:**
  - **7-Day Insight:** Large, readable cards for immediate planning.
  - **14-Day Forecast:** A comprehensive grid for long-term visibility.
- **Live Radar Integration:** A high-definition, interactive global radar powered by **Windy**, centered precisely on your location.
- **Intelligent Alerts:** Proactive warnings for severe storms, heavy snow, and high-wind advisories, ensuring you're never caught off guard.
- **Humidity & Wind Trends:** Deep-dive metrics including real-feel temperatures and daily humidity averages.

---

## Technical Excellence

### Architecture & Design
This project isn't just about looks-it's built on a foundation of clean code and architectural integrity:
- **SRP (Single Responsibility Principle):** Logic is decoupled into dedicated, testable functions for alerts, data processing, and UI generation.
- **Defensive Engineering:** Robust error handling ensures the app remains stable even when external APIs face issues or return partial data.
- **Modern Tech Stack:**
  - **Frontend:** Streamlit with custom CSS/HTML component injection.
  - **API Layer:** `httpx` for high-performance, asynchronous-ready requests.
  - **Processing:** `pandas` for time-series data manipulation.

### Reliability
We take stability seriously. Every core business logic-from alert detection to humidity averages-is verified by a **18-test suite**.

```bash
# Run the test suite
pytest test_weather_app.py
```

---

## Getting Started

### Prerequisites
- Python 3.12 or higher

### Installation

1. **Clone the repository:**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the app:**
   ```bash
   streamlit run Weather_app.py
   ```

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

---

# 🏈🏀 ScoreBet – Sports Prediction App (NBA & NFL)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![Machine Learning](https://img.shields.io/badge/ML-Pipeline-orange?logo=scikit-learn)
![API](https://img.shields.io/badge/API-Sports%20Data-blueviolet?logo=api)
![License](https://img.shields.io/badge/License-MIT-green)

**ScoreBet** is an advanced sports analytics application that provides real-time game tracking, AI-powered predictions, and player prop recommendations for both **NBA** and **NFL**.  
Built with **Streamlit**, it combines data from multiple APIs (ESPN, TheSportsDB, and API-Sports) to generate dynamic picks and insights.

---

## 🚀 Features

### 🏀 **NBA Module**
- **NBA Games:**  
  Displays all daily games grouped by date, including:
  - Live scores (`🟢 Live`) and final results (`🔴 Finished`)
  - Broadcast channel and time (converted to local timezone)
  - Automatic cleanup after midnight

- **NBA Picks:**  
  AI-generated predictions with:
  - Confidence bars (color-coded)
  - Match outcomes tracking (✅ Correct / ❌ Wrong)
  - Updated automatically with real games

- **NBA Model:**  
  Statistical prediction model for game outcomes based on historical data.

- **NBA Player Picks:**  
  Individual player prop recommendations including:
  - **Low risk bets:** odds between 1.01 and 2.10  
  - **High risk bets:** odds above 6.00  
  - Metrics for points, rebounds, and assists  
  - Player portraits via **TheSportsDB API**

---

### 🏈 **NFL Module**
*(Currently in development — mirrors NBA module structure)*  
- **NFL Games:**  
  Weekly game schedule display (Week 1–18) with date grouping  
- **NFL Picks:**  
  AI predictions for team outcomes  
- **NFL Model:**  
  Predictive ML model for win/loss probabilities  
- **NFL Player Picks:**  
  Individual props (touchdowns, yards, receptions)

All NFL data will be powered by the **API-Sports PRO Plan**, ensuring complete coverage for the **2025/26 season**.

---

## 📦 Project Structure

SCOREBET/
├── .streamlit/ # Streamlit configuration
├── src/
│ ├── api/ # External API integrations
│ │ ├── nba_data_api.py
│ │ ├── nfl_games_api.py
│ │ ├── odds_players_api.py
│ │ └── ...
│ ├── ml/ # Machine Learning modules
│ │ ├── model_train.py
│ │ ├── predict.py
│ │ └── pipeline.py
│ ├── ui/ # Streamlit app UI
│ │ ├── pages/
│ │ │ ├── 1_NBA_Games.py
│ │ │ ├── 2_NBA_Model.py
│ │ │ ├── 3_NBA_Picks.py
│ │ │ ├── 4_NBA_PlayerPicks.py
│ │ │ ├── 1_NFL_Games.py
│ │ │ └── ...
│ │ └── app.py
│ └── utils/ # Configs, logging, and helpers
│
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration
├── .gitignore # Ignored files and directories
└── README.md

## ⚙️ Installation

1️⃣ Clone the repository
```bash
git clone https://github.com/tutucanto10/ScoreBet.git
cd ScoreBet

2️⃣ Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # On Linux/Mac
.venv\Scripts\activate         # On Windows

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Create your .env file

Inside the project root, create a .env file with your API keys:

API_SPORTS_KEY=your_api_key_here
THESPORTSDB_KEY=your_api_key_here

5️⃣ Run the app
streamlit run src/ui/app.py

🧠 Tech Stack
Component	Description
Python 3.11	Core language
Streamlit	Web framework
pandas / NumPy	Data processing
scikit-learn	Machine learning
Requests / Asyncio	API communication
TheSportsDB	Player & team data
API-Sports	Live odds and match data
ESPN API	Real-time game updates

📅 Roadmap

- NBA Module fully implemented

- NBA Player Picks with portrait support

- Streamlit UI layout finalized

- NFL integration (Week-based layout)

- Player Props for NFL

- Dashboard performance metrics

🤝 Contributing

Contributions are welcome!
If you’d like to improve or extend ScoreBet, please fork the repo and submit a pull request.

🛡️ License

This project is licensed under the MIT License — feel free to use, modify, and share.

Developed with ❤️ by Artur Canto

Data-driven sports prediction for NBA & NFL fans.

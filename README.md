# Urban Mobility Flow Analysis with Graph Theory

Academic research project that models urban transport flows in São Paulo using **Graph Theory**, integrating real-time public transport data (SPTrans), social network datasets, and points of interest (Google Places).

> **Undergraduate Research (Iniciação Científica)**  
> Institution: Faculdade Impacta  
> Advisor: Prof. Kyung Moo Kim  
> Period: 2025 – 2026

---

## Overview

This project investigates how social dynamics and digital influence affect urban mobility patterns in São Paulo.

It combines:

- Real-time bus position data from **SPTrans (Olho Vivo API)**
- Historical social network datasets (Brightkite, Gowalla, etc.)
- Points of Interest popularity from **Google Places**
- Graph Theory algorithms (**Maximum Flow – Edmonds-Karp**)

The main goal is to model the flow of people between social activity zones and destinations, identifying potential bottlenecks and influence patterns in the urban transport network.

---

## Key Features

- Real-time data collection from SPTrans API
- Geocoding and POI enrichment using Google Maps / Places API
- Integration of historical social check-in datasets
- Graph modeling of transport + social influence
- Maximum flow calculation (Edmonds-Karp algorithm)
- Interactive map generation with Folium
- SQL Server data storage and analysis
- Simple forecasting with linear & polynomial regression

---

## Project Structure

```text
project_mobility/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── schema.sql
├── src/
│   ├── config.py                     # Loads secrets from environment
│   ├── collectors/
│   │   └── sptrans_collector.py      # Real-time SPTrans + Google collector
│   ├── analysis/
│   │   ├── flow_analysis.py          # Edmonds-Karp max-flow + map generation
│   │   └── prediction.py             # Regression forecasts
│   └── visualization/
├── scripts/
└── maps/                             # Generated interactive maps (gitignored)
```

---

## Technologies

| Category        | Tools                                      |
|-----------------|--------------------------------------------|
| Language        | Python 3.9+                                |
| Database        | SQL Server + pyodbc                        |
| APIs            | SPTrans Olho Vivo, Google Maps / Places    |
| Graph Theory    | Edmonds-Karp (Maximum Flow)                |
| Visualization   | Folium, Matplotlib                         |
| Data            | Pandas, NumPy, Kaggle datasets             |

---

## Database Schema

| Table                               | Description                                      |
|-------------------------------------|--------------------------------------------------|
| `Coleta_SPTrans`                    | Real-time bus positions                          |
| `Coleta_Google`                     | Geocoded locations and Place IDs                 |
| `Coleta_Google_Popularidade`        | Ratings and popularity of places                 |
| `Coleta_Sociais_Agregados`          | Aggregated social network metrics                |
| `Coleta_Interacao_SocialTransporte` | Relationship between transport and social impact |
| `Coleta_Checkins`                   | Historical social check-ins                      |

---

## How It Works

1. **Data Collection**  
   Continuously collects bus positions from SPTrans and enriches them with Google Places data.

2. **Social Data Integration**  
   Imports historical check-in and engagement datasets to create social activity zones.

3. **Graph Construction**  
   Builds a flow network:
   - Source → Social zones
   - Social zones → Nearby POIs
   - POIs → Sink

4. **Maximum Flow Analysis**  
   Uses the Edmonds-Karp algorithm to calculate the maximum flow and identify saturated edges (bottlenecks).

5. **Visualization**  
   Generates interactive HTML maps showing zones, POIs, and flow intensity.

---

## Getting Started

### Prerequisites

- Python 3.9+
- SQL Server (Express or higher)
- ODBC Driver 17 for SQL Server
- Valid API tokens (SPTrans + Google Maps)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/LuizFernando2-prog/project_mobility.git
cd project_mobility

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in your tokens

# 5. Create the database
# Run schema.sql in SQL Server Management Studio or sqlcmd

# 6. Run the real-time collector
python -m src.collectors.sptrans_collector

# 7. Run flow analysis for a specific year
python -m src.analysis.flow_analysis
```

---

## Research Context

This work is part of an undergraduate research project focused on applying **Graph Theory** to urban mobility problems, specifically studying how social networks and digital platforms influence commuting patterns and transport demand in large cities like São Paulo.

---

## Author

**Luiz Fernando**  
Backend Developer & Computer Engineering student  

- LinkedIn: [luiz-fernando-dev](https://www.linkedin.com/in/luiz-fernando-dev/)
- GitHub: [LuizFernando2-prog](https://github.com/LuizFernando2-prog)

---

## License

This project is intended for academic and research purposes.

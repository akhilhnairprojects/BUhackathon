# Trip Risk Checker — analysis notebooks

Questrom Chart Champ Datathon, BTS 2025 on-time data (200k student sample + 6.4M full file).

Run in order; each notebook writes to outputs/tables and outputs/figures.

| Notebook | What it does |
|---|---|
| 01_cleaning | One cleaning function for sample and full data; outcome definitions (disrupted >=15 min / cancelled / diverted; severe >=60 min); cleaning log |
| 02_eda | Headline patterns: departure hour, carrier, month, day of week, airports, delay causes, worst days |
| 03_enrichment | NOAA GHCN-Daily weather + OurAirports characteristics joined to flights; weather share of disruption; winter readiness |
| 04_routes_full_data | Full 6.4M file: route x carrier x time band; like-for-like carrier comparison; morning vs evening on the same route |
| 05_direct_vs_onestop | Constructed one-stop itineraries, misconnect curve by layover length, hub ranking, break-even fare saving |
| 06_model_validation | Booking-time and short-notice risk models (logistic + gradient boosting), grouped CV by date, odds ratios |
| 07_recommendations | Policy simulation, buffer rules, cost sensitivity, the 4 recommendations and KPIs |
| 08_infrastructure_and_layovers | Newark runway-closure event study, last-flight stranding, disruption-care triggers |

Requirements: pandas, numpy, pyarrow, matplotlib, seaborn, scikit-learn, requests.
The notebooks import helpers from src/ (prep.py, enrich.py, connections.py, style.py), included here.
Raw data is not included: place the student CSV and the full monthly .csv.gz files as described in src/prep.py.
HTML copies of every executed notebook are in notebooks_html/ for reading without Jupyter.

# Questrom Chart Champ Datathon 2026 — corporate travel reliability

Analytics consulting response to the RFP in `Questrom_Chart_Champs_Revised_Brief.pdf`: how a company
with heavy employee air travel can cut disruption while balancing cost and convenience.

## Layout

```
questrom_student_package_2025/   200k-flight sample (given)
questrom_full_flights_2025/      full 6.4M-flight 2025 monthly files (given)
src/
  prep.py          one cleaning function + outcome definitions, used for sample and full data
  enrich.py        OurAirports + NOAA GHCN-Daily download, station matching, weather flags
  connections.py   builds one-stop itineraries from real flight pairs; rebooking logic
  style.py         chart style
  build_nb.py      turns notebooks/_py/*.py into executed .ipynb notebooks
notebooks/
  01_cleaning · 02_eda · 03_enrichment · 04_routes_full_data · 05_direct_vs_onestop
  06_model_validation · 07_recommendations · 08_infrastructure_and_layovers   (sources in notebooks/_py/)
data/external/     downloaded public data + SOURCES.md
data/processed/    parquet tables used by notebooks and the app (not committed; rebuildable)
outputs/figures/   every chart in the deck (PNG)      outputs/tables/   every number in the deck (CSV)
deck/storyline.md  slide-by-slide outline, speaker notes, Q&A drills
app/app.py         Streamlit "Trip Risk Checker"
```

## Rebuild everything

```bash
pip install pandas numpy pyarrow matplotlib seaborn scikit-learn statsmodels requests nbformat nbclient ipykernel streamlit
```

```bash
python src/build_nb.py 01_cleaning 02_eda
```

```bash
python src/enrich.py download
```

```bash
python src/build_nb.py 03_enrichment 04_routes_full_data 05_direct_vs_onestop 06_model_validation 07_recommendations 08_infrastructure_and_layovers
```

Notebook 01 also builds `data/processed/flights_full.parquet` on first use of `prep.load_full()` (about
1 minute). Notebooks 03-07 take 2-6 minutes each.

## Run the app

```bash
streamlit run app/app.py
```

## Definitions

* **Disrupted** — arrived 15+ min late, cancelled or diverted.
* **Severe / "hour late"** — arrived 60+ min late, cancelled or diverted. In trip-level tables (05, 07)
  cancelled flights are rebooked on the next completed flight of the same airline and the realised
  delay is used.
* **Traveler burden** — departure before 6 a.m.; landing 11 p.m.-4 a.m.; 2h+ gate wait; overnight stranding.

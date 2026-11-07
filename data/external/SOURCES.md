# External data sources

| File | Source | URL | Accessed | Licence / terms |
|---|---|---|---|---|
| airports.csv, runways.csv | OurAirports open data | https://ourairports.com/data/ | 2026-11-06 | Public domain |
| ghcnd-stations.txt, ghcnd-inventory.txt | NOAA NCEI, Global Historical Climatology Network - Daily | https://www.ncei.noaa.gov/pub/data/ghcn/daily/ | 2026-11-06 | US Government work, public domain |
| weather/*.csv | NOAA NCEI Access Data Service, dataset `daily-summaries` (GHCN-Daily), 2025-01-01 to 2025-12-31, one station per airport | https://www.ncei.noaa.gov/access/services/data/v1 | 2026-11-06 | US Government work, public domain |

Station choice: for each airport, the nearest GHCN-Daily station (within 40 km) that reports
precipitation, temperature and wind in 2025. The mapping and distances are in
`data/processed/airports.parquet` (`station`, `station_km`).

Weather flags (daily, local): snow = snowfall >= 0.5 in (or snow observed with measurable
precipitation on a freezing day where snowfall is not measured); freezing = precipitation with
minimum temperature <= 32F, or glaze / ice pellets observed; heavy rain = precipitation >= 0.5 in
without snow; thunder = thunder observed; fog = heavy fog observed; wind = 2-minute gust >= 35 mph
or daily mean wind >= 20 mph. "Adverse" = any of these.

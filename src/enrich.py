"""External enrichment: airport characteristics (OurAirports) and NOAA daily weather.

    python src/enrich.py download     # fetch + cache everything under data/external/
    python src/enrich.py build        # build data/processed/airports.parquet + weather_daily.parquet

Sources are logged in data/external/SOURCES.md.
"""
from __future__ import annotations

import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import numpy as np
import pandas as pd
import requests

from prep import EXTERNAL, PROCESSED

WX_DIR = EXTERNAL / "weather"
URLS = {
    "airports.csv": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    "runways.csv": "https://davidmegginson.github.io/ourairports-data/runways.csv",
    "ghcnd-stations.txt": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt",
    "ghcnd-inventory.txt": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt",
}
NCEI = "https://www.ncei.noaa.gov/access/services/data/v1"
WX_TYPES = ["PRCP", "SNOW", "SNWD", "TMAX", "TMIN", "AWND", "WSF2", "WSF5",
            "WT01", "WT02", "WT03", "WT04", "WT05", "WT06", "WT08", "WT09", "WT16", "WT18"]
HEAD = {"User-Agent": "questrom-datathon-student-project"}


def _get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEAD, timeout=120, **kw)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(3 * (i + 1))
    return None


def download_reference():
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    for name, url in URLS.items():
        f = EXTERNAL / name
        if not f.exists():
            r = _get(url)
            if r is None:
                print("FAILED", url)
                continue
            f.write_bytes(r.content)
            print("saved", name, len(r.content) // 1024, "KB")


def airport_list() -> list[str]:
    s = pd.read_parquet(PROCESSED / "flights_sample.parquet", columns=["ORIGIN", "DEST"])
    return sorted(set(s.ORIGIN) | set(s.DEST))


def airports_table() -> pd.DataFrame:
    """Coordinates, elevation and runway capacity for every airport in the flight data."""
    a = pd.read_csv(EXTERNAL / "airports.csv", keep_default_na=False, na_values=[""])
    a = a[a.iata_code.isin(airport_list()) & a.type.isin(["large_airport", "medium_airport", "small_airport"])]
    a = a.sort_values("scheduled_service", ascending=False).drop_duplicates("iata_code")
    r = pd.read_csv(EXTERNAL / "runways.csv")
    r = r[(r.closed == 0) & r.airport_ident.isin(a.ident)]
    rw = r.groupby("airport_ident").agg(runways=("id", "size"), longest_runway_ft=("length_ft", "max"))
    a = a.merge(rw, left_on="ident", right_index=True, how="left")
    return a.rename(columns={"iata_code": "airport", "latitude_deg": "lat", "longitude_deg": "lon",
                             "elevation_ft": "elev_ft"})[
        ["airport", "name", "municipality", "iso_region", "lat", "lon", "elev_ft", "runways", "longest_runway_ft"]
    ].reset_index(drop=True)


def _haversine(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = (np.sin((lat2 - lat1) * p / 2) ** 2
         + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def station_candidates(k: int = 3, max_km: float = 40) -> pd.DataFrame:
    """Nearest GHCN-Daily stations that report precipitation, temperature and wind in 2025."""
    inv = pd.read_fwf(EXTERNAL / "ghcnd-inventory.txt", header=None,
                      colspecs=[(0, 11), (12, 20), (21, 30), (31, 35), (36, 40), (41, 45)],
                      names=["station", "lat", "lon", "element", "first", "last"])
    live = inv[inv["last"] >= 2025]
    need = live[live.element.isin(["PRCP", "TMAX", "AWND"])].groupby("station").element.nunique()
    st = live[live.station.isin(need[need == 3].index)].drop_duplicates("station")[["station", "lat", "lon"]]
    # fallback for airports with no wind-reporting station nearby: precipitation + temperature only
    need2 = live[live.element.isin(["PRCP", "TMAX"])].groupby("station").element.nunique()
    st2 = live[live.station.isin(need2[need2 == 2].index)].drop_duplicates("station")[["station", "lat", "lon"]]
    rows = []
    for a in airports_table().itertuples():
        for pool in (st, st2):
            d = _haversine(a.lat, a.lon, pool.lat.values, pool.lon.values)
            got = [(a.airport, rank, pool.station.values[i], round(float(d[i]), 1))
                   for rank, i in enumerate(np.argsort(d)[:k]) if d[i] <= max_km]
            if got:
                rows.extend(got)
                break
    return pd.DataFrame(rows, columns=["airport", "rank", "station", "km"])


def fetch_weather(airport: str, stations: list[str], start="2025-01-01", end="2025-12-31") -> str:
    out = WX_DIR / f"{airport}.csv"
    if out.exists():
        return "cached"
    for s in stations:
        r = _get(NCEI, params={"dataset": "daily-summaries", "stations": s, "startDate": start,
                               "endDate": end, "dataTypes": ",".join(WX_TYPES), "format": "csv",
                               "units": "standard"})
        if r is None or len(r.text) < 200:
            continue
        d = pd.read_csv(io.StringIO(r.text))
        if len(d) >= 300 and "PRCP" in d:
            d.insert(0, "airport", airport)
            d.to_csv(out, index=False)
            return s
    return "FAILED"


def download_weather(workers: int = 4):
    WX_DIR.mkdir(parents=True, exist_ok=True)
    cand = station_candidates()
    cand.to_csv(EXTERNAL / "airport_station_map_candidates.csv", index=False)
    jobs = {a: g.sort_values("rank").station.tolist() for a, g in cand.groupby("airport")}
    with ThreadPoolExecutor(workers) as ex:
        res = dict(zip(jobs, ex.map(lambda a: fetch_weather(a, jobs[a]), jobs)))
    failed = [a for a, v in res.items() if v == "FAILED"]
    missing = sorted(set(airport_list()) - set(jobs))
    print(f"weather files: {len(list(WX_DIR.glob('*.csv')))}  failed: {failed}  no station: {missing}")


def build():
    """Combine cached files into tidy tables with adverse-weather flags."""
    air = airports_table()
    frames = [pd.read_csv(f) for f in sorted(WX_DIR.glob("*.csv"))]
    w = pd.concat(frames, ignore_index=True)
    w = w.rename(columns={"DATE": "date", "STATION": "station"})
    w["date"] = pd.to_datetime(w["date"])
    for c in WX_TYPES:
        if c not in w:
            w[c] = np.nan
        w[c] = pd.to_numeric(w[c], errors="coerce")
    wt = lambda c: w[c].fillna(0) > 0
    snow_obs = w["SNOW"].fillna(0) >= 0.5
    # many airport stations do not measure snowfall: fall back to the "snow observed" weather
    # type with measurable precipitation on a cold day
    snow_wt = w["SNOW"].isna() & wt("WT18") & (w["PRCP"].fillna(0) >= 0.05) & (w["TMIN"] <= 32)
    w["wx_snow"] = (snow_obs | snow_wt).astype("int8")
    w["wx_freezing"] = (((w["PRCP"].fillna(0) >= 0.05) & (w["TMIN"] <= 32)) | wt("WT06") | wt("WT04")).astype("int8")
    w["wx_heavy_rain"] = ((w["PRCP"].fillna(0) >= 0.5) & (w["wx_snow"] == 0)).astype("int8")
    w["wx_thunder"] = wt("WT03").astype("int8")
    w["wx_fog"] = wt("WT02").astype("int8")                       # heavy fog only
    gust = w["WSF2"].fillna(w["WSF5"])
    w["wx_wind"] = ((gust >= 35) | (w["AWND"] >= 20)).fillna(False).astype("int8")
    flags = ["wx_snow", "wx_freezing", "wx_heavy_rain", "wx_thunder", "wx_fog", "wx_wind"]
    w["wx_adverse"] = w[flags].max(axis=1).astype("int8")
    w["wx_winter"] = w[["wx_snow", "wx_freezing"]].max(axis=1).astype("int8")
    keep = ["airport", "station", "date", "PRCP", "SNOW", "SNWD", "TMAX", "TMIN", "AWND", "WSF2",
            *flags, "wx_adverse", "wx_winter"]
    w = w[keep]
    PROCESSED.mkdir(parents=True, exist_ok=True)
    w.to_parquet(PROCESSED / "weather_daily.parquet", index=False)

    cand = pd.read_csv(EXTERNAL / "airport_station_map_candidates.csv")
    used = w.drop_duplicates("airport")[["airport", "station"]].merge(cand, on=["airport", "station"], how="left")
    air = air.merge(used[["airport", "station", "km"]].rename(columns={"km": "station_km"}), on="airport", how="left")
    air.to_parquet(PROCESSED / "airports.parquet", index=False)
    print("airports:", len(air), " with weather:", air.station.notna().sum(), " weather rows:", len(w))
    print(w[[*flags, "wx_adverse", "wx_winter"]].mean().round(3).to_string())
    return air, w


def write_sources():
    today = date.today().isoformat()
    (EXTERNAL / "SOURCES.md").write_text(f"""# External data sources

| File | Source | URL | Accessed | Licence / terms |
|---|---|---|---|---|
| airports.csv, runways.csv | OurAirports open data | https://ourairports.com/data/ | {today} | Public domain |
| ghcnd-stations.txt, ghcnd-inventory.txt | NOAA NCEI, Global Historical Climatology Network - Daily | https://www.ncei.noaa.gov/pub/data/ghcn/daily/ | {today} | US Government work, public domain |
| weather/*.csv | NOAA NCEI Access Data Service, dataset `daily-summaries` (GHCN-Daily), 2025-01-01 to 2025-12-31, one station per airport | https://www.ncei.noaa.gov/access/services/data/v1 | {today} | US Government work, public domain |

Station choice: for each airport, the nearest GHCN-Daily station (within 40 km) that reports
precipitation, temperature and wind in 2025. The mapping and distances are in
`data/processed/airports.parquet` (`station`, `station_km`).

Weather flags (daily, local): snow = snowfall >= 0.5 in (or snow observed with measurable
precipitation on a freezing day where snowfall is not measured); freezing = precipitation with
minimum temperature <= 32F, or glaze / ice pellets observed; heavy rain = precipitation >= 0.5 in
without snow; thunder = thunder observed; fog = heavy fog observed; wind = 2-minute gust >= 35 mph
or daily mean wind >= 20 mph. "Adverse" = any of these.
""", encoding="utf-8")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "download"
    if cmd == "download":
        download_reference()
        download_weather()
        write_sources()
    build()

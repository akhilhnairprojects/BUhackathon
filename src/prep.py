"""Shared cleaning for the BTS on-time data (200k student sample and full monthly files).

One function, `clean`, is applied to both so every number in the project uses the
same definitions.  See notebooks/01_cleaning.ipynb for the rules and the cleaning log.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = ROOT / "questrom_student_package_2025" / "questrom_flights_2025_student.csv"
VALIDATION_JSON = ROOT / "questrom_student_package_2025" / "validation_report.json"
FULL_DIR = ROOT / "questrom_full_flights_2025"
EXTERNAL = ROOT / "data" / "external"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
TABLES = ROOT / "outputs" / "tables"

CARRIER_NAMES = {
    "AA": "American", "AS": "Alaska", "B6": "JetBlue", "DL": "Delta", "UA": "United",
    "WN": "Southwest", "OO": "SkyWest", "YX": "Republic", "OH": "PSA", "MQ": "Envoy",
}
REGIONAL = {"OO", "YX", "OH", "MQ"}          # fly under mainline brands
CAUSE_COLS = ["CARRIER_DELAY", "WEATHER_DELAY", "NAS_DELAY", "SECURITY_DELAY", "LATE_AIRCRAFT_DELAY"]
STR_COLS = {c: "string" for c in
            ["CRS_DEP_TIME", "DEP_TIME", "CRS_ARR_TIME", "ARR_TIME", "OP_CARRIER_FL_NUM"]}
DOW_NAMES = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
BAND_ORDER = ["Early (5-6:59a)", "Morning (7-9:59a)", "Midday (10a-1:59p)",
              "Afternoon (2-5:59p)", "Evening (6-9:59p)", "Late night (10p-4:59a)"]

# Peak leisure/holiday travel windows in 2025 (inclusive)
HOLIDAY_WINDOWS = [
    ("2025-01-01", "2025-01-05"), ("2025-05-22", "2025-05-27"), ("2025-07-02", "2025-07-07"),
    ("2025-08-28", "2025-09-02"), ("2025-11-21", "2025-12-01"), ("2025-12-19", "2025-12-31"),
]

# Columns the full-data pass needs (keeps 6.4M rows manageable)
FULL_USECOLS = [
    "MONTH", "DAY_OF_WEEK", "FL_DATE", "OP_UNIQUE_CARRIER", "OP_CARRIER_FL_NUM", "ORIGIN", "DEST",
    "CRS_DEP_TIME", "DEP_DELAY", "CRS_ARR_TIME", "ARR_DELAY", "CANCELLED", "CANCELLATION_CODE",
    "DIVERTED", "CRS_ELAPSED_TIME", "DISTANCE", *CAUSE_COLS,
]


def load_raw(path, usecols=None) -> pd.DataFrame:
    """Read a BTS csv / csv.gz with time fields kept as strings (leading zeros matter)."""
    return pd.read_csv(path, dtype=STR_COLS, usecols=usecols, low_memory=False)


def _hhmm_to_min(s: pd.Series) -> pd.Series:
    """'HHMM' string -> minutes after midnight; '2400' is treated as 0000."""
    v = pd.to_numeric(s, errors="coerce")
    v = v.where(v != 2400, 0)
    return (v // 100) * 60 + (v % 100)


def _time_band(hour: pd.Series) -> pd.Series:
    cond = [hour.between(5, 6), hour.between(7, 9), hour.between(10, 13),
            hour.between(14, 17), hour.between(18, 21)]
    out = np.select(cond, BAND_ORDER[:5], default=BAND_ORDER[5])
    return pd.Categorical(out, categories=BAND_ORDER, ordered=True)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning rules and add outcome / feature columns. Never drops rows."""
    df = df.copy()
    df["FL_DATE"] = pd.to_datetime(df["FL_DATE"])
    df["CANCELLED"] = df["CANCELLED"].astype("int8")
    df["DIVERTED"] = df["DIVERTED"].astype("int8")
    df = df.drop(columns=[c for c in ["OP_CARRIER", "YEAR", "QUARTER"] if c in df.columns])
    df = df.rename(columns={"OP_UNIQUE_CARRIER": "CARRIER"})

    # --- scheduled / actual clock times -------------------------------------------------
    dep_min = _hhmm_to_min(df["CRS_DEP_TIME"])
    arr_min = _hhmm_to_min(df["CRS_ARR_TIME"])
    df["dep_hour"] = (dep_min // 60).astype("int8")
    df["arr_hour"] = (arr_min // 60).astype("int8")
    df["time_band"] = _time_band(df["dep_hour"])
    df["sched_dep"] = df["FL_DATE"] + pd.to_timedelta(dep_min, unit="m")
    # Arrival is in destination local time. Recover the time-zone shift from the schedule
    # itself so the arrival *date* is right for overnight flights.
    tz = ((arr_min - dep_min - df["CRS_ELAPSED_TIME"] + 720) % 1440) - 720
    df["sched_arr"] = df["sched_dep"] + pd.to_timedelta(df["CRS_ELAPSED_TIME"] + tz, unit="m")
    df["act_dep"] = df["sched_dep"] + pd.to_timedelta(df["DEP_DELAY"], unit="m")
    df["act_arr"] = df["sched_arr"] + pd.to_timedelta(df["ARR_DELAY"], unit="m")

    # --- outcomes (traveler's view: arrival, with cancel/divert counted as disruption) ---
    bad = (df["CANCELLED"] == 1) | (df["DIVERTED"] == 1)
    df["completed"] = (~bad).astype("int8")
    df["disrupted"] = (bad | (df["ARR_DELAY"] >= 15)).astype("int8")
    df["severe"] = (bad | (df["ARR_DELAY"] >= 60)).astype("int8")
    df["delay_2h"] = (bad | (df["ARR_DELAY"] >= 120)).astype("int8")

    # --- traveler-burden flags ----------------------------------------------------------
    df["early_dep"] = (df["dep_hour"] < 6).astype("int8")                 # before 6 a.m.
    sched_late = (df["sched_arr"].dt.hour >= 23) | (df["sched_arr"].dt.hour < 4)
    act_late = (df["act_arr"].dt.hour >= 23) | (df["act_arr"].dt.hour < 4)
    df["late_night_arrival"] = act_late.fillna(False).astype("int8")      # lands 11p-4a
    df["pushed_late_night"] = (act_late.fillna(False) & ~sched_late).astype("int8")
    df["long_wait"] = (df["DEP_DELAY"] >= 120).fillna(False).astype("int8")  # 2h+ at gate
    df["weekend"] = df["DAY_OF_WEEK"].isin([6, 7]).astype("int8")

    # --- descriptive features -----------------------------------------------------------
    df["carrier_name"] = df["CARRIER"].map(CARRIER_NAMES)
    df["regional"] = df["CARRIER"].isin(REGIONAL).astype("int8")
    df["route"] = df["ORIGIN"].astype(str) + "-" + df["DEST"].astype(str)
    df["dow_name"] = pd.Categorical(df["DAY_OF_WEEK"].map(DOW_NAMES),
                                    categories=list(DOW_NAMES.values()), ordered=True)
    df["dist_band"] = pd.cut(df["DISTANCE"], [0, 250, 500, 1000, 1500, 2500, 6000],
                             labels=["<250", "250-500", "500-1k", "1k-1.5k", "1.5k-2.5k", "2.5k+"])
    df["season"] = df["MONTH"].map({12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring",
                                    5: "Spring", 6: "Summer", 7: "Summer", 8: "Summer",
                                    9: "Fall", 10: "Fall", 11: "Fall"})
    hol = pd.Series(False, index=df.index)
    for a, b in HOLIDAY_WINDOWS:
        hol |= df["FL_DATE"].between(a, b)
    df["holiday_window"] = hol.astype("int8")
    return df


def load_sample() -> pd.DataFrame:
    return clean(load_raw(SAMPLE_CSV))


def full_files() -> list[Path]:
    """The 12 monthly .csv.gz files (the unzipped 2025_05.csv folder is a duplicate)."""
    return sorted(FULL_DIR.glob("2025_*.csv.gz"))


def load_full(cache: bool = True) -> pd.DataFrame:
    """All 6.4M flights, cleaned, slim columns. Cached to parquet after the first build."""
    pq = PROCESSED / "flights_full.parquet"
    if cache and pq.exists():
        return pd.read_parquet(pq)
    parts = []
    for f in full_files():
        d = clean(load_raw(f, usecols=FULL_USECOLS))
        d = d.drop(columns=["CRS_DEP_TIME", "CRS_ARR_TIME", "carrier_name", "dist_band"])
        for c in ["CARRIER", "ORIGIN", "DEST", "CANCELLATION_CODE", "season", "route"]:
            d[c] = d[c].astype("category")
        for c in ["DEP_DELAY", "ARR_DELAY", "CRS_ELAPSED_TIME", "DISTANCE", *CAUSE_COLS]:
            d[c] = d[c].astype("float32")
        parts.append(d)
    full = pd.concat(parts, ignore_index=True)
    for c in ["CARRIER", "ORIGIN", "DEST", "CANCELLATION_CODE", "season", "route"]:
        full[c] = full[c].astype("category")
    if cache:
        PROCESSED.mkdir(parents=True, exist_ok=True)
        full.to_parquet(pq, index=False)
    return full


# ---------------------------------------------------------------------------- statistics
def wilson(k, n, z: float = 1.96):
    """Wilson 95% interval for a proportion -> (low, high). Works on arrays."""
    k, n = np.asarray(k, dtype=float), np.asarray(n, dtype=float)
    p = np.divide(k, n, out=np.zeros_like(k), where=n > 0)
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return c - h, c + h


def rate_table(df: pd.DataFrame, by, min_n: int = 100) -> pd.DataFrame:
    """n, disruption / severe / cancel rates with Wilson CIs, and delay percentiles."""
    g = df.groupby(by, observed=True)
    out = g.agg(n=("disrupted", "size"), disrupted=("disrupted", "mean"), severe=("severe", "mean"),
                cancelled=("CANCELLED", "mean"), mean_arr_delay=("ARR_DELAY", "mean"),
                p90_arr_delay=("ARR_DELAY", lambda s: s.quantile(0.9)))
    lo, hi = wilson(out["disrupted"] * out["n"], out["n"])
    out["disrupted_lo"], out["disrupted_hi"] = lo, hi
    lo, hi = wilson(out["severe"] * out["n"], out["n"])
    out["severe_lo"], out["severe_hi"] = lo, hi
    return out[out["n"] >= min_n]

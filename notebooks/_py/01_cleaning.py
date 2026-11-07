# %% [markdown]
# # 01 · Data cleaning
# **Goal:** turn the raw BTS on-time file into an analysis-ready table with outcome definitions
# that match what a business traveler experiences. All rules live in `src/prep.py` so the 200k
# sample and the full 6.4M-flight files are cleaned identically.

# %%
import sys, json
sys.path.insert(0, "../src")
import numpy as np, pandas as pd
import prep
pd.set_option("display.width", 200, "display.max_columns", 60)

raw = prep.load_raw(prep.SAMPLE_CSV)
print(raw.shape)
raw.head(3)

# %% [markdown]
# ## 1. Audit the raw file

# %%
nulls = raw.isna().sum()
audit = pd.DataFrame({"dtype": raw.dtypes.astype(str), "nulls": nulls,
                      "null_pct": (nulls / len(raw) * 100).round(2), "unique": raw.nunique()})
audit

# %%
key = ["FL_DATE", "OP_UNIQUE_CARRIER", "OP_CARRIER_FL_NUM", "ORIGIN", "DEST", "CRS_DEP_TIME"]
comp = raw[(raw.CANCELLED == 0) & (raw.DIVERTED == 0)]
checks = {
    "full-row duplicates": int(raw.duplicated().sum()),
    "duplicate flight keys": int(raw.duplicated(key).sum()),
    "OP_CARRIER differs from OP_UNIQUE_CARRIER": int((raw.OP_UNIQUE_CARRIER != raw.OP_CARRIER).sum()),
    "ARR_DELAY missing on completed flights": int(comp.ARR_DELAY.isna().sum()),
    "ARR_DELAY present on cancelled/diverted flights": int(raw[(raw.CANCELLED == 1) | (raw.DIVERTED == 1)].ARR_DELAY.notna().sum()),
    "cause columns present when delay < 15 min": int(comp[comp.ARR_DELAY < 15].CARRIER_DELAY.notna().sum()),
    "cause columns missing when delay >= 15 min": int(comp[comp.ARR_DELAY >= 15].CARRIER_DELAY.isna().sum()),
    "'2400' in DEP_TIME / ARR_TIME": int((raw.DEP_TIME == "2400").sum() + (raw.ARR_TIME == "2400").sum()),
    "non-positive DISTANCE or AIR_TIME": int((raw.DISTANCE <= 0).sum() + (raw.AIR_TIME <= 0).sum()),
    "arrival delay > 1,000 min": int((raw.ARR_DELAY > 1000).sum()),
    "distinct sample_weight values": int(raw.sample_weight.nunique()),
}
pd.Series(checks, name="rows").to_frame()

# %% [markdown]
# **Reading the audit.** Every missing value is *structural*, not an error:
# * `ARR_DELAY` is blank only when a flight was cancelled or diverted - the worst outcomes for a
#   traveler. Dropping those rows would make every carrier look better than it is, so we keep them
#   and count them as disruptions.
# * The five delay-cause columns are only filled when a flight arrives 15+ minutes late.
# * `sample_weight` is one constant (31.99), so unweighted rates equal population rates.

# %% [markdown]
# ## 2. Apply the cleaning rules

# %%
df = prep.clean(raw)
print(df.shape)
df[["FL_DATE", "CARRIER", "route", "sched_dep", "sched_arr", "act_arr", "ARR_DELAY", "disrupted",
    "severe", "time_band", "late_night_arrival", "regional", "holiday_window"]].head(5)

# %% [markdown]
# ### Outcome definitions (used in every later notebook)
# | Measure | Definition | Why |
# |---|---|---|
# | **Disrupted** | arrived 15+ min late, **or** cancelled, **or** diverted | DOT's on-time standard, plus the outcomes that have no arrival delay |
# | **Severely disrupted** | arrived 60+ min late, or cancelled, or diverted | "missed the meeting" |
# | Arrival delay (min) | completed flights only | used for buffer-time rules (p90 / p95) |
# | Traveler burden | departure before 6 a.m.; landing 11 p.m.-4 a.m.; 2h+ departure delay; weekend travel | the employee's side of the same events |

# %%
# overnight / time-zone handling check: scheduled arrival minus departure should equal
# scheduled elapsed time plus a whole-hour time-zone shift
shift = ((df.sched_arr - df.sched_dep).dt.total_seconds() / 60 - df.CRS_ELAPSED_TIME)
print("implied time-zone shifts (hours) and share of flights:")
print((shift / 60).round(2).value_counts(normalize=True).head(12).round(4))
print("\nflights whose scheduled arrival is on the next calendar day:",
      int((df.sched_arr.dt.normalize() > df.FL_DATE).sum()))

# %% [markdown]
# ## 3. Validate against the organisers' report

# %%
rep = json.load(open(prep.VALIDATION_JSON))
val = pd.DataFrame([
    ("rows", rep["student_records"], len(df)),
    ("cancelled", rep["student_cancelled"], int(df.CANCELLED.sum())),
    ("diverted", rep["student_diverted"], int(df.DIVERTED.sum())),
    ("airports", rep["student_airports"], len(set(df.ORIGIN) | set(df.DEST))),
    ("carriers match", True, df.CARRIER.value_counts().to_dict() == rep["student_carriers"]),
    ("months match", True, {str(k): v for k, v in df.MONTH.value_counts().items()} == rep["student_months"]),
], columns=["check", "expected", "ours"])
val["ok"] = val.expected == val.ours
val

# %% [markdown]
# ## 4. Cleaning log

# %%
log = pd.DataFrame([
    ("Times stored as HHMM numbers", "Read as text, convert to minutes after midnight; '2400' -> '0000'", len(df)),
    ("Arrival date not given", "Rebuilt scheduled/actual arrival timestamps from schedule (handles overnight + time zones)", len(df)),
    ("ARR_DELAY blank for cancelled flights", "Kept; counted as disrupted and severely disrupted", int(df.CANCELLED.sum())),
    ("ARR_DELAY blank for diverted flights", "Kept; counted as disrupted and severely disrupted", int(df.DIVERTED.sum())),
    ("Delay-cause columns blank when delay < 15 min", "Left blank; cause analysis uses delayed flights only", int(df.CARRIER_DELAY.isna().sum())),
    ("OP_CARRIER duplicates OP_UNIQUE_CARRIER", "Dropped duplicate; renamed to CARRIER", len(df)),
    ("Extreme delays (> 1,000 min)", "Kept (real events); report medians/percentiles beside means", int((df.ARR_DELAY > 1000).sum())),
    ("TAIL_NUM blank", "Kept; only occurs on cancelled flights; not used as a feature", int(df.TAIL_NUM.isna().sum())),
    ("Rows removed", "None", 0),
], columns=["issue", "rule", "rows_affected"])
log.to_csv(prep.TABLES / "cleaning_log.csv", index=False)
log

# %%
prep.PROCESSED.mkdir(parents=True, exist_ok=True)
df.to_parquet(prep.PROCESSED / "flights_sample.parquet", index=False)
base = df[["disrupted", "severe", "CANCELLED", "DIVERTED"]].mean().rename("rate").to_frame()
base.loc["on_time_of_completed"] = (df.loc[df.completed == 1, "ARR_DELAY"] < 15).mean()
base.round(4)

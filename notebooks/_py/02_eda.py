# %% [markdown]
# # 02 · Exploratory analysis (200k student sample)
# **Question:** when, where and with whom is a business trip most likely to be disrupted?
#
# Every table reports the number of flights, the disruption rate with a 95% Wilson confidence
# interval, and hides groups with fewer than 100 flights. *Disrupted* = arrived 15+ min late,
# cancelled or diverted. *Severe* = 60+ min late, cancelled or diverted.

# %%
import sys
sys.path.insert(0, "../src")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
import prep, style
from style import INK, GREY, ACCENT, GOOD, BLUE, AMBER, PCT
style.use()
pd.set_option("display.width", 200, "display.max_columns", 60, "display.float_format", "{:.3f}".format)

df = pd.read_parquet(prep.PROCESSED / "flights_sample.parquet")
BASE = df.disrupted.mean()
print(f"{len(df):,} flights | disrupted {BASE:.1%} | severe {df.severe.mean():.1%} | cancelled {df.CANCELLED.mean():.2%}")

def show(by, min_n=100, save=None, sort=None):
    t = prep.rate_table(df, by, min_n)
    if sort: t = t.sort_values(sort)
    if save: t.to_csv(prep.TABLES / f"{save}.csv")
    return t

# %% [markdown]
# ## 1. What does a "typical" delay look like?

# %%
c = df[df.completed == 1].ARR_DELAY
fig, ax = plt.subplots()
ax.hist(c.clip(-60, 180), bins=np.arange(-60, 185, 5), color=GREY)
ax.hist(c[c >= 15].clip(upper=180), bins=np.arange(15, 185, 5), color=ACCENT)
ax.axvline(15, color=INK, lw=1, ls="--")
ax.text(18, ax.get_ylim()[1] * .9, f"{(c >= 15).mean():.0%} of completed flights\narrive 15+ min late", color=ACCENT, fontweight="bold")
ax.text(-58, ax.get_ylim()[1] * .9, f"Median flight arrives\n{abs(c.median()):.0f} min early", color=INK)
ax.set_xlabel("Arrival delay (minutes; values above 180 grouped at 180)"); ax.set_ylabel("Flights")
style.titled(ax, "Most flights arrive early - the risk is a long, expensive tail",
             f"Mean {c.mean():.0f} min, median {c.median():.0f} min, 90th percentile {c.quantile(.9):.0f} min, 99th {c.quantile(.99):.0f} min. Plus {df.CANCELLED.mean():.1%} cancelled.")
style.save(fig, "01_delay_distribution");

# %% [markdown]
# ## 2. Time of day - the biggest lever

# %%
hr = show("dep_hour", save="by_dep_hour")
hr

# %%
h = hr.loc[5:23]
fig, ax = plt.subplots()
cols = [GOOD if x <= 9 else (ACCENT if x >= 17 else GREY) for x in h.index]
ax.bar(h.index, h.disrupted, color=cols, yerr=[h.disrupted - h.disrupted_lo, h.disrupted_hi - h.disrupted], ecolor=INK, capsize=2)
ax.plot(h.index, h.severe, color=INK, marker="o", ms=4, lw=1.5, label="Severely disrupted (60+ min, cancelled, diverted)")
ax.axhline(BASE, color=INK, lw=.8, ls=":"); ax.text(23.6, BASE, f"avg {BASE:.0%}", va="center", fontsize=9)
ax.set_xticks(range(5, 24)); ax.set_xticklabels([f"{x % 12 or 12}{'a' if x < 12 else 'p'}" for x in range(5, 24)])
ax.yaxis.set_major_formatter(PCT); ax.set_xlabel("Scheduled departure hour"); ax.set_ylabel("Share of flights disrupted"); ax.legend(loc="upper left")
style.titled(ax, f"A 7 p.m. departure is {h.disrupted[19] / h.disrupted[6]:.1f}x as likely to be disrupted as a 6 a.m. one",
             "Share of flights arriving 15+ min late, cancelled or diverted, by scheduled departure hour. Bars show 95% CI.")
style.save(fig, "02_disruption_by_hour");

# %%
pv = df.pivot_table(index="dow_name", columns="time_band", values="disrupted", aggfunc="mean", observed=True)
fig, ax = plt.subplots(figsize=(10, 4.6))
sns.heatmap(pv, annot=True, fmt=".0%", cmap="RdYlGn_r", center=BASE, cbar=False, linewidths=2, linecolor="white", ax=ax, annot_kws={"fontsize": 11})
ax.set_xlabel(""); ax.set_ylabel(""); ax.grid(False)
ax.set_xticklabels([t.get_text().replace(" (", "\n(") for t in ax.get_xticklabels()], rotation=0)
style.titled(ax, "Sunday and Thursday-Friday evenings are the worst slots; any weekday morning is safe",
             "Share of flights disrupted by day of week and scheduled departure time")
style.save(fig, "03_heatmap_day_by_time");
pv.round(3)

# %% [markdown]
# ## 3. Season and cancellation causes

# %%
mo = show("MONTH", save="by_month")
cc = pd.crosstab(df.MONTH, df.CANCELLATION_CODE.map({"A": "Carrier", "B": "Weather", "C": "Air traffic system (NAS)", "D": "Security"}))
cc = cc.div(df.groupby("MONTH").size(), axis=0)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
mn = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
a1.bar(mn, mo.disrupted, color=[ACCENT if v > BASE + .03 else (GOOD if v < BASE - .03 else GREY) for v in mo.disrupted],
       yerr=[mo.disrupted - mo.disrupted_lo, mo.disrupted_hi - mo.disrupted], ecolor=INK, capsize=2)
a1.axhline(BASE, color=INK, lw=.8, ls=":"); a1.yaxis.set_major_formatter(PCT)
style.titled(a1, "Summer and December are the risky seasons", "Share of flights disrupted, by month")
cc[["Weather", "Carrier", "Air traffic system (NAS)"]].set_axis(mn).plot.bar(stacked=True, ax=a2, color=[BLUE, AMBER, ACCENT], width=.8, rot=0)
a2.yaxis.set_major_formatter(style.PercentFormatter(1.0, decimals=1)); a2.set_xlabel(""); a2.legend(title=None, loc="upper center", ncol=3, fontsize=9.5, bbox_to_anchor=(.5, 1.0))
style.titled(a2, "Cancellations spike in January (weather)", "Share of flights cancelled, by stated reason")
style.save(fig, "04_month_and_cancellations");
mo

# %% [markdown]
# ## 4. Carrier

# %%
ca = show(["CARRIER", "carrier_name", "regional"], save="by_carrier", sort="disrupted").reset_index()
fig, ax = plt.subplots(figsize=(10, 4.8))
y = np.arange(len(ca))
ax.hlines(y, ca.disrupted_lo, ca.disrupted_hi, color=INK, lw=1.2)
ax.scatter(ca.disrupted, y, s=110, color=[AMBER if r else BLUE for r in ca.regional], zorder=3)
ax.scatter(ca.severe, y, s=40, color="white", edgecolor=INK, zorder=3)
ax.set_yticks(y); ax.set_yticklabels([f"{n} ({c})" for n, c in zip(ca.carrier_name, ca.CARRIER)]); ax.invert_yaxis()
ax.axvline(BASE, color=INK, lw=.8, ls=":"); ax.xaxis.set_major_formatter(PCT); ax.set_xlabel("Share of flights")
ax.scatter([], [], s=110, color=BLUE, label="Mainline: disrupted"); ax.scatter([], [], s=110, color=AMBER, label="Regional: disrupted")
ax.scatter([], [], s=40, color="white", edgecolor=INK, label="Severely disrupted"); ax.legend(loc="lower right")
style.titled(ax, f"Carrier choice moves disruption risk by {ca.disrupted.max() - ca.disrupted.min():.0%} points",
             "Share of flights disrupted by operating carrier, with 95% CI. Unadjusted - route mix is controlled for in notebook 04.")
style.save(fig, "05_carrier");
ca

# %% [markdown]
# ## 5. Airports

# %%
ap = show("ORIGIN", min_n=1500, save="by_origin_top", sort="disrupted")
fig, ax = plt.subplots(figsize=(10, 7.5))
y = np.arange(len(ap))
ax.hlines(y, ap.disrupted_lo, ap.disrupted_hi, color=INK, lw=1)
ax.scatter(ap.disrupted, y, s=np.sqrt(ap.n) * 2.2, color=[ACCENT if v > BASE + .03 else (GOOD if v < BASE - .03 else GREY) for v in ap.disrupted], zorder=3)
ax.set_yticks(y); ax.set_yticklabels(ap.index); ax.axvline(BASE, color=INK, lw=.8, ls=":"); ax.xaxis.set_major_formatter(PCT)
ax.set_xlabel("Share of departing flights disrupted (dot size = flight volume)")
style.titled(ax, "Departing from DFW, DCA or the New York airports carries roughly twice the risk of SLC or LAX",
             "Busiest origin airports (1,500+ sampled flights), with 95% CI")
style.save(fig, "06_airports");
ap.sort_values("disrupted", ascending=False).head(10)

# %% [markdown]
# ## 6. Things that matter less than people think

# %%
di = show("dist_band", save="by_distance")
rg = show("regional"); hw = show("holiday_window"); wk = show("dow_name", save="by_dow")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.4))
a1.bar(di.index.astype(str), di.disrupted, color=GREY, yerr=[di.disrupted - di.disrupted_lo, di.disrupted_hi - di.disrupted], ecolor=INK, capsize=2)
a1.axhline(BASE, color=INK, lw=.8, ls=":"); a1.yaxis.set_major_formatter(PCT); a1.set_ylim(0, .4); a1.set_xlabel("Flight distance (miles)")
style.titled(a1, "Flight length barely matters", "Share of flights disrupted, by distance")
a2.bar(wk.index.astype(str), wk.disrupted, color=[ACCENT if v > BASE + .02 else (GOOD if v < BASE - .02 else GREY) for v in wk.disrupted],
       yerr=[wk.disrupted - wk.disrupted_lo, wk.disrupted_hi - wk.disrupted], ecolor=INK, capsize=2)
a2.axhline(BASE, color=INK, lw=.8, ls=":"); a2.yaxis.set_major_formatter(PCT); a2.set_ylim(0, .4)
style.titled(a2, "Tuesday and Wednesday are the calm days", "Share of flights disrupted, by day of week")
style.save(fig, "07_distance_and_weekday");
pd.concat({"distance": di, "regional carrier": rg, "holiday window": hw, "day of week": wk})[["n", "disrupted", "disrupted_lo", "disrupted_hi", "severe", "cancelled"]]

# %% [markdown]
# ## 7. Why do delays build through the day?
# Average delay minutes per flight, split by the cause the airline reported.

# %%
causes = {"LATE_AIRCRAFT_DELAY": "Late inbound aircraft", "CARRIER_DELAY": "Airline (crew, maintenance)", "NAS_DELAY": "Air traffic system", "WEATHER_DELAY": "Extreme weather", "SECURITY_DELAY": "Security"}
cm = df[df.completed == 1].assign(**{c: lambda d, c=c: d[c].fillna(0) for c in causes}).groupby("dep_hour")[list(causes)].mean().loc[5:23].rename(columns=causes)
share = df[list(causes)].sum() / df[list(causes)].sum().sum()
fig, ax = plt.subplots()
cm.iloc[:, :4].plot.bar(stacked=True, ax=ax, color=[ACCENT, AMBER, BLUE, INK], width=.85, rot=0)
ax.set_xticklabels([f"{x % 12 or 12}{'a' if x < 12 else 'p'}" for x in cm.index]); ax.set_xlabel("Scheduled departure hour"); ax.set_ylabel("Average delay minutes per flight")
style.titled(ax, "Delays snowball: late inbound aircraft drive the afternoon and evening build-up",
             f"Share of all delay minutes: late aircraft {share.iloc[0]:.0%}, airline {share.iloc[1]:.0%}, air traffic system {share.iloc[2]:.0%}, extreme weather {share.iloc[3]:.0%}")
style.save(fig, "08_delay_causes_by_hour");
share.rename(index=causes).round(3)

# %% [markdown]
# ## 8. Are the patterns driven by a few bad days?

# %%
day = df.groupby("FL_DATE").agg(n=("disrupted", "size"), disrupted=("disrupted", "mean"), cancelled=("CANCELLED", "mean"))
worst = day.sort_values("cancelled", ascending=False).head(15)
calm = df[~df.FL_DATE.isin(worst.index)]
rob = pd.DataFrame({
    "all days": [df.disrupted.mean(), df[df.dep_hour.between(5, 9)].disrupted.mean(), df[df.dep_hour.between(17, 21)].disrupted.mean(), df.CANCELLED.mean()],
    "excluding 15 worst days": [calm.disrupted.mean(), calm[calm.dep_hour.between(5, 9)].disrupted.mean(), calm[calm.dep_hour.between(17, 21)].disrupted.mean(), calm.CANCELLED.mean()],
}, index=["disrupted - all flights", "disrupted - 5-9:59 a.m.", "disrupted - 5-9:59 p.m.", "cancelled"])
rob.to_csv(prep.TABLES / "robustness_event_days.csv")
print(worst.round(3)); rob.round(4)

# %% [markdown]
# ## Takeaways
# 1. **Time of day** is the strongest single pattern: risk climbs every hour from 5 a.m. to 7 p.m.
#    because late aircraft cascade through the day.
# 2. **Carrier** and **airport** each move risk by roughly 10 points; these are unadjusted and are
#    tested on like-for-like routes in notebook 04.
# 3. **Season**: June-July and December are worst; January has the cancellations.
# 4. **Distance** barely matters; **Tuesday/Wednesday** are the calm days.
# 5. The morning-evening gap survives removing the 15 worst days of the year.

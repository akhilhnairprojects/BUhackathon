# %% [markdown]
# # 07 · What should the client change? Policy simulation, trade-offs and the employee's side
# Each candidate booking rule is simulated on the full 2025 file by asking: *if the same trips
# (same routes, same volumes) had been booked under this rule, what would have happened?*
# Within each route the flights that satisfy the rule stand in for the flights actually taken,
# and routes are weighted by their real volume. Outcomes include rebooking after cancellations
# (notebook 05).
#
# **Cost assumptions (stated, varied):** traveler time at $50 / $100 / $150 per hour; a missed
# meeting (60+ min late) at $500; an overnight stranding at $300 in incidentals.

# %%
import sys
sys.path.insert(0, "../src")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
import prep, style
from style import INK, GREY, ACCENT, GOOD, BLUE, AMBER, PCT
style.use()
pd.set_option("display.width", 220, "display.max_columns", 60, "display.float_format", "{:.3f}".format)

t = pd.read_parquet(prep.PROCESSED / "nonstop_trips.parquet")
t["severe_t"] = (t.trip_delay >= 60).astype("int8")          # includes rebooked cancellations
t["disrupted_t"] = (t.trip_delay >= 15).astype("int8")
t["delay2h_t"] = (t.trip_delay >= 120).astype("int8")
t["delay_h"] = t.trip_delay.clip(lower=0) / 60
t["route"] = t.route.astype(str); t["brand"] = t.brand.astype(str)
t["season"] = t.MONTH.map({12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring", 6: "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall"})
METRICS = ["disrupted_t", "severe_t", "delay2h_t", "overnight", "delay_h", "late_night_arrival", "early_dep", "long_wait"]
print(f"{len(t):,} trips")

def per_1000(d):
    m = d[METRICS].mean()
    return pd.Series({"disrupted": m.disrupted_t * 1000, "hour+ late or stranded": m.severe_t * 1000, "2h+ late": m.delay2h_t * 1000,
                      "stranded overnight": m.overnight * 1000, "delay hours": m.delay_h * 1000, "late-night arrivals (11p-4a)": m.late_night_arrival * 1000,
                      "pre-6am departures": m.early_dep * 1000, "2h+ gate waits": m.long_wait * 1000})

def cost(row, rate):
    return row["delay hours"] * rate + row["hour+ late or stranded"] * 500 + row["stranded overnight"] * 300

base = per_1000(t)
base

# %% [markdown]
# ## 1. Simulate the candidate rules (same routes, same volumes)

# %%
def reweighted(d, mask, min_n=20):
    """Metrics if every route's trips had used only its flights satisfying `mask`."""
    sub = d[mask]
    g = sub.groupby("route")[METRICS].agg(["mean", "size"])
    means = g.xs("mean", axis=1, level=1); n = g.xs("size", axis=1, level=1).iloc[:, 0]
    means = means[n >= min_n]
    w = d.groupby("route").size().reindex(means.index)
    m = means.mul(w, axis=0).sum() / w.sum()
    out = pd.Series({"disrupted": m.disrupted_t * 1000, "hour+ late or stranded": m.severe_t * 1000, "2h+ late": m.delay2h_t * 1000,
                     "stranded overnight": m.overnight * 1000, "delay hours": m.delay_h * 1000, "late-night arrivals (11p-4a)": m.late_night_arrival * 1000,
                     "pre-6am departures": m.early_dep * 1000, "2h+ gate waits": m.long_wait * 1000})
    out["share of trips covered"] = w.sum() / len(d)
    return out

# preferred carrier per route = lowest severe-trip rate among brands with 300+ flights on the route
rb = t.groupby(["route", "brand"]).agg(n=("severe_t", "size"), sev=("severe_t", "mean"))
rb = rb[rb.n >= 300]
best = rb.reset_index().sort_values("sev").groupby("route").first()
multi = rb.reset_index().groupby("route").brand.nunique()
best = best[multi.reindex(best.index) >= 2]
is_best = t.route.isin(best.index) & (t.brand.values == best.brand.reindex(t.route).values)
has_choice = t.route.isin(best.index)

morning = t.dep_hour.between(5, 9); sweet = t.dep_hour.between(7, 9); dawn = t.dep_hour.between(5, 6); midday = t.dep_hour.between(10, 13)
evening = t.dep_hour.between(17, 21); tuewed = t.DAY_OF_WEEK.isin([2, 3]); sunday_eve = (t.DAY_OF_WEEK == 7) & evening
pol = pd.DataFrame({
    "Baseline (all trips as flown)": base.reindex(reweighted(t, t.dep_hour >= 0).index),
    "A. Depart before 10 a.m.": reweighted(t, morning),
    "A'. Depart 7-9:59 a.m. (employee-friendly)": reweighted(t, sweet),
    "A''. Depart 5-6:59 a.m.": reweighted(t, dawn),
    "   (for contrast) depart 5-9:59 p.m.": reweighted(t, evening),
    "B. Preferred carrier on routes with a choice": pd.concat([reweighted(t[has_choice], is_best[has_choice]).drop("share of trips covered"), pd.Series({"share of trips covered": has_choice.mean()})]),
    "   (same routes, carriers as flown)": pd.concat([per_1000(t[has_choice]), pd.Series({"share of trips covered": has_choice.mean()})]),
    "A+B. Morning + preferred carrier": pd.concat([reweighted(t[has_choice], (is_best & morning)[has_choice]).drop("share of trips covered"), pd.Series({"share of trips covered": has_choice.mean()})]),
    "D. Fly Tuesday or Wednesday": reweighted(t, tuewed),
    "   (for contrast) Sunday evening": reweighted(t, sunday_eve),
}).T
for r in [50, 100, 150]:
    pol[f"cost per 1,000 trips @${r}/h"] = pol.apply(lambda row: cost(row, r), axis=1)
pol.to_csv(prep.TABLES / "policy_simulation.csv")
pol.round(1)

# %%
show = pol.loc[["Baseline (all trips as flown)", "A. Depart before 10 a.m.", "A'. Depart 7-9:59 a.m. (employee-friendly)", "B. Preferred carrier on routes with a choice", "A+B. Morning + preferred carrier", "D. Fly Tuesday or Wednesday"]]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.6))
lab = ["Today", "A\nBefore 10a", "A'\n7-10a", "B\nPreferred\ncarrier*", "A+B\ncombined*", "D\nTue/Wed"]
col = [GREY, GOOD, GOOD, BLUE, GOOD, BLUE]
a1.bar(lab, show["hour+ late or stranded"], color=col)
for i, v in enumerate(show["hour+ late or stranded"]):
    a1.text(i, v + 1, f"{v:.0f}", ha="center", fontsize=10.5, fontweight="bold" if i else None)
a1.set_ylabel("Trips per 1,000 arriving 60+ min late or stranded")
a1.set_title("Trips per 1,000 arriving an hour late or stranded", fontsize=12, loc="center", fontweight="normal")
a2.bar(lab, show["cost per 1,000 trips @$100/h"] / 1000, color=col)
for i, v in enumerate(show["cost per 1,000 trips @$100/h"] / 1000):
    a2.text(i, v + 1, f"${v:.0f}k", ha="center", fontsize=10.5)
a2.set_ylabel("Disruption cost per 1,000 trips ($ thousands)")
a2.set_title("Disruption cost per 1,000 trips (traveler time $100/h, $500 per missed meeting, $300 per stranding)", fontsize=11, loc="center", fontweight="normal")
saving = (show.iloc[0, show.columns.get_loc('cost per 1,000 trips @$100/h')] - show.loc['A. Depart before 10 a.m.', 'cost per 1,000 trips @$100/h']) / 1000
fig.suptitle(f"Booking before 10 a.m. halves the chance of being an hour late - worth about ${saving:.0f}k per 1,000 trips",
             x=0.01, ha="left", fontsize=15, fontweight="bold", color=INK)
fig.text(0.01, 0.9, "Same routes and volumes as flown in 2025, cancellations rebooked on the next flight; cost figures use stated assumptions", fontsize=10.5, color="#5B6477")
fig.subplots_adjust(top=0.8, wspace=0.25)
fig.text(0.01, -0.04, f"* on the {has_choice.mean():.0%} of trips on routes where 2+ airlines each fly 300+ times a year", fontsize=9.5, color="#5B6477")
style.save(fig, "23_policy_impact");

# %% [markdown]
# ## 2. The employee's side: reliability vs sleep
# The safest flights (5-6 a.m.) cost the most sleep; evening flights cause the late-night arrivals.

# %%
hr = t.groupby("dep_hour").agg(n=("severe_t", "size"), severe=("severe_t", "mean"), late_night=("late_night_arrival", "mean"), delay2h=("delay2h_t", "mean"), overnight=("overnight", "mean")).loc[5:22]
hr.to_csv(prep.TABLES / "burden_by_hour.csv")
fig, ax = plt.subplots(figsize=(10.5, 5))
ax.plot(hr.index, hr.severe, color=ACCENT, lw=2.5, marker="o", label="Arrive 60+ min late or stranded")
ax.plot(hr.index, hr.late_night, color=INK, lw=2, marker="s", label="Land between 11 p.m. and 4 a.m.")
ax.axvspan(6.5, 9.5, color=GOOD, alpha=.12); ax.text(8, hr.severe.max() * .95, "7-10 a.m.\nsweet spot", ha="center", color=GOOD, fontweight="bold")
ax.axvspan(4.5, 6.5, color=AMBER, alpha=.12); ax.text(5.5, hr.severe.max() * .95, "pre-6 a.m.\n(4 a.m. alarm)", ha="center", color="#B07A1A", fontsize=9.5)
ax.set_xticks(range(5, 23)); ax.set_xticklabels([f"{x % 12 or 12}{'a' if x < 12 else 'p'}" for x in range(5, 23)])
ax.yaxis.set_major_formatter(PCT); ax.set_xlabel("Scheduled departure hour"); ax.legend(loc="center left")
style.titled(ax, "A 7-10 a.m. departure keeps most of the reliability of a dawn flight without the 4 a.m. alarm",
             f"Share of trips, by departure hour. 7-9 a.m.: {hr.loc[7:9].severe.mean():.1%} an hour late vs {hr.loc[5:6].severe.mean():.1%} at 5-6 a.m. and {hr.loc[17:21].severe.mean():.1%} at 5-9 p.m.")
style.save(fig, "24_reliability_vs_sleep");
hr.round(3)

# %% [markdown]
# ### The last flight of the day
# When the last departure on a route is cancelled, there is nothing left to rebook onto.

# %%
day = t.sched_dep.dt.normalize()
last_dep = t.groupby(["route", "brand", day]).sched_dep.transform("max")
t["is_last"] = (t.sched_dep == last_dep).astype("int8")
lf = t.groupby("is_last").agg(trips=("severe_t", "size"), cancelled=("CANCELLED", "mean"), stranded_overnight=("overnight", "mean"), severe=("severe_t", "mean"), avg_delay_if_cancelled=("trip_delay", lambda s: s[t.loc[s.index, "CANCELLED"] == 1].mean() / 60))
lf.index = ["Earlier flights", "Last flight of the day on the route"]
lf.to_csv(prep.TABLES / "last_flight.csv")
print(f"The last flight of the day is {lf.stranded_overnight.iloc[1] / lf.stranded_overnight.iloc[0]:.1f}x as likely to strand the traveler overnight.")
lf

# %% [markdown]
# ## 3. Buffer rule: how early should a must-attend traveler plan to land?
# 95th percentile of trip delay (including rebooked cancellations) by departure time and season.

# %%
buf = t.pivot_table(index="time_band", columns="season", values="trip_delay", aggfunc=lambda s: s.quantile(.95), observed=True)[["Winter", "Spring", "Summer", "Fall"]]
buf90 = t.pivot_table(index="time_band", columns="season", values="trip_delay", aggfunc=lambda s: s.quantile(.90), observed=True)[["Winter", "Spring", "Summer", "Fall"]]
buf.to_csv(prep.TABLES / "buffer_p95.csv"); buf90.to_csv(prep.TABLES / "buffer_p90.csv")
fig, ax = plt.subplots(figsize=(9, 4.8))
sns.heatmap(buf / 60, annot=True, fmt=".1f", cmap="YlOrRd", cbar=False, linewidths=2, linecolor="white", ax=ax, annot_kws={"fontsize": 11})
ax.set_xlabel(""); ax.set_ylabel(""); ax.grid(False)
ax.set_yticklabels([tl.get_text().replace(" (", "\n(") for tl in ax.get_yticklabels()], rotation=0)
style.titled(ax, f"To be 95% sure of making the meeting, a summer evening flight needs a {buf.loc[buf.index[4], 'Summer'] / 60:.1f}-hour buffer - a morning one, {buf.loc[buf.index[1], 'Summer'] / 60:.1f}",
             "Hours of buffer needed = 95th percentile of trip delay (incl. rebooking after cancellations), by departure time and season")
style.save(fig, "25_buffer_rule");
(buf / 60).round(1)

# %% [markdown]
# ## 4. Disruption-care: how often would support triggers fire, and what would they cost?
# Trigger-based support rather than blanket perks. Frequencies come from the data; the allowance
# amounts are assumptions (low / mid / high).

# %%
it = pd.read_parquet(prep.PROCESSED / "onestop_itineraries.parquet")
trig = pd.DataFrame({
    "Delay of 2h+ -> meal credit": [t.delay2h_t.mean() * 1000, reweighted(t, morning)["2h+ late"], 25, 40, 60],
    "Stranded overnight -> hotel + late start next day": [t.overnight.mean() * 1000, reweighted(t, morning)["stranded overnight"], 200, 300, 450],
    "Missed connection (per 1,000 connecting trips, 90-min rule) -> meal + rebooking help": [it[it.min_layover == 90].misconnect.mean() * 1000, it[(it.min_layover == 90) & (it.dep_hour < 10)].misconnect.mean() * 1000, 25, 40, 60],
}, index=["events per 1,000 trips today", "events per 1,000 trips with morning rule", "low $", "mid $", "high $"]).T
for lvl in ["low", "mid", "high"]:
    trig[f"budget per 1,000 trips today ({lvl})"] = trig["events per 1,000 trips today"] * trig[f"{lvl} $"]
trig.to_csv(prep.TABLES / "care_triggers.csv")
trig.round(1)

# %% [markdown]
# ## 5. Summary table for the deck

# %%
b, a, s, c, ab, d = [pol.loc[k] for k in ["Baseline (all trips as flown)", "A. Depart before 10 a.m.", "A'. Depart 7-9:59 a.m. (employee-friendly)", "B. Preferred carrier on routes with a choice", "A+B. Morning + preferred carrier", "D. Fly Tuesday or Wednesday"]]
same = pol.loc["   (same routes, carriers as flown)"]
ns = pd.read_csv(prep.TABLES / "nonstop_vs_onestop.csv", index_col=0)
hub = pd.read_csv(prep.TABLES / "hub_ranking.csv", index_col=0)
summary = pd.DataFrame([
    ["1. Book departures before 10 a.m. (7-10 a.m. default) for time-critical trips", f"{b['hour+ late or stranded']:.0f} -> {a['hour+ late or stranded']:.0f} per 1,000 trips an hour late or stranded ({1 - a['hour+ late or stranded'] / b['hour+ late or stranded']:.0%} fewer); delay hours {b['delay hours']:.0f} -> {a['delay hours']:.0f}", "Earlier wake-up; fewer flight options; 7-10 a.m. keeps most of the gain", "Share of time-critical bookings before 10 a.m.; severe-disruption rate"],
    ["2. Nonstop first; if connecting, 90+ min layover via approved hubs", f"Nonstop {ns.loc['Nonstop', 'severe']:.0%} vs one-stop {ns.loc['One-stop, min layover 45 min', 'severe']:.0%} (45-min) / {ns.loc['One-stop, min layover 90 min', 'severe']:.0%} (90-min) an hour late; best hubs ~{hub.severe.iloc[0]:.0%} vs worst ~{hub.severe.iloc[-1]:.0%}", "Nonstops can cost more (break-even ~$100-200 one-way); longer layovers add ~1 h", "Share of trips nonstop; missed-connection rate; overnight strandings"],
    ["3. Route-level preferred carrier list", f"On the {c['share of trips covered']:.0%} of trips with a choice: {same['hour+ late or stranded']:.0f} -> {c['hour+ late or stranded']:.0f} per 1,000 ({1 - c['hour+ late or stranded'] / same['hour+ late or stranded']:.0%} fewer)", "May conflict with loyalty programmes or negotiated fares; review quarterly", "Compliance with preferred list; severe rate on covered routes"],
    ["4. Season & weather rule: day-before travel or extra buffer in summer/winter; forecast-triggered rebooking", f"Summer evening p95 delay {buf.loc[buf.index[4], 'Summer'] / 60:.1f} h vs morning {buf.loc[buf.index[1], 'Summer'] / 60:.1f} h; adverse-weather days 33% vs 18% disrupted", "Hotel nights for day-before travel; travel desk effort", "Meetings missed; rebookings triggered; hotel spend"],
    ["Supporting: Tue/Wed where flexible; avoid last flight of the day; trigger-based care", f"Tue/Wed {d['hour+ late or stranded']:.0f} vs {b['hour+ late or stranded']:.0f} per 1,000; last flight {lf.stranded_overnight.iloc[1] / lf.stranded_overnight.iloc[0]:.1f}x overnight stranding", "Scheduling flexibility; small care budget", "Overnight strandings; traveler satisfaction"],
], columns=["recommendation", "evidence", "trade-off", "KPI"])
summary.to_csv(prep.TABLES / "recommendations_summary.csv", index=False)
pd.set_option("display.max_colwidth", 200)
summary

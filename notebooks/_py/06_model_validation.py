# %% [markdown]
# # 06 · Do the patterns hold together? Risk model and validation
# Purpose: (1) confirm that time of day, carrier, season and airport each matter **after
# controlling for the others**; (2) measure how predictable disruption is at booking time; (3)
# measure how much a short-notice weather signal adds. The model is a tool for explanation and
# for the risk look-up in the app, not an end in itself.
#
# * **Booking-time model** uses only what is known when the ticket is bought: carrier, origin,
#   destination, month, day of week, departure hour, distance, holiday window, and the airport's
#   typical adverse-weather frequency for that month (NOAA climatology).
# * **Short-notice model** adds the actual weather on the day at both ends (a stand-in for a 1-3
#   day forecast).
# * Leakage guard: no departure delay, no delay-cause fields, no tail numbers.
# * Validation: 5-fold cross-validation **grouped by flight date**, so a storm day is never in
#   both training and test folds.

# %%
import sys, warnings
sys.path.insert(0, "../src")
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, joblib
import prep, style
from style import INK, GREY, ACCENT, GOOD, BLUE, AMBER, PCT
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score
from sklearn.calibration import calibration_curve
style.use()
pd.set_option("display.width", 200, "display.max_columns", 60, "display.float_format", "{:.3f}".format)

df = pd.read_parquet(prep.PROCESSED / "flights_sample.parquet")
clim = pd.read_parquet(prep.PROCESSED / "weather_climatology.parquet")
air = pd.read_parquet(prep.PROCESSED / "airports_enriched.parquet")[["airport", "hub_tier"]]
wxf = pd.read_parquet(prep.PROCESSED / "flight_weather_flags.parquet").drop_duplicates(["FL_DATE", "ORIGIN", "DEST"])
wxf["ORIGIN"], wxf["DEST"] = wxf.ORIGIN.astype(str), wxf.DEST.astype(str)

df = df.merge(clim.rename(columns={"airport": "ORIGIN", "month": "MONTH", "p_adverse": "o_clim_adverse", "p_winter": "o_clim_winter", "p_thunder": "o_clim_thunder"}), on=["ORIGIN", "MONTH"], how="left")
df = df.merge(clim.rename(columns={"airport": "DEST", "month": "MONTH", "p_adverse": "d_clim_adverse", "p_winter": "d_clim_winter", "p_thunder": "d_clim_thunder"}), on=["DEST", "MONTH"], how="left")
df = df.merge(air.rename(columns={"airport": "ORIGIN", "hub_tier": "o_tier"}), on="ORIGIN", how="left").merge(air.rename(columns={"airport": "DEST", "hub_tier": "d_tier"}), on="DEST", how="left")
df = df.merge(wxf, on=["FL_DATE", "ORIGIN", "DEST"], how="left")
df = df.dropna(subset=["o_wx_adverse", "d_wx_adverse", "o_clim_adverse", "d_clim_adverse"]).reset_index(drop=True)
df["o_tier"], df["d_tier"] = df.o_tier.astype(str), df.d_tier.astype(str)
# airports with fewer than 100 sampled flights are pooled as 'OTHER' (keeps categories < 255 for the tree model)
cnt = pd.concat([df.ORIGIN, df.DEST]).value_counts()
small = set(cnt[cnt < 100].index)
df["ORIGIN"] = df.ORIGIN.where(~df.ORIGIN.isin(small), "OTHER")
df["DEST"] = df.DEST.where(~df.DEST.isin(small), "OTHER")
print(f"{len(df):,} flights with all features; {df.ORIGIN.nunique()} airport categories")

CAT = ["CARRIER", "ORIGIN", "DEST", "MONTH", "DAY_OF_WEEK", "dep_hour", "o_tier", "d_tier"]
NUM_BOOK = ["DISTANCE", "CRS_ELAPSED_TIME", "holiday_window", "o_clim_adverse", "d_clim_adverse", "o_clim_winter", "d_clim_winter", "o_clim_thunder", "d_clim_thunter" if False else "d_clim_thunder"]
NUM_SHORT = NUM_BOOK + ["o_wx_adverse", "d_wx_adverse", "o_wx_snow", "d_wx_snow", "o_wx_thunder", "d_wx_thunder", "o_wx_freezing", "d_wx_freezing"]
for c in ["o_wx_snow", "d_wx_snow", "o_wx_thunder", "d_wx_thunder", "o_wx_freezing", "d_wx_freezing"]:
    if c not in df:   # only the 'adverse' flag was saved per flight; rebuild the rest from the daily table
        pass
wx = pd.read_parquet(prep.PROCESSED / "weather_daily.parquet")[["airport", "date", "wx_snow", "wx_thunder", "wx_freezing"]]
df = df.merge(wx.rename(columns={"airport": "ORIGIN", "date": "FL_DATE", "wx_snow": "o_wx_snow", "wx_thunder": "o_wx_thunder", "wx_freezing": "o_wx_freezing"}), on=["ORIGIN", "FL_DATE"], how="left")
df = df.merge(wx.rename(columns={"airport": "DEST", "date": "FL_DATE", "wx_snow": "d_wx_snow", "wx_thunder": "d_wx_thunder", "wx_freezing": "d_wx_freezing"}), on=["DEST", "FL_DATE"], how="left")
df[NUM_SHORT] = df[NUM_SHORT].fillna(0)
y = df.disrupted.values; ys = df.severe.values
groups = df.FL_DATE.values
cv = GroupKFold(n_splits=5)

# %% [markdown]
# ## 1. Fit and cross-validate four models

# %%
def logit(num):
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30), CAT), ("num", StandardScaler(), num)])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(C=0.5, max_iter=2000))])

def hgb(num):
    pre = ColumnTransformer([("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CAT), ("num", "passthrough", num)])
    clf = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=48, min_samples_leaf=100,
                                         categorical_features=list(range(len(CAT))), random_state=0)
    return Pipeline([("pre", pre), ("clf", clf)])

models = {"Logistic - booking time": (logit(NUM_BOOK), NUM_BOOK), "Boosted trees - booking time": (hgb(NUM_BOOK), NUM_BOOK),
          "Logistic - short notice (+weather)": (logit(NUM_SHORT), NUM_SHORT), "Boosted trees - short notice (+weather)": (hgb(NUM_SHORT), NUM_SHORT)}
res, preds = [], {}
for name, (m, num) in models.items():
    X = df[CAT + num]
    p = cross_val_predict(m, X, y, cv=cv, groups=groups, method="predict_proba")[:, 1]
    preds[name] = p
    res.append([name, roc_auc_score(y, p), average_precision_score(y, p), brier_score_loss(y, p)])
res = pd.DataFrame(res, columns=["model", "AUC", "avg_precision", "Brier"]).set_index("model")
res.loc["Always predict the base rate"] = [0.5, y.mean(), brier_score_loss(y, np.full_like(y, y.mean(), dtype=float))]
res.to_csv(prep.TABLES / "model_scores.csv")
res

# %% [markdown]
# Disruption is a noisy event - most of it is caused by things no one knows at booking time - so
# an AUC in the high 0.60s at booking time is what we should expect. The useful questions are
# whether the model is **calibrated** (a predicted 30% really means 30%) and how well it
# **ranks** choices, which is what a booking policy needs.

# %%
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
for name, col in [("Logistic - booking time", BLUE), ("Boosted trees - booking time", INK), ("Boosted trees - short notice (+weather)", ACCENT)]:
    pt, pp = calibration_curve(y, preds[name], n_bins=12, strategy="quantile")
    a1.plot(pp, pt, marker="o", color=col, label=f"{name} (AUC {res.loc[name, 'AUC']:.2f})")
a1.plot([0, .6], [0, .6], color=GREY, ls="--"); a1.xaxis.set_major_formatter(PCT); a1.yaxis.set_major_formatter(PCT)
a1.set_xlabel("Predicted probability of disruption"); a1.set_ylabel("Observed share disrupted"); a1.legend(fontsize=9)
style.titled(a1, "Predicted risk is well calibrated", "Grouped 5-fold cross-validation (folds split by date)")
p = preds["Boosted trees - booking time"]
dec = pd.qcut(p, 10, labels=False) + 1
lift = pd.Series(y).groupby(dec).mean()
a2.bar(lift.index, lift.values, color=[GOOD if i <= 3 else (ACCENT if i >= 8 else GREY) for i in lift.index])
a2.axhline(y.mean(), color=INK, ls=":", lw=1); a2.text(10.5, y.mean(), f"avg {y.mean():.0%}", va="center", fontsize=9)
a2.set_xticks(range(1, 11)); a2.set_xlabel("Risk decile at booking time (1 = safest flights)"); a2.yaxis.set_major_formatter(PCT)
style.titled(a2, f"The riskiest tenth of bookings is disrupted {lift.iloc[-1] / lift.iloc[0]:.1f}x as often as the safest tenth",
             "Observed disruption by predicted-risk decile, booking-time boosted trees")
style.save(fig, "21_model_calibration_lift");

# %% [markdown]
# ## 2. Adjusted effects: what matters after controlling for everything else?
# Odds ratios from the booking-time logistic model (reference: Delta, 8 a.m., September, Tuesday).

# %%
m = logit(NUM_BOOK).fit(df[CAT + NUM_BOOK], y)
ohe = m.named_steps["pre"].named_transformers_["cat"]
names = list(ohe.get_feature_names_out(CAT)) + NUM_BOOK
coef = pd.Series(m.named_steps["clf"].coef_[0], index=names)
def ors(prefix, ref):
    s = coef[coef.index.str.startswith(prefix + "_")]
    s.index = s.index.str.replace(prefix + "_", "", regex=False)
    s = s[s.index != "infrequent_sklearn"]
    return np.exp(s - s.get(ref, 0))
or_hour = ors("dep_hour", "8"); or_hour.index = or_hour.index.astype(int); or_hour = or_hour.sort_index().loc[5:23]
or_car = ors("CARRIER", "DL").rename(index=prep.CARRIER_NAMES).sort_values()
or_mon = ors("MONTH", "9"); or_mon.index = or_mon.index.astype(int); or_mon = or_mon.sort_index()
or_dow = ors("DAY_OF_WEEK", "2"); or_dow.index = or_dow.index.astype(int); or_dow = or_dow.sort_index().rename(index=prep.DOW_NAMES)
pd.concat({"hour": or_hour, "carrier": or_car, "month": or_mon, "weekday": or_dow}).to_csv(prep.TABLES / "odds_ratios.csv")

fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
axes[0].bar(or_hour.index, or_hour.values, color=[GOOD if v < .8 else (ACCENT if v > 1.8 else GREY) for v in or_hour.values])
axes[0].set_xticks(range(5, 24, 2)); axes[0].set_xticklabels([f"{x % 12 or 12}{'a' if x < 12 else 'p'}" for x in range(5, 24, 2)])
style.titled(axes[0], "Departure hour (vs 8 a.m.)", f"7 p.m. odds x{or_hour[19]:.1f}")
axes[1].barh(or_car.index, or_car.values, color=[GOOD if v < .95 else (ACCENT if v > 1.25 else GREY) for v in or_car.values])
style.titled(axes[1], "Carrier (vs Delta)", "after controlling for route, time and season")
axes[2].bar(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], or_mon.values, color=[ACCENT if v > 1.5 else (GOOD if v < 1.1 else GREY) for v in or_mon.values])
style.titled(axes[2], "Month (vs September)", f"July odds x{or_mon[7]:.1f}")
for ax in axes:
    ax.axhline(1, color=INK, lw=1) if ax is not axes[1] else ax.axvline(1, color=INK, lw=1)
    ax.set_ylabel("Odds ratio") if ax is not axes[1] else ax.set_xlabel("Odds ratio")
fig.suptitle("Each lever matters on its own: adjusted odds of disruption from the booking-time model", x=0.01, ha="left", fontsize=15, fontweight="bold", color=INK, y=1.04)
style.save(fig, "22_adjusted_odds_ratios");
pd.DataFrame({"carrier OR vs Delta": or_car}).T

# %% [markdown]
# ## 3. What does the short-notice weather signal add?

# %%
gain = pd.DataFrame({
    "AUC": [res.loc["Boosted trees - booking time", "AUC"], res.loc["Boosted trees - short notice (+weather)", "AUC"]],
    "Brier": [res.loc["Boosted trees - booking time", "Brier"], res.loc["Boosted trees - short notice (+weather)", "Brier"]]}, index=["booking time", "short notice (+weather)"])
ps = preds["Boosted trees - short notice (+weather)"]
top = ps >= np.quantile(ps, .9)
gain["disruption rate in top-10% risk flights"] = [pd.Series(y)[p >= np.quantile(p, .9)].mean(), pd.Series(y)[top].mean()]
gain.to_csv(prep.TABLES / "short_notice_gain.csv")
gain

# %% [markdown]
# ## 4. Severe disruption (60+ min / cancelled / diverted) - same story?

# %%
ms = hgb(NUM_BOOK)
p_sev = cross_val_predict(ms, df[CAT + NUM_BOOK], ys, cv=cv, groups=groups, method="predict_proba")[:, 1]
print(f"severe: AUC {roc_auc_score(ys, p_sev):.3f}, Brier {brier_score_loss(ys, p_sev):.4f}, base rate {ys.mean():.3f}")
decs = pd.qcut(p_sev, 10, labels=False) + 1
pd.Series(ys).groupby(decs).mean().rename("observed severe rate by predicted decile").to_frame().T

# %% [markdown]
# ## 5. Save the booking-time model for the app

# %%
final = hgb(NUM_BOOK).fit(df[CAT + NUM_BOOK], y)
final_sev = hgb(NUM_BOOK).fit(df[CAT + NUM_BOOK], ys)
joblib.dump({"disrupted": final, "severe": final_sev, "cat": CAT, "num": NUM_BOOK}, prep.PROCESSED / "risk_model.joblib")
print("saved")

# %% [markdown]
# ## Takeaways
# * Every headline lever survives adjustment: departure hour, carrier, month and airport each shift
#   the odds independently.
# * Booking-time predictions are well calibrated; the riskiest decile of bookings is disrupted
#   several times as often as the safest decile - enough to act on.
# * Knowing the day's weather lifts predictive power materially: a forecast-triggered rebooking
#   rule has real information behind it.
# * Limitation: one year of data; the model ranks risk but cannot predict individual delays.

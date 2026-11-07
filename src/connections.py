"""Build one-stop itineraries from pairs of real flights and score them against nonstops.

The BTS file has single flights only, so a "one-stop trip" A -> H -> B is constructed:
  * booked: flight A->H, then the first H->B flight of the same airline brand scheduled to leave
    at least `min_layover` minutes after the first leg's scheduled arrival (max 5 h wait);
  * realised: if the traveler reaches H at least `mct` minutes before the second leg actually
    leaves, they fly it; otherwise they take the next completed H->B flight of that brand.
Cancelled flights are handled the same way for nonstops and one-stops: the traveler takes the
next completed flight of the same brand on that route.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAINLINE_WITH_REGIONALS = ["AA", "DL", "UA", "AS"]
FIXED_PARTNER = {"MQ": "AA", "OH": "AA"}          # Envoy and PSA fly only for American
MAX_WAIT = 300                                     # longest layover we would book (minutes)
CAP = 24 * 60                                      # cap trip delay at 24 h


def add_brand(f: pd.DataFrame) -> pd.DataFrame:
    """Airline brand a ticket would be sold under.

    Mainline carriers keep their own code; Envoy/PSA -> American. SkyWest and Republic fly for
    several brands, which the data does not record, so each of their flights is assigned to the
    largest of AA/DL/UA/AS at the busier end of the route (documented heuristic)."""
    f = f.copy()
    vol = f.groupby("ORIGIN", observed=True).size()
    main = (f[f.CARRIER.isin(MAINLINE_WITH_REGIONALS)]
            .groupby(["ORIGIN", "CARRIER"], observed=True).size().unstack(fill_value=0)
            .reindex(columns=MAINLINE_WITH_REGIONALS, fill_value=0))
    top = main.idxmax(axis=1)
    o, d = f.ORIGIN.astype(str), f.DEST.astype(str)
    hub_end = np.where(o.map(vol).fillna(0).values >= d.map(vol).fillna(0).values, o.values, d.values)
    brand = f.CARRIER.astype(str).replace(FIXED_PARTNER)
    multi = f.CARRIER.isin(["OO", "YX"]).values
    brand = np.where(multi, pd.Series(hub_end).map(top).fillna("OO").values, brand.values)
    f["brand"] = pd.Categorical(brand)
    return f


def _next_completed(q: pd.DataFrame, comp: pd.DataFrame, t_col: str) -> pd.DataFrame:
    """For each row of q (ORIGIN, DEST, brand, t_col) find the first completed flight on that
    route/brand that actually departs at or after t_col. Returns act_arr / sched_dep of it."""
    q = q[["ORIGIN", "DEST", "brand", t_col]].rename(columns={t_col: "t"})
    q = q.assign(_i=np.arange(len(q))).dropna(subset=["t"]).sort_values("t")
    r = pd.merge_asof(q, comp, left_on="t", right_on="act_dep", by=["ORIGIN", "DEST", "brand"],
                      direction="forward", tolerance=pd.Timedelta(hours=48))
    out = pd.DataFrame({"nx_arr": pd.NaT}, index=np.arange(q._i.max() + 1 if len(q) else 0))
    out.loc[r._i.values, "nx_arr"] = r.act_arr.values
    return out


def completed_table(f: pd.DataFrame) -> pd.DataFrame:
    c = f.loc[f.completed == 1, ["ORIGIN", "DEST", "brand", "act_dep", "act_arr"]].copy()
    for k in ["ORIGIN", "DEST", "brand"]:
        c[k] = c[k].astype(str)
    return c.sort_values("act_dep").reset_index(drop=True)


def nonstop_realised(f: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    """Trip-level outcome for every single flight, with cancellations rebooked."""
    q = f[["ORIGIN", "DEST", "brand", "sched_dep", "sched_arr", "completed", "ARR_DELAY"]].copy()
    for k in ["ORIGIN", "DEST", "brand"]:
        q[k] = q[k].astype(str)
    bad = q.completed.values == 0
    nx = _next_completed(q[bad].assign(t=lambda d: d.sched_dep + pd.Timedelta(minutes=1)), comp, "t")
    delay = q.ARR_DELAY.astype("float64").values.copy()
    reb = (nx.nx_arr.values - q.sched_arr.values[bad]) / np.timedelta64(1, "m")
    delay[bad] = np.where(np.isnan(reb), CAP, np.clip(reb, -120, CAP))
    final = q.sched_arr.values + (delay * 60).astype("timedelta64[s]")
    return pd.DataFrame({"trip_delay": delay.astype("float32"),
                         "rebooked": bad.astype("int8"),
                         "overnight": ((pd.DatetimeIndex(final).normalize() > pd.DatetimeIndex(q.sched_arr.values).normalize())
                                       & (delay >= 180)).astype("int8")}, index=f.index)


def pick_triples(f: pd.DataFrame, hubs: list[str], airports: list[str], min_leg: int = 365,
                 min_nonstop: int = 365, max_circuity: float = 1.5) -> pd.DataFrame:
    """Markets A->B (with nonstop service) and the hubs H that offer a sensible connection."""
    rt = (f.groupby(["ORIGIN", "DEST"], observed=True)
            .agg(n=("DISTANCE", "size"), dist=("DISTANCE", "first"), elapsed=("CRS_ELAPSED_TIME", "median"))
            .reset_index())
    rt["ORIGIN"], rt["DEST"] = rt.ORIGIN.astype(str), rt.DEST.astype(str)
    ns = rt[(rt.n >= min_nonstop) & rt.ORIGIN.isin(airports) & rt.DEST.isin(airports)]
    leg = rt[rt.n >= min_leg]
    l1 = leg[leg.DEST.isin(hubs)].rename(columns={"DEST": "HUB", "n": "n1", "dist": "d1"})[["ORIGIN", "HUB", "n1", "d1"]]
    l2 = leg[leg.ORIGIN.isin(hubs)].rename(columns={"ORIGIN": "HUB", "n": "n2", "dist": "d2"})[["HUB", "DEST", "n2", "d2"]]
    t = l1.merge(l2, on="HUB").merge(ns.rename(columns={"n": "n_nonstop", "elapsed": "nonstop_elapsed"}), on=["ORIGIN", "DEST"])
    t["circuity"] = (t.d1 + t.d2) / t.dist
    return t[(t.circuity <= max_circuity) & (t.ORIGIN != t.DEST)].reset_index(drop=True)


def build_itineraries(f: pd.DataFrame, comp: pd.DataFrame, triples: pd.DataFrame, min_layover: int,
                      mct: int = 30, frac: float = 1.0, seed: int = 7) -> pd.DataFrame:
    """One row per booked one-stop itinerary under a minimum-layover policy, with its outcome."""
    cols = ["ORIGIN", "DEST", "brand", "sched_dep", "sched_arr", "act_dep", "act_arr", "completed",
            "CRS_ELAPSED_TIME", "MONTH", "dep_hour"]
    g = f[cols].copy()
    for k in ["ORIGIN", "DEST", "brand"]:
        g[k] = g[k].astype(str)

    # leg 1: A -> H, expanded to every onward destination B that hub H serves for this market
    l1 = g.merge(triples[["ORIGIN", "HUB", "DEST"]].rename(columns={"DEST": "FINAL"}),
                 left_on=["ORIGIN", "DEST"], right_on=["ORIGIN", "HUB"])
    if frac < 1:
        l1 = l1.sample(frac=frac, random_state=seed)
    l1 = l1.rename(columns={"sched_dep": "dep1", "sched_arr": "arr1", "act_arr": "act_arr1", "completed": "ok1",
                            "CRS_ELAPSED_TIME": "el1"}).drop(columns=["DEST", "act_dep"])
    l1["want"] = l1.arr1 + pd.Timedelta(minutes=min_layover)

    # leg 2 as booked: first scheduled H -> B departure of the brand after the minimum layover
    l2 = g.rename(columns={"ORIGIN": "HUB", "DEST": "FINAL", "sched_dep": "dep2", "sched_arr": "arr2",
                           "act_dep": "act_dep2", "act_arr": "act_arr2", "completed": "ok2",
                           "CRS_ELAPSED_TIME": "el2"})[["HUB", "FINAL", "brand", "dep2", "arr2", "act_dep2", "act_arr2", "ok2", "el2"]]
    it = pd.merge_asof(l1.sort_values("want"), l2.sort_values("dep2"), left_on="want", right_on="dep2",
                       by=["HUB", "FINAL", "brand"], direction="forward",
                       tolerance=pd.Timedelta(minutes=MAX_WAIT - min_layover))
    it = it.dropna(subset=["dep2"]).reset_index(drop=True)
    it["layover"] = (it.dep2 - it.arr1) / np.timedelta64(1, "m")
    it["sched_total"] = it.el1 + it.layover + it.el2

    # when does the traveler actually reach the hub?
    q = it.loc[it.ok1 == 0, ["ORIGIN", "HUB", "brand", "dep1"]].rename(columns={"HUB": "DEST"})
    q["t"] = q.dep1 + pd.Timedelta(minutes=1)
    nx = _next_completed(q, comp, "t")
    at_hub = it.act_arr1.copy()
    at_hub[it.ok1.values == 0] = nx.nx_arr.values
    it["at_hub"] = at_hub

    made = (it.ok1 == 1) & (it.ok2 == 1) & (it.at_hub + pd.Timedelta(minutes=mct) <= it.act_dep2)
    q = it.loc[~made, ["HUB", "FINAL", "brand", "at_hub"]].rename(columns={"HUB": "ORIGIN", "FINAL": "DEST"})
    q["t"] = q.at_hub + pd.Timedelta(minutes=mct)
    nx = _next_completed(q, comp, "t")
    final = it.act_arr2.copy()
    final[~made.values] = nx.nx_arr.values
    d = (final - it.arr2) / np.timedelta64(1, "m")
    it["trip_delay"] = np.minimum(d.fillna(CAP), CAP).astype("float32")
    it["made"] = made.astype("int8")
    it["misconnect"] = ((it.ok1 == 1) & (it.ok2 == 1) & ~made).astype("int8")   # late inbound only
    it["overnight"] = ((final.dt.normalize() > it.arr2.dt.normalize()).fillna(True) & (it.trip_delay >= 180)).astype("int8")
    it["min_layover"] = min_layover
    return it[["ORIGIN", "HUB", "FINAL", "brand", "MONTH", "dep_hour", "dep1", "layover", "sched_total",
               "trip_delay", "made", "misconnect", "overnight", "ok1", "ok2", "min_layover"]]


def trip_metrics(d: pd.DataFrame, by) -> pd.DataFrame:
    g = d.assign(disrupted=(d.trip_delay >= 15), severe=(d.trip_delay >= 60), very=(d.trip_delay >= 180),
                 pos=d.trip_delay.clip(lower=0)).groupby(by, observed=True)
    return g.agg(n=("trip_delay", "size"), disrupted=("disrupted", "mean"), severe=("severe", "mean"),
                 delay_3h=("very", "mean"), overnight=("overnight", "mean"),
                 exp_delay_min=("pos", "mean"), p90_delay=("trip_delay", lambda s: s.quantile(.9)))

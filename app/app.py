"""Trip Risk Checker - Streamlit app for the Questrom Chart Champ datathon.

    streamlit run app/app.py

Reads only the small precomputed tables in data/processed and outputs/tables (never the raw 6.4M rows).
"""
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
T = ROOT / "outputs" / "tables"
CARRIER = {"AA": "American", "AS": "Alaska", "B6": "JetBlue", "DL": "Delta", "UA": "United", "WN": "Southwest",
           "OO": "SkyWest", "YX": "Republic", "OH": "PSA", "MQ": "Envoy"}
REGIONAL = {"OO": "regional", "YX": "regional", "OH": "regional · American", "MQ": "regional · American"}
BANDS = ["Early (5-6:59a)", "Morning (7-9:59a)", "Midday (10a-1:59p)", "Afternoon (2-5:59p)", "Evening (6-9:59p)", "Late night (10p-4:59a)"]
BAND_SHORT = {"Early (5-6:59a)": "Early", "Morning (7-9:59a)": "Morning", "Midday (10a-1:59p)": "Midday",
              "Afternoon (2-5:59p)": "Afternoon", "Evening (6-9:59p)": "Evening", "Late night (10p-4:59a)": "Late night"}
SEASON = {m: s for s, ms in {"Winter": [12, 1, 2], "Spring": [3, 4, 5], "Summer": [6, 7, 8], "Fall": [9, 10, 11]}.items() for m in ms}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

INK, MUTED, TEAL, RED, BLUE, AMBER, GREY, LINE, BG2 = "#1F2A44", "#5B6477", "#2A9D8F", "#D1495B", "#3A6EA5", "#E9A23B", "#B8BEC9", "#E6E9EF", "#F5F7FA"

st.set_page_config(page_title="Trip Risk Checker", page_icon="✈", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------------------------------------------------------- style
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stApp, .stMarkdown, .stDataFrame {{ font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif; }}
.stApp {{ background: #FFFFFF; color: {INK}; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1240px; }}
#MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
h1, h2, h3 {{ font-family: 'Inter', sans-serif; letter-spacing: -0.01em; color: {INK}; }}
.hero {{ display:flex; align-items:flex-end; justify-content:space-between; gap:24px; margin: 0 0 6px 0; }}
.hero h1 {{ font-size: 30px; font-weight: 700; margin: 0; line-height: 1.15; }}
.hero p {{ color: {MUTED}; margin: 6px 0 0 0; font-size: 14.5px; }}
.chips {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }}
.chip {{ background:{BG2}; border:1px solid {LINE}; color:{MUTED}; border-radius: 999px; padding: 4px 11px; font-size: 12px; white-space:nowrap; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {LINE}; margin-top: 10px; }}
.stTabs [data-baseweb="tab"] {{ height: 42px; padding: 0 14px; font-weight: 600; color: {MUTED}; background: transparent; }}
.stTabs [aria-selected="true"] {{ color: {INK}; border-bottom: 2px solid {TEAL}; }}
.card {{ background:#FFFFFF; border:1px solid {LINE}; border-radius:14px; padding:18px 20px; box-shadow: 0 1px 2px rgba(31,42,68,0.04); height:100%; }}
.card.best {{ border-color:{TEAL}; box-shadow: 0 0 0 3px rgba(42,157,143,0.12); }}
.card .k {{ font-size:12.5px; color:{MUTED}; font-weight:500; margin-bottom:2px; }}
.card .name {{ font-size:15px; font-weight:600; color:{INK}; }}
.card .big {{ font-size:40px; font-weight:700; letter-spacing:-0.02em; line-height:1.05; margin:10px 0 4px 0; }}
.card .sub {{ font-size:12.5px; color:{MUTED}; }}
.card .row {{ display:flex; justify-content:space-between; font-size:13px; padding:5px 0; border-top:1px dashed {LINE}; }}
.card .row:first-of-type {{ border-top:none; }}
.pill {{ display:inline-block; border-radius:999px; padding:3px 10px; font-size:12px; font-weight:600; }}
.pill.low {{ background:#E6F4F2; color:#1C7A6F; }} .pill.mid {{ background:#FDF1DC; color:#A3690F; }} .pill.high {{ background:#FBE7EA; color:#A8323F; }}
.callout {{ border-left: 4px solid {TEAL}; background:{BG2}; border-radius: 10px; padding: 12px 16px; margin: 14px 0 6px 0; font-size:14px; }}
.callout.warn {{ border-left-color:{AMBER}; }}
.kpi {{ background:{BG2}; border-radius:12px; padding:14px 16px; }}
.kpi .k {{ font-size:12px; color:{MUTED}; font-weight:500; }}
.kpi .v {{ font-size:26px; font-weight:700; color:{INK}; margin-top:2px; }}
.kpi .d {{ font-size:12px; font-weight:600; }}
.section {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; font-weight:600; margin: 22px 0 8px 0; }}
.small {{ font-size:12.5px; color:{MUTED}; }}
div[data-testid="stDataFrame"] {{ border:1px solid {LINE}; border-radius:12px; overflow:hidden; }}
</style>
""", unsafe_allow_html=True)


def chart_theme():
    return {"config": {
        "font": "Inter", "background": "transparent",
        "axis": {"labelColor": MUTED, "titleColor": MUTED, "gridColor": LINE, "domainColor": LINE, "tickColor": LINE, "labelFontSize": 12, "titleFontSize": 12},
        "legend": {"labelColor": INK, "titleColor": MUTED},
        "title": {"color": INK, "fontSize": 14, "anchor": "start", "fontWeight": 600},
        "view": {"stroke": None},
    }}


alt.themes.register("trip", chart_theme)
alt.themes.enable("trip")


@st.cache_data
def load():
    lk = pd.read_parquet(P / "route_lookup.parquet")
    for c in ["route", "ORIGIN", "DEST", "CARRIER", "time_band", "season"]:
        lk[c] = lk[c].astype(str)
    air = pd.read_parquet(P / "airports_enriched.parquet")
    clim = pd.read_parquet(P / "weather_climatology.parquet")
    hub = pd.read_csv(T / "hub_ranking.csv", index_col=0)
    pol = pd.read_csv(T / "policy_simulation.csv", index_col=0)
    be = pd.read_csv(T / "breakeven_by_market.csv")
    buf = pd.read_csv(T / "buffer_p95.csv", index_col=0)
    curve = pd.read_csv(T / "layover_curve.csv", index_col=0)
    ns = pd.read_csv(T / "nonstop_vs_onestop.csv", index_col=0)
    wr = pd.read_csv(T / "winter_readiness.csv", index_col=0)
    return lk, air, clim, hub, pol, be, buf, curve, ns, wr


lk, air, clim, hub, pol, be, buf, curve, ns, wr = load()
names = {r.airport: (f"{r.airport} · {r.municipality}" if isinstance(r.municipality, str) else r.airport) for r in air.itertuples()}
BASE_SEV = lk.severe.mul(lk.n).sum() / lk.n.sum()


def pill(p):
    cls = "low" if p < 0.07 else ("mid" if p < 0.12 else "high")
    lab = "Low risk" if cls == "low" else ("Moderate" if cls == "mid" else "High risk")
    return f'<span class="pill {cls}">{lab}</span>'


def hours(m):
    return f"{max(m, 0) / 60:.1f} h"


# ----------------------------------------------------------------------------- header
st.markdown(f"""
<div class="hero">
  <div><h1>✈ Trip Risk Checker</h1>
  <p>Which flight gets you to the meeting? Risk by route, carrier, time and season — from every US domestic flight in 2025.</p></div>
  <div class="chips"><span class="chip">6.4M flights · BTS 2025</span><span class="chip">NOAA weather · 324 airports</span><span class="chip">3.4M simulated connections</span></div>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Trip Risk Checker", "Policy Simulator", "Hubs & Airports"])

# ----------------------------------------------------------------------------- tab 1
with tab1:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.3, 1.3, 1, 1])
        origins = sorted(lk.ORIGIN.unique())
        o = c1.selectbox("From", origins, index=origins.index("BOS") if "BOS" in origins else 0, format_func=lambda a: names.get(a, a))
        dests = sorted(lk[lk.ORIGIN == o].DEST.unique())
        d = c2.selectbox("To", dests, index=dests.index("ORD") if "ORD" in dests else 0, format_func=lambda a: names.get(a, a))
        month = c3.selectbox("Month", MONTHS, index=5)
        band = c4.selectbox("Departure time", BANDS, index=1)
    season = SEASON[MONTHS.index(month) + 1]

    sub = lk[(lk.ORIGIN == o) & (lk.DEST == d)]
    cell = sub[(sub.time_band == band) & (sub.season == season)]
    st.markdown(f'<div class="section">{o} → {d} · {month} · {BAND_SHORT[band].lower()} departure · chance of arriving an hour late, cancelled or diverted</div>', unsafe_allow_html=True)
    if cell.empty:
        st.markdown('<div class="callout warn">No nonstop flights in that slot in 2025. Try another time of day, or see the connection options below.</div>', unsafe_allow_html=True)
    else:
        cell = cell[cell.n >= 20].sort_values("severe_shrunk") if (cell.n >= 20).any() else cell.sort_values("severe_shrunk")
        cols = st.columns(min(len(cell), 4))
        for i, (col, r) in enumerate(zip(cols, cell.itertuples())):
            delta = r.severe_shrunk - BASE_SEV
            col.markdown(f"""
<div class="card {'best' if i == 0 else ''}">
  <div class="k">{'Recommended' if i == 0 else 'Alternative'} · {REGIONAL.get(r.CARRIER, 'mainline')}</div>
  <div class="name">{CARRIER.get(r.CARRIER, r.CARRIER)}</div>
  <div class="big" style="color:{TEAL if i == 0 else INK}">{r.severe_shrunk:.0%}</div>
  <div class="sub">{pill(r.severe_shrunk)} &nbsp; {delta:+.0%} vs US average</div>
  <div style="height:10px"></div>
  <div class="row"><span>Disrupted (15+ min)</span><b>{r.disrupted_shrunk:.0%}</b></div>
  <div class="row"><span>Cancelled</span><b>{r.cancelled:.1%}</b></div>
  <div class="row"><span>Land early to be 95% safe</span><b>{hours(r.p95_delay)}</b></div>
  <div class="row"><span>Flights in 2025</span><b>{int(r.n)}</b></div>
</div>""", unsafe_allow_html=True)
        best = cell.iloc[0]
        if len(cell) > 1:
            worst = cell.iloc[-1]
            st.markdown(f'<div class="callout"><b>Book {CARRIER.get(best.CARRIER)}.</b> {best.severe_shrunk:.0%} chance of being an hour late vs {worst.severe_shrunk:.0%} on {CARRIER.get(worst.CARRIER)} '
                        f'({(worst.severe_shrunk - best.severe_shrunk) * 100:.0f} points lower). Plan to land {hours(best.p95_delay)} before the meeting to be 95% safe.</div>', unsafe_allow_html=True)

    left, right = st.columns([1.5, 1])
    with left:
        prof = sub.groupby("time_band").apply(lambda g: pd.Series({"severe": np.average(g.severe_shrunk, weights=g.n), "n": g.n.sum()}), include_groups=False).reindex(BANDS).dropna().reset_index()
        prof["label"] = prof.time_band.map(BAND_SHORT)
        if len(prof) > 1:
            ch = alt.Chart(prof).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("label:N", sort=[BAND_SHORT[b] for b in BANDS], title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("severe:Q", title=None, axis=alt.Axis(format="%")),
                color=alt.condition(alt.datum.time_band == band, alt.value(RED), alt.value(GREY)),
                tooltip=[alt.Tooltip("time_band:N", title="departure"), alt.Tooltip("severe:Q", format=".1%", title="hour late"), alt.Tooltip("n:Q", title="flights")]
            ).properties(height=230, title="Same route by departure time · all carriers and seasons")
            st.altair_chart(ch, use_container_width=True)
    with right:
        m = MONTHS.index(month) + 1
        wo = clim[(clim.airport == o) & (clim.month == m)]; wd = clim[(clim.airport == d) & (clim.month == m)]
        if not wo.empty and not wd.empty:
            st.markdown(f"""
<div class="card">
  <div class="k">Weather exposure · {month}</div>
  <div class="row"><span>Adverse-weather days at {o}</span><b>{wo.p_adverse.iloc[0]:.0%}</b></div>
  <div class="row"><span>Adverse-weather days at {d}</span><b>{wd.p_adverse.iloc[0]:.0%}</b></div>
  <div class="row"><span>Snow / freezing days</span><b>{wo.p_winter.iloc[0]:.0%} · {wd.p_winter.iloc[0]:.0%}</b></div>
  <div class="row"><span>Thunderstorm days</span><b>{wo.p_thunder.iloc[0]:.0%} · {wd.p_thunder.iloc[0]:.0%}</b></div>
  <div class="sub" style="margin-top:8px">Flights touching an airport with adverse weather were 1.8x as likely to be disrupted in 2025.</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="section">Nonstop or one-stop?</div>', unsafe_allow_html=True)
    mk = be[(be.ORIGIN == o) & (be.DEST == d)]
    k1, k2, k3 = st.columns(3)
    if mk.empty:
        k1.markdown(f'<div class="kpi"><div class="k">Across {len(be):,} city pairs · one-stop vs nonstop</div><div class="v">+{be.extra_severe_pts.median() * 100:.0f} pts</div><div class="d">median extra chance of being an hour late</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><div class="k">Extra time per trip (90-min layover)</div><div class="v">{be.extra_hours.median():.1f} h</div><div class="d">median, schedule + expected delay</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi"><div class="k">Fare saving needed to break even</div><div class="v">${be["breakeven_$100/h"].median():.0f}</div><div class="d">median one-way, at $100 per hour</div></div>', unsafe_allow_html=True)
    else:
        r = mk.iloc[0]
        k1.markdown(f'<div class="kpi"><div class="k">Nonstop · hour late</div><div class="v">{r.severe_ns:.0%}</div><div class="d" style="color:{TEAL}">simulated incl. rebooking</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><div class="k">Best one-stop (90-min layover) · hour late</div><div class="v">{r.severe_os:.0%}</div><div class="d" style="color:{RED}">+{(r.severe_os - r.severe_ns) * 100:.0f} pts · {r.extra_hours:.1f} extra hours</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi"><div class="k">Fare saving needed to break even</div><div class="v">${r["breakeven_$100/h"]:.0f}</div><div class="d">${r["breakeven_$50/h"]:.0f} at $50/h · ${r["breakeven_$150/h"]:.0f} at $150/h · ${r["breakeven_$100/h_plus_$500_meeting"]:.0f} with a $500 meeting</div></div>', unsafe_allow_html=True)
    st.markdown(f'<p class="small" style="margin-top:10px">Overall: nonstop {ns.loc["Nonstop", "severe"]:.0%} vs one-stop {ns.loc["One-stop, min layover 45 min", "severe"]:.0%} (45-min layover) / '
                f'{ns.loc["One-stop, min layover 90 min", "severe"]:.0%} (90-min) chance of arriving an hour late. Missed connections fall from '
                f'{curve.loc[45, "misconnect"]:.0%} to {curve.loc[90, "misconnect"]:.0%} with a 90-minute minimum layover. One-stops are constructed from real flight pairs, not tickets sold.</p>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------- tab 2
with tab2:
    st.markdown('<div class="section">What would each booking rule have done to 1,000 trips in 2025?</div>', unsafe_allow_html=True)
    l, r = st.columns([1, 2.2])
    with l:
        with st.container(border=True):
            st.markdown("**Assumptions**")
            rate = st.slider("Value of a traveler's hour ($)", 25, 200, 100, 25)
            meeting = st.slider("Cost of arriving an hour+ late ($)", 0, 2000, 500, 50)
            hotel = st.slider("Cost of an overnight stranding ($)", 0, 1000, 300, 50)
            rules = {"A. Depart before 10 a.m.": "Depart before 10 a.m.", "A'. Depart 7-9:59 a.m. (employee-friendly)": "Depart 7-10 a.m.",
                     "B. Preferred carrier on routes with a choice": "Preferred carrier (where there is a choice)", "A+B. Morning + preferred carrier": "Morning + preferred carrier",
                     "D. Fly Tuesday or Wednesday": "Fly Tuesday or Wednesday", "   (for contrast) depart 5-9:59 p.m.": "(contrast) evening departures", "   (for contrast) Sunday evening": "(contrast) Sunday evening"}
            picked = st.multiselect("Rules to show", list(rules.values()), default=list(rules.values())[:5])
    rows_ = ["Baseline (all trips as flown)"] + [k for k, v in rules.items() if v in picked]
    sim = pol.loc[rows_].copy()
    sim["cost_k"] = (sim["delay hours"] * rate + sim["hour+ late or stranded"] * meeting + sim["stranded overnight"] * hotel) / 1000
    sim["label"] = ["Today (as flown)"] + [rules[k] for k in rows_[1:]]
    base = sim.iloc[0]
    with r:
        if len(sim) > 1:
            bst = sim.iloc[1:].sort_values("hour+ late or stranded").iloc[0]
            a, b, c = st.columns(3)
            a.markdown(f'<div class="kpi"><div class="k">Hour late or stranded · {bst.label}</div><div class="v">{bst["hour+ late or stranded"]:.0f} <span class="small">/ 1,000</span></div><div class="d" style="color:{TEAL}">today {base["hour+ late or stranded"]:.0f} · {(bst["hour+ late or stranded"] / base["hour+ late or stranded"] - 1):+.0%}</div></div>', unsafe_allow_html=True)
            b.markdown(f'<div class="kpi"><div class="k">Delay hours per 1,000 trips</div><div class="v">{bst["delay hours"]:.0f}</div><div class="d" style="color:{TEAL}">today {base["delay hours"]:.0f}</div></div>', unsafe_allow_html=True)
            c.markdown(f'<div class="kpi"><div class="k">Modeled saving per 1,000 trips</div><div class="v">${base.cost_k - bst.cost_k:.0f}k</div><div class="d">if fully adopted · excludes extra fares</div></div>', unsafe_allow_html=True)
        ch = alt.Chart(sim.reset_index()).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y("label:N", sort=None, title=None), x=alt.X("hour+ late or stranded:Q", title="Trips per 1,000 arriving an hour late or stranded"),
            color=alt.condition(alt.datum.label == "Today (as flown)", alt.value(GREY), alt.value(TEAL)),
            tooltip=["label", alt.Tooltip("hour+ late or stranded:Q", format=".0f"), alt.Tooltip("cost_k:Q", format=".0f", title="cost $k")]).properties(height=40 + 32 * len(sim))
        st.altair_chart(ch, use_container_width=True)
    tbl = pd.DataFrame({"Rule": sim.label, "Hour+ late or stranded": sim["hour+ late or stranded"].round(0), "Delay hours": sim["delay hours"].round(0),
                        "Stranded overnight": sim["stranded overnight"].round(1), "Late-night arrivals": sim["late-night arrivals (11p-4a)"].round(0),
                        "Pre-6am departures": sim["pre-6am departures"].round(0), "Cost ($k)": sim.cost_k.round(0),
                        "Saving vs today ($k)": (base.cost_k - sim.cost_k).round(0), "Trips covered": sim["share of trips covered"].fillna(1).map(lambda v: f"{v:.0%}")}).set_index("Rule")
    st.markdown('<div class="section">Per 1,000 trips · same routes and volumes as flown in 2025 · cancelled travelers rebooked</div>', unsafe_allow_html=True)
    st.dataframe(tbl, use_container_width=True)
    st.markdown('<div class="section">Buffer rule · hours to land before a must-attend meeting (95% confidence)</div>', unsafe_allow_html=True)
    st.dataframe((buf / 60).round(1), use_container_width=True)
    st.markdown('<p class="small">95th percentile of trip delay including rebooking after cancellations, nonstop trips, 2025. Example: a summer evening flight needs ~3.4 h of buffer; a morning flight ~1.1 h.</p>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------- tab 3
with tab3:
    st.markdown('<div class="section">Connecting hubs ranked · 60-minute minimum layover · simulated one-stop trips</div>', unsafe_allow_html=True)
    h = hub.reset_index().rename(columns={"HUB": "hub"})
    h["hub_name"] = h.hub + " · " + h.name.str.replace(" International Airport", "").str.replace(" Airport", "")
    l, r = st.columns([1.4, 1])
    with l:
        ch = alt.Chart(h).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y("hub_name:N", sort=alt.EncodingSortField("severe", order="ascending"), title=None),
            x=alt.X("severe:Q", title="Share of one-stop trips arriving an hour late", axis=alt.Axis(format="%")),
            color=alt.Color("severe:Q", scale=alt.Scale(range=[TEAL, GREY, RED]), legend=None),
            tooltip=["hub", alt.Tooltip("severe:Q", format=".1%", title="hour late"), alt.Tooltip("misconnect:Q", format=".1%", title="missed connection"),
                     alt.Tooltip("overnight:Q", format=".1%", title="stranded overnight"), alt.Tooltip("winter_fragility_pts:Q", format=".0%", title="winter fragility (pts)"),
                     alt.Tooltip("markets:Q", title="city pairs connected"), "dominant_carrier"]).properties(height=560)
        st.altair_chart(ch, use_container_width=True)
    with r:
        top, bot = h.sort_values("severe").iloc[0], h.sort_values("severe").iloc[-1]
        st.markdown(f"""
<div class="card">
  <div class="k">Best connecting hub</div><div class="name">{top.hub_name}</div>
  <div class="big" style="color:{TEAL}">{top.severe:.0%}</div><div class="sub">hour late · missed connection {top.misconnect:.0%}</div>
  <div style="height:14px"></div>
  <div class="k">Riskiest connecting hub</div><div class="name">{bot.hub_name}</div>
  <div class="big" style="color:{RED}">{bot.severe:.0%}</div><div class="sub">hour late · missed connection {bot.misconnect:.0%}</div>
  <div style="height:14px"></div>
  <div class="row"><span>Minimum layover 45 → 90 min</span><b>missed connections {curve.loc[45, 'misconnect']:.1%} → {curve.loc[90, 'misconnect']:.1%}</b></div>
  <div class="row"><span>Winter-fragile hubs (Dec-Feb)</span><b>IAH · DFW · ATL · DCA</b></div>
</div>""", unsafe_allow_html=True)
    st.dataframe(h.set_index("hub")[["name", "markets", "misconnect", "severe", "overnight", "exp_delay_min", "winter_fragility_pts", "dominant_carrier", "dominant_carrier_share", "runways"]]
                 .rename(columns={"markets": "city pairs", "misconnect": "missed connection", "severe": "hour late", "overnight": "stranded overnight", "exp_delay_min": "expected delay (min)", "winter_fragility_pts": "winter fragility", "dominant_carrier": "main carrier", "dominant_carrier_share": "main carrier share"})
                 .style.format({"missed connection": "{:.1%}", "hour late": "{:.1%}", "stranded overnight": "{:.1%}", "expected delay (min)": "{:.0f}", "winter fragility": "{:.0%}", "main carrier share": "{:.0%}"}), use_container_width=True)

    st.markdown('<div class="section">Airports · disruption, weather exposure and winter fragility</div>', unsafe_allow_html=True)
    a = air.dropna(subset=["lat"]).copy()
    a = a[(a.lon > -170) & a.hub_tier.isin(["large", "medium"])]
    a = a.merge(wr[["uplift_pts"]].rename(columns={"uplift_pts": "winter_fragility"}), left_on="airport", right_index=True, how="left")
    c1, c2 = st.columns([1, 2])
    mo = c1.select_slider("Month for weather exposure", MONTHS, value="January")
    metric = c2.radio("Colour by", ["Disruption rate", "Adverse-weather days in month", "Winter fragility"], horizontal=True)
    a = a.merge(clim[clim.month == MONTHS.index(mo) + 1][["airport", "p_adverse", "p_winter", "p_thunder"]], on="airport", how="left")
    field = {"Disruption rate": "disrupted", "Adverse-weather days in month": "p_adverse", "Winter fragility": "winter_fragility"}[metric]
    pts = alt.Chart(a).mark_circle(opacity=.9, stroke="white", strokeWidth=.6).encode(
        longitude="lon:Q", latitude="lat:Q", size=alt.Size("departures:Q", scale=alt.Scale(range=[40, 900]), legend=None),
        color=alt.Color(f"{field}:Q", scale=alt.Scale(range=[TEAL, "#F2E8C9", RED]), legend=alt.Legend(format="%", title=metric, orient="bottom")),
        tooltip=["airport", "name", "hub_tier", alt.Tooltip("departures:Q", format=","), alt.Tooltip("disrupted:Q", format=".1%"), alt.Tooltip("cancelled:Q", format=".2%"),
                 alt.Tooltip("p_adverse:Q", format=".0%", title=f"adverse days {mo}"), alt.Tooltip("p_winter:Q", format=".0%", title="snow/freezing days"),
                 alt.Tooltip("winter_fragility:Q", format=".0%", title="winter fragility (pts)"), "runways:Q", "dominant_carrier"]).project(type="albersUsa").properties(height=460)
    st.altair_chart(pts, use_container_width=True)
    st.markdown('<p class="small">Large and medium hubs. Winter fragility = extra disruption on snow/freezing days vs the airport\'s own clear days (NOAA GHCN-Daily, 2025). Sources: BTS, NOAA, OurAirports.</p>', unsafe_allow_html=True)

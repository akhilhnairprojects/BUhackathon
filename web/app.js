import { render } from "preact";
import { useState, useEffect, useMemo } from "preact/hooks";
import { html } from "htm/preact";

const BASE = window.DATA_BASE;
const CARRIER = { AA: "American", AS: "Alaska", B6: "JetBlue", DL: "Delta", UA: "United", WN: "Southwest", OO: "SkyWest", YX: "Republic", OH: "PSA", MQ: "Envoy" };
const KIND = { OO: "regional", YX: "regional", OH: "regional · American", MQ: "regional · American" };
const BRAND = { MQ: "AA", OH: "AA" };
const REGIONAL = new Set(["OO", "YX"]);
const MAINLINE = new Set(["AA", "DL", "UA", "AS"]);
const BANDS = ["Early (5–6:59a)", "Morning (7–9:59a)", "Midday (10a–1:59p)", "Afternoon (2–5:59p)", "Evening (6–9:59p)", "Late night (10p–4:59a)"];
const SHORT = ["Early", "Morning", "Midday", "Afternoon", "Evening", "Late night"];
const MID = [360, 510, 720, 960, 1200, 1410];          // minutes after midnight at the middle of each band
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const SEASON_OF = [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0];
const DOW_F = [1.27, 1.05, 0.81, 0.86, 1.03, 1.05, 0.93];  // hour-late rate by weekday relative to the national average
const LAYOVER = 90;                                       // minimum connection we book, minutes
const MIS_SCALE = 0.59;                                   // hub missed-connection rate at 60 min -> 90 min
const T = { teal: "#4A6B48", red: "#B1372B", amber: "#A9761D", blue: "#45413A", grey: "#CFC6B2", ink: "#17150F", muted: "#76715F", line: "#D8D2C4", paper: "#F5F2EC", paper2: "#E3DDD0" };
const pct = (v, d = 2) => (v == null || isNaN(v)) ? "–" : (v * 100).toFixed(d) + "%";
const fmt = (v, d = 0) => (v == null || isNaN(v)) ? "–" : Number(v).toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d });
const money = (v) => "$" + fmt(v);
const hrs = (m) => (Math.max(m, 0) / 60).toFixed(1) + " h";
const level = (p) => p < 0.07 ? ["low", "Low risk"] : p < 0.12 ? ["mid", "Moderate"] : ["high", "High risk"];
const bandOf = (m) => { m = ((m % 1440) + 1440) % 1440; return m < 300 ? 5 : m < 420 ? 0 : m < 600 ? 1 : m < 840 ? 2 : m < 1080 ? 3 : m < 1320 ? 4 : 5; };
const brand = (c) => BRAND[c] || c;
const compat = (a, b) => brand(a) === brand(b) || (REGIONAL.has(a) && (MAINLINE.has(b) || REGIONAL.has(b))) || (REGIONAL.has(b) && MAINLINE.has(a));
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const isoDate = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const parseDate = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
const cache = {};
async function getJSON(path) { if (!cache[path]) cache[path] = fetch(`${BASE}/${path}`).then(r => r.ok ? r.json() : null).catch(() => null); return cache[path]; }
let LAST = null;   // the trip last checked, for the cost page
function useRoute() {
  const read = () => { const r = (location.hash.replace("#", "") || "check").split("?")[0]; return ["check", "cost", "hubs"].includes(r) ? r : "check"; };
  const [r, setR] = useState(read);
  useEffect(() => { const f = () => setR(read()); addEventListener("hashchange", f); return () => removeEventListener("hashchange", f); }, []);
  return r;
}

// ------------------------------------------------------------------ tiny SVG charts
function Bars({ data, highlight, height = 220, fmtY = (v) => pct(v) }) {
  const w = 600, h = height, pl = 44, pb = 28, pt = 14;
  const max = Math.max(...data.map(d => d.v)) * 1.15 || 1;
  const bw = (w - pl - 10) / data.length;
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(t => t * max);
  return html`<svg viewBox="0 0 ${w} ${h}" width="100%" style="display:block">
    ${ticks.map(t => html`<g><line x1=${pl} x2=${w - 10} y1=${pt + (h - pt - pb) * (1 - t / max)} y2=${pt + (h - pt - pb) * (1 - t / max)} stroke=${t === 0 ? T.ink : T.line} stroke-dasharray=${t === 0 ? "" : "2 3"} /><text class="num" x=${pl - 8} y=${pt + (h - pt - pb) * (1 - t / max) + 4} font-size="10.5" fill=${T.muted} text-anchor="end">${fmtY(t)}</text></g>`)}
    ${data.map((d, i) => { const bh = (h - pt - pb) * d.v / max; const x = pl + i * bw + bw * 0.2; const hot = d.k === highlight; return html`<g>
      <rect x=${x} y=${h - pb - bh} width=${bw * 0.6} height=${bh} fill=${hot ? T.red : (d.color || T.ink)} fill-opacity=${hot || d.color ? 1 : 0.82} />
      <text class="num" x=${x + bw * 0.3} y=${h - pb - bh - 7} font-size="11.5" font-weight="500" fill=${hot ? T.red : T.ink} text-anchor="middle">${fmtY(d.v)}</text>
      <text x=${x + bw * 0.3} y=${h - 8} font-size="12" fill=${hot ? T.ink : T.muted} font-weight=${hot ? 500 : 400} text-anchor="middle">${d.label}</text></g>`; })}
  </svg>`;
}
function HBars({ data, maxV, color = () => T.teal, rowH = 30, labelW = 170, valueFmt = (v) => fmt(v) }) {
  const w = 640, h = data.length * rowH + 8, max = maxV || Math.max(...data.map(d => d.v)) * 1.1;
  return html`<svg viewBox="0 0 ${w} ${h}" width="100%" style="display:block">
    ${data.map((d, i) => { const y = i * rowH + 6, bw = (w - labelW - 70) * d.v / max; return html`<g>
      <line x1=${labelW} x2=${w - 60} y1=${y + rowH - 3} y2=${y + rowH - 3} stroke=${T.line} />
      <text x=${labelW - 12} y=${y + rowH / 2 + 2} font-size="12.5" fill=${T.ink} text-anchor="end">${d.label}</text>
      <rect x=${labelW} y=${y + 6} width=${Math.max(bw, 2)} height=${rowH - 14} fill=${color(d, i)} />
      <text class="num" x=${labelW + bw + 10} y=${y + rowH / 2 + 2} font-size="12" font-weight="500" fill=${T.ink}>${valueFmt(d.v)}</text></g>`; })}
  </svg>`;
}

// ------------------------------------------------------------------ layout
function Nav({ route }) {
  const tabs = [["check", "Check a trip"], ["cost", "Cost of missing"], ["hubs", "Hubs & airports"]];
  return html`<div class="nav"><div class="nav-in">
    <a class="brand" href="#check"><span class="logo">No. 01</span>Trip Risk Checker</a>
    <nav class="tabs">${tabs.map(([k, l]) => html`<a class="tab ${route === k ? "active" : ""}" href="#${k}">${l}</a>`)}</nav>
    <div class="chips"><span class="chip">6.4M flights</span><span class="chip">Weather at 324 airports</span><span class="chip">3.4M connections</span></div>
  </div></div>`;
}
function Section({ title, hint }) { return html`<div class="section"><h2>${title}</h2>${hint && html`<span class="hint">${hint}</span>`}</div>`; }
function Kpi({ k, v, d, tone, small }) { return html`<div class="card kpi"><div class="k">${k}</div><div class="v">${v}${small && html` <small>${small}</small>`}</div>${d && html`<div class="d ${tone || ""}">${d}</div>`}</div>`; }

// ------------------------------------------------------------------ route finding
// Nonstop options come straight from the route table. One-stop options are estimated from the two legs:
// the first leg's cell, the hub's missed-connection rate (scaled by how reliable that first leg is and by
// the layover), and the second leg's cell in the time band the traveler would actually depart in.
function findOptions({ o, d, routesO, conns, hubsByCode, b, season, dowF, directMin }) {
  const opts = [];
  const rec = routesO && routesO[d];
  const maxFlying = directMin * 1.5 + 45;   // a connection that flies much further than the direct line is a detour, not an option
  if (rec) for (const c of rec.c) {
    const [car, band, s, n, dis, sev, can, p95, sched] = c;
    if (band !== b || s !== season) continue;
    opts.push({ kind: "nonstop", carrier: car, n, dis, can, p: sev * dowF, raw: sev, time: sched, sched, legs: `${o} → ${d}`, stop: null });
  }
  let checked = 0;
  for (const [hub, connH] of Object.entries(conns)) {
    const leg1 = routesO && routesO[hub]; const legs2 = connH && connH[d]; const hinfo = hubsByCode[hub];
    if (!leg1 || !legs2 || !hinfo || hub === d) continue;
    const bestByCarrier = {};
    for (const c of leg1.c) {
      const [car, band, s, n, dis, sev, can, p95, sched] = c;
      if (band !== b || s !== season || n < 15) continue;
      const b2 = bandOf(MID[b] + sched + LAYOVER);
      for (const [car2, cells] of Object.entries(legs2)) {
        if (!compat(car, car2)) continue;
        const cell = cells[`${b2},${season}`]; if (!cell) continue;
        const [n2, sev2, sched2] = cell;
        if (sched + sched2 > maxFlying) continue;
        checked++;
        const mis = clamp(hinfo.mis * MIS_SCALE * clamp(sev / 0.097, 0.5, 2), 0.01, 0.5);
        // the hub's simulated one-stop record (60-min layovers, scaled to 90), adjusted for how reliable these two legs are,
        // and never below the chance that either leg on its own runs an hour late
        const legRel = clamp(((sev + sev2) / 2) / 0.097, 0.4, 2.5);
        const p = Math.max(1 - (1 - sev) * (1 - sev2), hinfo.sev * 0.907 * Math.pow(legRel, 0.5)) * dowF;
        const key = brand(car);
        const opt = { kind: "onestop", carrier: car, carrier2: car2, n, n2, dis, can, mis, p, raw: p / dowF, time: sched + LAYOVER + sched2, sched, legs: `${o} → ${hub} → ${d}`, stop: hub, stopName: hinfo.name };
        if (!bestByCarrier[key] || bestByCarrier[key].p > p) bestByCarrier[key] = opt;
      }
    }
    opts.push(...Object.values(bestByCarrier));
  }
  const thin = opts.filter(x => x.kind === "nonstop" && x.n >= 20);
  const kept = thin.length ? opts.filter(x => x.kind !== "nonstop" || x.n >= 20) : opts;
  return { options: kept.sort((x, y) => x.p - y.p), checked };
}

// ------------------------------------------------------------------ screen 1
function Check({ airports, summary }) {
  const byCode = useMemo(() => Object.fromEntries(airports.map(a => [a.code, a])), [airports]);
  const codes = useMemo(() => airports.map(a => a.code).sort(), [airports]);
  const hubsByCode = useMemo(() => Object.fromEntries(summary.hubs.map(h => [h.hub, h])), [summary]);
  const defaultDate = useMemo(() => { const t = new Date(); t.setDate(t.getDate() + 14); return isoDate(t); }, []);
  const [o, setO] = useState("BOS"); const [d, setD] = useState("ORD"); const [date, setDate] = useState(defaultDate); const [b, setB] = useState(1);
  const [routes, setRoutes] = useState(null); const [conns, setConns] = useState(null);
  useEffect(() => {
    let live = true; setRoutes(null); setConns(null);
    getJSON(`routes/${o}.json`).then(async r => {
      if (!live) return; const rr = r || {}; setRoutes(rr);
      const hubs = Object.keys(hubsByCode).filter(h => rr[h] && h !== o);
      const got = await Promise.all(hubs.map(h => getJSON(`conn/${h}.json`)));
      if (live) setConns(Object.fromEntries(hubs.map((h, i) => [h, got[i]]).filter(x => x[1])));
    });
    return () => { live = false; };
  }, [o]);
  const when = parseDate(date); const m = when.getMonth(); const dow = when.getDay(); const season = SEASON_OF[m]; const dowF = DOW_F[dow];
  const ready = routes && conns;
  const directMin = useMemo(() => { const r = routes && routes[d]; if (r && r.c.length) return r.c.reduce((s, c) => s + c[8] * c[3], 0) / r.c.reduce((s, c) => s + c[3], 0);
    const A = byCode[o], B = byCode[d]; if (!A || !B || A.lat == null || B.lat == null) return 240;
    const toR = Math.PI / 180, dLat = (B.lat - A.lat) * toR, dLon = (B.lon - A.lon) * toR, h = Math.sin(dLat / 2) ** 2 + Math.cos(A.lat * toR) * Math.cos(B.lat * toR) * Math.sin(dLon / 2) ** 2;
    const miles = 3959 * 2 * Math.asin(Math.sqrt(h)); return 40 + miles / 8; }, [routes, o, d]);
  const { options, checked } = useMemo(() => ready ? findOptions({ o, d, routesO: routes, conns, hubsByCode, b, season, dowF, directMin }) : { options: [], checked: 0 }, [ready, routes, conns, o, d, b, season, dowF, directMin]);
  const best = options[0], worst = options[options.length - 1];
  useEffect(() => { if (best) LAST = { o, d, date, best, worst, band: SHORT[b] }; }, [best, worst]);
  const rec = routes && routes[d];
  const chartLeg = rec ? { cells: rec.c, title: "Same route by departure time", sub: "Nonstop, all airlines and seasons · chance of arriving an hour late" }
    : (best && routes[best.stop]) ? { cells: routes[best.stop].c, title: `First leg ${o} → ${best.stop} by departure time`, sub: "All airlines and seasons · chance of arriving an hour late" } : null;
  const byBand = chartLeg ? BANDS.map((lab, i) => { const cs = chartLeg.cells.filter(c => c[1] === i); const n = cs.reduce((s, c) => s + c[3], 0); return n ? { k: i, label: SHORT[i], v: cs.reduce((s, c) => s + c[5] * c[3], 0) / n, n } : null; }).filter(Boolean) : [];
  const wo = byCode[o]?.clim?.[m + 1], wd = byCode[d]?.clim?.[m + 1];
  const be = rec?.be, bm = summary.be_median;
  const label = (c) => `${c} · ${byCode[c]?.name || c}`;
  const dayLabel = `${DAYS[dow]} ${when.getDate()} ${MONTHS[m].slice(0, 3)}`;
  const nice = (x) => x.kind === "nonstop" ? `${CARRIER[x.carrier] || x.carrier} nonstop` : `${CARRIER[x.carrier] || x.carrier} via ${x.stop}`;
  return html`
    <div class="hero"><div><div class="eyebrow">Check a trip</div><h1 style="margin-top:10px">Which flight actually gets you <em>to the meeting?</em></h1><p>Pick where you start, where you need to be and when. We rank every nonstop and same-airline connection by the chance of arriving an hour late, using a full year of US flights and the weather at both ends.</p></div></div>
    <div class="card pad"><div class="controls">
      <div class="field"><label>From</label><select class="select" value=${o} onChange=${e => setO(e.target.value)}>${codes.map(c => html`<option value=${c}>${label(c)}</option>`)}</select></div>
      <div class="field"><label>To</label><select class="select" value=${d} onChange=${e => setD(e.target.value)}>${codes.filter(c => c !== o).map(c => html`<option value=${c}>${label(c)}</option>`)}</select></div>
      <div class="field"><label>Travel date</label><input class="select date" type="date" value=${date} onChange=${e => e.target.value && setDate(e.target.value)} /></div>
      <div class="field"><label>Departure time</label><select class="select" value=${b} onChange=${e => setB(+e.target.value)}>${BANDS.map((x, i) => html`<option value=${i}>${x}</option>`)}</select></div>
    </div></div>
    <${Section} title=${`${o} → ${d} · ${dayLabel} · ${SHORT[b].toLowerCase()} departure`} hint="chance of arriving an hour late, cancelled or diverted" />
    ${!ready ? html`<div class="skeleton"></div>` : !options.length ? html`<div class="card empty">No nonstop or same-airline connection found for that departure time. Try another time of day.</div>` : html`
      <div class="grid g${Math.min(options.length, 4)}">${options.slice(0, 4).map((c, i) => { const [cls, txt] = level(c.p); return html`<div class="card rcard ${i === 0 ? "best" : ""}">
        <div class="tag">${i === 0 ? "Recommended" : "Alternative"} · ${c.kind === "nonstop" ? "nonstop" : `via ${c.stop}`}</div><div class="name">${CARRIER[c.carrier] || c.carrier}</div>
        <div class="big" style="color:${i === 0 ? T.ink : T.muted}">${pct(c.p)}</div>
        <div class="meta"><span class="pill ${cls}">${txt}</span><span>${(c.p - summary.base_sev >= 0 ? "+" : "") + pct(c.p - summary.base_sev)} vs US avg</span></div>
        <div class="rows">
          <div class="row"><span>Route</span><b>${c.legs}</b></div>
          <div class="row"><span>Total time</span><b>${hrs(c.time)}${c.stop ? ` · ${LAYOVER} min at ${c.stop}` : ""}</b></div>
          ${c.kind === "nonstop" ? html`<div class="row"><span>Disrupted (15+ min)</span><b>${pct(c.dis)}</b></div><div class="row"><span>Cancelled</span><b>${pct(c.can)}</b></div>`
            : html`<div class="row"><span>Missed connection (est.)</span><b>${pct(c.mis)}</b></div><div class="row"><span>Second leg</span><b>${CARRIER[c.carrier2] || c.carrier2}</b></div>`}
          <div class="row"><span>Flights observed</span><b>${fmt(c.n)}${c.n2 ? ` · ${fmt(c.n2)}` : ""}</b></div>
        </div>
      </div>`; })}</div>
      ${options.length > 1 && html`<div class="banner"><div><b>Book ${nice(best)}.</b> ${pct(best.p)} chance of being an hour late, ${((worst.p - best.p) * 100).toFixed(2)} points lower than ${nice(worst)}. Adjusted for a ${DAYS[dow]} in ${MONTHS[m]}.</div></div>`}
      <p class="foot">${rec ? `${options.filter(x => x.kind === "nonstop").length} nonstop and ` : "No nonstop flights in this slot; "}${options.filter(x => x.kind === "onestop").length} connecting options through ${Object.keys(conns).length} hubs (${fmt(checked)} leg pairs checked). Connections assume a ${LAYOVER}-minute layover on the same airline; their risk is estimated from the hub's simulated one-stop record and the reliability of the two legs; routes that fly more than 1.5x the direct distance are left out.</p>`}
    <div class="grid g2" style="margin-top:44px">
      <div class="card pad">${chartLeg ? html`<p class="chart-title">${chartLeg.title}</p><p class="chart-sub">${chartLeg.sub}</p>${byBand.length > 1 ? html`<${Bars} data=${byBand} highlight=${b} />` : html`<div class="foot">Not enough departures to compare.</div>`}` : html`<p class="chart-title">By departure time</p><div class="foot">Pick a route to compare departure times.</div>`}</div>
      <div class="card pad"><p class="chart-title">Weather exposure · ${MONTHS[m]}</p><p class="chart-sub">Share of days with adverse weather at each airport in this month</p>
        ${wo && wd ? html`<div class="rows" style="margin-top:0"><div class="row"><span>Adverse-weather days at ${o}</span><b>${pct(wo[0])}</b></div><div class="row"><span>Adverse-weather days at ${d}</span><b>${pct(wd[0])}</b></div><div class="row"><span>Snow / freezing days</span><b>${pct(wo[1])} · ${pct(wd[1])}</b></div><div class="row"><span>Thunderstorm days</span><b>${pct(wo[2])} · ${pct(wd[2])}</b></div></div><p class="foot">Flights touching an airport with adverse weather are 1.8x as likely to be disrupted. ${DAYS[dow]}s run ${dowF >= 1 ? `${((dowF - 1) * 100).toFixed(2)}% above` : `${((1 - dowF) * 100).toFixed(2)}% below`} the average weekday for hour-late arrivals.</p>` : html`<div class="foot">No weather station matched.</div>`}
      </div>
    </div>
    <${Section} title="Worth the stop?" hint="one-stops are built from real flight pairs, not tickets sold" />
    <div class="grid g3">
      ${be ? html`<${Kpi} k="Nonstop · hour late" v=${pct(be.ns)} d="simulated, cancellations rebooked" tone="good" /><${Kpi} k="Best one-stop (90-min layover) · hour late" v=${pct(be.os)} d=${`+${((be.os - be.ns) * 100).toFixed(2)} pts · ${be.xh.toFixed(1)} extra hours per trip`} tone="bad" /><${Kpi} k="Fare saving needed to break even" v=${"$" + fmt(be.b100)} d=${`$${fmt(be.b50)} at $50/h · $${fmt(be.b150)} at $150/h · $${fmt(be.bm)} with a $500 meeting`} />`
         : html`<${Kpi} k=${`Across ${fmt(bm.n)} city pairs · one-stop vs nonstop`} v=${"+" + (bm.pts * 100).toFixed(2) + " pts"} d="median extra chance of being an hour late" tone="bad" /><${Kpi} k="Extra time per trip (90-min layover)" v=${bm.xh.toFixed(1) + " h"} d="median · schedule plus expected delay" /><${Kpi} k="Fare saving needed to break even" v=${"$" + fmt(bm.b100)} d="median one-way, at $100 per hour of traveler time" />`}
    </div>
    <p class="foot">Overall: nonstop ${pct(summary.nsos["Nonstop"])} vs one-stop ${pct(summary.nsos["One-stop, min layover 45 min"])} (45-min layover) / ${pct(summary.nsos["One-stop, min layover 90 min"])} (90-min) chance of arriving an hour late. Missed connections fall from ${pct(summary.layover[45].mis)} to ${pct(summary.layover[90].mis)} with a 90-minute minimum layover.</p>`;
}

// ------------------------------------------------------------------ screen 2 · opportunity cost
const HABITS = [["Baseline (all trips as flown)", "Typical booking today"], ["A'. Depart 7-9:59 a.m. (employee-friendly)", "Morning departure (7–10 a.m.)"], ["D. Fly Tuesday or Wednesday", "Fly Tuesday or Wednesday"], ["   (for contrast) depart 5-9:59 p.m.", "Evening departure"], ["   (for contrast) Sunday evening", "Sunday evening"]];
function Cost({ summary }) {
  const [meet, setMeet] = useState(1500), [rate, setRate] = useState(100), [hotel, setHotel] = useState(300);
  const pol = Object.fromEntries(summary.policies.map(p => [p.key, p]));
  const base = pol["Baseline (all trips as flown)"];
  const perTrip = (p) => (p.hour_late * meet + p.delay_h * rate + p.overnight * hotel) / 1000;
  // a trip whose chance of being an hour late is p: scale the national delay hours and strandings with it
  const costOf = (p) => { const k = p / (base.hour_late / 1000); return p * meet + (base.delay_h / 1000) * k * rate + (base.overnight / 1000) * k * hotel; };
  const rows = HABITS.map(([k, l]) => ({ label: l, v: perTrip(pol[k]) }));
  const trip = LAST;
  const cBest = trip ? costOf(trip.best.p) : costOf(base.hour_late / 1000);
  const cWorst = trip && trip.worst !== trip.best ? costOf(trip.worst.p) : null;
  const nice = (x) => x.kind === "nonstop" ? `${CARRIER[x.carrier] || x.carrier} nonstop` : `${CARRIER[x.carrier] || x.carrier} via ${x.stop}`;
  return html`
    <div class="hero"><div><div class="eyebrow">Cost of missing</div><h1 style="margin-top:10px">What does missing the meeting <em>actually cost?</em></h1><p>Three numbers you choose, one answer. The chance of being an hour late comes from the trip you checked; the value of the meeting, of an hour and of a night in a hotel are yours to set.</p></div></div>
    <div class="grid" style="grid-template-columns: 300px 1fr; gap: 48px">
      <div class="card pad">
        <p class="chart-title">Your assumptions</p>
        <div class="rlabel"><span>What the meeting is worth</span><b>${money(meet)}</b></div><input class="range" type="range" min="0" max="5000" step="100" value=${meet} onInput=${e => setMeet(+e.target.value)} />
        <div class="rlabel"><span>Value of a traveler's hour</span><b>${money(rate)}</b></div><input class="range" type="range" min="25" max="250" step="25" value=${rate} onInput=${e => setRate(+e.target.value)} />
        <div class="rlabel"><span>A night stranded (hotel, meals)</span><b>${money(hotel)}</b></div><input class="range" type="range" min="0" max="1000" step="50" value=${hotel} onInput=${e => setHotel(+e.target.value)} />
        <p class="foot">Expected cost = chance of being an hour late × meeting value, plus the delay hours and overnight strandings that come with that level of risk, priced at your rates.</p>
      </div>
      <div>
        <div class="grid g3" style="margin-bottom:32px">
          <${Kpi} k=${trip ? `${trip.o} → ${trip.d} · ${nice(trip.best)}` : "Average US trip"} v=${money(cBest)} small="per trip" d=${`${pct(trip ? trip.best.p : base.hour_late / 1000)} chance of being an hour late`} tone="good" />
          ${cWorst != null ? html`<${Kpi} k=${`Riskiest option · ${nice(trip.worst)}`} v=${money(cWorst)} small="per trip" d=${`${pct(trip.worst.p)} chance of being an hour late`} tone="bad" />` : html`<${Kpi} k="Evening departure" v=${money(perTrip(pol["   (for contrast) depart 5-9:59 p.m."]))} small="per trip" d="national average, 5–10 p.m." tone="bad" />`}
          <${Kpi} k="Worth paying for the safer flight" v=${money(cWorst != null ? cWorst - cBest : perTrip(pol["   (for contrast) depart 5-9:59 p.m."]) - perTrip(pol["A'. Depart 7-9:59 a.m. (employee-friendly)"]))} small="fare premium" d="the gap in expected cost between the two" />
        </div>
        <div class="card pad"><p class="chart-title">Expected cost per trip by booking habit</p><p class="chart-sub">Same routes and volumes, if everyone booked this way · cancelled travelers rebooked</p>
          <${HBars} data=${rows} maxV=${Math.max(...rows.map(r => r.v)) * 1.15} color=${(d, i) => i === 0 ? T.grey : (d.label.startsWith("Morning") || d.label.startsWith("Fly") ? T.ink : T.red)} rowH=${36} labelW=${230} valueFmt=${(v) => money(v)} /></div>
        <p class="foot">${trip ? "" : "Check a trip first and this page will use that route's numbers. "}Fares are not in the data, so the premium shown is the most a safer flight is worth paying for, not what it costs.</p>
      </div>
    </div>`;
}

// ------------------------------------------------------------------ screen 3
function Hubs({ airports, summary }) {
  const hubs = [...summary.hubs].sort((a, b) => a.sev - b.sev);
  const [month, setMonth] = useState(0); const [metric, setMetric] = useState("dis");
  const [geo, setGeo] = useState(null);
  useEffect(() => { Promise.all([import("d3-geo"), import("topojson-client"), fetch("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json").then(r => r.json())]).then(([d3, topo, us]) => {
    const proj = d3.geoAlbersUsa().scale(1100).translate([480, 290]); const path = d3.geoPath(proj);
    setGeo({ states: path(topo.mesh(us, us.objects.states, (a, b) => a !== b)), nation: path(topo.feature(us, us.objects.nation)), proj });
  }).catch(() => setGeo({ error: true })); }, []);
  const big = airports.filter(a => (a.tier === "large" || a.tier === "medium") && a.lat != null);
  const val = (a) => metric === "dis" ? a.dis : metric === "wx" ? (a.clim?.[month + 1]?.[0] ?? null) : a.wf;
  const vals = big.map(val).filter(v => v != null); const lo = Math.min(...vals), hi = Math.max(...vals);
  const colorOf = (v) => { if (v == null) return T.grey; const t = (v - lo) / (hi - lo || 1); const a = [207, 198, 178], c = [177, 55, 43]; const mix = a.map((x, i) => x + (c[i] - x) * t); return `rgb(${mix.map(Math.round).join(",")})`; };
  const maxDep = Math.max(...big.map(a => a.dep));
  const top = hubs[0], bot = hubs[hubs.length - 1];
  return html`
    <div class="hero"><div><div class="eyebrow">Hubs & airports</div><h1 style="margin-top:10px">Connecting hubs, ranked by what happens to <em>one-stop trips</em></h1><p>3.4 million itineraries built from real flight pairs with a 60-minute minimum layover; a traveler who misses a connection is rebooked on the next flight of the same airline. Simulated, not observed tickets.</p></div></div>
    <div class="grid g2">
      <div class="card pad"><p class="chart-title">Share of one-stop trips arriving an hour late</p><p class="chart-sub">60-minute minimum layover</p>
        <${HBars} data=${hubs.map(h => ({ label: `${h.hub} · ${h.name.replace(" International Airport", "").replace(" Airport", "").slice(0, 26)}`, v: h.sev }))} maxV=${0.26} color=${(d) => d.v < 0.12 ? T.teal : d.v > 0.165 ? T.red : T.grey} rowH=${28} labelW=${215} valueFmt=${(v) => pct(v)} /></div>
      <div>
        <div class="card rcard best"><div class="tag">Best connecting hub</div><div class="name">${top.hub} · ${top.name}</div><div class="big" style="color:${T.ink}">${pct(top.sev)}</div><div class="meta">hour late · missed connection ${pct(top.mis)} · stranded overnight ${pct(top.ov)}</div></div>
        <div class="card rcard" style="margin-top:32px"><div class="tag" style="color:${T.red}">Riskiest connecting hub</div><div class="name">${bot.hub} · ${bot.name}</div><div class="big" style="color:${T.red}">${pct(bot.sev)}</div><div class="meta">hour late · missed connection ${pct(bot.mis)} · stranded overnight ${pct(bot.ov)}</div>
          <div class="rows"><div class="row"><span>Minimum layover 45 → 90 min</span><b>missed connections ${pct(summary.layover[45].mis)} → ${pct(summary.layover[90].mis)}</b></div><div class="row"><span>Winter-fragile hubs (Dec–Feb)</span><b>IAH · DFW · ATL · DCA</b></div><div class="row"><span>Nonstop, same city pairs</span><b>${pct(summary.nsos["Nonstop"])} hour late</b></div></div></div>
      </div>
    </div>
    <div class="card" style="margin-top:32px; overflow:auto"><table class="table"><thead><tr><th>Hub</th><th>Airport</th><th class="num">City pairs</th><th class="num">Missed connection</th><th class="num">Hour late</th><th class="num">Stranded overnight</th><th class="num">Expected delay</th><th class="num">Winter fragility</th><th>Main carrier</th></tr></thead>
      <tbody>${hubs.map(h => html`<tr><td><b>${h.hub}</b></td><td>${h.name}</td><td class="num">${fmt(h.markets)}</td><td class="num">${pct(h.mis)}</td><td class="num">${pct(h.sev)}</td><td class="num">${pct(h.ov)}</td><td class="num">${fmt(h.delay)} min</td><td class="num">${h.wf == null ? "–" : "+" + pct(h.wf)}</td><td>${CARRIER[h.carrier] || h.carrier} (${pct(h.share)})</td></tr>`)}</tbody></table></div>
    <${Section} title="Airports · disruption, weather exposure and winter fragility" hint="large and medium hubs · dot size = departures" />
    <div class="card pad">
      <div style="display:flex; gap:14px; align-items:center; flex-wrap:wrap; margin-bottom:10px">
        <div class="seg">${[["dis", "Disruption rate"], ["wx", "Adverse-weather days"], ["wf", "Winter fragility"]].map(([k, l]) => html`<button class=${metric === k ? "on" : ""} onClick=${() => setMetric(k)}>${l}</button>`)}</div>
        ${metric === "wx" && html`<select class="select" style="width:160px" value=${month} onChange=${e => setMonth(+e.target.value)}>${MONTHS.map((x, i) => html`<option value=${i}>${x}</option>`)}</select>`}
        <div class="legend" style="margin-left:auto"><span>${pct(lo)}</span><i style="background:linear-gradient(90deg, ${T.grey}, ${T.red}); width:120px; margin:0"></i><span>${pct(hi)}</span></div>
      </div>
      ${!geo ? html`<div class="skeleton" style="height:420px"></div>` : geo.error ? html`<div class="foot">Map outline could not be loaded.</div>` : html`<svg viewBox="0 0 960 600" width="100%" style="display:block">
        <path d=${geo.nation} fill=${T.paper2} fill-opacity="0.55" stroke=${T.ink} stroke-width="0.6" /><path d=${geo.states} fill="none" stroke=${T.paper} stroke-width="1" />
        ${big.map(a => { const p = geo.proj([a.lon, a.lat]); if (!p) return null; const v = val(a); const r = 4 + Math.sqrt(a.dep / maxDep) * 22; return html`<g><circle cx=${p[0]} cy=${p[1]} r=${r} fill=${colorOf(v)} fill-opacity="0.92" stroke=${T.paper} stroke-width="1.2"><title>${a.code} · ${a.full}
Disrupted ${pct(a.dis)} · cancelled ${pct(a.can)}
Adverse-weather days (${MONTHS[month]}) ${pct(a.clim?.[month + 1]?.[0])} · winter fragility ${a.wf == null ? "–" : "+" + pct(a.wf)}
${fmt(a.dep)} departures · ${a.runways || "?"} runways · main carrier ${CARRIER[a.carrier] || a.carrier}</title></circle>${a.tier === "large" && r > 12 && html`<text class="num" x=${p[0]} y=${p[1] + 3.5} font-size="9" font-weight="500" text-anchor="middle" fill=${(v - lo) / (hi - lo || 1) > 0.55 ? T.paper : T.ink}>${a.code}</text>`}</g>`; })}
      </svg>`}
      <p class="foot">Winter fragility = extra disruption on snow/freezing days vs the airport's own clear days. Hover a dot for details.</p>
    </div>`;
}

// ------------------------------------------------------------------ app
function App() {
  const route = useRoute();
  const [airports, setAirports] = useState(null); const [summary, setSummary] = useState(null);
  useEffect(() => { getJSON("airports.json").then(setAirports); getJSON("summary.json").then(setSummary); }, []);
  const ready = airports && summary;
  return html`<${Nav} route=${route} /><main class="wrap">
    ${!ready ? html`<div class="skeleton"></div>` : route === "cost" ? html`<${Cost} summary=${summary} />` : route === "hubs" ? html`<${Hubs} airports=${airports} summary=${summary} />` : html`<${Check} airports=${airports} summary=${summary} />`}
    <div class="colophon"><div><div class="brand"><span class="logo">Questrom Chart Champ Datathon</span></div><div class="brand" style="margin-top:4px">Trip Risk Checker</div><p class="foot" style="margin-top:8px">Sources: BTS On-Time Performance (one full year, ten airlines), NOAA daily weather, OurAirports.</p></div>
    <p class="foot">Built for the Questrom Chart Champ Datathon, November 2026. Disrupted = 15+ min late, cancelled or diverted. Hour late = 60+ min late, cancelled or diverted; connection and cost figures count cancelled travelers at their rebooked arrival. Weekday and month adjustments use national patterns. Route cells with fewer than 15 flights are hidden; thin cells are shrunk toward the route mean.</p></div>
  </main>`;
}
render(html`<${App} />`, document.getElementById("app"));

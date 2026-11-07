import { render } from "preact";
import { useState, useEffect, useMemo } from "preact/hooks";
import { html } from "htm/preact";

const BASE = window.DATA_BASE;
const CARRIER = { AA: "American", AS: "Alaska", B6: "JetBlue", DL: "Delta", UA: "United", WN: "Southwest", OO: "SkyWest", YX: "Republic", OH: "PSA", MQ: "Envoy" };
const KIND = { OO: "regional", YX: "regional", OH: "regional · American", MQ: "regional · American" };
const BANDS = ["Early (5–6:59a)", "Morning (7–9:59a)", "Midday (10a–1:59p)", "Afternoon (2–5:59p)", "Evening (6–9:59p)", "Late night (10p–4:59a)"];
const BAND_KEYS = ["Early (5-6:59a)", "Morning (7-9:59a)", "Midday (10a-1:59p)", "Afternoon (2-5:59p)", "Evening (6-9:59p)", "Late night (10p-4:59a)"];
const SHORT = ["Early", "Morning", "Midday", "Afternoon", "Evening", "Late night"];
const SEASONS = ["Winter", "Spring", "Summer", "Fall"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const SEASON_OF = [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0];
const T = { teal: "#4A6B48", red: "#B1372B", amber: "#A9761D", blue: "#45413A", grey: "#CFC6B2", ink: "#17150F", muted: "#76715F", line: "#D8D2C4", paper: "#F5F2EC", paper2: "#E3DDD0" };
const pct = (v, d = 0) => (v == null || isNaN(v)) ? "–" : (v * 100).toFixed(d) + "%";
const fmt = (v, d = 0) => (v == null || isNaN(v)) ? "–" : Number(v).toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d });
const hrs = (m) => (Math.max(m, 0) / 60).toFixed(1) + " h";
const level = (p) => p < 0.07 ? ["low", "Low risk"] : p < 0.12 ? ["mid", "Moderate"] : ["high", "High risk"];
const cache = {};
async function getJSON(path) { if (!cache[path]) cache[path] = fetch(`${BASE}/${path}`).then(r => r.json()); return cache[path]; }
function useRoute() {
  const read = () => (location.hash.replace("#", "") || "check").split("?")[0];
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
  const tabs = [["check", "Check a trip"], ["simulate", "Policy simulator"], ["hubs", "Hubs & airports"]];
  return html`<div class="nav"><div class="nav-in">
    <a class="brand" href="#check"><span class="logo">No. 01</span>Trip Risk Checker</a>
    <nav class="tabs">${tabs.map(([k, l]) => html`<a class="tab ${route === k ? "active" : ""}" href="#${k}">${l}</a>`)}</nav>
    <div class="chips"><span class="chip">6.4M flights · BTS 2025</span><span class="chip">NOAA · 324 airports</span><span class="chip">3.4M connections</span></div>
  </div></div>`;
}
function Section({ title, hint }) { return html`<div class="section"><h2>${title}</h2>${hint && html`<span class="hint">${hint}</span>`}</div>`; }
function Kpi({ k, v, d, tone, small }) { return html`<div class="card kpi"><div class="k">${k}</div><div class="v">${v}${small && html` <small>${small}</small>`}</div>${d && html`<div class="d ${tone || ""}">${d}</div>`}</div>`; }

// ------------------------------------------------------------------ screen 1
function Check({ airports, summary }) {
  const byCode = useMemo(() => Object.fromEntries(airports.map(a => [a.code, a])), [airports]);
  const origins = useMemo(() => airports.map(a => a.code).sort(), [airports]);
  const [o, setO] = useState("BOS"); const [d, setD] = useState("ORD"); const [m, setM] = useState(5); const [b, setB] = useState(1);
  const [routes, setRoutes] = useState(null);
  useEffect(() => { setRoutes(null); getJSON(`routes/${o}.json`).then(setRoutes); }, [o]);
  const dests = useMemo(() => routes ? Object.keys(routes).sort() : [], [routes]);
  useEffect(() => { if (routes && !routes[d] && dests.length) setD(dests.includes("ORD") ? "ORD" : dests[0]); }, [routes]);
  const season = SEASON_OF[m];
  const rec = routes && routes[d];
  const cells = rec ? rec.c : [];
  let cellNow = cells.filter(c => c[1] === b && c[2] === season).map(c => ({ carrier: c[0], n: c[3], dis: c[4], sev: c[5], can: c[6], p95: c[7], sched: c[8] })).sort((x, y) => x.sev - y.sev);
  if (cellNow.some(c => c.n >= 20)) cellNow = cellNow.filter(c => c.n >= 20);
  const best = cellNow[0], worst = cellNow[cellNow.length - 1];
  const byBand = BANDS.map((lab, i) => { const cs = cells.filter(c => c[1] === i); const n = cs.reduce((s, c) => s + c[3], 0); return n ? { k: i, label: SHORT[i], v: cs.reduce((s, c) => s + c[5] * c[3], 0) / n, n } : null; }).filter(Boolean);
  const wo = byCode[o]?.clim?.[m + 1], wd = byCode[d]?.clim?.[m + 1];
  const be = rec?.be, bm = summary.be_median;
  const label = (c) => `${c} · ${byCode[c]?.name || c}`;
  return html`
    <div class="hero"><div><div class="eyebrow">Check a trip</div><h1 style="margin-top:10px">Which flight actually gets you <em>to the meeting?</em></h1><p>Risk by route, carrier, departure time and season, from every US domestic flight of ten carriers in 2025, with NOAA weather at both ends.</p></div></div>
    <div class="card pad"><div class="controls">
      <div class="field"><label>From</label><select class="select" value=${o} onChange=${e => setO(e.target.value)}>${origins.map(c => html`<option value=${c}>${label(c)}</option>`)}</select></div>
      <div class="field"><label>To</label><select class="select" value=${d} onChange=${e => setD(e.target.value)}>${dests.map(c => html`<option value=${c}>${label(c)}</option>`)}</select></div>
      <div class="field"><label>Month</label><select class="select" value=${m} onChange=${e => setM(+e.target.value)}>${MONTHS.map((x, i) => html`<option value=${i}>${x}</option>`)}</select></div>
      <div class="field"><label>Departure time</label><select class="select" value=${b} onChange=${e => setB(+e.target.value)}>${BANDS.map((x, i) => html`<option value=${i}>${x}</option>`)}</select></div>
    </div></div>
    <${Section} title=${`${o} → ${d} · ${MONTHS[m]} · ${SHORT[b].toLowerCase()} departure`} hint="chance of arriving an hour late, cancelled or diverted" />
    ${!routes ? html`<div class="skeleton"></div>` : !cellNow.length ? html`<div class="card empty">No nonstop flights in that slot in 2025. Try another departure time, or see the connection options below.</div>` : html`
      <div class="grid g${Math.min(cellNow.length, 4)}">${cellNow.slice(0, 4).map((c, i) => { const [cls, txt] = level(c.sev); return html`<div class="card rcard ${i === 0 ? "best" : ""}">
        <div class="tag">${i === 0 ? "Recommended" : "Alternative"} · ${KIND[c.carrier] || "mainline"}</div><div class="name">${CARRIER[c.carrier] || c.carrier}</div>
        <div class="big" style="color:${i === 0 ? T.ink : T.muted}">${pct(c.sev)}</div>
        <div class="meta"><span class="pill ${cls}">${txt}</span><span>${(c.sev - summary.base_sev >= 0 ? "+" : "") + pct(c.sev - summary.base_sev)} vs US avg</span></div>
        <div class="rows"><div class="row"><span>Disrupted (15+ min)</span><b>${pct(c.dis)}</b></div><div class="row"><span>Cancelled</span><b>${pct(c.can, 1)}</b></div><div class="row"><span>Land early to be 95% safe</span><b>${hrs(c.p95)}</b></div><div class="row"><span>Flights in 2025</span><b>${fmt(c.n)}</b></div></div>
      </div>`; })}</div>
      ${cellNow.length > 1 && html`<div class="banner"><span class="ico">✓</span><div><b>Book ${CARRIER[best.carrier]}.</b> ${pct(best.sev)} chance of being an hour late vs ${pct(worst.sev)} on ${CARRIER[worst.carrier]} (${((worst.sev - best.sev) * 100).toFixed(0)} points lower). Plan to land ${hrs(best.p95)} before the meeting to be 95% safe.</div></div>`}`}
    <div class="grid g2" style="margin-top:44px">
      <div class="card pad"><p class="chart-title">Same route by departure time</p><p class="chart-sub">All carriers and seasons · chance of arriving an hour late</p>${byBand.length > 1 ? html`<${Bars} data=${byBand} highlight=${b} />` : html`<div class="foot">Not enough departures to compare.</div>`}</div>
      <div class="card pad"><p class="chart-title">Weather exposure · ${MONTHS[m]}</p><p class="chart-sub">Share of days with adverse weather (NOAA, 2025)</p>
        ${wo && wd ? html`<div class="rows" style="margin-top:0"><div class="row"><span>Adverse-weather days at ${o}</span><b>${pct(wo[0])}</b></div><div class="row"><span>Adverse-weather days at ${d}</span><b>${pct(wd[0])}</b></div><div class="row"><span>Snow / freezing days</span><b>${pct(wo[1])} · ${pct(wd[1])}</b></div><div class="row"><span>Thunderstorm days</span><b>${pct(wo[2])} · ${pct(wd[2])}</b></div></div><p class="foot">Flights touching an airport with adverse weather were 1.8x as likely to be disrupted in 2025.</p>` : html`<div class="foot">No weather station matched.</div>`}
      </div>
    </div>
    <${Section} title="Nonstop or one-stop?" hint="one-stops are constructed from real flight pairs, not tickets sold" />
    <div class="grid g3">
      ${be ? html`<${Kpi} k="Nonstop · hour late" v=${pct(be.ns)} d="simulated, cancellations rebooked" tone="good" /><${Kpi} k="Best one-stop (90-min layover) · hour late" v=${pct(be.os)} d=${`+${((be.os - be.ns) * 100).toFixed(0)} pts · ${be.xh.toFixed(1)} extra hours per trip`} tone="bad" /><${Kpi} k="Fare saving needed to break even" v=${"$" + fmt(be.b100)} d=${`$${fmt(be.b50)} at $50/h · $${fmt(be.b150)} at $150/h · $${fmt(be.bm)} with a $500 meeting`} />`
         : html`<${Kpi} k=${`Across ${fmt(bm.n)} city pairs · one-stop vs nonstop`} v=${"+" + (bm.pts * 100).toFixed(0) + " pts"} d="median extra chance of being an hour late" tone="bad" /><${Kpi} k="Extra time per trip (90-min layover)" v=${bm.xh.toFixed(1) + " h"} d="median · schedule plus expected delay" /><${Kpi} k="Fare saving needed to break even" v=${"$" + fmt(bm.b100)} d="median one-way, at $100 per hour of traveler time" />`}
    </div>
    <p class="foot">Overall: nonstop ${pct(summary.nsos["Nonstop"])} vs one-stop ${pct(summary.nsos["One-stop, min layover 45 min"])} (45-min layover) / ${pct(summary.nsos["One-stop, min layover 90 min"])} (90-min) chance of arriving an hour late. Missed connections fall from ${pct(summary.layover[45].mis, 1)} to ${pct(summary.layover[90].mis, 1)} with a 90-minute minimum layover.</p>`;
}

// ------------------------------------------------------------------ screen 2
const RULES = [["A. Depart before 10 a.m.", "Depart before 10 a.m."], ["A'. Depart 7-9:59 a.m. (employee-friendly)", "Depart 07:00–09:59"], ["B. Preferred carrier on routes with a choice", "Preferred carrier (with a choice)"], ["A+B. Morning + preferred carrier", "Morning + preferred carrier"], ["D. Fly Tuesday or Wednesday", "Fly Tuesday or Wednesday"], ["   (for contrast) depart 5-9:59 p.m.", "(contrast) Evening departures"], ["   (for contrast) Sunday evening", "(contrast) Sunday evening"]];
function Simulate({ summary }) {
  const [rate, setRate] = useState(100), [meet, setMeet] = useState(500), [hotel, setHotel] = useState(300);
  const [on, setOn] = useState(new Set(RULES.slice(0, 5).map(r => r[0])));
  const pol = Object.fromEntries(summary.policies.map(p => [p.key, p]));
  const base = pol["Baseline (all trips as flown)"];
  const cost = (p) => (p.delay_h * rate + p.hour_late * meet + p.overnight * hotel) / 1000;
  const rows = [["Baseline (all trips as flown)", "Today (as flown)"], ...RULES.filter(r => on.has(r[0]))].map(([k, l]) => ({ ...pol[k], label: l, cost: cost(pol[k]) }));
  const baseRow = rows[0];
  const bestRule = rows.slice(1).sort((a, b) => a.hour_late - b.hour_late)[0];
  const toggle = (k) => setOn(s => { const n = new Set(s); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const buf = summary.buffer, maxB = Math.max(...Object.values(buf).flatMap(r => Object.values(r)));
  const heat = (v) => { const t = v / maxB; return `rgba(177,55,43,${(0.05 + t * 0.55).toFixed(2)})`; };
  return html`
    <div class="hero"><div><div class="eyebrow">Policy simulator</div><h1 style="margin-top:10px">What would each booking rule have done to <em>1,000 trips?</em></h1><p>Same routes and volumes as flown in 2025; within each route the flights meeting the rule stand in for the flights taken. Cancelled travelers are rebooked on the next flight of the same airline. Modeled, if fully adopted; excludes extra fares.</p></div></div>
    <div class="grid" style="grid-template-columns: 300px 1fr; gap: 48px">
      <div class="card pad">
        <p class="chart-title">Assumptions</p>
        <div class="rlabel"><span>Value of a traveler's hour</span><b>$${rate}</b></div><input class="range" type="range" min="25" max="200" step="25" value=${rate} onInput=${e => setRate(+e.target.value)} />
        <div class="rlabel"><span>Cost of arriving an hour+ late</span><b>$${fmt(meet)}</b></div><input class="range" type="range" min="0" max="2000" step="50" value=${meet} onInput=${e => setMeet(+e.target.value)} />
        <div class="rlabel"><span>Cost of an overnight stranding</span><b>$${fmt(hotel)}</b></div><input class="range" type="range" min="0" max="1000" step="50" value=${hotel} onInput=${e => setHotel(+e.target.value)} />
        <p class="chart-title" style="margin-top:18px">Rules</p>
        ${RULES.map(([k, l]) => html`<label class="check"><input type="checkbox" checked=${on.has(k)} onChange=${() => toggle(k)} />${l}</label>`)}
      </div>
      <div>
        ${bestRule && html`<div class="grid g3" style="margin-bottom:32px">
          <${Kpi} k=${`Hour late or stranded · ${bestRule.label}`} v=${fmt(bestRule.hour_late)} small="/ 1,000 trips" d=${`today ${fmt(base.hour_late)} · ${((bestRule.hour_late / base.hour_late - 1) * 100).toFixed(0)}%`} tone="good" />
          <${Kpi} k="Delay hours per 1,000 trips" v=${fmt(bestRule.delay_h)} d=${`today ${fmt(base.delay_h)}`} tone="good" />
          <${Kpi} k="Modeled saving per 1,000 trips" v=${"$" + fmt(baseRow.cost - bestRule.cost) + "k"} d="if fully adopted · excludes extra fares" />
        </div>`}
        <div class="card pad"><p class="chart-title">Trips per 1,000 arriving an hour late or stranded</p><p class="chart-sub">Cancelled travelers rebooked on the next flight</p>
          <${HBars} data=${rows.map(r => ({ label: r.label, v: r.hour_late }))} maxV=${Math.max(...rows.map(r => r.hour_late)) * 1.15} color=${(d, i) => i === 0 ? T.grey : (d.label.startsWith("(contrast)") ? T.red : T.ink)} rowH=${36} labelW=${230} /></div>
      </div>
    </div>
    <div class="card" style="margin-top:32px; overflow:auto"><table class="table"><thead><tr><th>Rule</th><th class="num">Hour+ late or stranded</th><th class="num">Delay hours</th><th class="num">Stranded overnight</th><th class="num">Late-night arrivals</th><th class="num">Pre-6am departures</th><th class="num">Cost ($k)</th><th class="num">Saving vs today ($k)</th><th class="num">Trips covered</th></tr></thead>
      <tbody>${rows.map((r, i) => html`<tr class=${i === 0 ? "base" : ""}><td>${r.label}</td><td class="num">${fmt(r.hour_late)}</td><td class="num">${fmt(r.delay_h)}</td><td class="num">${fmt(r.overnight, 1)}</td><td class="num">${fmt(r.late_night)}</td><td class="num">${fmt(r.early)}</td><td class="num">${fmt(r.cost)}</td><td class="num">${i === 0 ? "–" : fmt(baseRow.cost - r.cost)}</td><td class="num">${r.cover == null ? "100%" : pct(r.cover)}</td></tr>`)}</tbody></table></div>
    <p class="foot">Per 1,000 trips. "Trips covered" is the share of 2025 trips on routes where the rule can apply (e.g. routes with two or more airlines for the preferred-carrier rule).</p>
    <${Section} title="Buffer rule · hours to land before a must-attend meeting" hint="95th percentile of trip delay incl. rebooking, nonstop trips, 2025" />
    <div class="card pad"><div class="heat"><div class="h" style="padding-left:0">Departure</div>${SEASONS.map(s => html`<div class="h" style="text-align:center">${s}</div>`)}
      ${BAND_KEYS.map((k, i) => html`<div class="l">${BANDS[i]}</div>${SEASONS.map(s => html`<div class="c" style="background:${heat(buf[k][s])}; color:${buf[k][s] / maxB > 0.6 ? "#fff" : T.ink}">${buf[k][s].toFixed(1)} h</div>`)}`)}</div>
      <p class="foot">Example: a summer evening flight needs about ${buf["Evening (6-9:59p)"]["Summer"].toFixed(1)} h of buffer; a morning flight ${buf["Morning (7-9:59a)"]["Summer"].toFixed(1)} h.</p></div>`;
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
    <div class="hero"><div><div class="eyebrow">Hubs & airports</div><h1 style="margin-top:10px">Connecting hubs, ranked by what happens to <em>one-stop trips</em></h1><p>3.4 million itineraries constructed from real flight pairs with a 60-minute minimum layover; a traveler who misses a connection is rebooked on the next flight of the same airline. Simulated, not observed tickets.</p></div></div>
    <div class="grid g2">
      <div class="card pad"><p class="chart-title">Share of one-stop trips arriving an hour late</p><p class="chart-sub">60-minute minimum layover · 2025</p>
        <${HBars} data=${hubs.map(h => ({ label: `${h.hub} · ${h.name.replace(" International Airport", "").replace(" Airport", "").slice(0, 26)}`, v: h.sev }))} maxV=${0.26} color=${(d) => d.v < 0.12 ? T.teal : d.v > 0.165 ? T.red : T.grey} rowH=${28} labelW=${215} valueFmt=${(v) => pct(v)} /></div>
      <div>
        <div class="card rcard best"><div class="tag">Best connecting hub</div><div class="name">${top.hub} · ${top.name}</div><div class="big" style="color:${T.ink}">${pct(top.sev)}</div><div class="meta">hour late · missed connection ${pct(top.mis)} · stranded overnight ${pct(top.ov, 1)}</div></div>
        <div class="card rcard" style="margin-top:32px"><div class="tag" style="color:${T.red}">Riskiest connecting hub</div><div class="name">${bot.hub} · ${bot.name}</div><div class="big" style="color:${T.red}">${pct(bot.sev)}</div><div class="meta">hour late · missed connection ${pct(bot.mis)} · stranded overnight ${pct(bot.ov, 1)}</div>
          <div class="rows"><div class="row"><span>Minimum layover 45 → 90 min</span><b>missed connections ${pct(summary.layover[45].mis, 1)} → ${pct(summary.layover[90].mis, 1)}</b></div><div class="row"><span>Winter-fragile hubs (Dec–Feb)</span><b>IAH · DFW · ATL · DCA</b></div><div class="row"><span>Nonstop, same city pairs</span><b>${pct(summary.nsos["Nonstop"])} hour late</b></div></div></div>
      </div>
    </div>
    <div class="card" style="margin-top:32px; overflow:auto"><table class="table"><thead><tr><th>Hub</th><th>Airport</th><th class="num">City pairs</th><th class="num">Missed connection</th><th class="num">Hour late</th><th class="num">Stranded overnight</th><th class="num">Expected delay</th><th class="num">Winter fragility</th><th>Main carrier</th></tr></thead>
      <tbody>${hubs.map(h => html`<tr><td><b>${h.hub}</b></td><td>${h.name}</td><td class="num">${fmt(h.markets)}</td><td class="num">${pct(h.mis, 1)}</td><td class="num">${pct(h.sev, 1)}</td><td class="num">${pct(h.ov, 1)}</td><td class="num">${fmt(h.delay)} min</td><td class="num">${h.wf == null ? "–" : "+" + pct(h.wf)}</td><td>${CARRIER[h.carrier] || h.carrier} (${pct(h.share)})</td></tr>`)}</tbody></table></div>
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
Disrupted ${pct(a.dis, 1)} · cancelled ${pct(a.can, 2)}
Adverse-weather days (${MONTHS[month]}) ${pct(a.clim?.[month + 1]?.[0])} · winter fragility ${a.wf == null ? "–" : "+" + pct(a.wf)}
${fmt(a.dep)} departures · ${a.runways || "?"} runways · main carrier ${CARRIER[a.carrier] || a.carrier}</title></circle>${a.tier === "large" && r > 12 && html`<text class="num" x=${p[0]} y=${p[1] + 3.5} font-size="9" font-weight="500" text-anchor="middle" fill=${(v - lo) / (hi - lo || 1) > 0.55 ? T.paper : T.ink}>${a.code}</text>`}</g>`; })}
      </svg>`}
      <p class="foot">Winter fragility = extra disruption on snow/freezing days vs the airport's own clear days (NOAA GHCN-Daily, 2025). Hover a dot for details. Sources: BTS, NOAA, OurAirports.</p>
    </div>`;
}

// ------------------------------------------------------------------ app
function App() {
  const route = useRoute();
  const [airports, setAirports] = useState(null); const [summary, setSummary] = useState(null);
  useEffect(() => { getJSON("airports.json").then(setAirports); getJSON("summary.json").then(setSummary); }, []);
  const ready = airports && summary;
  return html`<${Nav} route=${route} /><main class="wrap">
    ${!ready ? html`<div class="skeleton"></div>` : route === "simulate" ? html`<${Simulate} summary=${summary} />` : route === "hubs" ? html`<${Hubs} airports=${airports} summary=${summary} />` : html`<${Check} airports=${airports} summary=${summary} />`}
    <div class="colophon"><div><div class="brand"><span class="logo">Questrom Chart Champ Datathon</span></div><div class="brand" style="margin-top:4px">Trip Risk Checker</div><p class="foot" style="margin-top:8px">Sources: BTS On-Time Performance 2025, NOAA GHCN-Daily, OurAirports.</p></div>
    <p class="foot">Built for the Questrom Chart Champ Datathon, November 2026. Disrupted = 15+ min late, cancelled or diverted. Hour late = 60+ min late, cancelled or diverted; policy and connection figures count cancelled travelers at their rebooked arrival. Route cells with fewer than 15 flights are hidden; thin cells are shrunk toward the route mean.</p></div>
  </main>`;
}
render(html`<${App} />`, document.getElementById("app"));

// Builds deck/Arrive_On_Time_Arrive_Ready.pptx from the analysis outputs.
//   NODE_PATH="$PWD/deck/build/node_modules" node deck/build/build_deck.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const SKILL = "C:/Users/anair/AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/local-agent-mode-sessions/skills-plugin/5f747424-bd78-4f57-bf8b-35b9c207c779/eda4a44d-ca96-4cbf-a650-5f57f41d4346/skills/pptx";
const { applyTheme } = require(SKILL + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..", "..");
const FIG = (n) => path.join(ROOT, "outputs", "figures", n);
const OUT = path.join(ROOT, "deck", "Arrive_On_Time_Arrive_Ready.pptx");

const THEME = {
  name: "Arrive Ready",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2A44", lt1: "FFFFFF", dk2: "5B6477", lt2: "EEF1F6",
    accent1: "2A9D8F", accent2: "D1495B", accent3: "3A6EA5", accent4: "E9A23B", accent5: "B8BEC9", accent6: "0F1A33",
    hlink: "3A6EA5", folHlink: "5B6477",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Arrive on time, arrive ready";
pres.author = "Questrom MSBA team";
const C = pres.SchemeColor;
const W = 13.33, H = 7.5, M = 0.5;

// ------------------------------------------------------------------ layouts
const footer = (dark) => ({
  text: {
    text: "Questrom Chart Champ Datathon · November 2026 · BTS On-Time Performance 2025 (6.4M flights) + NOAA GHCN-Daily",
    options: { x: M, y: H - 0.45, w: 9, h: 0.3, fontSize: 9, color: dark ? C.accent5 : C.text2, margin: 0 },
  },
});
const titlePh = (color) => ({ placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: W - 2 * M, h: 0.9, fontSize: 26, bold: true, color, margin: 0, valign: "top", align: "left" }, text: "" } });
pres.defineSlideMaster({ title: "CONTENT", background: { color: HEX.lt1 }, objects: [titlePh(C.text1), footer(false)],
  slideNumber: { x: W - 1.0, y: H - 0.45, w: 0.5, h: 0.3, fontSize: 9, color: C.text2, align: "right" } });
pres.defineSlideMaster({ title: "DARK", background: { color: HEX.accent6 }, objects: [titlePh(C.background1), footer(true)],
  slideNumber: { x: W - 1.0, y: H - 0.45, w: 0.5, h: 0.3, fontSize: 9, color: C.accent5, align: "right" } });
pres.defineSlideMaster({ title: "COVER", background: { color: HEX.accent6 }, objects: [footer(true)] });

// ------------------------------------------------------------------ helpers
function img(slide, file, x, y, w, h, name) {
  slide.addImage({ path: FIG(file), x, y, w, h, sizing: { type: "contain", w, h }, objectName: name || file });
}
function stat(slide, value, label, x, y, w, color, valueSize) {
  const vs = valueSize || 40, vh = vs >= 34 ? 0.9 : vs >= 28 ? 0.65 : 0.5;
  slide.addText(value, { x, y, w, h: vh, fontSize: vs, bold: true, color: color || C.accent1, margin: 0, isTextBox: true, valign: "top", objectName: "stat " + label, fontFace: THEME.headFontFace });
  slide.addText(label, { x, y: y + vh, w, h: 0.8, fontSize: 12.5, color: C.text2, margin: 0, isTextBox: true, valign: "top", objectName: "label " + label });
}
function bullets(slide, items, x, y, w, h, size, color) {
  const runs = items.map((t, i) => (typeof t === "string"
    ? { text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1, paraSpaceAfter: 10 } }
    : { text: t.text, options: Object.assign({ bullet: { indent: 14 }, breakLine: i < items.length - 1, paraSpaceAfter: 10 }, t.options || {}) }));
  slide.addText(runs, { x, y, w, h, fontSize: size || 14, color: color || C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "bullets" });
}
function side(slide, items, x, size) {
  // right-hand commentary column with a small heading rule-free design (no panel)
  slide.addText("What it means", { x: x || 9.5, y: 1.5, w: 3.35, h: 0.4, fontSize: 12, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "side head", charSpacing: 1 });
  bullets(slide, items, x || 9.5, 1.95, 3.35, 4.6, size || 13.5);
}
function panel(slide, x, y, w, h, fillScheme) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fillScheme || C.background2 }, line: { color: fillScheme || C.background2 }, rectRadius: 0.08, objectName: "panel" });
}
function numberCircle(slide, n, x, y, color) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: 0.42, h: 0.42, fill: { color: color || C.accent1 }, line: { color: color || C.accent1 }, objectName: "circle " + n });
  slide.addText(String(n), { x, y, w: 0.42, h: 0.42, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "num " + n });
}
function rows(slide, items, x, y, w, color, gap) {
  items.forEach((it, i) => {
    const yy = y + i * (gap || 1.0);
    numberCircle(slide, i + 1, x, yy + 0.05, color);
    slide.addText([{ text: it.head, options: { bold: true, breakLine: true } }, { text: it.body, options: { color: C.text2, fontSize: 12.5 } }],
      { x: x + 0.6, y: yy, w: w - 0.6, h: (gap || 1.0) - 0.05, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "row " + (i + 1) });
  });
}
function tag(slide, text, x, y, w) {
  slide.addText(text, { x, y, w, h: 0.3, fontSize: 10, italic: true, color: C.text2, margin: 0, isTextBox: true, objectName: "tag" });
}
function notes(slide, t) { slide.addNotes(t); }
function content(title, section) { const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section }); s.addText(title, { placeholder: "title" }); return s; }
const hdr = (t, size) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text1 }, fontSize: size || 12 } });
const cell = (t, o) => ({ text: t, options: Object.assign({ fontSize: 11.5, color: C.text1, valign: "top" }, o || {}) });

// ================================================================== OPENING
pres.addSection({ title: "Opening" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "Opening" });
  s.addText("Arrive on time,\narrive ready", { x: M, y: 1.6, w: 8.5, h: 2.4, fontSize: 54, bold: true, color: C.background1, margin: 0, isTextBox: true, fontFace: THEME.headFontFace, objectName: "cover title" });
  s.addText("A data-driven travel policy for a company that flies", { x: M, y: 4.1, w: 9, h: 0.6, fontSize: 22, color: C.accent5, margin: 0, isTextBox: true, objectName: "cover sub" });
  s.addText("6.4 million US domestic flights in 2025 · NOAA daily weather at 324 airports · 3.4 million constructed one-stop trips · four recommendations and a pilot",
    { x: M, y: 4.8, w: 9.5, h: 0.8, fontSize: 14, color: C.accent5, margin: 0, isTextBox: true, objectName: "cover facts" });
  s.addText("Prepared by [TEAM NAME — replace] · Questrom MSBA · Chart Champ Datathon, 7 November 2026", { x: M, y: 6.1, w: 9.5, h: 0.4, fontSize: 12, color: C.accent1, margin: 0, isTextBox: true, objectName: "cover team" });
  [[10.3, "accent1"], [11.1, "accent2"], [11.9, "accent4"]].forEach(([x, c], i) => s.addShape(pres.ShapeType.ellipse, { x, y: 2.2, w: 0.6, h: 0.6, fill: { color: C[c] }, line: { color: C[c] }, objectName: "dot " + i }));
  notes(s, "One sentence on who we are and the ask: cut disruption for a company whose people fly constantly, without blowing up cost or convenience. We looked at every US domestic flight of the ten reporting carriers in 2025 — 6.4 million flights — plus NOAA weather.");
}
{
  const s = content("Nearly 1 in 4 flights in the data is disrupted; 1 in 10 is an hour late, cancelled or diverted", "Opening");
  stat(s, "23.5%", "disrupted: arrived 15+ min late, cancelled or diverted (full 2025 file)", M, 1.6, 2.8, C.accent2);
  stat(s, "9.7%", "severely disrupted: 60+ min late, cancelled or diverted", 3.5, 1.6, 2.8, C.accent2);
  stat(s, "1.5%", "cancelled (95,166 flights) and 0.3% diverted (18,015)", M, 3.7, 2.8, C.accent4);
  stat(s, "460 h", "of delay per 1,000 trips once cancelled travelers are rebooked (simulation)", 3.5, 3.7, 2.8, C.accent4);
  img(s, "01_delay_distribution.png", 6.7, 1.4, 6.2, 4.3);
  s.addText("Most flights land early. The cost sits in the long tail — and the tail is what costs you a meeting.", { x: M, y: 5.9, w: 12.3, h: 0.5, fontSize: 15, italic: true, color: C.text2, margin: 0, isTextBox: true, objectName: "takeaway" });
  tag(s, "The data has no passenger purpose; 'trips' means flights in the dataset. Cost figures later use stated assumptions.", M, 6.5, 12.3);
  notes(s, "Most flights land early; the median flight is 6 minutes early. The problem is the tail. Per 1,000 trips that is roughly 460 lost hours and 14 overnight strandings once cancelled travelers are rebooked. At $100 an hour of traveler time and $500 per missed meeting that is about $98k per 1,000 trips — assumptions we vary on the impact slide.");
}
{
  const s = content("How we measured it: the traveler's outcome, on every flight, compared like with like", "Opening");
  rows(s, [
    { head: "All 6.4M domestic flights of 10 carriers in 2025 (BTS)", body: "329 airports. The 200k sample every team received reproduces it: every carrier's rate falls inside the sample's 95% confidence interval." },
    { head: "Outcome = what the traveler feels", body: "Arrival 15+ / 60+ minutes late, cancelled or diverted. In the policy simulation, cancelled travelers are rebooked on the next flight of the same airline and the realised delay is counted." },
    { head: "Enriched with public data", body: "NOAA daily weather at 324 airports (snow, ice, storms, wind, fog); OurAirports runway and location data; FAA / Port Authority construction notices." },
    { head: "One-stop trips constructed from real flight pairs", body: "3.4 million itineraries through the 20 busiest hubs, a 30-minute connection rule, rebooking when a connection breaks. Simulated, not observed tickets." },
    { head: "Validation built in", body: "Same route / month / time-of-day comparisons; cross-validation grouped by date; confidence intervals; results re-checked without the 15 worst days." },
  ], M, 1.45, 8.2, C.accent3);
  stat(s, "6.4M", "flights · 329 airports · 10 carriers", 9.5, 1.6, 3.3, C.text1, 34);
  stat(s, "324", "airports matched to a NOAA station (98.9% of flights)", 9.5, 3.2, 3.3, C.text1, 34);
  stat(s, "3.4M", "constructed one-stop itineraries (simulated)", 9.5, 4.8, 3.3, C.text1, 34);
  notes(s, "Forty-five seconds. Two points matter: we treated cancellations honestly by rebooking them rather than dropping them, and we compared like with like before saying any carrier, hub or hour is better. Everything labelled 'simulated' is constructed from real flights, not observed tickets.");
}

// ================================================================== FINDINGS
pres.addSection({ title: "Findings" });
{
  const s = content("Finding 1 — Time of day is the biggest lever: 7 p.m. departures are 3.2x as likely to be disrupted as 6 a.m.", "Findings");
  img(s, "02_disruption_by_hour.png", M, 1.4, 8.7, 5.3);
  side(s, [
    "Severe disruption: 5.4% for 05:00-09:59 departures vs 14.5% for 17:00-21:59 (full file).",
    "Late inbound aircraft are 39% of delay minutes — delays cascade through the day.",
    "Not a route-mix artefact: same carrier, same route, evening is worse on 98% of 3,198 pairs; adjusted odds x3.1 vs 8 a.m.; holds without the 15 worst days.",
  ]);
  notes(s, "Why does it happen? Delays snowball: each departure wave inherits the lateness of the aircraft arriving before it. Morning is lower in every month. This is the most reliable pattern in the data and the cheapest to act on. (Route-carrier pairs: 3,198 with 100+ flights in both windows; with a stricter route threshold the share is ~97% of ~2,000 routes — same conclusion.)");
}
{
  const s = content("Finding 2 — Carrier choice is worth 5-10 points, but only when compared on the same route", "Findings");
  img(s, "14_carrier_route_adjusted.png", M, 1.4, 8.7, 5.3);
  side(s, [
    "Like-for-like (same route, month, time of day): United 5 pts safer than rivals, Republic and Envoy 4; PSA 7 and Alaska 6 worse.",
    "Raw rankings mislead — Alaska flies in the calm West; Delta's raw lead shrinks on shared routes.",
    "On the 43% of trips with 2+ airlines on the route the median best-vs-worst gap is 6.8 pts (ORD-BOS: 22). Hence a route-level list, not a blanket airline pick.",
  ]);
  notes(s, "Rigor slide: each carrier is compared only with the other carriers flying the same route in the same month and time of day, weighted over 2.5 million flights in 37 thousand cells. Regional airlines are shown as operated; the brand they fly for is not in the data.");
}
{
  const s = content("Finding 3 — Weather matters more than the airlines' weather code shows", "Findings");
  img(s, "10_weather_conditions.png", M, 1.4, 8.7, 5.3);
  side(s, [
    "Flights touching an airport with adverse weather: 33% disrupted vs 18% on clear days (1.8x). Snow or freezing rain roughly doubles it.",
    "BTS's 'weather' code covers extreme weather only (≈6-7% of delay minutes); ordinary bad weather sits under air-traffic and late-aircraft codes.",
    "It is foreseeable: June-July and December are the risky months; exposure by airport and month is in the appendix.",
  ]);
  notes(s, "Method: every flight joined to NOAA's daily record at both ends. Flights on adverse-weather days carry about 23% more disruptions than clear-day rates imply — an unadjusted figure, because bad-weather flights cluster in winter and at certain hubs, so treat it as an upper bound. The point is not that the airlines are wrong; their code is defined narrowly. The point is that weather risk is foreseeable in two ways: by season and airport when booking, and 1-3 days out from a forecast.");
}
{
  const s = content("Finding 4 — A stop is a gamble: one-stop trips are 1.7x as likely to make you an hour late", "Findings");
  img(s, "17_nonstop_vs_onestop.png", M, 1.3, 12.3, 4.1);
  stat(s, "9% → 16%", "chance of arriving an hour late, nonstop vs one-stop with a 45-min layover, same city pairs (simulated)", M, 5.5, 4.0, C.accent2, 30);
  stat(s, "51 → 23", "missed connections per 1,000 connecting trips when the minimum layover rises from 45 to 90 minutes", 4.7, 5.5, 4.0, C.accent1, 30);
  stat(s, "~$400", "one-way fare saving a one-stop needs on the biggest markets to pay for ~4 extra hours (at $100/h; $200 at $50/h)", 8.9, 5.5, 4.0, C.accent4, 30);
  notes(s, "Built from real flight pairs on 1,730 city pairs between the 60 busiest airports. Nonstop 9% an hour late; one-stop 16% with a 45-minute layover, 14% with 90. Overnight strandings triple. Break-even: a one-stop needs to be about $400 cheaper one-way on the biggest markets to pay for the traveler's extra time — before counting a missed meeting. These are constructed itineraries, not tickets sold.");
}
{
  const s = content("Finding 4, continued — The hub decides the odds: SLC, LAX and SEA are half as risky as DCA or DFW", "Findings");
  img(s, "19_hub_ranking.png", M, 1.4, 8.7, 5.3);
  side(s, [
    "One-stops through SLC / LAX / SEA: 9-10% an hour late. Through DCA / DFW / LGA: 20-21% (60-minute layover, simulated).",
    "Winter changes the ranking: IAH, DFW, ATL and DCA add 30-40 pts of disruption on snow or ice days.",
    "Construction matters too: during Newark's spring 2025 runway closure EWR went from 21% to 35% disrupted while JFK and LGA were flat (appendix).",
  ]);
  notes(s, "Hub ranking with a 60-minute minimum layover. Winter fragility and the Newark event study are in the appendix. Newark overlapped with air-traffic-control staffing problems, so construction is a watch-list rule, not a ranking of airports by condition.");
}
{
  const s = content("The employee's side — the safest flight is not the kindest one, but 07:00-09:59 is close", "Findings");
  img(s, "24_reliability_vs_sleep.png", M, 1.4, 8.7, 5.3);
  side(s, [
    "05:00-06:59 departures: 4.9% an hour late — and a 4 a.m. alarm.",
    "07:00-09:59: 5.6% — nearly all the reliability, no dawn start, zero late-night arrivals.",
    "17:00-21:59: 14-15% an hour late and most of the 11 p.m.-4 a.m. landings. The last flight of the day is 3.9x as likely to strand a traveler overnight (2.8% vs 0.7%).",
  ]);
  notes(s, "We are not asking people to fly at dawn. The 7-to-10 window keeps about 95% of the reliability gain. Burden metrics — early departures, late-night arrivals, 2h+ gate waits, overnight strandings — ride alongside reliability in every policy test.");
}

// ================================================================== RECOMMENDATIONS
pres.addSection({ title: "Recommendations" });
{
  const s = content("Four recommendations — each conditional, with an owner, an exception rule and a measurable outcome", "Recommendations");
  const num = (n) => cell(n, { bold: true, color: C.accent1, fontSize: 18, align: "center" });
  const rowsT = [
    [hdr("#"), hdr("Recommendation"), hdr("Evidence (simulated on the same routes and volumes, per 1,000 trips)"), hdr("Owner · exception"), hdr("Measure of success")],
    [num("1"), cell("Pilot a morning preference (07:00-09:59) for time-critical trips, subject to fare and availability", { bold: true }),
      cell("Hour-late or stranded 96 → 52-55 if fully adopted (−43 to −46%); delay hours 460 → 270; overnight strandings 14 → 3"), cell("Travel manager · override with a reason code; no rule for flexible trips"), cell("Share of time-critical bookings before 10 a.m.; severe-disruption rate; traveler feedback")],
    [num("2"), cell("Compare nonstop vs connection on total trip cost; when connecting, 90+ min layover via approved hubs", { bold: true }),
      cell("Hour late 9% nonstop vs 16% / 14% one-stop (45 / 90 min); missed connections 51 → 23 per 1,000; best hubs half the risk of the worst"), cell("Travel manager · one-stop allowed when it saves more than the break-even (~$400 on big markets at $100/h)"), cell("Share of trips nonstop; missed-connection rate; overnight strandings")],
    [num("3"), cell("Route-specific carrier preferences, after checking contracts and loyalty terms", { bold: true }),
      cell("On the 43% of trips with a real choice: 98 → 84 (−15%); with rule 1: 96 → 43"), cell("Procurement · negotiated fares win where the gap is under 5 pts; refresh quarterly"), cell("Compliance with the list; severe rate on covered routes; fare delta")],
    [num("4"), cell("Arrival buffers and day-before travel for high-impact meetings in Jun-Jul and Dec-Feb; forecast-triggered rebooking", { bold: true }),
      cell("Summer/winter afternoon-evening trips: 16% hour-late → 7% if moved to the morning; day-before travel cuts it to ~3.5% and pays when the meeting is worth > ~$1,600 (hotel $200). On forecast-adverse days: 23% → 9%"), cell("Travel desk · applies only to meetings the traveler flags as must-attend"), cell("Meetings missed; rebookings triggered; hotel spend vs disruption avoided")],
  ];
  s.addTable(rowsT, { x: M, y: 1.4, w: 12.33, colW: [0.45, 3.15, 4.2, 2.45, 2.08], border: { type: "solid", pt: 0.75, color: HEX.lt2 }, fill: { color: HEX.lt1 }, margin: 0.08, autoPage: false, objectName: "recommendations table", rowH: [0.45, 1.05, 1.05, 0.95, 1.3] });
  s.addText("Supporting measures: fly Tuesday or Wednesday where flexible (80 vs 96 per 1,000) · never the last flight of the day for must-attend trips · trigger-based traveler care.",
    { x: M, y: 6.4, w: 12.3, h: 0.45, fontSize: 12, italic: true, color: C.text2, margin: 0, isTextBox: true, objectName: "supporting" });
  notes(s, "Everything is a default or a soft warning in the booking tool, not a ban. Rule 1 alone is worth about $44k per 1,000 trips at our mid assumptions if fully adopted; the pilot target is a 96-to-55 reduction, not 52, because some trips cannot move. Rule 4 is the lowest-confidence rule: actual weather stands in for a forecast, so we present it as a watch rule with the economics shown.");
}
{
  const s = content("Impact — a morning preference halves the chance of being an hour late; modeled saving $13k-$76k per 1,000 trips", "Recommendations");
  img(s, "23_policy_impact.png", M, 1.3, 12.3, 3.5);
  tag(s, "Simulated on 2025 routes and volumes, if fully adopted; cancelled travelers rebooked. Excludes extra fares, hotels and policy costs.", M, 4.8, 12.3);
  const h = (t) => hdr(t, 11); const c = (t, o) => cell(t, Object.assign({ fontSize: 11.5, align: "center" }, o || {}));
  s.addTable([
    [h("Saving per 1,000 trips ($k), rule 1"), h("Missed meeting $0"), h("$500"), h("$1,000")],
    [c("Traveler time $50 / h", { align: "left" }), c("13"), c("35"), c("57")],
    [c("Traveler time $100 / h", { align: "left", bold: true }), c("23"), c("44", { bold: true }), c("66")],
    [c("Traveler time $150 / h", { align: "left" }), c("32"), c("54"), c("76")],
  ], { x: M, y: 5.2, w: 6.6, colW: [2.7, 1.3, 1.3, 1.3], border: { type: "solid", pt: 0.75, color: HEX.lt2 }, margin: 0.05, autoPage: false, objectName: "sensitivity" });
  bullets(s, [
    "Components at the mid case: $19k of traveler time (190 fewer delay hours), $22k of missed meetings (44 fewer), $3k of strandings — counted once each, no overlap.",
    "Paying more for reliability is worth it when the fare premium is below the saving per trip: ~$44 per trip at the mid case, ~$13 at the low case.",
    "Rules 1+3 together: 96 → 43 per 1,000, ~$54k at the mid case.",
  ], 7.4, 5.2, 5.4, 1.7, 11.5);
  notes(s, "Everything here is a modeled benefit under stated assumptions, not confirmed net savings. The sensitivity table varies the value of an hour and the cost of a missed meeting; strandings are a fixed $300. Extra fares for morning nonstops are the main cost we cannot see in the data — the break-even per trip tells you how much premium is acceptable.");
}
{
  const s = content("Traveler care, sized from the data — prevention first, then support that fires on measured events", "Recommendations");
  stat(s, "48 → 29", "2h+ delays per 1,000 trips (today → with the morning preference): meal credit, healthier options where the airport has them; $1.2k-2.9k per 1,000 trips today", M, 1.7, 4.0, C.accent3, 34);
  stat(s, "14 → 3", "overnight strandings per 1,000 trips: hotel plus a late start the next morning; $2.8k-6.4k per 1,000 trips today", 4.7, 1.7, 4.0, C.accent3, 34);
  stat(s, "23 → 16", "missed connections per 1,000 connecting trips under the 90-minute rule (all day → departing before 10 a.m.): meal plus rebooking help", 8.9, 1.7, 4.0, C.accent3, 34);
  rows(s, [
    { head: "Triggers, not blanket perks", body: "Support is attached to events the data counts: a 2h+ delay, an overnight stranding, a missed connection, an approved long layover (lounge pass)." },
    { head: "The budget is small next to the problem", body: "At mid assumptions the care budget is roughly $6k per 1,000 trips against ~$98k of disruption cost — and the booking rules cut the triggers by 40-80%." },
    { head: "Measured by satisfaction, not health claims", body: "Dollar amounts are assumptions; frequencies are measured. Track traveler satisfaction and uptake in the pilot." },
  ], M, 3.7, 12.3, C.accent3, 1.0);
  notes(s, "Care is the employee-facing half of the policy. It is deliberately cheap and conditional: the rules prevent most of the events, and support covers the rest. We make no claims about health outcomes — that is not in the data.");
}
{
  const s = content("Implementation — defaults and soft warnings in the booking tool, a weather watch at the travel desk, a one-quarter pilot", "Recommendations");
  rows(s, [
    { head: "Booking tool (owner: travel manager)", body: "Default sort: 07:00-09:59 nonstops on preferred carriers. Soft warnings on evening departures, last flight of the day, connections under 90 minutes, non-approved hubs. Override with a reason code." },
    { head: "Travel desk (owner: travel desk lead)", body: "Weather watch 72 hours out for trips through fragile hubs; proactive rebooking to earlier flights. Check FAA construction notices before tight connections. Care triggers fire automatically." },
    { head: "Pilot (owner: analytics)", body: "Two business units for one quarter vs a control group. Track severe-disruption rate, delay hours per 100 trips, strandings, missed connections, compliance, fare delta, traveler satisfaction. Target: 96 → ~55 per 1,000." },
    { head: "Keep it current", body: "Preferred-carrier and approved-hub lists refreshed quarterly from BTS data — the pipeline is built." },
  ], M, 1.45, 7.6, C.accent3, 1.2);
  img(s, "app_screenshot.jpg", 8.4, 1.45, 4.45, 3.4, "app screenshot");
  s.addText("Trip Risk Checker (Streamlit): route, month and departure-time risk per carrier, nonstop vs one-stop break-even, policy simulator with adjustable cost assumptions, hub and weather explorer.",
    { x: 8.4, y: 4.95, w: 4.45, h: 1.3, fontSize: 11.5, color: C.text2, margin: 0, isTextBox: true, objectName: "app caption" });
  notes(s, "Implementation is deliberately light: defaults and warnings in the tool the company already uses, and a travel-desk process. The app is how the travel desk and travelers would use the analysis; it is also our Q&A tool for any constraint the judges raise.");
}
{
  const s = content("Limitations we would state to the client — and what we would do next", "Recommendations");
  s.addText("Limitations", { x: M, y: 1.5, w: 5.8, h: 0.45, fontSize: 16, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "lim head" });
  bullets(s, [
    "One year of data (2025); associations, not proven causes — hence like-for-like comparisons and the cascade mechanism.",
    "Operating carrier only: regional airlines fly for several brands; SkyWest / Republic assigned by a documented heuristic.",
    "No fares, tickets or passenger counts: one-stops and rebooking are simulated; rebooking assumes a seat on the next flight.",
    "Daily weather at one station per airport; actual weather stands in for a forecast (rule 4 is lower confidence).",
    "The risk model ranks (AUC 0.67 booking-time, 0.71 with day-of weather); it does not predict a specific delay.",
  ], M, 2.05, 5.8, 4.3, 13);
  s.addText("Next steps", { x: 7.0, y: 1.5, w: 5.8, h: 0.45, fontSize: 16, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "next head" });
  bullets(s, [
    "Add fares (BTS DB1B) to replace the break-even assumption with observed price gaps.",
    "Extend to 3-5 years of flights and weather so seasonal rules rest on more than one winter.",
    "Join the client's own trip records — routes, purposes, costs — and run the pilot.",
    "Automate the quarterly refresh of preferred-carrier and approved-hub lists.",
  ], 7.0, 2.05, 5.8, 4.3, 13);
  notes(s, "We would rather name the limitations than have the judges find them. Every one has a mitigation in the method, and the next steps show how the work compounds with the client's own data.");
}
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Recommendations" });
  s.addText("The ask: approve a one-quarter controlled pilot", { placeholder: "title" });
  const lines = [
    ["1", "Morning preference (07:00-09:59) for time-critical trips", "hour-late trips −43 to −46%"],
    ["2", "Nonstop first; 90+ minutes via approved hubs when connecting", "missed connections 51 → 23 per 1,000"],
    ["3", "Route-specific carrier preferences", "−15% on covered routes; −55% with rule 1"],
    ["4", "Buffers, day-before travel and forecast-triggered rebooking (watch rule)", "summer/winter afternoon trips 16% → 7%"],
  ];
  lines.forEach(([n, t, e], i) => {
    const y = 1.6 + i * 1.0;
    numberCircle(s, n, M, y + 0.1, C.accent1);
    s.addText(t, { x: 1.15, y, w: 7.4, h: 0.6, fontSize: 19, bold: true, color: C.background1, margin: 0, isTextBox: true, objectName: "close " + n });
    s.addText(e, { x: 8.7, y: y + 0.05, w: 4.15, h: 0.6, fontSize: 15, color: C.accent1, margin: 0, isTextBox: true, objectName: "close effect " + n });
  });
  s.addText("Two business units, one quarter, against a control group; modeled saving $13k-$76k per 1,000 trips depending on how a lost hour and a missed meeting are valued. Decision needed today: approve the pilot and name the owners.",
    { x: M, y: 5.75, w: 12.3, h: 0.8, fontSize: 14, color: C.accent5, margin: 0, isTextBox: true, objectName: "ask" });
  s.addText("Questions — the Trip Risk Checker is live for any route, month or constraint you want to test.", { x: M, y: 6.5, w: 12.3, h: 0.4, fontSize: 13, italic: true, color: C.accent5, margin: 0, isTextBox: true, objectName: "questions" });
  notes(s, "Close on the decision: a controlled pilot, with owners named. Whatever constraint the judges raise — single-carrier contract, no early flights, budget cut, same-day only — the app answers it live, and the Q&A drills in deck/storyline.md have the numbers.");
}

// ================================================================== APPENDIX
pres.addSection({ title: "Appendix" });
{
  const s = content("Appendix A1 — Model validation: calibrated at booking time; day-of weather adds real information", "Appendix");
  img(s, "21_model_calibration_lift.png", M, 1.4, 6.2, 3.0);
  img(s, "22_adjusted_odds_ratios.png", 6.9, 1.4, 6.0, 3.0);
  const c = (t) => ({ text: t, options: { fontSize: 11, color: C.text1 } });
  s.addTable([
    [hdr("Model (5-fold CV grouped by date; 200k sample)", 11), hdr("AUC", 11), hdr("Avg precision", 11), hdr("Brier", 11)],
    [c("Logistic — booking time"), c("0.665"), c("0.375"), c("0.168")],
    [c("Boosted trees — booking time"), c("0.671"), c("0.381"), c("0.168")],
    [c("Logistic — short notice (+ day-of weather)"), c("0.699"), c("0.437"), c("0.161")],
    [c("Boosted trees — short notice (+ day-of weather)"), c("0.706"), c("0.450"), c("0.160")],
    [c("Always predict the base rate"), c("0.500"), c("0.235"), c("0.180")],
  ], { x: M, y: 4.6, w: 7.4, colW: [4.1, 1.1, 1.2, 1.0], border: { type: "solid", pt: 0.75, color: HEX.lt2 }, margin: 0.06, autoPage: false, objectName: "model table" });
  bullets(s, [
    "Booking-time features only: carrier, origin, destination, month, weekday, departure hour, distance, duration, hub tier, airport-month weather climatology. No departure delay, cause codes or tail numbers.",
    "Riskiest decile of bookings is disrupted 5.5x as often as the safest (47% vs 9%); for the severe outcome 23.5% vs 3.4%.",
    "A model with fewer features (carrier, route, hour, month) scores ~0.63 — the climatology and hub features add the rest.",
  ], 8.2, 4.6, 4.65, 2.3, 11);
  notes(s, "Disruption is noisy — most of it is caused by things nobody knows at booking — so an AUC in the high 0.60s is what one should expect. What matters is calibration and ranking, and both hold.");
}
{
  const s = content("Appendix A2 — Data quality: no rows dropped, every missing value structural, sample reproduces the population", "Appendix");
  const c = (t, o) => cell(t, Object.assign({ fontSize: 10.5 }, o || {}));
  const log = parseCsv(fs.readFileSync(path.join(ROOT, "outputs", "tables", "cleaning_log.csv"), "utf8"));
  const tbl = [[hdr("Issue", 11), hdr("Rule", 11), hdr("Rows (200k sample)", 11), hdr("Rows (full file)", 11)]];
  const full = { "ARR_DELAY blank for cancelled flights": "95,166", "ARR_DELAY blank for diverted flights": "18,015", "Rows removed": "0" };
  log.slice(1).forEach((r) => tbl.push([c(r[0]), c(r[1]), c(Number(r[2]).toLocaleString(), { align: "right" }), c(full[r[0]] || (r[0].startsWith("Times") || r[0].startsWith("Arrival") || r[0].startsWith("OP_") ? "6,398,056" : "—"), { align: "right" })]));
  s.addTable(tbl, { x: M, y: 1.45, w: 8.3, colW: [2.6, 3.6, 1.05, 1.05], border: { type: "solid", pt: 0.75, color: HEX.lt2 }, margin: 0.05, autoPage: false, objectName: "cleaning log" });
  s.addText("Sample vs population", { x: 9.3, y: 1.5, w: 3.5, h: 0.4, fontSize: 14, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "svp head" });
  bullets(s, [
    "200,000-flight uniform sample of 6,398,056 flights (organisers' validation report reproduced exactly: 2,907 cancelled, 570 diverted, 327 airports).",
    "Full file: 329 airports, 95,166 cancellations (1.5%), 18,015 diversions (0.3%); disrupted 23.55%, severe 9.70%.",
    "Every carrier's population rate falls inside the sample's 95% Wilson interval.",
    "Route, hub and connection results use the full file; the sample carries the national patterns and the model.",
  ], 9.3, 2.0, 3.5, 4.3, 11.5);
  notes(s, "The cleaning log answers 'what did you do to the data': nothing was dropped, and every blank has a structural reason.");
}
{
  const s = content("Appendix A3 — When: day-of-week by time-of-day, and the month profile", "Appendix");
  img(s, "03_heatmap_day_by_time.png", M, 1.4, 6.3, 5.0);
  img(s, "04_month_and_cancellations.png", 6.9, 1.9, 6.0, 4.0);
  notes(s, "Left: Sunday and Thursday-Friday evenings are the worst slots; any weekday morning is safe. Right: June-July and December are the risky months; January has the cancellations (weather); November's spike is air-traffic-system coded.");
}
{
  const s = content("Appendix A4 — Planning tables: the buffer a must-attend traveler needs, and weather exposure by airport and month", "Appendix");
  img(s, "25_buffer_rule.png", M, 1.4, 6.3, 5.0);
  img(s, "13_weather_climatology.png", 6.9, 1.4, 6.0, 5.0);
  notes(s, "Left: hours of buffer for 95% confidence (incl. rebooking after cancellations) by departure time and season. Right: share of adverse-weather days by airport and month in 2025 — one year, so a guide rather than a climatology.");
}
{
  const s = content("Appendix A5 — Hub fragility: winter readiness by outcome, and Newark's 2025 runway closure", "Appendix");
  img(s, "12_winter_readiness.png", M, 1.4, 6.3, 4.1);
  img(s, "26_newark_construction.png", 6.9, 1.4, 6.0, 4.1);
  bullets(s, [
    "Winter readiness is measured by outcome: how much a hub degrades on its own snow / freezing days. No public de-icing capacity list exists.",
    "Newark: 21% → 35% disrupted and 0.9% → 3.9% cancelled during the 4L-22R closure (15 Apr - 2 Jun 2025) while JFK and LGA were flat; ATC staffing problems overlapped. Hence a watch rule: check FAA construction notices before tight connections.",
    "Sources: BTS On-Time Performance 2025; NOAA NCEI GHCN-Daily; OurAirports; Port Authority of NY & NJ / FAA notices; full list in data/external/SOURCES.md.",
  ], M, 5.6, 12.3, 1.3, 11);
  notes(s, "Two reasons a hub can be fragile that the carrier and hour do not capture: weather it is not used to, and construction. Both argue for the approved-hub list being refreshed quarterly.");
}

function parseCsv(text) {
  const out = []; let row = [], field = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) { if (ch === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else q = false; } else field += ch; }
    else if (ch === '"') q = true;
    else if (ch === ",") { row.push(field); field = ""; }
    else if (ch === "\n" || ch === "\r") { if (ch === "\r" && text[i + 1] === "\n") i++; row.push(field); out.push(row); row = []; field = ""; }
    else field += ch;
  }
  if (field.length || row.length) { row.push(field); out.push(row); }
  return out.filter((r) => r.length > 1);
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();

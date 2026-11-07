// Product pitch deck for the Trip Risk Checker app.
//   NODE_PATH="$PWD/deck/build/node_modules" node deck/build/build_pitch.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const SKILL = "C:/Users/anair/AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/local-agent-mode-sessions/skills-plugin/5f747424-bd78-4f57-bf8b-35b9c207c779/eda4a44d-ca96-4cbf-a650-5f57f41d4346/skills/pptx";
const { applyTheme } = require(SKILL + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..", "..");
const FIGDIR = path.join(ROOT, "outputs", "figures");
const FIG = (n) => path.join(FIGDIR, n);
const OUT = path.join(ROOT, "deck", "Trip_Risk_Checker_Pitch.pptx");
const shot = (n) => fs.existsSync(FIG(`app_tab${n}.png`)) ? `app_tab${n}.png` : `app_tab${n}_pane.jpg`;

const THEME = {
  name: "Trip Risk Checker", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: "1F2A44", lt1: "FFFFFF", dk2: "5B6477", lt2: "F5F7FA", accent1: "2A9D8F", accent2: "D1495B", accent3: "3A6EA5", accent4: "E9A23B", accent5: "B8BEC9", accent6: "0F1A33", hlink: "3A6EA5", folHlink: "5B6477" },
};
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Trip Risk Checker";
const C = pres.SchemeColor;
const W = 13.33, H = 7.5, M = 0.6;

const footer = (dark) => ({ text: { text: "Trip Risk Checker · Questrom MSBA · Chart Champ Datathon 2026", options: { x: M, y: H - 0.45, w: 8, h: 0.3, fontSize: 9, color: dark ? C.accent5 : C.text2, margin: 0 } } });
const titlePh = (color) => ({ placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: W - 2 * M, h: 0.8, fontSize: 28, bold: true, color, margin: 0, valign: "top", align: "left" }, text: "" } });
pres.defineSlideMaster({ title: "LIGHT", background: { color: HEX.lt1 }, objects: [titlePh(C.text1), footer(false)], slideNumber: { x: W - 1.1, y: H - 0.45, w: 0.5, h: 0.3, fontSize: 9, color: C.text2, align: "right" } });
pres.defineSlideMaster({ title: "DARK", background: { color: HEX.accent6 }, objects: [titlePh(C.background1), footer(true)], slideNumber: { x: W - 1.1, y: H - 0.45, w: 0.5, h: 0.3, fontSize: 9, color: C.accent5, align: "right" } });
pres.defineSlideMaster({ title: "COVER", background: { color: HEX.accent6 }, objects: [footer(true)] });

function img(s, file, x, y, w, h, name) { s.addImage({ path: FIG(file), x, y, w, h, sizing: { type: "contain", w, h }, objectName: name || file }); }
function frame(s, file, x, y, w, h) {   // screenshot in a soft "browser window" frame
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: C.background2 }, line: { color: HEX.accent5, width: 0.75 }, rectRadius: 0.12, shadow: { type: "outer", blur: 6, offset: 2, angle: 90, color: "1F2A44", opacity: 0.12 }, objectName: "frame " + file });
  [[0.22, "accent2"], [0.42, "accent4"], [0.62, "accent1"]].forEach(([dx, c], i) => s.addShape(pres.ShapeType.ellipse, { x: x + dx, y: y + 0.13, w: 0.12, h: 0.12, fill: { color: C[c] }, line: { color: C[c] }, objectName: "dot " + i }));
  s.addImage({ path: FIG(file), x: x + 0.12, y: y + 0.38, w: w - 0.24, h: h - 0.5, sizing: { type: "cover", w: w - 0.24, h: h - 0.5 }, objectName: file });
}
function text(s, t, x, y, w, h, o) { s.addText(t, Object.assign({ x, y, w, h, fontSize: 14, color: C.text1, margin: 0, isTextBox: true, valign: "top", objectName: typeof t === "string" ? t.slice(0, 30) : "text" }, o || {})); }
function stat(s, v, l, x, y, w, color, size) {
  const vs = size || 40, vh = vs >= 34 ? 0.85 : 0.6;
  text(s, v, x, y, w, vh, { fontSize: vs, bold: true, color: color || C.accent1 });
  text(s, l, x, y + vh, w, 0.8, { fontSize: 12.5, color: C.text2 });
}
function bullets(s, items, x, y, w, h, size, color) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1, paraSpaceAfter: 9 } }));
  s.addText(runs, { x, y, w, h, fontSize: size || 14, color: color || C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "bullets" });
}
function circle(s, n, x, y, color) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: 0.44, h: 0.44, fill: { color: color || C.accent1 }, line: { color: color || C.accent1 }, objectName: "c" + n });
  text(s, String(n), x, y, 0.44, 0.44, { fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle" });
}
function card(s, x, y, w, h, head, body, color, n) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.1, objectName: "card " + head });
  if (n) circle(s, n, x + 0.25, y + 0.25, color);
  text(s, head, x + (n ? 0.85 : 0.25), y + 0.27, w - (n ? 1.1 : 0.5), 0.45, { fontSize: 14.5, bold: true, color: color || C.text1 });
  text(s, body, x + 0.25, y + (n ? 0.85 : 0.75), w - 0.5, h - 1.0, { fontSize: 12.5, color: C.text2 });
}
function slide(title, master, section) { const s = pres.addSlide({ masterName: master || "LIGHT", sectionTitle: section }); s.addText(title, { placeholder: "title" }); return s; }
const notes = (s, t) => s.addNotes(t);

// ================================================================== 1 cover
pres.addSection({ title: "Pitch" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "Pitch" });
  text(s, "✈", M, 1.3, 1, 0.9, { fontSize: 40, color: C.accent1 });
  text(s, "Trip Risk Checker", M, 2.0, 9, 1.2, { fontSize: 52, bold: true, color: C.background1 });
  text(s, "Know the risk before you book.", M, 3.2, 9, 0.7, { fontSize: 24, color: C.accent5 });
  text(s, "A booking-time risk score for every US domestic route, carrier, departure time and season — built from 6.4 million flights and NOAA weather, delivered as a web app your travel desk and travelers can use today.", M, 4.1, 8.0, 1.3, { fontSize: 15, color: C.accent5 });
  text(s, "Prepared by [TEAM NAME — replace] · Questrom MSBA · 7 November 2026", M, 6.0, 9, 0.4, { fontSize: 12, color: C.accent1 });
  frame(s, shot(1), 9.0, 1.4, 4.0, 2.9);
  notes(s, "Thirty-second opener: every booking tool shows price and schedule; none shows the chance of missing the meeting. We built the one that does, from every US domestic flight in 2025.");
}
// ================================================================== 2 problem
{
  const s = slide("Booking tools show price and schedule. They do not show the chance of missing the meeting.");
  stat(s, "23.5%", "of flights are disrupted — 15+ min late, cancelled or diverted (6.4M US domestic flights, 2025)", M, 1.6, 3.9, C.accent2);
  stat(s, "9.7%", "arrive an hour+ late, are cancelled or diverted — the trips that cost a meeting", 4.7, 1.6, 3.9, C.accent2);
  stat(s, "3.2x", "difference in disruption risk between a 7 p.m. and a 6 a.m. departure on the same routes", 8.8, 1.6, 3.9, C.accent4);
  card(s, M, 3.9, 3.9, 2.5, "The traveler", "Picks by price and time, lands an hour late, misses the meeting, sleeps in an airport hotel. The cost is invisible at booking.", C.accent3, 1);
  card(s, 4.7, 3.9, 3.9, 2.5, "The travel manager", "Has a policy about fares and class of service — and nothing about reliability, because nobody has put the numbers in front of them.", C.accent3, 2);
  card(s, 8.8, 3.9, 3.9, 2.5, "The company", "Pays roughly $98k per 1,000 trips in lost time, missed meetings and strandings (at $100/h, $500 per missed meeting, $300 per stranding).", C.accent3, 3);
  notes(s, "The data is public and the risk is predictable, but it never reaches the moment of booking. That is the gap the product closes.");
}
// ================================================================== 3 insight
{
  const s = slide("The risk is predictable at booking time — four levers the data makes visible");
  const items = [
    ["Departure hour", "Risk climbs every hour from 5 a.m. to 7 p.m. as late aircraft cascade. Morning 5.4% vs evening 14.5% an hour late.", "02_disruption_by_hour.png"],
    ["Carrier on the route", "Like-for-like, carriers differ by 5-10 points on the same route; the right pick is route-specific, not a blanket airline.", "14_carrier_route_adjusted.png"],
    ["The hub", "One-stops via SLC, LAX or SEA: 9-10% an hour late. Via DCA, DFW or LGA: 20-21%. A 90-minute layover halves missed connections.", "19_hub_ranking.png"],
    ["Season and weather", "Flights touching adverse weather are 1.8x as likely to be disrupted; exposure by airport and month is knowable when you book.", "10_weather_conditions.png"],
  ];
  items.forEach(([h, b, f], i) => {
    const x = M + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.55;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 5.95, h: 2.35, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.1, objectName: "tile " + h });
    img(s, f, x + 0.15, y + 0.15, 2.4, 2.05, "thumb " + f);
    text(s, h, x + 2.7, y + 0.25, 3.1, 0.4, { fontSize: 14.5, bold: true, color: C.accent1 });
    text(s, b, x + 2.7, y + 0.7, 3.1, 1.6, { fontSize: 12, color: C.text2 });
  });
  notes(s, "Four findings from the analysis, each validated like-for-like. The product turns them into a single number per option: the chance of arriving an hour late.");
}
// ================================================================== 4 product
{
  const s = slide("The product — one screen answers 'which flight gets me to the meeting?'");
  frame(s, shot(1), M, 1.4, 8.1, 5.4);
  bullets(s, [
    "Pick a route, month and departure window; every carrier that flies it gets a risk score with a plain-English pill (low / moderate / high).",
    "Each card shows disruption, cancellation, the buffer to land for 95% confidence, and the evidence base (flights in 2025).",
    "A recommendation line names the safest option and the buffer in one sentence.",
    "Below: the same route by departure time, weather exposure for that month, and nonstop vs one-stop with the fare saving needed to break even.",
  ], 9.0, 1.5, 3.75, 5.2, 12.5);
  notes(s, "Walk the screen top to bottom: inputs, carrier cards, recommendation, then the context panels. Everything is precomputed — the page loads in under a second.");
}
// ================================================================== 5 simulator
{
  const s = slide("For the travel manager — a policy simulator that re-runs last year's trips under each rule");
  frame(s, shot(2), M, 1.4, 8.1, 5.4);
  bullets(s, [
    "Toggle booking rules (before 10 a.m., 07:00-09:59, preferred carrier, Tue/Wed) and see trips per 1,000 arriving an hour late, delay hours and overnight strandings.",
    "Cost assumptions are sliders — the value of an hour, a missed meeting, a stranding — so the business case is yours, not ours.",
    "Burden metrics ride along: late-night arrivals and pre-6 a.m. departures, so policy is judged on the employee's side too.",
    "The buffer table: hours to land before a must-attend meeting by season and departure time.",
  ], 9.0, 1.5, 3.75, 5.2, 12.5);
  notes(s, "This is the Q&A weapon: any constraint — single carrier, no early flights, budget cut — becomes a slider or a rule toggle, with the numbers recomputed live.");
}
// ================================================================== 6 hubs
{
  const s = slide("For connections — hubs ranked by what actually happens to one-stop trips");
  frame(s, shot(3), M, 1.4, 8.1, 5.4);
  bullets(s, [
    "3.4 million one-stop itineraries constructed from real flight pairs, with a 30-minute connection rule and rebooking when a connection breaks.",
    "Every major hub ranked by hour-late rate, missed connections and overnight strandings; winter fragility and dominant carrier alongside.",
    "An airport map coloured by disruption, monthly weather exposure or winter fragility — the approved-hub list, explained.",
  ], 9.0, 1.5, 3.75, 5.2, 12.5);
  notes(s, "Constructed itineraries, not tickets sold — we say so on the screen. The ranking is refreshed from BTS data each quarter.");
}
// ================================================================== 7 how it works
{
  const s = slide("How it works — public data in, a risk score out, refreshed every quarter");
  const steps = [
    ["BTS On-Time Performance", "6.4M flights, 10 carriers, 329 airports, 2025. Cleaned with one shared function; no rows dropped."],
    ["NOAA GHCN-Daily", "Daily weather at the station nearest each of 324 airports: snow, ice, storms, wind, fog."],
    ["Simulation", "Cancelled travelers rebooked on the next flight; 3.4M one-stop trips built from flight pairs."],
    ["Lookup tables + model", "Route x carrier x time x season rates (shrunk for thin cells); a calibrated booking-time risk model (AUC 0.67-0.71)."],
    ["Streamlit app", "Reads only the small precomputed tables; loads in under a second; deployable on Streamlit Community Cloud from a GitHub repo."],
  ];
  steps.forEach(([h, b], i) => {
    const x = M + i * 2.47;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.7, w: 2.3, h: 3.1, fill: { color: i === 4 ? C.accent1 : C.background2 }, line: { color: i === 4 ? C.accent1 : C.background2 }, rectRadius: 0.1, objectName: "step " + h });
    circle(s, i + 1, x + 0.2, y = 1.9, i === 4 ? C.accent6 : C.accent3);
    text(s, h, x + 0.2, 2.5, 1.95, 0.6, { fontSize: 13.5, bold: true, color: i === 4 ? C.background1 : C.text1 });
    text(s, b, x + 0.2, 3.1, 1.95, 1.6, { fontSize: 11.5, color: i === 4 ? C.background1 : C.text2 });
    if (i < 4) text(s, "→", x + 2.3, 3.0, 0.2, 0.5, { fontSize: 18, color: C.accent5, align: "center" });
  });
  stat(s, "8", "notebooks, fully reproducible from the raw files in ~20 minutes", M, 5.2, 3.0, C.text1, 30);
  stat(s, "< 1 s", "page load — the app never touches the 6.4M rows", 3.7, 5.2, 3.0, C.text1, 30);
  stat(s, "quarterly", "refresh of carrier, hub and route tables from new BTS releases", 6.8, 5.2, 3.0, C.text1, 30);
  stat(s, "$0", "hosting on Streamlit Community Cloud; public data only", 9.9, 5.2, 2.9, C.text1, 30);
  notes(s, "No proprietary data, no PII, no infrastructure to run. The whole pipeline is eight notebooks and a 400-line app.");
}
var y;
// ================================================================== 8 value
{
  const s = slide("What it is worth — a modeled $13k-$76k per 1,000 trips from the first rule alone");
  img(s, "23_policy_impact.png", M, 1.4, 7.6, 3.3);
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text1 }, fontSize: 11 } });
  const c = (t, o) => ({ text: t, options: Object.assign({ fontSize: 11.5, align: "center", color: C.text1 }, o || {}) });
  s.addTable([
    [hdr("Saving per 1,000 trips ($k)"), hdr("Meeting $0"), hdr("$500"), hdr("$1,000")],
    [c("Traveler time $50 / h", { align: "left" }), c("13"), c("35"), c("57")],
    [c("Traveler time $100 / h", { align: "left", bold: true }), c("23"), c("44", { bold: true }), c("66")],
    [c("Traveler time $150 / h", { align: "left" }), c("32"), c("54"), c("76")],
  ], { x: 8.5, y: 1.5, w: 4.25, colW: [1.9, 0.75, 0.8, 0.8], border: { type: "solid", pt: 0.75, color: HEX.lt2 }, margin: 0.05, autoPage: false, objectName: "sensitivity" });
  text(s, "Morning preference, if fully adopted; cancelled travelers rebooked; excludes extra fares, hotels and policy costs.", 8.5, 3.45, 4.25, 0.8, { fontSize: 10.5, italic: true, color: C.text2 });
  card(s, M, 4.95, 3.9, 1.9, "Rules 1 + 3 together", "Hour-late trips 96 → 43 per 1,000 (−55%), ~$54k per 1,000 trips at the mid case.", C.accent1);
  card(s, 4.7, 4.95, 3.9, 1.9, "Employee side", "Late-night arrivals 74 → 0.4 per 1,000; overnight strandings 14 → 3; the 07:00-09:59 variant keeps pre-6 a.m. departures at zero.", C.accent3);
  card(s, 8.8, 4.95, 3.9, 1.9, "Traveler care budget", "~$6k per 1,000 trips at mid assumptions, triggered by measured events — a rounding error next to the disruption cost.", C.accent4);
  notes(s, "Every number is a modeled benefit under stated assumptions; the sensitivity table is the honest range. The pilot turns the model into a measured result.");
}
// ================================================================== 9 rollout
{
  const s = slide("Rollout — a one-quarter pilot, then the booking tool");
  const phases = [
    ["Weeks 1-2 · Launch", "Host the app (Streamlit Community Cloud, free); travel desk and two business units get the link; owners named.", C.accent1],
    ["Quarter 1 · Pilot", "Morning preference and preferred-carrier defaults for time-critical trips in two units vs a control group. Track severe-disruption rate, delay hours per 100 trips, strandings, compliance, fare delta, traveler satisfaction.", C.accent3],
    ["Quarter 2 · Integrate", "Defaults and soft warnings inside the booking tool (evening departure, last flight of the day, <90-min connection, non-approved hub); override with a reason code.", C.accent4],
    ["Ongoing · Refresh", "Quarterly rebuild from new BTS and NOAA releases; add fares (DB1B), a forecast feed for rule 4, and the client's own trip records.", C.accent2],
  ];
  phases.forEach(([h, b, col], i) => {
    const x = M + i * 3.08;
    s.addShape(pres.ShapeType.rect, { x, y: 1.6, w: 2.9, h: 0.08, fill: { color: col }, line: { color: col }, objectName: "bar " + i });
    text(s, h, x, 1.85, 2.9, 0.5, { fontSize: 14.5, bold: true, color: col });
    text(s, b, x, 2.4, 2.9, 2.6, { fontSize: 12.5, color: C.text2 });
  });
  s.addShape(pres.ShapeType.roundRect, { x: M, y: 4.9, w: 12.13, h: 1.6, fill: { color: C.background2 }, line: { color: C.background2 }, rectRadius: 0.1, objectName: "target" });
  stat(s, "96 → ~55", "hour-late or stranded trips per 1,000 — the pilot target (not the fully-adopted 52)", M + 0.3, 5.05, 4.0, C.accent1, 28);
  stat(s, "4", "KPIs on one page: severe rate, delay hours, strandings, compliance — plus fare delta and satisfaction", 4.9, 5.05, 3.8, C.text1, 28);
  stat(s, "0", "new systems to buy: a link, then defaults in the tool you already use", 9.0, 5.05, 3.6, C.text1, 28);
  notes(s, "Light rollout by design: a hosted link first, policy defaults second, integration third. The quarterly refresh is scripted.");
}
// ================================================================== 10 trust
{
  const s = slide("What we would say to a skeptical CFO — the limits are on the screen, not hidden");
  bullets(s, [
    "Simulated vs observed is labelled everywhere: one-stop trips and rebooking are constructed from real flights, not tickets sold.",
    "One year of data (2025); associations with like-for-like controls, not proven causes. Results hold without the 15 worst days.",
    "Operating carrier only — regional airlines fly for several brands; SkyWest / Republic assigned by a documented heuristic.",
    "No fares in the data: the break-even fare saving is the honest substitute until DB1B fares are added.",
    "Weather: daily, one station per airport; actual weather stands in for a forecast, so the weather rule is a watch rule.",
    "The model ranks risk (AUC 0.67 at booking, 0.71 with day-of weather); it does not predict a specific delay.",
  ], M, 1.5, 7.3, 5.2, 13.5);
  card(s, 8.3, 1.5, 4.45, 2.4, "Validated", "Grouped cross-validation by date; calibration checked; the 200k sample reproduces the 6.4M population inside its confidence intervals.", C.accent1);
  card(s, 8.3, 4.1, 4.45, 2.4, "Reproducible", "Eight notebooks, one cleaning function, every chart and table regenerated from the raw files; sources logged with dates and licences.", C.accent3);
  notes(s, "We would rather name the limitations than have a client find them. Each one has a mitigation and a next step.");
}
// ================================================================== 11 ask
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Pitch" });
  s.addText("The ask", { placeholder: "title" });
  const lines = [
    ["1", "Approve a one-quarter controlled pilot in two business units", "owners: travel manager, travel desk lead, analytics"],
    ["2", "Host the Trip Risk Checker for the travel desk and travelers", "Streamlit Community Cloud from the project repo — free, public data only"],
    ["3", "Adopt the four booking defaults as soft warnings, not bans", "override with a reason code; refreshed quarterly"],
  ];
  lines.forEach(([n, t, e], i) => {
    const y = 1.7 + i * 1.3;
    circle(s, n, M, y + 0.1, C.accent1);
    text(s, t, 1.3, y, 11.4, 0.6, { fontSize: 22, bold: true, color: C.background1 });
    text(s, e, 1.3, y + 0.6, 11.4, 0.5, { fontSize: 14, color: C.accent1 });
  });
  text(s, "Modeled saving $13k-$76k per 1,000 trips depending on how a lost hour and a missed meeting are valued — the pilot replaces the model with a measurement.", M, 5.8, 12.1, 0.8, { fontSize: 14, color: C.accent5 });
  notes(s, "End on the decision. The app is live for any route or constraint the room wants to test.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();

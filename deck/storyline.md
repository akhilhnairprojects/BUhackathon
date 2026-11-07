# Deck storyline — "Arrive on time, arrive ready"
### Corporate travel analytics proposal · Questrom Chart Champ Datathon · Nov 7, 2026

All numbers below trace to `outputs/tables/` and the figures to `outputs/figures/`. Rubric weights:
business relevance 30 · rigor 30 · visuals & story 25 · critical thinking & Q&A 15. Aim for ~12 main
slides + appendix; 8-10 minutes of talking.

---

## Slide 1 — Title
**Arrive on time, arrive ready: a data-driven travel policy for [Client]**
Sub: 6.4 million US domestic flights (2025) · NOAA weather · 4 recommendations

*Notes:* one sentence on who we are and the ask: cut disruption without blowing up cost or convenience.

## Slide 2 — The problem in one number
**Nearly 1 in 4 business flights is disrupted; 1 in 10 makes you an hour late or strands you.**
Big numbers: 23.5% disrupted (15+ min late, cancelled or diverted) · 9.6% an hour+ late or stranded
(incl. rebooking after cancellations) · 1.4% stranded overnight · 460 delay-hours per 1,000 trips.
Figure: `01_delay_distribution.png` (small) or just the big numbers.

*Notes:* "Most flights land early. The problem is the tail — and the tail is what costs you a meeting.
Per 1,000 trips that is ~460 lost hours and 14 overnight strandings. At $100/hour of traveler time,
$500 per missed meeting and $300 per stranding, disruption costs roughly **$98k per 1,000 trips**
(assumptions, varied later)."

## Slide 3 — How we measured it (method, 1 slide)
- Data: BTS On-Time Performance, all 6.4M domestic flights of 10 carriers in 2025 (200k sample
  validated against it: every carrier rate inside the sample's 95% CI).
- Enrichment: NOAA daily weather at 324 airports; OurAirports runway/coordinate data.
- Outcome = what the traveler feels: **arrival** 15+/60+ min late, cancelled or diverted; cancelled
  flights are **rebooked on the next flight** so they count fully.
- One-stop trips **constructed** from real flight pairs (3.4M itineraries) to compare with nonstops.
- Validation: like-for-like comparisons (same route, month, time), grouped cross-validation by date,
  confidence intervals everywhere, results re-checked without the 15 worst days.

*Notes:* keep to 45 seconds; the point is "we treated cancellations honestly and compared like with like."

## Slide 4 — Finding 1: time of day is the biggest lever
Figure: `02_disruption_by_hour.png`
**A 7 p.m. departure is 3.2x as likely to be disrupted as a 6 a.m. one** (35% vs 11%).
Adjusted for carrier, route, season (model): 7 p.m. odds **x3.1** vs 8 a.m.

*Notes:* "Why? Delays snowball — late inbound aircraft are 39% of delay minutes
(`08_delay_causes_by_hour.png`). Holds for the **same carrier on the same route**: evening is worse
on 98% of 3,198 route-carrier pairs, median +20 points (`16_same_route_morning_evening.png`)."

## Slide 5 — Finding 2: carrier choice is worth 5-10 points, but only like-for-like
Figure: `14_carrier_route_adjusted.png` (+ `05_carrier.png` as raw context)
**Like-for-like, United runs 5 pts safer than its rivals on the same route; PSA 7 pts worse.**
On the 43% of trips where 2+ airlines fly the route, the median best-vs-worst gap is **6.8 points**;
on routes like ORD-BOS it exceeds 20 (`route_preferred_carrier.csv`).

*Notes:* "Raw rankings mislead: Alaska looks fine because it flies in the calm West; Delta's raw lead
shrinks when compared on the same routes. Policy must be route-level, not a blanket airline pick."

## Slide 6 — Finding 3: season and weather — more than the airlines admit
Figures: `04_month_and_cancellations.png`, `10_weather_conditions.png`
June-July (30-31% disrupted) and December (27%) are the risky months; September the calm one (17%).
NOAA: flights touching an airport with adverse weather are **1.8x** as likely to be disrupted
(33% vs 18%); snow/freezing days roughly double it. Excess disruption on adverse days = **23% of all
disruptions**, vs the 7% of delay minutes the airlines label "weather".

*Notes:* "Weather hides inside 'air traffic' and 'late aircraft' codes. It also widens the gap between
carriers (`11_carrier_weather_resilience.png`) — Alaska +7 pts on bad days, Envoy +20."

## Slide 7 — Finding 4: a stop is a gamble; the hub and the layover decide the odds
Figures: `17_nonstop_vs_onestop.png`, `18_layover_curve.png`, `19_hub_ranking.png`
- Same city pairs: nonstop **9%** an hour late vs one-stop **16%** (45-min layover) / **14%** (90-min).
- Stranded overnight: 1.3% nonstop vs 3.7% one-stop (45-min).
- Requiring **90 minutes** instead of 45 cuts missed connections from 5.1% to 2.3%.
- Hubs differ 2x: SLC / LAX / SEA ~9-10% an hour late vs DCA / DFW / LGA ~20-21%.

*Notes:* "Break-even: valuing the traveler's time at $100/h, a one-stop must be about **$400 cheaper
one-way** on the biggest markets (median across 1,598 pairs in `20_breakeven_fare.png`) just to pay
for the extra 4 hours — before a missed meeting. Winter adds a twist: southern hubs that rarely see
ice (IAH, DFW, ATL, DCA) add ~30-40 pts of disruption when it comes (`12_winter_readiness.png`).
Construction matters too: during Newark's runway 4L-22R closure (Apr 15 - Jun 2, 2025) EWR went
from 21% to 35% disrupted and cancellations from 0.9% to 3.9%, while JFK/LGA were flat — about
+14 pts relative (`26_newark_construction.png`; ATC staffing problems overlapped). Hence the
watch-list rule: check FAA construction notices before booking tight connections through a hub."

## Slide 8 — The employee's side: the safest flight is not the kindest
Figure: `24_reliability_vs_sleep.png`
5-6 a.m.: 4.8% an hour late but a 4 a.m. alarm. 7-10 a.m.: 5.6% — nearly as good, no dawn start.
Evening: 14-15% an hour late and most of the late-night (11 p.m.-4 a.m.) arrivals.
Last flight of the day: **3.9x** as likely to strand the traveler overnight (2.8% vs 0.7%).

*Notes:* "We are not asking people to fly at dawn. The 7-10 a.m. window keeps ~95% of the reliability
gain. Avoid the last departure when the meeting is must-attend."

## Slide 9 — Recommendations (the slide judges photograph)
Figure: `23_policy_impact.png` as the backdrop; table from `recommendations_summary.csv`.

| # | Recommendation | Evidence (per 1,000 trips, same routes) | Trade-off | KPI |
|---|---|---|---|---|
| 1 | **Book before 10 a.m. for time-critical trips (7-10 a.m. default)** | hour-late/stranded 96 → 52 (-46%); delay hours 460 → 270; strandings 14 → 3 | Earlier start, fewer options | % time-critical bookings before 10 a.m.; severe rate |
| 2 | **Nonstop first. If connecting: 90+ min layover via approved hubs** | hour-late 9% nonstop vs 16%/14% one-stop; missed connections 5.1% → 2.3%; best hubs half the risk of worst | Nonstops cost more (break-even ~$400 one-way on big markets); +1 h layover | % nonstop; missed-connection rate; strandings |
| 3 | **Route-level preferred-carrier list (43% of trips have a choice)** | 98 → 84 hour-late (-15%) on covered routes; combined with #1: 96 → 43 | Loyalty/negotiated fares; refresh quarterly | Compliance; severe rate on covered routes |
| 4 | **Season & weather rule: buffer or day-before in Jun-Jul & Dec-Feb; forecast-triggered rebooking** | 95% buffer: summer evening 3.4 h vs morning 1.1 h; adverse-weather days 33% vs 18% disrupted; day-of weather lifts model AUC 0.67 → 0.71 | Hotel nights; travel-desk effort | Meetings missed; rebookings triggered |

Supporting: fly Tue/Wed where flexible (80 vs 96); never the last flight for must-attend trips;
trigger-based traveler care (next slide).

*Notes:* "Rule 1 alone is worth ~$44k per 1,000 trips at our mid assumptions; rules 1+3 together
~$54k. Everything is implementable in the booking tool as defaults and soft warnings, not bans."

## Slide 10 — Traveler care, sized from the data (prevention first, care second)
Table from `care_triggers.csv`:
- 2h+ delay → meal credit (healthy options where available): **48 events per 1,000 trips** today →
  29 with the morning rule; budget $1.2k-2.9k per 1,000 trips.
- Overnight stranding → hotel + late start next morning: **14 → 2.7** per 1,000; $2.8k-6.4k.
- Missed connection → meal + rebooking help: 23 per 1,000 connecting trips → 16.
- Approved 90-min connections → lounge pass (~40 usable minutes); amenities in appendix.

*Notes:* "Dollar values are assumptions, frequencies are measured. The care budget is a rounding error
next to the $98k disruption cost — and the booking rules cut it by 40-80%."

## Slide 11 — Implementation and how to measure success
- Booking tool: default sort = 7-10 a.m. nonstops on preferred carriers; soft warning on
  evening / last-flight / <90-min connections / non-approved hubs; override with a reason code.
- Travel desk: weather watch 72 h out for trips through fragile hubs; proactive rebooking.
- Pilot: 2 business units for a quarter vs control; track **severe-disruption rate, delay hours per
  100 trips, overnight strandings, compliance, traveler satisfaction, fare delta**.
- Refresh preferred-carrier and hub lists quarterly from BTS data (pipeline is built).
- Trip Risk Checker app for travelers and the travel desk (screenshot).

## Slide 12 — Limitations and what we'd do next
- One year (2025); association, not causation; operating carrier only (regionals fly for several brands).
- No fares, tickets or passenger counts: one-stops are constructed; rebooking assumes a seat.
- Daily weather at one station per airport; actual weather stands in for a forecast.
- Model ranks risk (AUC 0.67-0.71), it does not predict a specific delay.
- Next: add fares (DB1B), 3-5 years of data, client's own trip records.

## Appendix
A1 Cleaning log (`cleaning_log.csv`) · A2 Sample vs population (`sample_vs_population.csv`) ·
A3 Model validation (`21_model_calibration_lift.png`, `22_adjusted_odds_ratios.png`, `model_scores.csv`) ·
A4 Robustness without worst days (`robustness_event_days.csv`) · A5 Weather method & sources
(`data/external/SOURCES.md`) · A6 Winter readiness table · A7 Hub amenities · A8 Airport map
(`09_airport_map.png`) · A9 Heatmap day × time (`03_heatmap_day_by_time.png`).

---

## Q&A drills — hypothetical business constraints

**"We have a corporate contract with one airline."** Keep rules 1, 2 and 4 — they are
airline-neutral and deliver most of the gain (96 → 52 from timing alone). Within one airline, the
route-level table still shows its safest departure times and hubs. Quantify what the contract costs
in disruption on the routes where that airline trails (`route_preferred_carrier.csv`).

**"Nobody will take flights before 7 a.m."** We don't ask them to: 7-10 a.m. gives 5.6% vs 4.8% at
dawn — and 14% in the evening. The gain is the *before-10* part, not the *dawn* part.

**"Travel budget is cut 10%."** Nonstops often cost more, but a one-stop needs to be ~$400 cheaper on
big markets to break even on time alone. Save money on *flexible* trips (midday, one-stop via SLC/LAX/
SEA-type hubs, Tue/Wed) and protect *time-critical* trips. Two-tier policy by trip purpose.

**"Same-day travel only, no hotels."** Then timing does the work: morning nonstop; p95 buffer table
says how early to land (1-2 h morning, 3+ h summer evening). Day-before is only for must-attend.

**"Only our top 5 city pairs matter."** The app gives route-specific answers; e.g. LGA-ORD: nonstop
15.5% vs one-stop 20% an hour late; best carrier Republic 25% disrupted vs Delta 36%.

**"Why should we believe a 200k sample?"** Every carrier's population rate falls inside the sample's
CI (`sample_vs_population.csv`); route-level and connection results use the full 6.4M file.

**"Isn't this just weather you can't control?"** 23% of disruptions sit on adverse-weather days —
which means 77% don't. And weather is predictable in two ways: seasonally (climatology by airport
and month) and 1-3 days out (model AUC rises 0.67 → 0.71 with day-of weather).

**"Correlation, not causation?"** Agreed — so we compared the same route, same month, same time of
day (carrier) and the same carrier on the same route (time of day), and re-ran without the 15 worst
days. The mechanism (late aircraft cascade) is visible in the cause data.

**"What about employee wellbeing — are you making people miserable?"** Burden metrics are in the
simulation: the morning rule removes late-night arrivals (74 → 0.4 per 1,000) and overnight
strandings (14 → 3) while the 7-10 a.m. variant keeps pre-6 a.m. departures at zero.


---

## Revision log (after team review, Nov 6 evening) and number reconciliation

**Changed in the deck**
- Cover: team-name placeholder is marked `[TEAM NAME — replace]`.
- Slide 2 now uses the full-file definitions the team package uses: 23.5% disrupted, **9.7% severe** (60+ min / cancelled / diverted, no rebooking); "flights in the data", not "business flights". The 460 delay-hours figure is labelled as the rebooking simulation.
- Slide 3: **329 airports** in the full file (the sample has 327; 326 was the sample's origin count).
- Finding 3 retitled "Weather matters more than the airlines' weather code shows"; the 23%-vs-7% framing is gone from the title (BTS's code covers extreme weather only; the 23% excess is unadjusted for season and hub — upper bound, said in the notes). One chart on the slide; the month chart moved to A3. Chart legend no longer overlaps a bar.
- Recommendations reframed as conditional, with owner, exception rule and measure of success. Rule 4 is now quantified: summer/winter afternoon-evening trips 16.1% hour-late → 6.7% if moved to 07:00-09:59; day-before travel ~3.5% (pays when the meeting is worth > ~$1,600 at a $200 hotel); on adverse-weather days 22.8% → 8.5%.
- Impact slide: labelled "if fully adopted" and "modeled benefit, excludes extra fares/hotels"; sensitivity table ($50/$100/$150 per hour x $0/$500/$1,000 per missed meeting) = $13k-$76k per 1,000 trips, mid case $44k; components $19k time + $22k meetings + $3k strandings, counted once each. Pilot target stated as 96 → ~55 (not 52).
- Traveler care is its own slide; "23 → 16" is labelled per 1,000 *connecting* trips (90-min rule, all day → before 10 a.m.) so it does not clash with "51 → 23" (45- vs 90-min layover).
- Closing slide is a decision request (approve a one-quarter controlled pilot) with rule 4 shown as a percentage like the others.
- A1: 5.5x decile lift (the 2.9x was wrong). A2: full-file counts 95,166 cancellations / 18,015 diversions beside the sample counts. A5 amenities cut; Newark paired with winter readiness. App screenshot on the implementation slide.

**Why the deck and the team package differ (both are right, different definitions)**
| Item | Deck | Team package | Reason |
|---|---|---|---|
| Severe disruption | 9.7% (slide 2) and 96 per 1,000 = 9.6% (policy slides) | 9.70% | 9.6% counts cancelled travelers at their *rebooked* arrival; 9.7% counts them as severe outright |
| Morning vs evening severe | 5.4% (05:00-09:59) vs 14.5% (17:00-21:59), full file | 5.38% vs 14.74% | evening window differs slightly (ours 17-21:59; 17-23:59 gives 14.1%) |
| Evening worse than morning | 98% of 3,198 route-carrier pairs | 96.6% of 1,959 routes | pairs with 100+ flights in both windows vs route-level with a stricter threshold |
| Model AUC | 0.67 booking-time, 0.71 with day-of weather | 0.63 | our model adds hub tier and airport-month weather climatology (and day-of weather in the second model) |
| Airports | 329 (full) / 327 (sample) | 329 / 327 | fixed on slide 3 |

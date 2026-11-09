# Arrive on time, arrive ready

**Winning entry, Questrom Chart Champ Datathon (Boston University Questrom School of Business, November 2026).**

A data-driven travel policy for a company whose people fly constantly, and a website that puts the
analysis in a traveler's hands.

- **Live website:** https://trip-risk-checker.vercel.app
- **Walkthrough video:** [Using Trip Risk Checker](https://www.youtube.com/watch?v=uhpqE3nwuj4)
- **Final deck:** [`deck/Arrive_On_Time_Simple.pptx`](deck/Arrive_On_Time_Simple.pptx)

[![Using Trip Risk Checker](https://img.youtube.com/vi/uhpqE3nwuj4/hqdefault.jpg)](https://www.youtube.com/watch?v=uhpqE3nwuj4)

## The team

| | |
| --- | --- |
| Akhil Nair | Shon Shaju |
| Drishti Chulani | Tanmay Yenge |

## The event

The Questrom Chart Champ Datathon is an analytics case competition. Teams received a request for
proposal from a company with heavy employee air travel and one question: **how can it cut travel
disruption while balancing cost and convenience?** The data was the US Bureau of Transportation
Statistics on-time file for 2025: every domestic flight of ten airlines, 6.4 million flights.
Teams had to deliver findings, recommendations with their impact, and a plan to implement them.

## How this entry won

Our team took first place. The entry answered the brief with a short list of things a travel
manager can act on, each one measured on the full year of flights, and backed it with a tool the
judges could try on the spot.

1. **It measured what a traveler feels.** Not average delay, but the chance of arriving an hour
   late, cancelled or diverted. One flight in ten (9.7%) ends that way; 23.5% are disrupted by 15
   minutes or more.
2. **Four findings, each controlled for the others.**
   - *Fly in the morning.* A 7 p.m. departure is three times as likely to be disrupted as a 6 a.m.
     one. Leaving between 7 and 10 a.m. gives 5.6% hour-late arrivals against 14 to 15% in the evening.
   - *Pick the airline by route.* Compared only on the same route, month and time of day, the gap
     between the best and worst airline is typically 7 points, and up to 22 on Boston to Chicago.
   - *Weather is foreseeable.* Flights touching an airport with adverse weather are 1.8 times as
     likely to be disrupted (33% against 18%), and the risky months and airports are known at booking.
   - *A stop is a gamble.* Nonstop trips arrive an hour late 9% of the time; the same city pairs
     with one stop, 16%. The hub and the layover length decide the odds.
3. **Four booking defaults, not bans.** Morning preference for time-critical trips, nonstop first
   with 90-minute layovers through approved hubs, the preferred airline by route, and a weather
   buffer in risky months.
4. **A quantified impact.** Replayed on the same routes and volumes, the defaults cut hour-late
   trips from 96 to about 55 per 1,000 and save $13k to $76k per 1,000 trips, depending on what an
   hour and a missed meeting are worth.
5. **A working product.** The Trip Risk Checker answers any route, date and departure time live,
   so every number in the deck could be checked during Q&A.
6. **Stated limitations.** One year of data, constructed rather than observed connections, no
   fares, and weather hindsight standing in for a forecast are all spelled out in the deck.

## The website

[trip-risk-checker.vercel.app](https://trip-risk-checker.vercel.app) has three pages.

- **Check a trip.** Pick where you start, where you need to be, the travel date and a departure
  time. Every nonstop and same-airline connection is ranked by the chance of arriving an hour late.
- **Cost of missing.** Set what the meeting, an hour of your time and a night stranded are worth,
  and see the expected cost of each option and how much a safer flight is worth paying for.
- **Hubs & airports.** Twenty connecting hubs ranked by what happens to one-stop trips, and a map
  of disruption, weather exposure and winter fragility.

It is a static Preact app with no build step. The data it reads is precomputed by the notebooks
and shipped with the deployment.

## What is in this repository

```
src/
  prep.py          one cleaning function and the outcome definitions, used for sample and full data
  enrich.py        OurAirports and NOAA GHCN-Daily download, station matching, weather flags
  connections.py   builds one-stop itineraries from real flight pairs, with rebooking
  style.py         chart style
  build_nb.py      turns notebooks/_py/*.py into executed notebooks
notebooks/         01 cleaning · 02 exploratory analysis · 03 weather enrichment ·
                   04 route-level detail · 05 nonstop vs one-stop and hubs ·
                   06 risk model and validation · 07 policy simulation and costs ·
                   08 Newark case study and layovers
outputs/figures/   every chart in the deck      outputs/tables/   every number in the deck
deck/              the final deck, earlier versions, and the scripts that build it
web/               the Trip Risk Checker (index.html, app.js, styles.css, data/)
video/             the HyperFrames project behind the walkthrough video
app/app.py         an earlier Streamlit prototype of the checker
```

The raw flight files (the 200k-flight student sample and the full 6.4M-flight monthly files) were
supplied by the organisers and are not included.

## Definitions

- **Disrupted:** arrived 15 or more minutes late, cancelled or diverted.
- **Hour late:** arrived 60 or more minutes late, cancelled or diverted. In trip-level tables a
  cancelled traveler is rebooked on the next completed flight of the same airline and counted at
  that arrival.
- **One-stop trips** are constructed from real same-day flight pairs (3.4 million itineraries on
  1,730 city pairs). They are simulated trips, not tickets sold.

## Data sources

- Bureau of Transportation Statistics, On-Time Performance, calendar year 2025.
- NOAA GHCN-Daily weather station records, matched to 324 of 326 airports.
- OurAirports for coordinates and runways.

Details and download logs are in [`data/external/SOURCES.md`](data/external/SOURCES.md).

## Run it yourself

Install the Python packages:

```bash
pip install -r requirements.txt
```

Rebuild the analysis (needs the raw flight files in place):

```bash
python src/build_nb.py 01_cleaning 02_eda
```

```bash
python src/enrich.py download
```

```bash
python src/build_nb.py 03_enrichment 04_routes_full_data 05_direct_vs_onestop 06_model_validation 07_recommendations 08_infrastructure_and_layovers
```

Preview the website locally, then open http://localhost:8080:

```bash
python -m http.server 8080 --directory web
```

Deploy the website to Vercel (needs the Vercel CLI signed in):

```bash
python web/deploy.py
```

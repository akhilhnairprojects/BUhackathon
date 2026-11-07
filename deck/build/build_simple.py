"""Build the simplified deck on the 'White and Blue Modern Aviation' template.

    python deck/build/build_simple.py "<template.pptx>" deck/Arrive_On_Time_Simple.pptx

Keeps the template's own slides (fonts, logo, photos, dots), rewrites their text, swaps photos for
our charts where a chart is the point, and reorders: title, executive summary, introduction, four
findings, recommendations, implementation, website, limitations, thank you, three appendix slides.
"""
import copy
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from pptx.dml.color import RGBColor
import io, re, zipfile

PAPER, INK, BRICK, RULE = "F5F2EC", "17150F", "B1372B", "D8D2C4"

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "outputs" / "figures"
CH = FIG / "deck"            # charts recoloured to the app palette (deck/build/recolor_charts.py)
TEAM = "[Team name]"
URL = "trip-risk-checker.vercel.app"

src, out = Path(sys.argv[1]), Path(sys.argv[2])
prs = Presentation(str(src))
slides = list(prs.slides)                     # template order, 1-based in comments below


def shape(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(name)


def set_text(sh, text, size=None, bold_lead=None):
    """Replace a text box's content, keeping the first run's formatting. Paragraphs split on \\n.
    bold_lead: text placed in a bold run in front of the first paragraph (e.g. a label)."""
    tf = sh.text_frame
    p0 = tf.paragraphs[0]
    run0 = p0.runs[0]
    rpr = copy.deepcopy(run0._r.find("{http://schemas.openxmlformats.org/drawingml/2006/main}rPr"))
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    for r in list(p0.runs)[1:]:
        r._r.getparent().remove(r._r)
    lines = text.split("\n")
    run0.text = lines[0]
    if size:
        run0.font.size = Pt(size)
        rpr = copy.deepcopy(run0._r.find("{http://schemas.openxmlformats.org/drawingml/2006/main}rPr"))
    if bold_lead:
        lead = copy.deepcopy(run0._r)
        lead.find("{http://schemas.openxmlformats.org/drawingml/2006/main}t").text = bold_lead
        lead.find("{http://schemas.openxmlformats.org/drawingml/2006/main}rPr").set("b", "1")
        run0._r.addprevious(lead)
    for line in lines[1:]:
        p = copy.deepcopy(p0._p)
        for r in p.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}r")[1:]:
            p.remove(r)
        r = p.find("{http://schemas.openxmlformats.org/drawingml/2006/main}r")
        r.find("{http://schemas.openxmlformats.org/drawingml/2006/main}t").text = line
        if rpr is not None:
            r.replace(r.find("{http://schemas.openxmlformats.org/drawingml/2006/main}rPr"), copy.deepcopy(rpr))
        p0._p.getparent().append(p)


def remove(sh):
    sh._element.getparent().remove(sh._element)


def swap_image(slide, group_name, img, align="left", width=None):
    """Replace the template photo (a picture inside a group) with img, fitted inside the group's box."""
    g = shape(slide, group_name)
    x, y, w, h = g.left, g.top, g.width, g.height
    if width:
        w, h = Inches(width), Inches(width * 2)
    remove(g)
    iw, ih = Image.open(img).size
    s = min(w / iw, h / ih)
    nw, nh = int(iw * s), int(ih * s)
    nx = x if align == "left" else x + w - nw
    pic = slide.shapes.add_picture(str(img), nx, y, nw, nh)
    pic.name = "Chart"
    return pic


def clear(slide, keep):
    """Drop every shape except the logo, the dots and the named ones."""
    for sh in list(slide.shapes):
        if sh.name not in {"Freeform 2", "Group 3", *keep}:
            remove(sh)


def clone(slide, proto, x, y, w, h, text, bold_lead=None, size=None):
    """A copy of a template text box (so the font stays the template's), placed and filled."""
    el = copy.deepcopy(proto._element)
    el.nvSpPr.cNvPr.id = max(sh.shape_id for sh in slide.shapes) + 1
    slide.shapes._spTree.append(el)
    sh = slide.shapes[-1]
    sh.left, sh.top, sh.width, sh.height = Inches(x), Inches(y), Inches(w), Inches(h)
    sh.text_frame.word_wrap = True
    set_text(sh, text, size=size, bold_lead=bold_lead)
    if bold_lead:                     # the label in the app's brick, like the subheads elsewhere in the deck
        sh.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string(BRICK)
    return sh


def grid(slide, proto, items, cols=2, x0=1.12, y0=4.95, w=8.3, h=1.75, gx=0.6, gy=0.1, size=12):
    for i, (lead, body) in enumerate(items):
        r, c = divmod(i, cols)
        clone(slide, proto, x0 + c * (w + gx), y0 + r * (h + gy), w, h, body, bold_lead=lead + " ", size=size)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def crop(img, ratio, name):
    """Crop the top of a screenshot to the given width/height ratio (for the wide strip on the implementation slide)."""
    im = Image.open(img)
    w, h = im.size
    nh = int(w / ratio)
    outp = FIG / name
    im.crop((0, 0, w, min(nh, h))).save(outp)
    return outp


# ---------------------------------------------------------------- 1 · title (template slide 1)
s = slides[0]
set_text(shape(s, "TextBox 4"), "Arrive on time,", size=88)
tb5 = shape(s, "TextBox 5"); r = tb5.text_frame.paragraphs[0].runs; r[0].text = "arrive"; r[1].text = " ready"
for x in r: x.font.size = Pt(88)
shape(s, "TextBox 13").width = Inches(4.5)
set_text(shape(s, "TextBox 12"), "A data-driven travel policy for a company whose people fly constantly.")
set_text(shape(s, "TextBox 13"), f"{TEAM} · Questrom MSBA")
notes(s, "Who we are and the ask in one sentence: cut the chance that a traveler misses a meeting, without blowing up cost or convenience. "
         "We looked at every US domestic flight of ten airlines for a full year, 6.4 million flights, plus the daily weather at both ends.")

# ---------------------------------------------------------------- 2 · executive summary (template slide 4)
s = slides[3]
t = shape(s, "TextBox 15"); t.width = Inches(10)
set_text(t, "Executive summary")
proto = shape(s, "TextBox 16")
clear(s, {"TextBox 15", "Group 13", "AutoShape 20"})
grid(s, proto, [
    ("The problem.", "One flight in ten gets the traveler there an hour late or not at all (9.7%); 23.5% are disrupted. Most flights land early; the cost sits in that tail, and the tail is predictable."),
    ("What we found.", "Morning departures are a third as likely to be disrupted as evening ones. The right airline on a route is worth 5 to 7 points. Bad weather nearly doubles the risk and is foreseeable by month and airport. A stop lifts the chance of an hour-late arrival from 9% to 16%."),
    ("What we recommend.", "Four defaults in the booking tool, not bans: morning preference for time-critical trips, nonstop first with 90-minute layovers via approved hubs, the preferred airline by route, and a weather buffer in risky months."),
    ("The impact.", "Hour-late trips cut by about half, from 96 to roughly 50 per 1,000, and $13k to $76k saved per 1,000 trips depending on what an hour and a meeting are worth. The ask: a one-quarter pilot in two business units against a control group."),
], cols=2, x0=1.12, y0=5.0, w=6.0, h=2.6, gx=0.5, gy=0.2, size=15)
notes(s, "The whole story on one slide: the size of the problem, the four findings, the four defaults and what they are worth. Everything after this is evidence.")

# ---------------------------------------------------------------- 3 · introduction (template slide 2)
s = slides[1]
set_text(shape(s, "TextBox 3"), "One flight in ten gets you there an hour late")
set_text(shape(s, "TextBox 28"), "What we did")
set_text(shape(s, "TextBox 27"), "We took every US domestic flight of ten airlines for a full year, 6.4 million flights, added the weather at both airports, "
         "and asked one question: which choices get a traveler to the meeting on time?")
set_text(shape(s, "TextBox 16"), "23.5% of flights are disrupted (15+ min late, cancelled or diverted). 9.7% arrive an hour late or not at all.")
remove(shape(s, "TextBox 26")); remove(shape(s, "Group 20")); remove(shape(s, "Freeform 24"))
set_text(shape(s, "TextBox 25"), "Most flights land early. The cost sits in the tail.")
notes(s, "Most flights land early; the median flight is six minutes early. The problem is the tail: the 10% that arrive an hour late, "
         "are cancelled or diverted. That tail is what costs a meeting, and it is predictable.")

# ---------------------------------------------------------------- 3 · finding 1 (template slide 3)
s = slides[2]
set_text(shape(s, "TextBox 15"), "Finding 1 · Fly in the morning")
set_text(shape(s, "TextBox 19"), "What we found")
set_text(shape(s, "TextBox 17"), "A 7 p.m. departure is three times as likely to be disrupted as a 6 a.m. one. Delays snowball: every departure inherits the lateness of the aircraft before it.")
set_text(shape(s, "TextBox 20"), "What it means")
set_text(shape(s, "TextBox 18"), "Leaving between 7 and 10 a.m. keeps nearly all the benefit with no dawn start: 5.6% an hour late, against 14 to 15% in the evening.")
swap_image(s, "Group 13", CH / "02_disruption_by_hour.png")
set_text(shape(s, "TextBox 16"), "Chance of disruption by scheduled departure hour, all flights.")
remove(shape(s, "TextBox 30")); remove(shape(s, "Group 24")); remove(shape(s, "Freeform 28"))
set_text(shape(s, "TextBox 29"), "Same airline, same route: evening is worse on 98% of routes.")
notes(s, "This is the most reliable pattern in the data and the cheapest to act on. It is not a route-mix effect: on the same airline and route, "
         "evening is worse than morning on 98% of routes, and the morning advantage holds in every month.")

# ---------------------------------------------------------------- 4 · finding 2 (template slide 9)
s = slides[8]
t = shape(s, "TextBox 15"); t.height = Inches(1.56)
set_text(t, "Finding 2 · Pick the airline by route")
set_text(shape(s, "TextBox 20"), "Raw rankings mislead: an airline that flies mostly in calm western skies looks better than it is. We compared airlines only on the same route, month and time of day.")
set_text(shape(s, "TextBox 18"), "What we found")
set_text(shape(s, "TextBox 16"), "Like for like, United runs about 5 points safer than its rivals on shared routes; PSA and Alaska run 6 to 7 points worse.")
set_text(shape(s, "TextBox 19"), "What it means")
set_text(shape(s, "TextBox 17"), "On the 43% of trips where two or more airlines fly the route, the gap between best and worst is typically 7 points, and up to 22 on Boston to Chicago. Prefer by route, not by brand.")
swap_image(s, "Group 13", CH / "14_carrier_route_adjusted.png", align="right")
notes(s, "Each airline is compared only with the other airlines flying the same route in the same month and time of day. Regional airlines are shown as operated.")

# ---------------------------------------------------------------- 5 · finding 3 (template slide 5)
s = slides[4]
set_text(shape(s, "TextBox 15"), "Finding 3 · Weather is foreseeable")
set_text(shape(s, "TextBox 20"), "Flights touching an airport with bad weather are 1.8x as likely to be disrupted.")
set_text(shape(s, "TextBox 18"), "What we found")
set_text(shape(s, "TextBox 16"), "33% of flights are disrupted on adverse-weather days against 18% on clear days. Snow and freezing rain roughly double the risk. The airlines' own weather code captures only a sliver of this.")
set_text(shape(s, "TextBox 19"), "What it means")
set_text(shape(s, "TextBox 17"), "June, July and December are the risky months, and each airport has its own pattern. Book around it, and watch the forecast one to three days out.")
swap_image(s, "Group 13", CH / "10_weather_conditions.png")
notes(s, "Every flight was joined to the daily weather record at both ends. The point is not that airlines are wrong; their weather code is defined narrowly. "
         "Weather risk is foreseeable by season and airport at booking time, and from the forecast a few days out.")

# ---------------------------------------------------------------- 6 · finding 4 (template slide 8)
s = slides[7]
set_text(shape(s, "TextBox 15"), "Finding 4 · A stop is a gamble")
set_text(shape(s, "TextBox 21"), "What we found")
set_text(shape(s, "TextBox 17"), "Nonstop trips arrive an hour late 9% of the time. The same city pairs with one stop: 16%. Overnight strandings triple.")
set_text(shape(s, "TextBox 20"), "The hub decides the odds")
set_text(shape(s, "TextBox 16"), "Connecting through Salt Lake City, Los Angeles or Seattle: about 10% an hour late. Through Washington National, Dallas or LaGuardia: over 20%.")
set_text(shape(s, "TextBox 23"), "Layover length matters")
set_text(shape(s, "TextBox 19"), "Raising the minimum layover from 45 to 90 minutes cuts missed connections from 51 to 23 per 1,000 connecting trips.")
set_text(shape(s, "TextBox 22"), "What it means")
set_text(shape(s, "TextBox 18"), "A one-stop needs to be about $400 cheaper one way to pay for the traveler's extra time, before counting a missed meeting. Fly nonstop when you can.")
swap_image(s, "Group 13", CH / "17_nonstop_vs_onestop.png", align="right")
notes(s, "Built from 3.4 million one-stop itineraries constructed from real flight pairs on 1,730 city pairs. Simulated trips, not tickets sold. "
         "Hub ranking and winter fragility are on the Hubs page of the website.")

# ---------------------------------------------------------------- 7 · recommendations and impact (template slide 7)
s = slides[6]
set_text(shape(s, "TextBox 16"), "What we recommend")
set_text(shape(s, "TextBox 17"), "Four defaults in the booking tool, not bans. Modeled on the same routes and volumes as flown; per 1,000 trips. "
         "Together they halve the chance of arriving an hour late and save $13k to $76k per 1,000 trips, depending on what an hour and a missed meeting are worth.")
swap_image(s, "Group 14", CH / "23_policy_impact.png", align="right")
tbl = shape(s, "Table 13").table
rows = [["Rule", "What changes", "Impact per 1,000 trips"],
        ["1 · Morning preference", "Time-critical trips default to 7 to 10 a.m. departures", "Hour-late trips 96 to 55 (down 43%)"],
        ["2 · Nonstop first", "Connect only with 90+ minutes via approved hubs", "Missed connections 51 to 23"],
        ["3 · Airline by route", "Preferred airline on routes with a real choice", "Down 15% on covered routes; 55% with rule 1"],
        ["4 · Weather buffer", "Day-before travel in risky months; rebook on a bad forecast", "Afternoon trips in summer and winter 16% to 7%"]]
for r, row in enumerate(rows):
    for c, txt in enumerate(row):
        cell = tbl.cell(r, c)
        set_text(cell, txt)
notes(s, "Everything is a default or a soft warning in the booking tool, not a ban. Rule 1 alone is worth about $44k per 1,000 trips at mid assumptions. "
         "Rule 4 is the lowest-confidence rule, because actual weather stands in for a forecast.")

# ---------------------------------------------------------------- 8 · implementation (template slide 12)
s = slides[11]
set_text(shape(s, "TextBox 15"), "Implementation")
strip = crop(FIG / "app_tab1.png", 11.45 / 2.31, "app_strip.png")
swap_image(s, "Group 13", strip)
set_text(shape(s, "TextBox 20"), "Booking tool")
set_text(shape(s, "TextBox 19"), "Default sort: 7 to 10 a.m. nonstops on the preferred airline. Soft warnings on evening departures, the last flight of the day, tight connections and risky hubs. Override with a reason code.")
set_text(shape(s, "TextBox 18"), "A weather watch 72 hours out for trips through fragile hubs, with proactive rebooking to earlier flights.", bold_lead="Travel desk. ")
set_text(shape(s, "TextBox 17"), "Two business units for one quarter against a control group. Track hour-late trips, strandings, compliance and fare cost.", bold_lead="Pilot. ")
set_text(shape(s, "TextBox 16"), "Preferred-airline and approved-hub lists refreshed every quarter from the public flight data. The pipeline is built.", bold_lead="Keep it current. ")
remove(shape(s, "TextBox 30")); remove(shape(s, "Group 24")); remove(shape(s, "Freeform 28"))
set_text(shape(s, "TextBox 29"), "Light touch: defaults in the tool you already use.")
notes(s, "Implementation is deliberately light: defaults and warnings in the booking tool the company already uses, plus a travel-desk process. "
         "The pilot gives a before-and-after against a control group within one quarter.")

# ---------------------------------------------------------------- 9 · next steps: the website (template slide 11)
s = slides[10]
set_text(shape(s, "TextBox 17"), "Next step · The website")
swap_image(s, "Group 15", FIG / "app_tab1.png", align="right")
swap_image(s, "Group 13", FIG / "app_tab2.png", width=6.4)
set_text(shape(s, "TextBox 19"), "Pick where you start, where you need to be and the date. The Trip Risk Checker ranks every nonstop and same-airline connection by the chance of arriving an hour late.", bold_lead="Check a trip. ")
set_text(shape(s, "TextBox 20"), "Put your own value on the meeting, an hour and a night stranded; see what each option is expected to cost and how much a safer flight is worth paying for.", bold_lead="Cost of missing. ")
set_text(shape(s, "TextBox 18"), f"Live at {URL}. Hubs & airports page maps disruption, weather exposure and winter fragility.")
notes(s, "This is how the travel desk and travelers would use the analysis. It answers any route, date or constraint live, and it is our Q&A tool.")

# ---------------------------------------------------------------- 11 · limitations (template slide 14)
s = slides[13]
t = shape(s, "TextBox 23"); t.width = Inches(10)
set_text(t, "Limitations")
proto = shape(s, "TextBox 27")
clear(s, {"TextBox 23"})
grid(s, proto, [
    ("One year of data.", "Calendar 2025 only, so no year-to-year variation. Newark's spring runway closure and air-traffic-control trouble are in the data and treated as a case study, not a trend."),
    ("Flights, not tickets.", "One-stop trips are constructed from real same-day flight pairs, not observed itineraries. SkyWest and Republic flights are assigned to an airline brand by a stated heuristic."),
    ("Hindsight stands in for a forecast.", "The weather rule uses the weather that actually happened. A real one-to-three-day forecast will catch less, so this is the lowest-confidence rule."),
    ("No fares.", "The data has no prices. Break-even figures say what a safer flight is worth paying for, not what it costs; the pilot measures the real fare premium."),
    ("Disruption is noisy.", "At booking time the model reaches an AUC of 0.67 to 0.68. It is calibrated and ranks choices well, which is what a policy needs, but it cannot call a single flight."),
    ("Assumptions are yours to set.", "Meeting value, hourly value and the cost of a night stranded drive the dollar figures; the website lets you change them. Route cells under 15 flights are hidden and thin cells are shrunk toward the route mean."),
], cols=2, x0=1.12, y0=4.6, w=8.3, h=1.85, gx=0.6, gy=0.1, size=14)
notes(s, "Say these before anyone asks. None of them changes the direction of the recommendations; they change how confident we are in the size of each effect, and the pilot is how we find out.")

# ---------------------------------------------------------------- 11 · thank you (template slide 15)
s = slides[14]
set_text(shape(s, "TextBox 12"), TEAM)
set_text(shape(s, "TextBox 13"), "Questrom MSBA · Chart Champ Datathon")
set_text(shape(s, "TextBox 26"), URL)
set_text(shape(s, "TextBox 27"), "November 2026")
set_text(shape(s, "TextBox 11"), "Questions? The Trip Risk Checker is live for any route, date or constraint you want to test.")
set_text(shape(s, "TextBox 14"), "Try it live")
set_text(shape(s, "TextBox 15"), f"Created by: {TEAM}")

# ---------------------------------------------------------------- appendix 1 · data and definitions (template slide 6)
s = slides[5]
t = shape(s, "TextBox 15"); t.width = Inches(12)
set_text(t, "Appendix 1 · Data and definitions")
proto = shape(s, "TextBox 16")
clear(s, {"TextBox 15"})
grid(s, proto, [
    ("Flight data.", "BTS On-Time Performance, calendar 2025, ten reporting airlines, 6.4 million US domestic flights from the full monthly files, plus the 200k-flight student sample used for exploration and the risk model."),
    ("Weather.", "NOAA GHCN-Daily station records matched to 324 of 326 airports. Daily flags for snow, freezing precipitation, heavy rain, thunderstorms, heavy fog and high wind; adverse = any of them. Climatology = share of such days by airport and month."),
    ("Airports.", "OurAirports for coordinates and runways, FAA hub tiers, and Port Authority and FAA notices for the Newark runway closure (15 April to 2 June 2025)."),
    ("Outcomes.", "Disrupted = arrived 15+ minutes late, cancelled or diverted. Hour late (severe) = 60+ minutes late, cancelled or diverted. Traveler burden = departure before 6 a.m., landing 11 p.m. to 4 a.m., a two-hour-plus wait, or a night stranded."),
    ("Trip-level accounting.", "In trip tables a cancelled traveler is rebooked on the next completed flight of the same airline brand and counted at that arrival; trip delay is capped at 24 hours. Groups under 100 flights are hidden; rates carry 95% Wilson intervals."),
    ("Cleaning.", "One function (src/prep.py) cleans the sample and the full file identically: outcome flags, local departure hour and band, season, holiday window, route key, carrier names. The cleaning log sits in outputs/tables."),
], cols=2, x0=1.12, y0=4.6, w=8.3, h=1.85, gx=0.6, gy=0.1, size=14)

# ---------------------------------------------------------------- appendix 2 · models (template slide 10)
s = slides[9]
t = shape(s, "TextBox 15"); t.width = Inches(12)
set_text(t, "Appendix 2 · Models")
proto = shape(s, "TextBox 17")
clear(s, {"TextBox 15"})
grid(s, proto, [
    ("Booking-time risk model.", "Logistic regression and histogram gradient boosting (scikit-learn) on carrier, origin, destination, month, weekday, departure hour, distance, holiday window and the airports' weather climatology. No delay or cause fields, no tail numbers."),
    ("Validation.", "Five-fold cross-validation grouped by flight date, so a storm day never sits in both folds. Disruption: AUC 0.67, Brier 0.168 against a 23.5% base rate; the riskiest tenth of bookings is disrupted 46% of the time. Hour late: AUC 0.68, Brier 0.084. The day's actual weather lifts AUC to 0.71."),
    ("Adjusted effects.", "Odds ratios from the logistic model (reference Delta, 8 a.m., September, Tuesday) confirm that hour, carrier, month and airport each matter after controlling for the others. Airlines are also compared only within the same route, month and time band."),
    ("Website route cells.", "For each route: carrier × departure band × season, with the hour-late rate, disruption, cancellations, p95 delay and scheduled time. Cells under 15 flights are hidden; thin cells are shrunk toward the route mean. Weekday factor = national hour-late rate on that weekday ÷ all days (Sunday 1.27, Tuesday 0.81)."),
    ("Connecting options.", "Same brand, 90-minute layover, second leg in the band the traveler would actually depart in; detours over 1.5× the direct distance dropped. Risk = the larger of (either leg an hour late) and (the hub's simulated one-stop rate × 0.907 × √ leg reliability), × weekday factor."),
    ("Missed connections.", "Hub rate at a 60-minute layover × 0.59 (the 90-minute ratio from the simulation) × first-leg reliability, bounded between 1% and 50%. Shown as an estimate, not an observation."),
], cols=2, x0=1.12, y0=4.6, w=8.3, h=1.85, gx=0.6, gy=0.1, size=14)

# ---------------------------------------------------------------- appendix 3 · simulations, costs and tools (template slide 13)
s = slides[12]
t = shape(s, "TextBox 23"); t.width = Inches(12)
set_text(t, "Appendix 3 · Simulations, costs and tools")
proto = shape(s, "TextBox 26")
clear(s, {"TextBox 23"})
grid(s, proto, [
    ("Connection simulation.", "3.4 million one-stop itineraries built from real same-day flight pairs on 1,730 city pairs (src/connections.py). Booked: the first same-brand onward flight at least L minutes after the scheduled arrival, L = 45, 60, 90 or 120. Realised: the connection holds if the traveler is at the hub 30 minutes before the onward flight actually leaves; otherwise the next completed flight."),
    ("Policy simulation.", "Each rule is replayed on the full 2025 file: within every route, the flights that satisfy the rule stand in for those actually taken, weighted by real volume. Outcomes per 1,000 trips: hour late, delay hours, two-hour waits, dawn departures, late-night landings, nights stranded."),
    ("Cost model.", "Expected cost per trip = chance of an hour late × meeting value + delay hours × hourly value + nights stranded × night cost. Notebook defaults: $500 meeting, $50 / $100 / $150 per hour, $300 per night. Break-even fare for a one-stop = extra hours × hourly value, plus extra risk × meeting value."),
    ("Website.", "Static Preact app on Vercel: Check a trip (route finder with connections, date and departure band), Cost of missing (your own values), Hubs and airports (ranking, table, map). Two decimals at trip-risk-checker.vercel.app; whole numbers at trip-risk-checker-simple.vercel.app."),
    ("Tools.", "Python: pandas, NumPy, pyarrow, scikit-learn, statsmodels, matplotlib, seaborn; Jupyter notebooks built from scripts; Preact and htm, d3-geo and TopoJSON for the map; Vercel hosting; HyperFrames and Playwright for the walkthrough video."),
    ("Notebooks.", "01 cleaning · 02 exploratory analysis · 03 weather enrichment · 04 route-level detail on the full file · 05 nonstop vs one-stop and hubs · 06 risk model and validation · 07 policy simulation and costs · 08 Newark case study and layovers. Every chart is in outputs/figures and every number in outputs/tables."),
], cols=2, x0=1.12, y0=4.6, w=8.3, h=1.85, gx=0.6, gy=0.1, size=13)

# subheads: the template's 20pt bold labels are sized for one short word; widen them so ours stay on one line
for sl in slides:
    for sh in sl.shapes:
        if sh.has_text_frame and sh.text_frame.paragraphs and sh.text_frame.paragraphs[0].runs:
            f = sh.text_frame.paragraphs[0].runs[0].font
            if f.size and f.size.pt == 20 and f.bold:
                sh.width = Inches(5.4)
                for r in sh.text_frame.paragraphs[0].runs:
                    r.font.color.rgb = RGBColor.from_string(BRICK)
    # the app's paper ground on every slide
    sl.background.fill.solid()
    sl.background.fill.fore_color.rgb = RGBColor.from_string(PAPER)

# table: ink header, hairline rules, like the app's tables
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
for sl in slides:
    for sh in sl.shapes:
        if sh.has_table:
            for r, row in enumerate(sh.table.rows):
                for cell in row.cells:
                    if r == 0:
                        cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor.from_string(INK)
                    for ln in cell._tc.tcPr:
                        if ln.tag.startswith(A + "ln"):
                            for c in ln.iter(A + "srgbClr"):
                                c.set("val", RULE)

# ---------------------------------------------------------------- order and deletions
order = [0, 3, 1, 2, 8, 4, 7, 6, 11, 10, 13, 14, 5, 9, 12]
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
keep = [ids[i] for i in order]
for sid in ids:
    if sid not in keep:
        prs.part.drop_rel(sid.rId)
    sldIdLst.remove(sid)
for sid in keep:
    sldIdLst.append(sid)
buf = io.BytesIO()
prs.save(buf)

# ---------------------------------------------------------------- app palette on the package itself
# template colours are literal: black text and lines -> ink, the blue accent -> brick, table header
# text -> paper; the blue logo and the cut-out 747 (white ground) are re-coloured as images.
def tint(png_bytes, hex_rgb):
    im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    a = im.getchannel("A")
    solid = Image.new("RGBA", im.size, tuple(int(hex_rgb[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    solid.putalpha(a)
    o = io.BytesIO(); solid.save(o, "PNG"); return o.getvalue()

src_zip = zipfile.ZipFile(buf)
out_zip = zipfile.ZipFile(str(out), "w", zipfile.ZIP_DEFLATED)
for item in src_zip.infolist():
    data = src_zip.read(item.filename)
    if item.filename.startswith("ppt/slides/slide") and item.filename.endswith(".xml"):
        t = data.decode("utf-8")
        t = re.sub(r'srgbClr val="(000000|191919)"', f'srgbClr val="{INK}"', t)
        t = re.sub(r'srgbClr val="5196[Bb][Aa]"', f'srgbClr val="{BRICK}"', t)
        t = t.replace('srgbClr val="FFFFFF"', f'srgbClr val="{PAPER}"')
        data = t.encode("utf-8")
    elif item.filename == "ppt/media/image2.png":
        data = tint(data, BRICK)
    elif item.filename == "ppt/media/image3.svg":
        data = data.replace(b'fill="#5196ba"', b'fill="#' + BRICK.lower().encode() + b'"')
    elif item.filename == "ppt/media/image1.jpeg" and (CH / "plane_paper.png").exists():
        o = io.BytesIO(); Image.open(CH / "plane_paper.png").convert("RGB").save(o, "JPEG", quality=94); data = o.getvalue()
    out_zip.writestr(item, data)
out_zip.close()
print(f"wrote {out} with {len(keep)} slides")

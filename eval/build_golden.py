"""Builds eval/golden_set.json. Edit the cases here, then run: python eval/build_golden.py"""
import json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
NS = "NOT_SPECIFIED"

def case(id, title, tests, verdict, required, forbidden, fields, text, note=""):
    return dict(id=id, title=title, tests=tests, submission=text.strip("\n"),
                expected=dict(verdict=verdict, rulesRequired=required, rulesForbidden=forbidden, fields=fields),
                note=note)

D, R, A = "Decline", "Refer to Underwriter", "In Appetite"
ALL_D = ["D1", "D2", "D3", "D4"]
ALL_R = ["R1", "R2", "R3", "R4", "R5"]

# G01-G03 are the three submissions shown on the site; their text is read from index.html.
html = (ROOT.parent / "index.html").read_text(encoding="utf-8")
def sample(sid):
    m = re.search(r'\{id:"%s",label:"[^"]+",text:\n`(.*?)`\}' % sid, html, re.S)
    return m.group(1)

CASES = [
case("G01", "Restaurant, limits and alcohol not stated", "R4 material gap", R, ["R4"], ALL_D,
     {"namedInsured": ["copper skillet"], "location": ["tempe"], "effectiveDate": ["11/01/2026"],
      "glLimits": NS, "priorCarrier": NS}, sample("rest")),
case("G02", "HVAC contractor, three losses and an open claim", "D2 and D3 together; D4 must not fire", D, ["D2", "D3"], ["D4"],
     {"namedInsured": ["summit air"], "location": ["mesa"], "glLimits": ["1m/2m"], "effectiveDate": ["12/01"]}, sample("hvac")),
case("G03", "Tech office, clean", "A1 clean risk", A, ["A1"], ALL_D + ALL_R,
     {"namedInsured": ["larkfield"], "location": ["phoenix"], "glLimits": ["1m/2m"], "effectiveDate": ["11/15"]}, sample("office")),

case("G04", "Cannabis dispensary presented as retail", "D1 excluded class", D, ["D1"], [],
     {"namedInsured": ["green mesa"], "effectiveDate": ["12/01/2026"], "glLimits": ["1m/2m"]}, """
From: Tom Avery <tavery@westgatebrokerage.com>
Subject: BOP — Green Mesa Wellness LLC (retail)

Retail account for you. Green Mesa Wellness LLC operates a state-licensed
recreational cannabis dispensary at a strip-center storefront in Phoenix, AZ.

- BOP: GL $1M/$2M + contents
- BPP $240,000 (leased space), annual sales ~$3.8M
- Operating since 2021, 14 employees
- No losses since inception, loss runs attached
- Central-station alarm, vault for inventory

Effective 12/01/2026. Standard retail risk in my view. Appetite?
"""),
case("G05", "Adult entertainment venue", "D1 excluded class", D, ["D1"], [],
     {"namedInsured": ["velvet room"], "effectiveDate": ["01/01/2027"]}, """
From: Renee Castillo <rcastillo@sonoranrisk.com>
Subject: GL + liquor — Velvet Room Entertainment LLC

Submission for Velvet Room Entertainment LLC, Scottsdale AZ. Gentlemen's
club with live adult entertainment and a full bar, open 6 nights.

- GL $1M/$2M plus liquor liability
- Annual receipts ~$2.6M, liquor about 55% of sales
- In business since 2015, 32 employees plus contracted performers
- No claims in the last five years, loss runs attached

Effective 01/01/2027. Incumbent is exiting the class. Can you look?
"""),
case("G06", "Iron foundry", "D1 excluded class", D, ["D1"], [],
     {"namedInsured": ["ironbridge"], "location": ["tucson"], "effectiveDate": ["11/15/2026"]}, """
From: Paul Demetriou <pdemetriou@cactuscommercial.com>
Subject: Package — Ironbridge Castings Inc.

Ironbridge Castings Inc., Tucson AZ. Grey-iron foundry: melts, pours and
machines castings for mining and heavy-equipment customers. Two furnaces,
85 employees across two shifts.

- Property + GL $1M/$2M
- Building $4,200,000, equipment and stock $3,100,000
- Established 1998
- One loss in the last three years: 2025 forklift damage to a customer's
  truck, $18,000 paid, closed

Effective 11/15/2026.
"""),
case("G07", "Office with one large closed loss", "D4 single loss over $100k; D3 must not fire", D, ["D4"], ["D2", "D3"],
     {"namedInsured": ["halden"], "location": ["chandler"], "effectiveDate": ["12/15/2026"], "glLimits": ["1m/2m"]}, """
From: Lisa Monroe <lmonroe@horizonbrokers.com>
Subject: Package — Halden & Pryce CPAs PLLC

Halden & Pryce CPAs PLLC, accounting office in Chandler AZ, 22 staff.

- Package: BPP $310,000 (leased suite) + GL $1M/$2M
- Annual revenue ~$4.1M
- In business since 2011
- Loss runs: one claim. March 2025, sprinkler line burst over the server
  room, $140,000 paid, closed. Nothing else in five years.

Effective 12/15/2026. Good account apart from the one water loss.
"""),
case("G08", "Gift shop with three small losses", "D3 frequency; D2 and D4 must not fire", D, ["D3"], ["D2", "D4"],
     {"namedInsured": ["juniper lane"], "location": ["flagstaff"], "effectiveDate": ["11/20/2026"]}, """
From: Dana Ruiz <druiz@horizonbrokers.com>
Subject: BOP — Juniper Lane Gifts LLC

Juniper Lane Gifts LLC, gift and home-decor shop in downtown Flagstaff AZ.

- BOP: BPP $95,000 (leased), GL $1M/$2M
- Sales ~$620,000, 5 employees
- Open since 2014
- Loss runs, all closed:
    2024 customer slip-and-fall, $4,200
    2025 theft of stock, $2,900
    2026 display shelf fell on a customer, $7,800

Effective 11/20/2026. Small dollars on all three.
"""),
case("G09", "Restaurant with one open litigated claim", "D2 open claim; D3 and D4 must not fire", D, ["D2"], ["D3", "D4"],
     {"namedInsured": ["casa brasa"], "location": ["glendale"], "effectiveDate": ["12/01/2026"], "glLimits": ["1m/2m"]}, """
From: Marcus Bell <mbell@keystonecommercial.com>
Subject: BOP — Casa Brasa Grill LLC

Casa Brasa Grill LLC, full-service restaurant in Glendale AZ. Beer and
wine only, about 8% of sales.

- BOP: GL $1M/$2M, BPP $160,000 (leased)
- Sales ~$1.1M, 16 employees
- Operating since 2018
- One claim on the loss runs: 2025 alleged food-borne illness. Suit has
  been filed, claim is open, reserved at $15,000.

Effective 12/01/2026.
"""),
case("G10", "Painter, two losses, one open", "D2 must win over R3", D, ["D2"], ["D3", "D4"],
     {"namedInsured": ["redrock painting"], "location": ["sedona"], "effectiveDate": ["01/15/2027"]}, """
From: Priya Nair <pnair@anchorrisk.com>
Subject: GL — Redrock Painting Co LLC

Redrock Painting Co LLC, residential and light-commercial painting
contractor, Sedona AZ.

- GL only, $1M/$2M occurrence
- Payroll ~$380,000, 7 painters
- In business since 2016, no work above 3 stories
- Loss runs, last three years:
    2024 overspray on parked vehicles, $9,500 paid, closed
    2026 ladder fell and injured a homeowner, OPEN, reserved $40,000

Effective 01/15/2027.
"""),
case("G11", "Carpenter, four losses and limits not stated", "Decline must win over missing information (AC-4)", D, ["D3"], ["D2", "D4"],
     {"namedInsured": ["bolt & beam", "bolt and beam"], "location": ["peoria"], "glLimits": NS, "effectiveDate": ["12/10/2026"]}, """
From: Tom Avery <tavery@westgatebrokerage.com>
Subject: GL — Bolt & Beam Carpentry LLC

Bolt & Beam Carpentry LLC, finish carpentry and cabinet installation,
Peoria AZ. Need a GL quote, limits to be decided once we see pricing.

- Payroll ~$450,000, 8 carpenters
- In business since 2013
- Loss runs, last three years, all closed:
    2024 scratched flooring, $3,000
    2024 cabinet fell from wall, $5,500
    2025 water line nicked during install, $12,000
    2026 damaged countertop, $8,000

Effective 12/10/2026.
"""),
case("G12", "Apartments, one loss of exactly $100,000", "Boundary: D4 must not fire at exactly $100k", A, ["A1"], ALL_D + ["R3"],
     {"namedInsured": ["cedar court"], "location": ["tempe"], "effectiveDate": ["12/01/2026"], "glLimits": ["1m/2m"]}, """
From: Lisa Monroe <lmonroe@horizonbrokers.com>
Subject: Package — Cedar Court Apartments LLC

Cedar Court Apartments LLC, 24-unit garden apartment community, Tempe AZ.

- Property + GL $1M/$2M
- Building $3,600,000, BPP $40,000, rental income $420,000
- Owned and operated since 2012
- Loss runs: one claim. 2025 kitchen fire in unit 11, total incurred
  $100,000, closed. No other losses in five years.

Effective 12/01/2026. Expiring with the incumbent, remarketing on price.
"""),
case("G13", "Office, one loss just over $100,000", "D4 fires at $100,500", D, ["D4"], ["D2", "D3"],
     {"namedInsured": ["marlowe"], "location": ["gilbert"], "effectiveDate": ["11/30/2026"]}, """
From: Renee Castillo <rcastillo@sonoranrisk.com>
Subject: Package — Marlowe Billing Services Inc.

Marlowe Billing Services Inc., medical billing office in Gilbert AZ.

- Package: BPP $180,000 (leased) + GL $1M/$2M
- Revenue ~$2.9M, 30 employees
- In business since 2017
- One claim on the loss runs: 2024 roof leak damaged equipment,
  $100,500 paid, closed.

Effective 11/30/2026.
"""),
case("G14", "Law firm, property values over $10M in total", "R1, needs the three values added", R, ["R1"], ALL_D,
     {"namedInsured": ["whitlock"], "location": ["phoenix"], "effectiveDate": ["01/01/2027"], "glLimits": ["1m/2m"]}, """
From: Paul Demetriou <pdemetriou@cactuscommercial.com>
Subject: Package — Whitlock & Sayre LLP

Whitlock & Sayre LLP, law firm, owns and occupies its office building in
midtown Phoenix AZ. 70 attorneys and staff.

- Property + GL $1M/$2M
- Building $9,500,000
- BPP $800,000
- Business income $1,200,000
- Established 1994
- No losses in the last five years, loss runs attached

Effective 01/01/2027.
"""),
case("G15", "Architects, property values of exactly $10M", "Boundary: R1 must not fire at exactly $10M", A, ["A1"], ALL_D + ["R1"],
     {"namedInsured": ["ostrander"], "location": ["scottsdale"], "effectiveDate": ["12/01/2026"]}, """
From: Dana Ruiz <druiz@horizonbrokers.com>
Subject: Package — Ostrander Architecture Group Inc.

Ostrander Architecture Group Inc., architecture office, owns its building
in Scottsdale AZ. 45 staff.

- Property + GL $1M/$2M
- Building $8,500,000
- BPP $1,000,000
- Business income $500,000
- In business since 2003
- No losses in the last five years, loss runs attached

Effective 12/01/2026. Professional liability is placed elsewhere.
"""),
case("G16", "Boutique open 15 months", "R2 new venture", R, ["R2"], ALL_D,
     {"namedInsured": ["thistle"], "location": ["tucson"], "effectiveDate": ["11/15/2026"]}, """
From: Priya Nair <pnair@anchorrisk.com>
Subject: BOP — Thistle & Thread Boutique LLC

Thistle & Thread Boutique LLC, women's clothing boutique, Tucson AZ.

- BOP: BPP $70,000 (leased), GL $1M/$2M
- Sales running ~$410,000 annualized, 3 employees
- Opened August 2025
- No losses since opening

Effective 11/15/2026.
"""),
case("G17", "Frame shop, exactly two years in business", "Boundary: R2 must not fire at exactly two years", A, ["A1"], ALL_D + ["R2"],
     {"namedInsured": ["pinyon"], "location": ["prescott"], "effectiveDate": ["12/01/2026"]}, """
From: Marcus Bell <mbell@keystonecommercial.com>
Subject: BOP — Pinyon Print & Frame LLC

Pinyon Print & Frame LLC, custom framing and print shop, Prescott AZ.

- BOP: BPP $85,000 (leased), GL $1M/$2M
- Sales ~$380,000, 4 employees
- Opened December 1, 2024, so two full years in business at inception
- No losses since opening, loss runs attached

Effective 12/01/2026.
"""),
case("G18", "Plumber with two closed losses", "R3; no decline rule should fire", R, ["R3"], ALL_D,
     {"namedInsured": ["agave plumbing"], "location": ["mesa"], "effectiveDate": ["12/05/2026"], "glLimits": ["1m/2m"]}, """
From: Tom Avery <tavery@westgatebrokerage.com>
Subject: GL — Agave Plumbing Services LLC

Agave Plumbing Services LLC, residential service and repair plumber,
Mesa AZ.

- GL only, $1M/$2M occurrence
- Payroll ~$510,000, 8 plumbers
- In business since 2012
- Loss runs, last three years, both closed:
    2024 supply line failure, $14,000
    2025 water heater install leak, $22,000

Effective 12/05/2026.
"""),
case("G19", "Apartments, unit count not stated", "R4 material gap for habitational", R, ["R4"], ALL_D,
     {"namedInsured": ["sunridge"], "location": ["yuma"], "effectiveDate": ["01/01/2027"]}, """
From: Lisa Monroe <lmonroe@horizonbrokers.com>
Subject: Package — Sunridge Villas LLC

Sunridge Villas LLC, apartment community in Yuma AZ. Two-story frame
buildings, built 1996, roofs replaced 2021.

- Property + GL $1M/$2M
- Buildings $5,800,000, BPP $35,000, rental income $690,000
- Owned since 2009
- No losses in the last five years

Effective 01/01/2027.
"""),
case("G20", "Bike shop, loss runs not yet provided", "R4 material gap: loss history", R, ["R4"], ALL_D,
     {"namedInsured": ["copperline"], "location": ["tempe"], "lossSummary": NS, "effectiveDate": ["11/25/2026"]}, """
From: Renee Castillo <rcastillo@sonoranrisk.com>
Subject: BOP — Copperline Cycles LLC

Copperline Cycles LLC, bicycle sales and repair shop, Tempe AZ.

- BOP: BPP $130,000 (leased), GL $1M/$2M
- Sales ~$900,000, 6 employees
- In business since 2019
- Loss runs have been requested from the current carrier and I will
  forward them when they arrive.

Effective 11/25/2026. Can you start on it in the meantime?
"""),
case("G21", "Consulting office, time in business not stated", "R4 material gap: years in business", R, ["R4"], ALL_D,
     {"namedInsured": ["tallgrass"], "location": ["phoenix"], "yearsInBusiness": NS, "effectiveDate": ["12/01/2026"]}, """
From: Paul Demetriou <pdemetriou@cactuscommercial.com>
Subject: Package — Tallgrass Consulting Group LLC

Tallgrass Consulting Group LLC, management consulting office, Phoenix AZ.
12 consultants.

- Package: BPP $60,000 (leased) + GL $1M/$2M
- Revenue ~$2.2M
- Loss runs attached, no claims

Effective 12/01/2026.
"""),
case("G22", "Daycare", "R5 class outside both lists", R, ["R5"], ALL_D,
     {"namedInsured": ["little saguaro"], "location": ["chandler"], "effectiveDate": ["01/01/2027"]}, """
From: Dana Ruiz <druiz@horizonbrokers.com>
Subject: BOP — Little Saguaro Learning Center LLC

Little Saguaro Learning Center LLC, daycare and preschool licensed for
60 children, Chandler AZ.

- BOP: BPP $75,000 (leased), GL $1M/$2M
- Revenue ~$780,000, 14 staff
- Operating since 2015
- No losses in the last five years, loss runs attached

Effective 01/01/2027.
"""),
case("G23", "Self-storage facility described by unit count", "R5; must not be read as habitational", R, ["R5"], ALL_D,
     {"namedInsured": ["lockhaven"], "location": ["surprise"], "effectiveDate": ["12/15/2026"]}, """
From: Marcus Bell <mbell@keystonecommercial.com>
Subject: Package — Lockhaven Self Storage LLC

Lockhaven Self Storage LLC, 310-unit self-storage facility, Surprise AZ.
Gated, single-story metal buildings.

- Property + GL $1M/$2M
- Buildings $4,100,000, BPP $25,000, rental income $510,000
- Operating since 2010
- No losses in the last five years, loss runs attached

Effective 12/15/2026.
"""),
case("G24", "Apartments, 64 units", "R5: habitational over 50 units is outside target", R, ["R5"], ALL_D,
     {"namedInsured": ["mesquite terrace"], "location": ["phoenix"], "effectiveDate": ["01/01/2027"]}, """
From: Priya Nair <pnair@anchorrisk.com>
Subject: Package — Mesquite Terrace Apartments LP

Mesquite Terrace Apartments LP, 64-unit apartment community, Phoenix AZ.

- Property + GL $1M/$2M
- Buildings $8,200,000, BPP $60,000, rental income $900,000
- Owned since 2006
- No losses in the last five years, loss runs attached

Effective 01/01/2027.
"""),
case("G25", "Apartments, exactly 50 units", "Boundary: 50 units is still target", A, ["A1"], ALL_D + ["R5"],
     {"namedInsured": ["palo verde"], "location": ["mesa"], "effectiveDate": ["12/01/2026"]}, """
From: Tom Avery <tavery@westgatebrokerage.com>
Subject: Package — Palo Verde Flats LLC

Palo Verde Flats LLC, 50-unit apartment community, Mesa AZ.

- Property + GL $1M/$2M
- Buildings $6,400,000, BPP $50,000, rental income $780,000
- Owned since 2014
- No losses in the last five years, loss runs attached

Effective 12/01/2026.
"""),
case("G26", "Florist, email and loss run disagree", "Contradiction treated as a material gap", R, ["R4"], ALL_D,
     {"namedInsured": ["desert bloom"], "location": ["mesa"], "effectiveDate": ["11/30/2026"]}, """
From: Lisa Monroe <lmonroe@horizonbrokers.com>
Subject: BOP — Desert Bloom Florist LLC

Desert Bloom Florist LLC, retail florist, Mesa AZ.

- BOP: BPP $65,000 (leased), GL $1M/$2M
- Sales ~$540,000, 6 employees
- In business since 2010
- Clean loss history, no claims.

Effective 11/30/2026.

--- pasted from carrier loss run ---
Policy 2025-26 | DOL 06/14/2025 | Customer slip on wet floor | Paid $22,000 | CLOSED
""", note="Assumption to confirm: a submission that contradicts itself on losses is referred, because the loss history cannot be relied on."),
case("G27", "New bakery cafe with two losses", "R2 and R3 together", R, ["R2", "R3"], ALL_D,
     {"namedInsured": ["kiln & crumb", "kiln and crumb"], "location": ["tempe"], "effectiveDate": ["11/15/2026"]}, """
From: Renee Castillo <rcastillo@sonoranrisk.com>
Subject: BOP — Kiln & Crumb Bakery Cafe LLC

Kiln & Crumb Bakery Cafe LLC, counter-service bakery cafe, Tempe AZ.
No alcohol served.

- BOP: BPP $120,000 (leased), GL $1M/$2M
- Sales running ~$700,000 annualized, 9 employees
- Opened January 2026
- Two claims since opening, both closed:
    2026 customer burn from spilled coffee, $3,100
    2026 small oven fire, $6,400

Effective 11/15/2026.
"""),
case("G28", "Restaurant, complete and clean", "A1; alcohol is stated so no gap", A, ["A1"], ALL_D + ALL_R,
     {"namedInsured": ["olive & ember", "olive and ember"], "location": ["scottsdale"], "effectiveDate": ["12/01/2026"], "glLimits": ["1m/2m"]}, """
From: Paul Demetriou <pdemetriou@cactuscommercial.com>
Subject: BOP — Olive & Ember Trattoria LLC

Olive & Ember Trattoria LLC, full-service Italian restaurant, Scottsdale AZ.
Beer and wine only, about 12% of sales. No delivery, no catering.

- BOP: GL $1M/$2M, BPP $210,000 (leased)
- Sales ~$1.9M, 24 employees
- Operating since 2013
- No losses in the last five years, loss runs attached

Effective 12/01/2026.
"""),
case("G29", "Bookstore with one old loss", "A1; a 2020 loss is outside the three-year window", A, ["A1"], ALL_D + ["R3"],
     {"namedInsured": ["second chapter"], "location": ["flagstaff"], "effectiveDate": ["12/01/2026"]}, """
From: Dana Ruiz <druiz@horizonbrokers.com>
Subject: BOP — Second Chapter Books LLC

Second Chapter Books LLC, independent bookstore, Flagstaff AZ.

- BOP: BPP $150,000 (leased), GL $1M/$2M
- Sales ~$670,000, 5 employees
- In business since 2008
- Loss runs: one claim, 2020 burst pipe, $9,000 paid, closed. Nothing
  since.

Effective 12/01/2026.
"""),
case("G30", "Electrician, three losses but only one in the window", "D3 and R3 must not fire on old losses", A, ["A1"], ALL_D + ["R3"],
     {"namedInsured": ["brightwire"], "location": ["gilbert"], "effectiveDate": ["12/01/2026"], "glLimits": ["1m/2m"]}, """
From: Marcus Bell <mbell@keystonecommercial.com>
Subject: GL — Brightwire Electric LLC

Brightwire Electric LLC, residential and light-commercial electrician,
Gilbert AZ.

- GL only, $1M/$2M occurrence
- Payroll ~$720,000, 10 electricians
- In business since 2009
- Full loss history, all closed:
    2019 damaged drywall, $11,000
    2020 fixture fell, $6,500
    2025 scorched panel cover, $4,800

Effective 12/01/2026.
"""),
]

assert len(CASES) == 30 and len({c["id"] for c in CASES}) == 30
(ROOT / "golden_set.json").write_text(json.dumps(CASES, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
from collections import Counter
print(len(CASES), Counter(c["expected"]["verdict"] for c in CASES))

# RescueRoute

RescueRoute is an explainable Python command-line program that matches simulated surplus-food donations with compatible recipient organizations and volunteer drivers. It compares a FIFO (first in, first out) baseline with a greedy urgency-first strategy on the same input data and explains every decision in plain language.

> **Disclaimer:** RescueRoute is an educational prototype built for a class project. It uses simulated data only. It is not food-safety certified, clinically validated, approved for emergency operations, or ready for real-world deployment.

## Team and roles

| Member | Primary role | Main responsibilities |
|---|---|---|
| Brandon/Tri | Algorithm & Optimization Lead | FIFO and greedy strategies, complexity analysis, strategy comparison |
| Brandon/Tri | Data & Matching Lead | CSV files, loading, validation, matching rules, test data |
| Jacob Tucay | Product & Quality Lead | Explanations, metrics, printing, tests, README, demo materials |

All members share responsibility for design, debugging, testing, documentation, code review, and the final presentation.

## Setup and running

Requires Python 3.9 or newer.

```bash
pip install -r requirements.txt     # installs pytest (the program itself needs no extra libraries)
python3 rescueroute.py              # run both strategies on the sample data
python3 -m pytest -v                # run the automated tests
```

## Project structure

```
rescue-route/
├── rescueroute.py           # the whole program
├── test_rescueroute.py      # 17 automated pytest tests
├── data/
│   ├── donations.csv
│   ├── recipients.csv
│   └── volunteers.csv
├── COMPARISON_REPORT.md
├── CONTRIBUTIONS.md
├── requirements.txt
└── README.md
```

## Architecture

`rescueroute.py` is organized into sections that run in this order:

1. **Loading** (Functions 1 to 4): read the three CSV files into lists of dictionaries and convert text into numbers.
2. **Validation** (Functions 5 to 7): check IDs, food types, quantities, capacities, areas, and times. Bad data raises a `ValueError` with a clear message, and the program stops before running.
3. **Matching** (Functions 8 to 10): for each donation, check compatibility in stages and pick the first feasible recipient and volunteer in file order.
4. **Strategies** (Functions 11 to 14, 18 to 20): FIFO uses arrival order; greedy uses the urgency-first rule. Both use the same matching function, so the only difference between them is the processing order.
5. **Explanations** (Functions 15 to 17): each decision gets a sentence saying why it was assigned, unassigned, or deferred.
6. **Metrics and printing** (Functions 21 to 24): calculate metrics for each strategy, print everything, and list each donation whose outcome changed.

## Data model

CSV files use 24-hour `HH:MM` times. The program stores them as minutes since midnight and prints them as 12-hour times (for example, `2:30 PM`).

| Entity | Fields |
|---|---|
| Donation | `donation_id`, `donor_name`, `food_type`, `quantity`, `ready_time`, `expiry_time`, `pickup_area` |
| Recipient | `recipient_id`, `name`, `accepted_food_types` (separated by `;`), `capacity`, `area`, `closing_time` |
| Volunteer | `volunteer_id`, `name`, `vehicle_capacity`, `area`, `available_from`, `available_until`, `max_pickups` |
| Assignment | `donation_id`, `recipient_id`, `volunteer_id`, `scheduled_time` (pickup), `delivery_time`, `status`, `reason`, `deferred_by` |

Allowed food types: `prepared`, `produce`, `bakery`, `dairy`, `canned`, `seafood`.
Allowed areas: `North`, `South`, `East`, `West`, `Central`.

### Data structures used

| Structure | Where | Why |
|---|---|---|
| List of dictionaries | donations, recipients, volunteers | one record per row, easy to read and print |
| Dictionary | remaining capacity, volunteer state, lookup by ID | direct lookup by ID |
| Set | accepted food types, duplicate-ID detection, urgent IDs | fast membership checks |
| Deque | FIFO order | natural first-in, first-out queue |
| Heap (`heapq`) | greedy order | always gives back the most urgent donation next |
| List | assignment history | keeps decisions in processing order |
| Dictionary | metrics | named values that are easy to print and compare |

## Validation rules

The program stops with an error message if any of these fail:

- IDs are present and not duplicated.
- Quantities, capacities, and maximum pickups are greater than 0.
- Food types and areas are in the allowed lists.
- Times are valid `HH:MM` values.
- A volunteer's `available_until` is later than `available_from`.

A donation whose expiry time is at or before its ready time is still valid data. It is reported as unassigned because it is already expired.

## Matching rules and assumptions

A donation, recipient, and volunteer are a feasible match only if all of these are true:

1. The donation is not already expired at its ready time.
2. The recipient accepts the donation's food type.
3. The recipient has enough remaining capacity for the full quantity.
4. The volunteer's vehicle can carry the full quantity.
5. The volunteer has not reached their maximum pickups.
6. The delivery happens no later than the donation's expiry, the recipient's closing time, and the end of the volunteer's shift.

Timing assumptions (simulated, no real maps):

- Travel within the same area takes 10 minutes; between different areas it takes 25 minutes.
- A volunteer drives from their current location to the donor, waits until the food is ready if needed, then drives to the recipient.
- After a delivery, the volunteer is located at the recipient and is free again at the delivery time.
- Donations are never split between recipients or volunteers.
- A donation is "urgent" if its shelf life (expiry minus ready time) is 120 minutes or less.

## FIFO baseline

Donations are processed in the order they appear in `donations.csv`, using a `deque`. Each donation gets the first feasible recipient and volunteer. If none exists, the explanation names the first rule that failed.

## Greedy urgency-first rule

**Rule:** Schedule donations with the earliest expiry time (least remaining shelf life) first. If two donations expire at the same time, schedule the larger quantity first. If still tied, schedule the donation that arrived earlier.

**What it optimizes locally:** at each step, it protects the food that will be lost soonest if nobody acts.

**Why it is reasonable:** long-lasting food can often wait for a later driver or recipient, but food that expires soon has no second chance.

**Where it may fail:**

- It ignores quantity except as a tie-breaker, so several small urgent donations can use up space that one large, longer-lasting donation needed. In our sample data, greedy rescued more urgent donations (5 of 6 vs 3 of 6) but fewer total units (102 vs 118).
- It still uses "first feasible" matching, so it may place an urgent donation with a recipient that a later donation needed more.
- It does not look ahead or change earlier choices, so it is not guaranteed to be globally optimal.

**Fairness and starvation concerns:** a donation with a long shelf life can be pushed back again and again by newer, more urgent donations. If capacity runs out before its turn, it is never rescued even though it arrived first. The program reports this as a deferral and lists which donations went ahead. Possible fixes include an "aging" rule that raises a donation's priority the longer it waits, or reserving some capacity for long-lasting food.

## Explainability

Every decision is printed as a full sentence. Examples from the sample run:

- **Assigned:** Donation D-1004 (25 units of prepared from Event Catering Co) was assigned to Community Shelter (R-201) with volunteer Maria (V-301) because it expires at 2:30 PM (75 min shelf life), Community Shelter accepts prepared and had room for 30 units, and the volunteer's vehicle holds 30 units...
- **Unassigned:** Donation D-1010 (8 units of seafood) could not be assigned because no recipient accepts seafood donations.
- **Deferred:** D-1001 (expires 5:00 PM) was considered after D-1005, D-1004, D-1007, D-1006, D-1008, which arrived later but had less remaining shelf life under the urgency-first greedy rule and were assigned first.

## Metrics

| Metric | Definition |
|---|---|
| Donations received / assigned / unassigned | counts |
| Food quantity rescued | total units of assigned donations |
| Food quantity at risk | total units of unassigned donations |
| Urgent rescue rate | urgent donations assigned ÷ urgent donations |
| Recipient capacity utilization | units rescued ÷ total recipient capacity |
| Volunteer capacity utilization | pickups used ÷ total maximum pickups |

Rates return 0% instead of crashing when there is nothing to divide by.

## Complexity analysis

Let *n* = donations, *r* = recipients, *v* = volunteers.

| Step | Time | Notes |
|---|---|---|
| Loading and validation | O(n + r + v) | one pass per file; set lookups are O(1) |
| Matching one donation | O(r · v) | the filters are O(r + v); the timing check tries every remaining pair in the worst case |
| FIFO total | O(n log n + n · r · v) | sort by arrival order, then match each donation |
| Greedy ordering | O(n log n) | n heap pushes and n heap pops at O(log n) each |
| Deferral detection | O(n²) | compares each donation with those handled before it |
| Greedy total | O(n² + n · r · v) | |
| Metrics | O(n) | |

Space used is O(n + r + v) for the data, state dictionaries, and history. For class-sized data these costs are tiny; the O(n²) deferral check is the first part we would improve for very large inputs.

## Testing

`test_rescueroute.py` has 17 pytest tests that check expected outcomes:

normal compatible match, duplicate donation ID, invalid values, expired donation, nearly expired donation, no compatible food type, insufficient recipient capacity, no volunteer with enough vehicle capacity, volunteer maximum pickups, two donations competing for the same capacity, empty input files, greedy ordering and tie-breakers, FIFO and greedy producing different results, a starvation/deferral case, metric values, invalid recipient/volunteer data, and the sample data loading correctly.

## Limitations

- Travel times are fixed, simulated values, not real distances or traffic.
- Donations cannot be split across recipients or vehicles.
- Each volunteer carries one donation per trip.
- Matching picks the first feasible pair in file order, not the best pair.
- One bad row stops the whole program instead of being skipped.
- The greedy rule is not globally optimal and can starve long-lasting donations.
- Not suitable for real food handling or real operational use.

## Possible future work (stretch features)

Aging/fairness rule, best-pair matching (for example, earliest delivery), skipping bad rows instead of stopping, a Streamlit dashboard, simulated map distances, what-if analysis, and comparison with a constraint-optimization tool.

## References and AI assistance

- Course examples: greedy scheduling (CampusSpace Room Scheduler), queues with `deque` (SwiftServe Support Desk), sets for duplicate detection (StreamBox), and validation with `ValueError` (WildFire Evacuation Planner).
- Python documentation: 
csv - load the donation, recipient, and volunteer files
heapq - greedy urgency-first priority queue
collections.deque - FIFO queue
os - build file paths to data folder
- pytest documentation: Used to write and test the automated test suite
- AI assistance: 
We used Claude to help us with the initial creation of the code for the program structure, FIFO and greedy algorithms, validation and matching functions, sample CSV data creation and pytest testing.
We then used it to re-style the code to match the class examples (lists of dictionaries for the data structure, numbered function comments and use of ValueError for validation) and to help us set up our dev environment.

We then double checked all functions and ran the program through all 17 tests, confirming correct outputs by tracing through multiple donations manually to check that assignments and timing were correct.

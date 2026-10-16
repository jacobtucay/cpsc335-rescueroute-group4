# RescueRoute

RescueRoute is a Python command-line program that matches simulated food donations with recipients (shelters, pantries) and volunteer drivers. It compares two strategies on the same data and explains every decision in plain language:

- FIFO: first come, first served
- Greedy urgency-first: the donation that expires soonest goes first

> Disclaimer: This is an educational prototype for CPSC 335 using simulated data only. It is not food-safety certified or approved for real-world use.

# Team

| Member | Role | Contributions |
|---|---|---|
| Jacob Tucay | Product & Quality Lead (also built the core program) | Wrote `rescueroute.py` (loading, validation, matching, FIFO, greedy, explanations, metrics, comparison), the 17 tests, the README, the comparison report, and the video script. Set up the GitHub repo. |
| Brandon Sam | Presentation & Demo Lead | Slide deck and demo video |
| Tri Bui | Quality Assurance | Reviewed the code, tests, and documentation, and checked that everything runs correctly |

# How to run

Requires Python 3.9 or newer.

```bash
pip install -r requirements.txt    # installs pytest
python3 rescueroute.py             # runs both strategies on the sample data
python3 -m pytest -v               # runs the 17 tests
```

On Ubuntu/WSL, install pytest with `sudo apt install python3-pytest`.

# Files

| File | What it is |
|---|---|
| `rescueroute.py` | The whole program |
| `test_rescueroute.py` | 17 automated tests |
| `data/` | Sample `donations.csv`, `recipients.csv`, `volunteers.csv` |
| `COMPARISON_REPORT.md` | FIFO vs greedy results and analysis |
| `CONTRIBUTIONS.md` | Each member's contribution statement |

# How it works

1. Load the three CSV files into lists of dictionaries (Functions 1 to 4).
2. Validate the data (Functions 5 to 7). Duplicate IDs, unknown food types or areas, bad times, and quantities of 0 or less raise a `ValueError` and stop the program.
3. Order the donations: FIFO by arrival, greedy by urgency (Functions 11 to 14).
4. Match each donation to the first recipient and volunteer that pass every rule (Function 9).
5. Explain each decision as assigned, unassigned, or deferred (Functions 15 to 17).
6. Measure and compare both strategies (Functions 21 to 24).

Both strategies use the same matching rules. Only the order is different.

# Data model

Times are 24-hour `HH:MM` in the CSV files. The program stores them as minutes since midnight and prints them as 12-hour times.

| Entity | Fields |
|---|---|
| Donation | ID, donor name, food type, quantity, ready time, expiry time, pickup area |
| Recipient | ID, name, accepted food types (separated by `;`), capacity, area, closing time |
| Volunteer | ID, name, vehicle capacity, area, available from/until, max pickups |
| Assignment | donation ID, recipient ID, volunteer ID, pickup time, delivery time, status, reason |

Allowed food types: prepared, produce, bakery, dairy, canned, seafood. Allowed areas: North, South, East, West, Central.

Data structures: dictionaries for lookup by ID and tracking state, sets for food types and duplicate IDs, a `deque` for FIFO, a heap (`heapq`) for greedy, and a list for the decision history.

# Matching rules

A donation is matched only if all of these are true, checked in this order:

1. It is not already expired when it is ready.
2. A recipient accepts its food type.
3. That recipient has enough room left.
4. A volunteer's vehicle can carry it.
5. That volunteer has pickups left.
6. It can be delivered before it expires, before the recipient closes, and before the volunteer's shift ends.

Travel time is simulated: 10 minutes within the same area, 25 minutes between areas. A donation is "urgent" if it lasts 120 minutes or less after it is ready.

# Greedy rule

Rule: Handle the donation with the earliest expiry time first. If tied, handle the larger quantity first. If still tied, handle the one that arrived first.

- What it optimizes: at each step, it saves the food that will be lost soonest.
- Why it is reasonable: long-lasting food can wait, but food about to expire cannot.
- Where it can fail: it never looks ahead. In our sample data, greedy saved more urgent donations (5 of 6 vs 3 of 6) but less food overall (102 vs 118 units), because small urgent donations used space that larger donations needed.
- Fairness and starvation: a long-lasting donation can keep getting pushed back by newer, more urgent ones and never get a turn. An "aging" rule that raises priority the longer a donation waits could fix this.

# Metrics

Donations received, assigned, and unassigned; food rescued and at risk (units); urgent rescue rate; recipient capacity utilization (units rescued ÷ total capacity); and volunteer capacity utilization (pickups used ÷ total max pickups). Rates show 0% instead of crashing when there is nothing to divide by.

# Complexity

n = donations, r = recipients, v = volunteers.

| Step | Time |
|---|---|
| Loading and validation | O(n + r + v) |
| Matching one donation | O(r · v) |
| FIFO total | O(n log n + n · r · v) |
| Greedy ordering (heap) | O(n log n) |
| Finding deferrals | O(n²) |
| Greedy total | O(n² + n · r · v) |

Space is O(n + r + v).

# Tests

17 pytest tests check expected results, including: a normal match, duplicate IDs, invalid values, expired and nearly expired food, no compatible food type, not enough recipient capacity, no vehicle big enough, max pickups, two donations competing for space, empty files, the greedy order, FIFO and greedy giving different results, a starvation case, and metric values.

# Limitations

- Travel times are simulated, not real distances.
- Donations cannot be split, and each trip carries one donation.
- Matching picks the first workable pair, not the best one.
- One bad row stops the program instead of being skipped.
- Greedy is not guaranteed to be optimal and can starve long-lasting donations.

# References and AI assistance

- CPSC 335 course examples: greedy scheduling (CampusSpace Room Scheduler), `deque` queues (SwiftServe Support Desk), sets for lookups (StreamBox), and `ValueError` validation (WildFire Evacuation Planner).
- Python documentation: [`csv`](https://docs.python.org/3/library/csv.html), [`heapq`](https://docs.python.org/3/library/heapq.html), [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque), [`os`](https://docs.python.org/3/library/os.html).
- [pytest documentation](https://docs.pytest.org/).
- Sample data: all donations, recipients, and volunteers are simulated and do not represent real organizations or people.
- AI assistance: We used Claude (an AI assistant by Anthropic) to help create the first version of the program, sample data, and tests; to restyle the code to match our class examples; to draft parts of this README and the comparison report; and to set up our development environment. We reviewed every function, ran the program and all 17 tests, and traced several donations by hand to confirm the results. Every team member can explain how the code works, and we take full responsibility for the submitted work.

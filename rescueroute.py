# RescueRoute: Food Donation Matching
# CPSC 335 Group Project
# Team: Jacob Tucay, Brandon Sam, Tri Bui
#
# This program matches surplus food donations with recipients (shelters, pantries)
# and volunteer drivers. It compares two strategies:
#   1. FIFO baseline: first come, first served
#   2. Greedy urgency-first: the donation that expires soonest goes first


import csv
import heapq
import os
from collections import deque


# ---------- Settings ----------

# Folder that holds the three CSV files (next to this .py file)
DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# The only food types and areas we allow (sets make "is this allowed?" checks fast)
VALID_FOOD_TYPES = {"prepared", "produce", "bakery", "dairy", "canned", "seafood"}
VALID_AREAS = {"North", "South", "East", "West", "Central"}

# Simulated travel times in minutes
SAME_AREA_MINUTES = 10
DIFFERENT_AREA_MINUTES = 25

# A donation is urgent if it lasts this many minutes or less after it is ready
URGENT_MINUTES = 120

# Helper Functions

# Helper Function 1: Turn a clock time into minutes since midnight
def time_to_minutes(time_text):
    hours, minutes = time_text.strip().split(":")
    hours = int(hours)
    minutes = int(minutes)
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        raise ValueError(f"Invalid time: {time_text}")
    return hours * 60 + minutes

# Helper Function 2: Turn minutes since midnight back into an clock time
def format_time(total_minutes):
    hour_24 = total_minutes // 60
    minute = total_minutes % 60
    period = "AM" if hour_24 < 12 else "PM"
    hour_12 = hour_24 % 12
    if hour_12 == 0:    # 0 o'clock and 12 o'clock both show as 12
        hour_12 = 12
    return f"{hour_12}:{minute:02d} {period}"

# Helper Function 3: Simulated drive time between two areas
def travel_minutes(from_area, to_area):
    if from_area == to_area:
        return SAME_AREA_MINUTES
    return DIFFERENT_AREA_MINUTES

# Loading the Data

# Function 1: Read a CSV file into a list of dictionaries (one dictionary per row)
def load_csv(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

# Function 2: Load donations and turn the text into numbers
def load_donations(file_path):
    donations = []
    for row in load_csv(file_path):
        donations.append({
            "id": row["donation_id"].strip(),
            "donor": row["donor_name"].strip(),
            "food_type": row["food_type"].strip().lower(),
            "quantity": int(row["quantity"]),
            "ready": time_to_minutes(row["ready_time"]),
            "expiry": time_to_minutes(row["expiry_time"]),
            "area": row["pickup_area"].strip(),
            "arrival_order": len(donations),    # 0 for the first row, 1 for the next row, etc.
        })
    return donations

# Function 3: Load recipients from CSV file
def load_recipients(file_path):
    recipients = []
    for row in load_csv(file_path):
        food_types = set()
        for food in row["accepted_food_types"].split(";"):
            if food.strip():
                food_types.add(food.strip().lower())
        recipients.append({
            "id": row["recipient_id"].strip(),
            "name": row["name"].strip(),
            "accepts": food_types,
            "capacity": int(row["capacity"]),
            "area": row["area"].strip(),
            "closing": time_to_minutes(row["closing_time"]),
        })
    return recipients

# Function 4: Load volunteers
def load_volunteers(file_path):
    volunteers = []
    for row in load_csv(file_path):
        volunteers.append({
            "id": row["volunteer_id"].strip(),
            "name": row["name"].strip(),
            "capacity": int(row["vehicle_capacity"]),
            "area": row["area"].strip(),
            "start": time_to_minutes(row["available_from"]),
            "end": time_to_minutes(row["available_until"]),
            "max_pickups": int(row["max_pickups"]),
        })
    return volunteers

# Validate Data

# Function 5: Validate donation data
def validate_donations(donations):
    seen_ids = set()    # catch duplicate IDs
    for donation in donations:
        donation_id = donation["id"]
        if not donation_id:
            raise ValueError("Every donation must have an ID.")
        if donation_id in seen_ids:
            raise ValueError(f"Duplicate donation ID: {donation_id}")
        seen_ids.add(donation_id)

        if donation["food_type"] not in VALID_FOOD_TYPES:
            raise ValueError(f"Unknown food type for {donation_id}: {donation['food_type']}")
        if donation["quantity"] <= 0:
            raise ValueError(f"Quantity for {donation_id} must be greater than 0.")
        if donation["area"] not in VALID_AREAS:
            raise ValueError(f"Unknown pickup area for {donation_id}: {donation['area']}")
        # Expired food get's reporter later as "already expired"
    return True

# Function 6: Validate recipient data
def validate_recipients(recipients):
    seen_ids = set()
    for recipient in recipients:
        recipient_id = recipient["id"]
        if not recipient_id:
            raise ValueError("Every recipient must have an ID.")
        if recipient_id in seen_ids:
            raise ValueError(f"Duplicate recipient ID: {recipient_id}")
        seen_ids.add(recipient_id)

        if not recipient["accepts"]:
            raise ValueError(f"{recipient_id} must accept at least one food type.")
        bad_types = recipient["accepts"] - VALID_FOOD_TYPES # leftovers are not allowed
        if bad_types:
            raise ValueError(f"Unknown food types for {recipient_id}: {sorted(bad_types)}")
        if recipient["capacity"] <= 0:
            raise ValueError(f"Capacity for {recipient_id} must be greater than 0.")
        if recipient["area"] not in VALID_AREAS:
            raise ValueError(f"Unknown area for {recipient_id}: {recipient['area']}")
    return True

# Function 7: Validate volunteer data
def validate_volunteers(volunteers):
    seen_ids = set()
    for volunteer in volunteers:
        volunteer_id = volunteer["id"]
        if not volunteer_id:
            raise ValueError("Every volunteer must have an ID.")
        if volunteer_id in seen_ids:
            raise ValueError(f"Duplicate volunteer ID: {volunteer_id}")
        seen_ids.add(volunteer_id)

        if volunteer["capacity"] <= 0:
            raise ValueError(f"Vehicle capacity for {volunteer_id} must be greater than 0.")
        if volunteer["area"] not in VALID_AREAS:
            raise ValueError(f"Unknown area for {volunteer_id}: {volunteer['area']}")
        if volunteer["end"] <= volunteer["start"]:
            raise ValueError(f"{volunteer_id} must be available until a time later than their start time.")
        if volunteer["max_pickups"] <= 0:
            raise ValueError(f"Max pickups for {volunteer_id} must be greater than 0.")
    return True

# ---------- Matching ----------

# Function 8: Set up the starting state for one run
# Each strategy gets its own fresh state, so FIFO and greedy start from the same data.
def create_state(recipients, volunteers):
    return {
        "room_left": {r["id"]: r["capacity"] for r in recipients},   # space left at each recipient
        "free_at": {v["id"]: v["start"] for v in volunteers},        # when each volunteer is free
        "location": {v["id"]: v["area"] for v in volunteers},        # where each volunteer is now
        "pickups_used": {v["id"]: 0 for v in volunteers},            # trips each volunteer has done
    }

# Function 9: Find a match for a donation
# Checks each rule in order, so a failure can say which rule failed
def find_match(donation, recipients, volunteers, state):
    # Check 1: the food must not already be expired when it becomes ready
    if donation["expiry"] <= donation["ready"]:
        return None, f"it was already expired at its ready time ({format_time(donation['ready'])})"

    # Check 2: some recipient must accept this food type
    accepting = [r for r in recipients if donation["food_type"] in r["accepts"]]
    if not accepting:
        return None, f"no recipient accepts {donation['food_type']} donations"

    # Check 3: there must still be room for one of the recipients
    with_room = [r for r in accepting if state["room_left"][r["id"]] >= donation["quantity"]]
    if not with_room:
        room_text = ", ".join(f"{r['name']} has {state['room_left'][r['id']]}" for r in accepting)
        return None, (f"no compatible recipient had room for {donation['quantity']} units "
                      f"({room_text} left)")

    # Check 4: volunteer's vehicle must be big enough
    big_enough = [v for v in volunteers if v["capacity"] >= donation["quantity"]]
    if not big_enough:
        largest = max((v["capacity"] for v in volunteers), default=0)
        return None, (f"no volunteer vehicle can carry {donation['quantity']} units "
                      f"(largest holds {largest})")

    # Check 5: that volunteer must still have trips left
    has_trips = [v for v in big_enough if state["pickups_used"][v["id"]] < v["max_pickups"]]
    if not has_trips:
        return None, "every volunteer with a large enough vehicle already reached their maximum pickups"

    # Check 6: make sure the food can be delivered in time
    for recipient in with_room:
        for volunteer in has_trips:
            arrive_at_donor = state["free_at"][volunteer["id"]] + travel_minutes(
                state["location"][volunteer["id"]], donation["area"])
            pickup = max(donation["ready"], arrive_at_donor)    # cannot pick up before food is ready
            delivery = pickup + travel_minutes(donation["area"], recipient["area"])

            on_time = delivery <= donation["expiry"]    # before the food expires
            still_open = delivery <= recipient["closing"]   # before the recipient closes
            on_shift = delivery <= volunteer["end"] # before the volunteer's shift ends
            if on_time and still_open and on_shift:
                return {"recipient": recipient, "volunteer": volunteer,
                        "pickup": pickup, "delivery": delivery}, None

    return None, (f"no recipient and volunteer pair could deliver before the food expired at "
                  f"{format_time(donation['expiry'])} while the recipient was still open "
                  f"and the volunteer was on shift")

# Function 10: Update the state after a successful match
def update_state(state, donation, match):
    recipient_id = match["recipient"]["id"]
    volunteer_id = match["volunteer"]["id"]
    state["room_left"][recipient_id] -= donation["quantity"]    # recipient has less room
    state["free_at"][volunteer_id] = match["delivery"]  # volunteer busy until drop-off
    state["location"][volunteer_id] = match["recipient"]["area"]    # volunteer ends at the recipient
    state["pickups_used"][volunteer_id] += 1    # one more trip used

# FIFO and Greedy Algorithm

# Function 11: FIFO order. Put donations in a queue by arrival order.
def fifo_order(donations):
    queue = deque()
    for donation in sorted(donations, key=lambda d: d["arrival_order"]):
        queue.append(donation)
    return queue

# Function 12: Greedy rule: soonest expiry first, then larger quantity, then earlier arrival
def greedy_key(donation):
    return (donation["expiry"], -donation["quantity"], donation["arrival_order"])

# Function 13: Sort donations by urgency using a heap
def greedy_order(donations):
    donations_by_id = {d["id"]: d for d in donations}   # dictionary for quick lookup by ID
    heap = []
    for donation in donations:
        heapq.heappush(heap, (greedy_key(donation), donation["id"]))
    ordered = []
    while heap:
        priority, donation_id = heapq.heappop(heap) # pops the most urgent one
        ordered.append(donations_by_id[donation_id])
    return ordered

# Function 14: Find donations that were passed by later, more urgent ones
def find_deferrals(ordered_donations):
    deferrals = {}
    for position, donation in enumerate(ordered_donations):
        deferrals[donation["id"]] = []
        for earlier in ordered_donations[:position]:    # everything handled before this one
            if earlier["arrival_order"] > donation["arrival_order"]:
                deferrals[donation["id"]].append(earlier)
    return deferrals

# Explanations

# Function 15: Explain why a donation was assigned
def explain_assigned(donation, match, room_before):
    recipient = match["recipient"]
    volunteer = match["volunteer"]
    shelf_life = donation["expiry"] - donation["ready"]
    return (f"Assigned: Donation {donation['id']} ({donation['quantity']} units of "
            f"{donation['food_type']} from {donation['donor']}) was assigned to "
            f"{recipient['name']} ({recipient['id']}) with volunteer {volunteer['name']} "
            f"({volunteer['id']}) because it expires at {format_time(donation['expiry'])} "
            f"({shelf_life} min shelf life), {recipient['name']} accepts {donation['food_type']} "
            f"and had room for {room_before} units, and the volunteer's vehicle holds "
            f"{volunteer['capacity']} units. Pickup {format_time(match['pickup'])}, delivery "
            f"{format_time(match['delivery'])} (before expiry and before closing at "
            f"{format_time(recipient['closing'])}).")

# Function 16: Explain why a donation could not be assigned
def explain_unassigned(donation, reason):
    return (f"Unassigned: Donation {donation['id']} ({donation['quantity']} units of "
            f"{donation['food_type']}) could not be assigned because {reason}.")

# Function 17: Explain why a donation waited its turn under greedy
def explain_deferral(donation, jumped_ahead):
    if not jumped_ahead:
        return ""
    names = ", ".join(f"{d['id']} (expires {format_time(d['expiry'])})" for d in jumped_ahead)
    return (f" Deferred: {donation['id']} (expires {format_time(donation['expiry'])}) was "
            f"considered after {names}, which arrived later but had less remaining shelf life "
            f"under the urgency-first greedy rule and were assigned first.")

# Function 18: Process donations in the given order and record every decision
def run_strategy(ordered_donations, recipients, volunteers, deferrals=None):
    state = create_state(recipients, volunteers)
    assignments = []
    assigned_ids = set()                       

    for donation in ordered_donations:
        jumped_ahead = []
        if deferrals is not None:
            for other in deferrals[donation["id"]]:
                if other["id"] in assigned_ids:
                    jumped_ahead.append(other)

        match, reason = find_match(donation, recipients, volunteers, state)

        if match is not None:
            room_before = state["room_left"][match["recipient"]["id"]]
            update_state(state, donation, match)
            assigned_ids.add(donation["id"])
            assignments.append({
                "donation_id": donation["id"],
                "recipient_id": match["recipient"]["id"],
                "volunteer_id": match["volunteer"]["id"],
                "scheduled_time": match["pickup"],
                "delivery_time": match["delivery"],
                "status": "ASSIGNED",
                "reason": explain_assigned(donation, match, room_before)
                          + explain_deferral(donation, jumped_ahead),
                "deferred_by": [d["id"] for d in jumped_ahead],
            })
        else:
            assignments.append({
                "donation_id": donation["id"],
                "recipient_id": None,
                "volunteer_id": None,
                "scheduled_time": None,
                "delivery_time": None,
                "status": "UNASSIGNED",
                "reason": explain_unassigned(donation, reason)
                          + explain_deferral(donation, jumped_ahead),
                "deferred_by": [d["id"] for d in jumped_ahead],
            })
    return assignments

# Function 19: FIFO baseline
def run_fifo(donations, recipients, volunteers):
    return run_strategy(fifo_order(donations), recipients, volunteers)

# Function 20: Greedy urgency-first strategy
def run_greedy(donations, recipients, volunteers):
    ordered = greedy_order(donations)
    return run_strategy(ordered, recipients, volunteers, find_deferrals(ordered))

# Helper Function 4: Divide, but return 0 instead of crashing when dividing by 0
def safe_rate(part, whole):
    if whole == 0:
        return 0.0
    return part / whole

# Function 21: Calculate the metrics for one strategy (stored in a dictionary)
def compute_metrics(assignments, donations, recipients, volunteers):
    donations_by_id = {d["id"]: d for d in donations}
    assigned = [a for a in assignments if a["status"] == "ASSIGNED"]
    unassigned = [a for a in assignments if a["status"] == "UNASSIGNED"]

    rescued = sum(donations_by_id[a["donation_id"]]["quantity"] for a in assigned)
    at_risk = sum(donations_by_id[a["donation_id"]]["quantity"] for a in unassigned)

    urgent_ids = set()
    for d in donations:
        shelf_life = d["expiry"] - d["ready"]
        if 0 < shelf_life <= URGENT_MINUTES:
            urgent_ids.add(d["id"])
    urgent_rescued = len([a for a in assigned if a["donation_id"] in urgent_ids])

    total_capacity = sum(r["capacity"] for r in recipients)
    total_pickup_slots = sum(v["max_pickups"] for v in volunteers)

    return {
        "donations_received": len(donations),
        "donations_assigned": len(assigned),
        "donations_unassigned": len(unassigned),
        "quantity_rescued": rescued,
        "quantity_at_risk": at_risk,
        "urgent_donations": len(urgent_ids),
        "urgent_rescued": urgent_rescued,
        "urgent_rescue_rate": safe_rate(urgent_rescued, len(urgent_ids)),
        "recipient_capacity_utilization": safe_rate(rescued, total_capacity),
        "volunteer_capacity_utilization": safe_rate(len(assigned), total_pickup_slots),
    }

# Labels used when printing metrics
METRIC_LABELS = [
    ("donations_received", "Donations received"),
    ("donations_assigned", "Donations assigned"),
    ("donations_unassigned", "Donations unassigned"),
    ("quantity_rescued", "Food quantity rescued (units)"),
    ("quantity_at_risk", "Food quantity at risk (units)"),
    ("urgent_rescue_rate", f"Urgent rescue rate (<= {URGENT_MINUTES} min)"),
    ("recipient_capacity_utilization", "Recipient capacity utilization"),
    ("volunteer_capacity_utilization", "Volunteer capacity utilization"),
]
PERCENT_METRICS = {"urgent_rescue_rate", "recipient_capacity_utilization",
                   "volunteer_capacity_utilization"}

# Helper Function 5: Show rates as percentages and counts as plain numbers
def format_metric(key, value):
    if key in PERCENT_METRICS:
        return f"{value * 100:.1f}%"
    return str(value)

# Function 22: Print every decision with its explanation
def print_decisions(title, assignments):
    print(f"\n--- {title}: Decisions ---")
    if not assignments:
        print("None")
    for number, assignment in enumerate(assignments, start=1):
        print(f"{number}. {assignment['reason']}")

# Function 23: Print the metrics for one strategy
def print_metrics(title, metrics):
    print(f"\n--- {title}: Metrics ---")
    for key, label in METRIC_LABELS:
        line = f"{label}: {format_metric(key, metrics[key])}"
        if key == "urgent_rescue_rate":
            line += f" ({metrics['urgent_rescued']} of {metrics['urgent_donations']})"
        print(line)


# Function 24: Compare FIFO and greedy and explain what changed
def compare_strategies(fifo_results, greedy_results, fifo_metrics, greedy_metrics):
    print("\n--- Strategy Comparison: FIFO vs Greedy ---")
    print(f"{'Metric':<40}{'FIFO':>10}{'Greedy':>10}")
    for key, label in METRIC_LABELS:
        fifo_value = format_metric(key, fifo_metrics[key])
        greedy_value = format_metric(key, greedy_metrics[key])
        print(f"{label:<40}{fifo_value:>10}{greedy_value:>10}")

    # Look at each donation and print the ones whose result changed
    greedy_by_id = {a["donation_id"]: a for a in greedy_results}
    print("\nWhat changed and why:")
    changed = 0
    for fifo_a in fifo_results:
        greedy_a = greedy_by_id[fifo_a["donation_id"]]
        if fifo_a["status"] != greedy_a["status"] or fifo_a["recipient_id"] != greedy_a["recipient_id"]:
            changed += 1
            print(f"\n{fifo_a['donation_id']}: FIFO = {fifo_a['status']}, Greedy = {greedy_a['status']}")
            print(f"  FIFO:   {fifo_a['reason']}")
            print(f"  Greedy: {greedy_a['reason']}")
    if changed == 0:
        print("None. Both strategies made the same assignments.")

    # Short summary
    urgent_diff = greedy_metrics["urgent_rescued"] - fifo_metrics["urgent_rescued"]
    quantity_diff = greedy_metrics["quantity_rescued"] - fifo_metrics["quantity_rescued"]
    print(f"\nResult: Compared with FIFO, greedy rescued {urgent_diff:+d} urgent donation(s) "
          f"and {quantity_diff:+d} units of food overall.")
    print("Greedy handles the soonest-expiring food first, so short-lived donations get "
          "recipient space and drivers before longer-lasting food uses them up.")
    if quantity_diff < 0:
        print("Trade-off: the total amount rescued went down. Long-lasting donations were "
              "deferred and then found no room left, so the urgency rule can starve them.")


# Program Demo
def main():
    print("--- RescueRoute: Food Donation Matching ---")
    print("Educational prototype. Simulated data only.")

    # Step 1: Load the data from the CSV files
    donations = load_donations(os.path.join(DATA_FOLDER, "donations.csv"))
    recipients = load_recipients(os.path.join(DATA_FOLDER, "recipients.csv"))
    volunteers = load_volunteers(os.path.join(DATA_FOLDER, "volunteers.csv"))

    # Step 2: Validate the data.
    try:
        validate_donations(donations)
        validate_recipients(recipients)
        validate_volunteers(volunteers)
    except ValueError as error:
        print("Data error:", error)
        return

    print(f"\nLoaded {len(donations)} donations, {len(recipients)} recipients, "
          f"{len(volunteers)} volunteers.")

    # Step 3: Run both strategies on the same data
    fifo_results = run_fifo(donations, recipients, volunteers)
    greedy_results = run_greedy(donations, recipients, volunteers)

    # Step 4: Calculate metrics for both
    fifo_metrics = compute_metrics(fifo_results, donations, recipients, volunteers)
    greedy_metrics = compute_metrics(greedy_results, donations, recipients, volunteers)

    # Step 5: Print results and compare
    print_decisions("FIFO Baseline", fifo_results)
    print_metrics("FIFO Baseline", fifo_metrics)
    print_decisions("Greedy Urgency-First", greedy_results)
    print_metrics("Greedy Urgency-First", greedy_metrics)
    compare_strategies(fifo_results, greedy_results, fifo_metrics, greedy_metrics)


if __name__ == "__main__":
    main()
# Automated tests for RescueRoute
# Run with:  python3 -m pytest -v
#
# Each test builds a tiny, hand-made scenario where we already know the right answer,
# then uses assert to check that the program gives that answer.

import pytest

from rescueroute import (
    compute_metrics, greedy_order, load_donations, load_recipients, load_volunteers,
    run_fifo, run_greedy, validate_donations, validate_recipients, validate_volunteers,
    time_to_minutes, DATA_FOLDER,
)
import os


# ---------- Helper functions that build test data ----------

def make_donation(donation_id, quantity=10, food_type="prepared", ready="13:00",
                  expiry="16:00", area="Central", arrival_order=0):
    return {"id": donation_id, "donor": f"Donor {donation_id}", "food_type": food_type,
            "quantity": quantity, "ready": time_to_minutes(ready),
            "expiry": time_to_minutes(expiry), "area": area, "arrival_order": arrival_order}


def make_recipient(recipient_id, accepts=("prepared",), capacity=50, area="Central", closing="18:00"):
    return {"id": recipient_id, "name": f"Recipient {recipient_id}", "accepts": set(accepts),
            "capacity": capacity, "area": area, "closing": time_to_minutes(closing)}


def make_volunteer(volunteer_id, capacity=30, area="Central", start="13:00", end="18:00", max_pickups=5):
    return {"id": volunteer_id, "name": f"Volunteer {volunteer_id}", "capacity": capacity,
            "area": area, "start": time_to_minutes(start), "end": time_to_minutes(end),
            "max_pickups": max_pickups}


# Find the decision for one donation in a list of results
def result_for(results, donation_id):
    for assignment in results:
        if assignment["donation_id"] == donation_id:
            return assignment
    return None


# ---------- Tests ----------

# Test 1: A normal donation finds a recipient and volunteer
def test_normal_compatible_match():
    results = run_fifo([make_donation("D1")], [make_recipient("R1")], [make_volunteer("V1")])
    assignment = result_for(results, "D1")
    assert assignment["status"] == "ASSIGNED"
    assert assignment["recipient_id"] == "R1"
    assert assignment["volunteer_id"] == "V1"
    assert "accepts prepared" in assignment["reason"]


# Test 2: Duplicate donation IDs are rejected
def test_duplicate_donation_id():
    donations = [make_donation("D1"), make_donation("D1", arrival_order=1)]
    with pytest.raises(ValueError, match="Duplicate donation ID: D1"):
        validate_donations(donations)


# Test 3: Bad values are rejected (unknown food type, zero quantity, bad time)
def test_invalid_values_are_rejected():
    with pytest.raises(ValueError, match="Unknown food type"):
        validate_donations([make_donation("D1", food_type="pizza")])
    with pytest.raises(ValueError, match="greater than 0"):
        validate_donations([make_donation("D1", quantity=0)])
    with pytest.raises(ValueError, match="Invalid time"):
        time_to_minutes("25:00")


# Test 4: Food that is already expired is not assigned
def test_expired_donation():
    donation = make_donation("D1", ready="14:00", expiry="14:00")
    results = run_fifo([donation], [make_recipient("R1")], [make_volunteer("V1")])
    assert result_for(results, "D1")["status"] == "UNASSIGNED"
    assert "already expired" in result_for(results, "D1")["reason"]


# Test 5: Nearly expired food cannot be delivered in time
# (20 minutes of shelf life, but a cross-area trip takes 25 minutes)
def test_nearly_expired_donation():
    donation = make_donation("D1", ready="13:00", expiry="13:20", area="North")
    results = run_fifo([donation], [make_recipient("R1", area="South")],
                       [make_volunteer("V1", area="North")])
    assert result_for(results, "D1")["status"] == "UNASSIGNED"
    assert "before the food expired" in result_for(results, "D1")["reason"]


# Test 6: No recipient accepts the food type
def test_no_compatible_food_type():
    donation = make_donation("D1", food_type="seafood")
    results = run_fifo([donation], [make_recipient("R1", accepts=("prepared", "bakery"))],
                       [make_volunteer("V1")])
    assert result_for(results, "D1")["status"] == "UNASSIGNED"
    assert "no recipient accepts seafood" in result_for(results, "D1")["reason"]


# Test 7: The recipient does not have enough room
def test_insufficient_recipient_capacity():
    donation = make_donation("D1", quantity=40)
    results = run_fifo([donation], [make_recipient("R1", capacity=30)],
                       [make_volunteer("V1", capacity=50)])
    assert result_for(results, "D1")["status"] == "UNASSIGNED"
    assert "had room for 40 units" in result_for(results, "D1")["reason"]


# Test 8: No volunteer has a big enough vehicle
def test_no_volunteer_with_enough_vehicle_capacity():
    donation = make_donation("D1", quantity=40)
    results = run_fifo([donation], [make_recipient("R1", capacity=100)],
                       [make_volunteer("V1", capacity=25)])
    assert result_for(results, "D1")["status"] == "UNASSIGNED"
    assert "no volunteer vehicle can carry 40 units" in result_for(results, "D1")["reason"]


# Test 9: A volunteer cannot go over their maximum pickups
def test_volunteer_max_pickups():
    donations = [make_donation("D1", arrival_order=0), make_donation("D2", arrival_order=1)]
    results = run_fifo(donations, [make_recipient("R1")], [make_volunteer("V1", max_pickups=1)])
    assert result_for(results, "D1")["status"] == "ASSIGNED"
    assert result_for(results, "D2")["status"] == "UNASSIGNED"
    assert "maximum pickups" in result_for(results, "D2")["reason"]


# Test 10: Two donations compete for the same space. The first in line gets it.
def test_two_donations_compete_for_same_capacity():
    donations = [make_donation("D1", quantity=20, arrival_order=0),
                 make_donation("D2", quantity=20, arrival_order=1)]
    results = run_fifo(donations, [make_recipient("R1", capacity=30)], [make_volunteer("V1")])
    assert result_for(results, "D1")["status"] == "ASSIGNED"
    assert result_for(results, "D2")["status"] == "UNASSIGNED"
    assert "Recipient R1 has 10 left" in result_for(results, "D2")["reason"]


# Test 11: Empty input files do not crash the program
def test_empty_input_files(tmp_path):
    (tmp_path / "donations.csv").write_text(
        "donation_id,donor_name,food_type,quantity,ready_time,expiry_time,pickup_area\n")
    (tmp_path / "recipients.csv").write_text(
        "recipient_id,name,accepted_food_types,capacity,area,closing_time\n")
    (tmp_path / "volunteers.csv").write_text(
        "volunteer_id,name,vehicle_capacity,area,available_from,available_until,max_pickups\n")

    donations = load_donations(tmp_path / "donations.csv")
    recipients = load_recipients(tmp_path / "recipients.csv")
    volunteers = load_volunteers(tmp_path / "volunteers.csv")
    assert donations == [] and recipients == [] and volunteers == []

    results = run_greedy(donations, recipients, volunteers)
    metrics = compute_metrics(results, donations, recipients, volunteers)
    assert results == []
    assert metrics["donations_received"] == 0
    assert metrics["urgent_rescue_rate"] == 0.0      # no divide-by-zero crash


# Test 12: The greedy order follows the rule and its tie-breakers
def test_greedy_order_follows_the_rule():
    donations = [
        make_donation("A", quantity=10, expiry="17:00", arrival_order=0),
        make_donation("B", quantity=5, expiry="14:00", arrival_order=1),
        make_donation("C", quantity=20, expiry="14:00", arrival_order=2),  # same expiry as B, bigger
        make_donation("D", quantity=20, expiry="14:00", arrival_order=3),  # full tie with C, arrived later
    ]
    ordered_ids = [d["id"] for d in greedy_order(donations)]
    assert ordered_ids == ["C", "D", "B", "A"]


# Test 13: FIFO and greedy give different results on the same data
def test_fifo_and_greedy_produce_different_results():
    # D1 lasts all afternoon and arrives first. D2 expires soon. Room for only one.
    donations = [make_donation("D1", quantity=20, expiry="18:00", arrival_order=0),
                 make_donation("D2", quantity=20, expiry="14:00", arrival_order=1)]
    recipients = [make_recipient("R1", capacity=20)]
    volunteers = [make_volunteer("V1")]

    fifo = run_fifo(donations, recipients, volunteers)
    greedy = run_greedy(donations, recipients, volunteers)

    assert result_for(fifo, "D1")["status"] == "ASSIGNED"
    assert result_for(fifo, "D2")["status"] == "UNASSIGNED"
    assert result_for(greedy, "D2")["status"] == "ASSIGNED"
    assert result_for(greedy, "D1")["status"] == "UNASSIGNED"

    fifo_metrics = compute_metrics(fifo, donations, recipients, volunteers)
    greedy_metrics = compute_metrics(greedy, donations, recipients, volunteers)
    assert greedy_metrics["urgent_rescue_rate"] > fifo_metrics["urgent_rescue_rate"]


# Test 14: Starvation. A long-lasting donation arrives first but keeps getting pushed back.
def test_starvation_case_explains_deferral():
    donations = [make_donation("LONG", quantity=10, expiry="20:00", arrival_order=0),
                 make_donation("U1", quantity=10, expiry="14:00", arrival_order=1),
                 make_donation("U2", quantity=10, expiry="14:10", arrival_order=2)]
    results = run_greedy(donations, [make_recipient("R1", capacity=20)], [make_volunteer("V1")])
    long_result = result_for(results, "LONG")
    assert long_result["status"] == "UNASSIGNED"          # starved: no room was left
    assert long_result["deferred_by"] == ["U1", "U2"]
    assert "Deferred: LONG" in long_result["reason"]
    assert "less remaining shelf life" in long_result["reason"]


# Test 15: The metric numbers are calculated correctly
def test_metrics_values():
    donations = [make_donation("D1", quantity=10, expiry="14:00", arrival_order=0),  # urgent (60 min)
                 make_donation("D2", quantity=30, food_type="seafood", arrival_order=1)]  # cannot be placed
    recipients = [make_recipient("R1", capacity=40)]
    volunteers = [make_volunteer("V1", max_pickups=2)]
    metrics = compute_metrics(run_fifo(donations, recipients, volunteers),
                              donations, recipients, volunteers)
    assert metrics["donations_assigned"] == 1
    assert metrics["donations_unassigned"] == 1
    assert metrics["quantity_rescued"] == 10
    assert metrics["quantity_at_risk"] == 30
    assert metrics["urgent_rescue_rate"] == 1.0
    assert metrics["recipient_capacity_utilization"] == pytest.approx(10 / 40)
    assert metrics["volunteer_capacity_utilization"] == pytest.approx(1 / 2)


# Test 16: Bad recipient and volunteer data are rejected
def test_bad_recipient_and_volunteer_data():
    with pytest.raises(ValueError, match="Unknown food types"):
        validate_recipients([make_recipient("R1", accepts=("prepared", "bricks"))])
    with pytest.raises(ValueError, match="Unknown area"):
        validate_volunteers([make_volunteer("V1", area="Mars")])


# Test 17: The sample data files load and pass validation
def test_sample_data_loads():
    donations = load_donations(os.path.join(DATA_FOLDER, "donations.csv"))
    recipients = load_recipients(os.path.join(DATA_FOLDER, "recipients.csv"))
    volunteers = load_volunteers(os.path.join(DATA_FOLDER, "volunteers.csv"))
    assert validate_donations(donations)
    assert validate_recipients(recipients)
    assert validate_volunteers(volunteers)
    assert len(donations) == 11

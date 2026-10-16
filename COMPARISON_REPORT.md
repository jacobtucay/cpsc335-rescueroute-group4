# FIFO vs Greedy Comparison Report

*RescueRoute educational prototype, simulated data only.*

## Setup

Both strategies used the same sample data: 11 donations, 4 recipients, and 3 volunteers (`data/` folder). Both use the same matching rules. The only difference is the order in which donations are handled.

- **FIFO:** arrival order.
- **Greedy:** earliest expiry first, then larger quantity, then earlier arrival.

## Results

| Metric | FIFO | Greedy |
|---|---|---|
| Donations received | 11 | 11 |
| Donations assigned | 6 | 6 |
| Donations unassigned | 5 | 5 |
| Food quantity rescued (units) | 118 | 102 |
| Food quantity at risk (units) | 92 | 108 |
| Urgent rescue rate | 50.0% (3 of 6) | 83.3% (5 of 6) |
| Recipient capacity utilization | 76.1% | 65.8% |
| Volunteer capacity utilization | 75.0% | 75.0% |

## What changed and why

Under FIFO, the long-lasting donations D-1001 (expires 5:00 PM) and D-1002 (expires 8:00 PM) arrived first, so they took shelter and pantry space and used Maria's early trips. By the time the urgent donations were processed, D-1007 (produce, expires 2:45 PM) could not be delivered in time and D-1008 (prepared, expires 3:30 PM) found no recipient with enough room left.

Under greedy, the urgent donations were handled first, so D-1007 and D-1008 were both rescued. The cost was that D-1001 and D-1002 were deferred and then found no room left. Those two donations were larger (20 and 30 units), so greedy rescued fewer total units even though it saved more urgent food.

Four other donations (D-1003 through D-1006) were still assigned under both strategies, but to different recipients or volunteers, because the earlier choices changed which space and drivers were still free.

Three donations failed under both strategies for reasons the processing order cannot fix: D-1009 (40 units, more than any vehicle or remaining space allows), D-1010 (no recipient accepts seafood), and D-1011 (already expired).

## Takeaway

Greedy is better at its stated goal: protecting food that is about to expire. It is not better on every measure. It rescued less total food and showed starvation, where donations that arrived first never got a turn. A real system would need a balance, such as an aging rule or reserved capacity for long-lasting food.

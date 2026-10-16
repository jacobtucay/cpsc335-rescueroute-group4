FIFO vs Greedy Comparison Report

As seen in the table below, the two strategies were tested using the same input data (11 donations, 4 recipients, 3 volunteers) and the same matching rules. The only difference between the two strategies was the priority logic: while FIFO prioritizes donations in the order of their arrival, greedy prioritizes the nearest expiry, followed by a higher quantity and the earliest arrival time.

Results

| Metric | FIFO | Greedy |
|---|---|---|
| Donations assigned | 6 of 11 | 6 of 11 |
| Food rescued (units) | 118 | 102 |
| Food at risk (units) | 92 | 108 |
| Urgent rescue rate | 50.0% (3 of 6) | 83.3% (5 of 6) |
| Recipient capacity used | 76.1% | 65.8% |
| Volunteer capacity used | 75.0% | 75.0% |

Changes and Impact

Using FIFO, the first two donations to arrive (D-1001 and D-1002) could be scheduled first due to their availability until 5:00 PM and 8:00 PM, respectively. However, they consumed the recipients’ capacity and the volunteers’ time, resulting in two donations not being rescued despite their urgency (D-1007, which had an expiry time at 2:45 PM, and D-1008, which was available until 3:30 PM).


Using a greedy approach, the donations with the nearest expiry time (D-1007) and followed by a higher quantity (D-1008) were scheduled before the ones arriving earlier but with a smaller quantity (D-1001) and leaving a later expiry time (D-1002). Accordingly, D-1007 and D-1008 were both rescued, while D-1001 and D-1002 could not be accommodated. As a result, the greedy method rescued fewer units of food compared to FIFO.

The donations assigned according to the two strategies (D-1003-D-1006) were identical for the two strategies. Additionally, three donations (D-1009, D-1010, and D-1011) could not be scheduled using either strategy; D-1009 was too large for all volunteers, D-1010 had no recipient interested in seafood, and D-1011 was expired by the time of pickup.

Conclusion

While the greedy approach was evidently more efficient regarding the donations with nearby expiry times, it resulted in fewer donations being rescued overall and created a starvation scenario, where the donations with earlier arrival times were constantly pushed below the newer donations. A better approach to donation scheduling would be to consider time-sensitive factors such as an aging factor increasing the priority of a donation the longer it has been in the system.
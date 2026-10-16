Individual Contribution Statements

Each team member’s contribution is described below.

Jacob Tucay (Product & Quality Lead, core program)

What I built:
My contribution includes everything related to the Python code and reports of this project. Specifically, I coded rescueroute.py, including loading and validating the data, implementing the matching rules and FIFO and greedy strategies, writing the explanation of actions, metrics, and comparison of FIFO and greedy strategy. Additionally, I prepared the sample data files in the data folder, wrote all the 17 tests in test_rescueroute.py, and wrote the README, comparison report, and video script. Finally, I created the GitHub repository and committed the code.

What I tested or reviewed:
I tested the program and 17 tests, ensuring that they are working correctly. In addition, I followed several donations through the code to ensure that they are distributed correctly according to the FIFO and greedy strategies. These include, among others, D-1007 and D-1001.

What I learned:
I have learned how processing order affects the outcome even when the same rules are applied. While the greedy algorithm rescued more nutritionally valuable food donations (5 out of 6 urgent donations), FIFO saved more food donations in total (118 compared to 102). I also learned how to implement a FIFO (First In, First Out) data structure using a deque, a priority queue using a heap, and sets to store unique elements for fast lookup and checking for duplicates. Moreover, I learned how to work with Git and GitHub to commit my code to the repository.

Brandon Sam (Presentation & Demo Lead)

What I built:
I built the slide deck for the final presentation, including the project description, data description, matching rules, FIFO vs greedy comparison, results, and trade-off analysis. Besides, I recorded a video based on the video script, demonstrating the code, running the program, and executing the test suite.

What I tested or reviewed:
While recording the video, I ran the program and tests to ensure that the results were consistent with the description in the video script.

What I learned:
The core insight that I learned is that FIFO and greedy algorithms utilize the same matching rules, and the only difference is the order in which donations are processed. This difference affects the outcome, including the number of rescued food donations and nutritionally valuable donations. For instance, greedy algorithms risk lower total food donations due to the starvation problem, where some donations are always moved to the end of the queue.

Tri Bui (Quality Assurance)

What I reviewed:
I reviewed the code, tests, and README file for any possible issues. In addition, I executed the program and all 17 tests on my computer to ensure that they work correctly. Finally, I compared the output of the program with the comparison report to ensure that all numbers matched.

What I learned:
I learned how the program follows the matching rules sequentially and highlights the first rule that is not met, explaining why a donation was not matched. In the same way, I learned how tests ensure that the program follows these rules and the FIFO policy. For instance, the greedy algorithm’s tests demonstrate that the priority queue is correctly ordered according to the tie-breakers.
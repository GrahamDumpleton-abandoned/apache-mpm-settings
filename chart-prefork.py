import csv
import sys

import matplotlib.pyplot as plt

active_process_count = []
active_processes = []
idle_process_count = []

with open(sys.argv[1], 'rb') as fileobj:
    reader = csv.DictReader(fileobj)
    for row in reader:
        active_process_count.append(row['Active Process Count'])
        active_processes.append(row['Active Processes'])
        idle_process_count.append(row['Idle Process Count'])

plt.figure(1)

plt.subplot(311)
plt.ylabel('Available Processes')
plt.fill_between(range(len(idle_process_count)),
                 idle_process_count, color='green')

plt.subplot(312)
plt.ylabel('Active Processes')
plt.fill_between(range(len(active_processes)),
                 active_processes, color='blue')

plt.subplot(313)
plt.xlabel('Maintenance Cycle')
plt.ylabel('Concurrent Requests')
plt.fill_between(range(len(active_process_count)),
                 active_process_count, color='red')

plt.show()

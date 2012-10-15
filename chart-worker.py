import csv
import sys

import matplotlib.pyplot as plt

active_thread_count = []
active_processes = []
idle_thread_count = []

with open(sys.argv[1], 'rb') as fileobj:
    reader = csv.DictReader(fileobj)
    for row in reader:
        active_thread_count.append(row['Active Thread Count'])
        active_processes.append(row['Active Processes'])
        idle_thread_count.append(row['Idle Thread Count'])

plt.figure(1)

plt.subplot(311)
plt.ylabel('Available Threads')
plt.fill_between(range(len(idle_thread_count)),
                 idle_thread_count, color='green')

plt.subplot(312)
plt.ylabel('Active Processes')
plt.fill_between(range(len(active_processes)),
                 active_processes, color='blue')

plt.subplot(313)
plt.xlabel('Maintenance Cycle')
plt.ylabel('Concurrent Requests')
plt.fill_between(range(len(active_thread_count)),
                 active_thread_count, color='red')

plt.show()

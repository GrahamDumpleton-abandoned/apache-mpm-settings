import csv
import sys

import matplotlib.pyplot as plt

active_process_count = []
active_processes = []
idle_process_count = []
process_creation = []

with open(sys.argv[1], 'rb') as fileobj:
    reader = csv.DictReader(fileobj)
    for row in reader:
        active_process_count.append(row['Active Process Count'])
        active_processes.append(row['Active Processes'])
        idle_process_count.append(row['Idle Process Count'])
        process_creation.append(row['Process Creation'])

plt.figure(1, figsize=(15, 9))

plt.subplot(411)
plt.ylabel('Concurrent Requests')
plt.fill_between(range(len(active_process_count)),
                 active_process_count, color='red')

plt.subplot(412)
plt.ylabel('Process Creation')
plt.fill_between(range(len(process_creation)),
                 process_creation, color='orange')

plt.subplot(413)
plt.ylabel('Active Processes')
plt.fill_between(range(len(active_processes)),
                 active_processes, color='blue')

plt.subplot(414)
plt.xlabel('Maintenance Cycle')
plt.ylabel('Available Processes')
plt.fill_between(range(len(idle_process_count)),
                 idle_process_count, color='green')

plt.show()

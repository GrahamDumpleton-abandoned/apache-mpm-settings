import sys
import prefork
import random

configuration = prefork.Configuration()

if len(sys.argv) > 1:
    fileobj = open(sys.argv[1], 'r')
    configuration.parse_settings(fileobj)

configuration.dump_settings()

simulator = prefork.Simulator(configuration)

simulator.dump_columns()
simulator.dump_statistics()

mu = 0.75
sigma = 0.01

for i in range(20):
    simulator.dump_statistics()

for i in range(int(mu*configuration.ap_daemons_limit)):
    simulator.increment_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

current = simulator.active_process_count

def traffic(capacity, maximum):
    target = max(0, min(random.normalvariate(mu, sigma), 1.0))
    count = min(int(target * maximum), capacity)
    return count

for i in range(configuration.ap_daemons_limit):
    count = traffic(simulator.active_processes,
        configuration.ap_daemons_limit)

    delta = count - current

    if delta > 0:
        for j in range(delta):
            simulator.increment_requests()
    elif delta < 0:
        for j in range(-delta):
            simulator.decrement_requests()

    simulator.process_maintenance()
    simulator.dump_statistics()
    current = simulator.active_process_count

for i in range(current):
    simulator.decrement_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

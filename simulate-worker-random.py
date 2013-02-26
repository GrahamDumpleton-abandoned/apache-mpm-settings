import sys
import worker
import random

configuration = worker.Configuration()

if len(sys.argv) > 1:
    fileobj = open(sys.argv[1], 'r')
    configuration.parse_settings(fileobj)

configuration.dump_settings()

simulator = worker.Simulator(configuration)

simulator.dump_columns()
simulator.dump_statistics()

mu = 0.5
sigma = 0.3

for i in range(20):
    simulator.dump_statistics()

for i in range(int(mu*(configuration.ap_daemons_limit *
        configuration.ap_threads_per_child))):
    simulator.increment_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

current = simulator.active_thread_count

def traffic(capacity, maximum):
    target = max(0, min(random.normalvariate(mu, sigma), 1.0))
    count = min(int(target * maximum), capacity)
    return count

for i in range(configuration.ap_daemons_limit *
        configuration.ap_threads_per_child):

    count = traffic(simulator.active_processes *
        configuration.ap_threads_per_child,
        configuration.ap_daemons_limit *
        configuration.ap_threads_per_child)

    delta = count - current

    if delta > 0:
        for j in range(delta):
            simulator.increment_requests()
    elif delta < 0:
        for j in range(-delta):
            simulator.decrement_requests()

    simulator.process_maintenance()
    simulator.dump_statistics()
    current = simulator.active_thread_count

for i in range(current):
    simulator.decrement_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

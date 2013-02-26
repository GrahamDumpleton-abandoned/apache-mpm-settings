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

for i in range(configuration.ap_daemons_limit):
    simulator.dump_statistics()

upskip = 1
for i in range(0, configuration.ap_daemons_limit *
        configuration.ap_threads_per_child, upskip):
    for j in range(upskip):
        simulator.increment_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

downskip = 1
for i in range(0, configuration.ap_daemons_limit *
        configuration.ap_threads_per_child, downskip):
    for j in range(downskip):
        simulator.decrement_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

for i in range(configuration.ap_daemons_limit):
    simulator.dump_statistics()

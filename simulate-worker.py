import sys
import worker

configuration = worker.Configuration()

if len(sys.argv) > 1:
    fileobj = open(sys.argv[1], 'r')
    configuration.parse_settings(fileobj)

configuration.dump_settings()

simulator = worker.Simulator(configuration)

simulator.dump_columns()
simulator.dump_statistics()

for i in range(configuration.ap_threads_per_child):
    simulator.dump_statistics()

skip = 1
for i in range(0, configuration.ap_daemons_limit *
        configuration.ap_threads_per_child, skip):
    for i in range(skip):
        simulator.increment_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

for i in range(configuration.ap_daemons_limit *
        configuration.ap_threads_per_child):
    simulator.decrement_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

for i in range(configuration.ap_threads_per_child):
    simulator.dump_statistics()

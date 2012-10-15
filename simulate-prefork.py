import sys
import prefork

configuration = prefork.Configuration()

if len(sys.argv) > 1:
    fileobj = open(sys.argv[1], 'r')
    configuration.parse_settings(fileobj)

configuration.dump_settings()

simulator = prefork.Simulator(configuration)

simulator.dump_columns()
simulator.dump_statistics()

for i in range(configuration.children_to_start*2):
    simulator.dump_statistics()

skip = 1
for i in range(0, configuration.ap_daemons_limit, skip):
    for i in range(skip):
        simulator.increment_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

for i in range(configuration.ap_daemons_limit):
    simulator.decrement_requests()
    simulator.process_maintenance()
    simulator.dump_statistics()

for i in range(configuration.children_to_start*2):
    simulator.dump_statistics()

import sys
import prefork

config = prefork.Configuration()

if len(sys.argv) > 1:
    fileobj = open(sys.argv[1], 'r')
    config.parse_settings(fileobj)

config.dump_settings()

import sys
import StringIO

def info(s, *args):
    print >> sys.stderr, s % args

def warn(s, *args):
    print >> sys.stderr, s % args

# Following is based on Apache 2.2.21 code base.

# Hardwired Worker MPM Defaults. These are what will be relied upon if no
# MPM settings are provided in the Apache configuration file.

DEFAULT_START_DAEMON = 5
DEFAULT_MAX_FREE_DAEMON = 10
DEFAULT_MIN_FREE_DAEMON = 5
DEFAULT_MAX_REQUESTS_PER_CHILD = 10000

DEFAULT_SERVER_LIMIT = 256
MAX_SERVER_LIMIT = 20000
HARD_THREAD_LIMIT = 1

MAX_SPAWN_RATE = 32

class Configuration(object):

    ap_daemons_to_start = 0

    ap_daemons_min_free = 0
    ap_daemons_max_free = 0

    ap_daemons_limit = 0

    server_limit = DEFAULT_SERVER_LIMIT

    ap_max_requests_per_child = 0

    directives = {
        'StartServers': 'set_daemons_to_start',
        'MinSpareServers': 'set_min_free_servers',
        'MaxSpareServers': 'set_max_free_servers',
        'MaxClients': 'set_max_clients',
        'ServerLimit': 'set_server_limit',
        'MaxRequestsPerChild': 'set_max_requests_per_child',
    }

    def set_defaults(self):
        self.ap_daemons_to_start = DEFAULT_START_DAEMON
        self.ap_daemons_min_free = DEFAULT_MIN_FREE_DAEMON
        self.ap_daemons_max_free = DEFAULT_MAX_FREE_DAEMON
        self.ap_daemons_limit = self.server_limit
        self.ap_max_requests_per_child = DEFAULT_MAX_REQUESTS_PER_CHILD

    def set_daemons_to_start(self, value):
        self.ap_daemons_to_start = value

    def set_min_free_servers(self, value):
        self.ap_daemons_min_free = value

        if self.ap_daemons_min_free <= 0:
            warn('WARNING: detected MinSpareServers set to non-positive.')
            warn('Resetting to 1 to avoid almost certain Apache failure.')
            warn('Please read the documentation.')

            self.ap_daemons_min_free = 1

    def set_max_free_servers(self, value):
        self.ap_daemons_max_free = value

    def set_max_clients(self, value):
        self.ap_daemons_limit = value

        if self.ap_daemons_limit > self.server_limit:
            warn('WARNING: MaxClients of %d exceeds ServerLimit value '
                    'of %d servers, ', self.ap_daemons_limit,
                    self.server_limit)
            warn('lowering MaxClients to %d.  To increase, please '
                    'see the ServerLimit directive', self.server_limit)

            self.ap_daemons_limit = self.server_limit

        elif self.ap_daemons_limit < 1:
            warn('WARNING: Require MaxClients > 0, setting to 1.')

            self.ap_daemons_limit = 1

    def set_server_limit(self, value):
        self.server_limit = value

        if self.server_limit < 1:
            warn('WARNING: Require ServerLimit > 0, setting to 1')

            self.server_limit = 1

    def set_max_requests_per_child(self, value):
        self.ap_max_requests_per_child = value

    def _parse_settings(self, fileobj):
        actions = {}
        for line in fileobj:
            directive, value = line.strip().split()
            if directive in self.directives:
                name = self.directives[directive]
                method = getattr(self, name, None)
                if method:
                    actions[name] = (method, value)

        for method, value in actions.values():
            method(int(value))

        # This stops thrashing were processes killed almost straight
        # after they have been created.

        if self.ap_daemons_max_free < self.ap_daemons_min_free + 1:
            self.ap_daemons_max_free = self.ap_daemons_min_free + 1

        # Can't start more than maximum number of daemons allowed.

        self.children_to_start = self.ap_daemons_to_start
        if self.children_to_start > self.ap_daemons_limit:
            self.children_to_start = self.ap_daemons_limit

    def parse_settings(self, fileobj):
        # We actually have to perform the parse twice to simulate
        # what Apache does as the server limit gets reset on the
        # first past based on values and then used by the second.

        data = fileobj.read()

        self.set_defaults()
        fileobj = StringIO.StringIO(data)
        self._parse_settings(fileobj)

        self.set_defaults()
        fileobj = StringIO.StringIO(data)
        self._parse_settings(fileobj)

    def dump_settings(self):
        info('daemons_to_start = %d', self.ap_daemons_to_start)
        info('children_to_start = %d', self.children_to_start)
        info('daemons_min_free = %d', self.ap_daemons_min_free)
        info('daemons_max_free = %d', self.ap_daemons_max_free)
        info('daemons_limit = %d', self.ap_daemons_limit)
        info('server_limit = %d', self.server_limit)
        info('max_requests_per_child = %d', self.ap_max_requests_per_child)

class Simulator(object):

    def __init__(self, configuration):
        self.configuration = configuration

        self.active_processes = configuration.children_to_start
        self.active_process_count = 0

        self.idle_process_count = self.active_processes

        self.idle_spawn_rate = 1

    def dump_columns(self):
        print 'Active Process Count,Active Processes,Idle Process Count'

    def dump_statistics(self):
        print ','.join(map(str, (self.active_process_count,
                self.active_processes, self.idle_process_count)))

    def increment_requests(self):
        if self.active_process_count < self.configuration.ap_daemons_limit:
            self.active_process_count += 1
            self.idle_process_count -= 1
            return True
        return False

    def decrement_requests(self):
        if self.active_process_count > 0:
            self.active_process_count -= 1
            self.idle_process_count += 1
            return True
        return False

    def increment_processes(self):
        if self.active_processes < self.configuration.ap_daemons_limit:
            self.active_processes += 1
            self.idle_process_count += 1
            return True
        return False

    def decrement_processes(self):
        if self.active_processes > 0:
            self.active_processes -= 1
            self.idle_process_count -= 1
            return True
        return False

    def process_maintenance(self):
        if self.idle_process_count > self.configuration.ap_daemons_max_free:
            self.decrement_processes()
            self.idle_spawn_rate = 1

        elif self.idle_process_count < self.configuration.ap_daemons_min_free:
            if self.active_processes == self.configuration.ap_daemons_limit:
                if (self.active_process_count >=
                        self.configuration.ap_daemons_limit):

                    if self.idle_process_count == 0:
                        # Reached MaxClients.
                        pass

                    else:
                        # Within MinSpareServers of MaxClients.
                        pass

            else:
                if self.idle_spawn_rate >= 8:
                    # Server seems too busy, increase StartServers
                    # or Min/MaxSpareThreads.
                    pass

                for i in range(self.idle_spawn_rate):
                    self.increment_processes()

                if self.idle_spawn_rate < MAX_SPAWN_RATE:
                    self.idle_spawn_rate *= 2
        else:
            self.idle_spawn_rate = 1

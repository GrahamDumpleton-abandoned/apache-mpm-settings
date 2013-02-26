import sys
import StringIO

def info(s, *args):
    print >> sys.stderr, s % args

def warn(s, *args):
    print >> sys.stderr, s % args

# Following is based on Apache 2.2.21 code base.

# Hardwired Worker MPM Defaults. These are what will be relied upon if no
# MPM settings are provided in the Apache configuration file.

DEFAULT_START_DAEMON = 3
DEFAULT_MAX_FREE_DAEMON = 10
DEFAULT_MIN_FREE_DAEMON = 3
DEFAULT_THREADS_PER_CHILD = 25
DEFAULT_MAX_REQUESTS_PER_CHILD = 10000

DEFAULT_SERVER_LIMIT = 16
MAX_SERVER_LIMIT = 20000
DEFAULT_THREAD_LIMIT = 64
MAX_THREAD_LIMIT = 20000

MAX_SPAWN_RATE = 32

class Configuration(object):

    ap_threads_per_child = 0
    ap_daemons_to_start = 0

    min_spare_threads = 0
    max_spare_threads = 0

    ap_daemons_limit = 0

    server_limit = DEFAULT_SERVER_LIMIT
    thread_limit = DEFAULT_THREAD_LIMIT

    ap_max_requests_per_child = 0

    directives = {
        'StartServers': 'set_daemons_to_start',
        'MinSpareThreads': 'set_min_spare_threads',
        'MaxSpareThreads': 'set_max_spare_threads',
        'MaxClients': 'set_max_clients',
        'ThreadsPerChild': 'set_threads_per_child',
        'ServerLimit': 'set_server_limit',
        'ThreadLimit': 'set_thread_limit',
        'MaxRequestsPerChild': 'set_max_requests_per_child',
    }

    def set_defaults(self):
        self.ap_daemons_to_start = DEFAULT_START_DAEMON
        self.min_spare_threads = (DEFAULT_MIN_FREE_DAEMON *
                DEFAULT_THREADS_PER_CHILD)
        self.max_spare_threads = (DEFAULT_MAX_FREE_DAEMON *
                DEFAULT_THREADS_PER_CHILD)
        self.ap_daemons_limit = self.server_limit
        self.ap_threads_per_child = DEFAULT_THREADS_PER_CHILD
        self.ap_max_requests_per_child = DEFAULT_MAX_REQUESTS_PER_CHILD

    def set_daemons_to_start(self, value):
        self.ap_daemons_to_start = value

    def set_min_spare_threads(self, value):
        self.min_spare_threads = value

        if self.min_spare_threads <= 0:
            warn('WARNING: detected MinSpareThreads set to non-positive.')
            warn('Resetting to 1 to avoid almost certain Apache failure.')
            warn('Please read the documentation.')

            self.min_spare_threads = 1

    def set_max_spare_threads(self, value):
        self.max_spare_threads = value

    def set_max_clients(self, value):
        max_clients = value

        if max_clients < self.ap_threads_per_child:
            warn('WARNING: MaxClients (%d) must be at least as large',
                    max_clients)
            warn('as ThreadsPerChild (%d). Automatically',
                    self.ap_threads_per_child)
            warn('increasing MaxClients to %d.', self.ap_threads_per_child)

            max_clients = self.ap_threads_per_child

        self.ap_daemons_limit = max_clients / self.ap_threads_per_child

        if (max_clients > 0) and (max_clients % self.ap_threads_per_child):
            warn('WARNING: MaxClients (%d) is not an integer multiple',
                    self.max_clients)
            warn('of ThreadsPerChild (%d), lowering MaxClients to %d',
                    self.ap_threads_per_child,
                    self.ap_daemons_limit * self.ap_threads_per_child)
            warn('for a maximum of %d child processes.',
                    self.ap_daemons_limit)

            max_clients = self.ap_daemons_limit * self.ap_threads_per_child

        if self.ap_daemons_limit > self.server_limit:
            wanr('WARNING: MaxClients of %d would require %d servers,',
                    max_clients, self.ap_daemons_limit)
            warn('and would exceed the ServerLimit value of %d.',
                    self.server_limit)
            warn('Automatically lowering MaxClients to %d. To increase,',
                    self.server_limit * self.ap_threads_per_child)

            self.ap_daemons_limit = self.server_limit

        elif self.ap_daemons_limit < 1:
            warn('WARNING: Require MaxClients > 0, setting to 1.')

            self.ap_daemons_limit = 1

    def set_threads_per_child(self, value):
        self.ap_threads_per_child = value

        if self.ap_threads_per_child > self.thread_limit:
            warn('WARNING: ThreadsPerChild of %d exceeds ThreadLimit '
                    'value of %d', self.ap_threads_per_child,
                     self.thread_limit)
            warn('threads, lowering ThreadsPerChild to %d. To increase, '
                   'please see the', self.thread_limit)
            warn('ThreadLimit directive.')

            self.ap_threads_per_child = self.thread_limit

        elif self.ap_threads_per_child < 1:
            warn('WARNING: Require ThreadsPerChild > 0, setting to 1')

            self.ap_threads_per_child = 1

    def set_server_limit(self, value):
        self.server_limit = value

        if self.server_limit < 1:
            warn('WARNING: Require ServerLimit > 0, setting to 1')

            self.server_limit = 1

    def set_thread_limit(self, value):
        self.thread_limit = value

        if self.thread_limit < 1:
            warn('WARNING: Require ThreadLimit > 0, setting to 1')

            self.thread_limit = 1

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

        # Need to make sure that ThreadsPerChild is always done first.

        item = actions.pop('ThreadsPerChild', None)

        if item:
            method, value = item
            method(int(value))

        for method, value in actions.values():
            method(int(value))

        # This stops thrashing were processes killed almost straight
        # after they have been created.

        if self.max_spare_threads < (self.min_spare_threads +
                self.ap_threads_per_child):
            self.max_spare_threads = (self.min_spare_threads +
                self.ap_threads_per_child)

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
        info('threads_per_child = %d', self.ap_threads_per_child)
        info('daemons_to_start = %d', self.ap_daemons_to_start)
        info('children_to_start = %d', self.children_to_start)
        info('min_spare_threads = %d', self.min_spare_threads)
        info('max_spare_threads = %d', self.max_spare_threads)
        info('daemons_limit = %d', self.ap_daemons_limit)
        info('server_limit = %d', self.server_limit)
        info('thread_limit = %d', self.thread_limit)
        info('max_requests_per_child = %d', self.ap_max_requests_per_child)

class Simulator(object):

    def __init__(self, configuration):
        self.configuration = configuration

        self.active_processes = configuration.children_to_start
        self.active_thread_count = 0

        self.idle_thread_count = (self.active_processes *
                configuration.ap_threads_per_child)

        self.idle_spawn_rate = 1

        self.process_creation = 0

    def dump_columns(self):
        print ('Active Thread Count,Active Processes,Idle Thread Count,'
                'Process Creation')

    def dump_statistics(self):
        print ','.join(map(str, (self.active_thread_count,
                self.active_processes, self.idle_thread_count,
                self.process_creation)))
        self.process_creation = 0

    def increment_requests(self):
        if self.active_thread_count < (self.configuration.ap_daemons_limit *
                self.configuration.ap_threads_per_child):
            self.active_thread_count += 1
            self.idle_thread_count -= 1
            return True
        return False

    def decrement_requests(self):
        if self.active_thread_count > 0:
            self.active_thread_count -= 1
            self.idle_thread_count += 1
            return True
        return False

    def increment_processes(self):
        if self.active_processes < self.configuration.ap_daemons_limit:
            self.active_processes += 1
            self.idle_thread_count += self.configuration.ap_threads_per_child
            self.process_creation += 1
            return True
        return False

    def decrement_processes(self):
        if self.active_processes > 0:
            self.active_processes -= 1
            self.idle_thread_count -= self.configuration.ap_threads_per_child
            self.process_creation -= 1
            return True
        return False

    def process_maintenance(self):
        if self.idle_thread_count > self.configuration.max_spare_threads:
            self.decrement_processes()
            self.idle_spawn_rate = 1

        elif self.idle_thread_count < self.configuration.min_spare_threads:
            if self.active_processes == self.configuration.ap_daemons_limit:
                if self.active_thread_count >= (
                        self.configuration.ap_daemons_limit *
                        self.configuration.ap_threads_per_child):

                    if self.idle_thread_count == 0:
                        # Reached MaxClients.
                        pass

                    else:
                        # Within MinSpareThreads of MaxClients.
                        pass

            else:
                if self.idle_spawn_rate >= 8:
                    # Server seems to busy, increase StartServers,
                    # ThreadsPerChild or Min/MaxSpareThreads.
                    pass

                for i in range(self.idle_spawn_rate):
                    self.increment_processes()

                if self.idle_spawn_rate < MAX_SPAWN_RATE:
                    self.idle_spawn_rate *= 2
        else:
            self.idle_spawn_rate = 1

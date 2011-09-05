#!/usr/bin/env python
"""
Construct a build order diagram from a Make build system. In order to get all
required information (start time, end time, arguments) about the invoked sub
processes, strace is used.

To use this utility, a filtered strace log file of Make is required:

  strace -ftts 1024 make -Bsj12 2>&1|egrep exit_group\|vfork\|execve > make.log
  cat make.log | ./build_order.py > static/data/strace.json

"""

# TODO: strace does not output the date (only the time), so strace logs
# containing time string from two or more days will result in garbage.

import simplejson as json


class Syscall(object):
    def __init__(self, start_time, cmd):
        self.cmd = cmd
        self.duration = 0
        self.end = 0
        self.start = start_time

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<Syscall duration=%d cmd=%s>' % (self.duration, self.cmd)

    def to_dict(self):
        return {'cmd': self.cmd, 'duration': self.duration,
                'start': self.start, 'end': self.end}


class JSONSyscallEncoder(json.JSONEncoder):

    def default(self, syscall):
        if isinstance(syscall, Syscall):
            return syscall.to_dict()
        return json.JSONEncoder.default(self, syscall)

def ptime(x):
    """
    Convert an ISO time string into milliseconds.
    
    >>> ptime('16:09:18.502932')
    332
    """
    h, m, s, micro = int(x[0:2]), int(x[3:5]), int(x[6:8]), int(x[9:15])
    return (micro / 1000) + 1000 * (s + 60 * (m + 60 * h))


def parse_strace_output(fd, duration_threshold):
    """
    The first line of the given file descriptor should contain the absolute start
    time (format in ``%H:%M:%S.%f``) of the master Make process, followed by a
    space and the complete ``execve`` system call.
    """
    zero_line = fd.readline().split(None, 1)
    zero_time = ptime(zero_line[0])
    origin = Syscall(0, zero_line[1].strip())

    syscalls = {0: [origin]}

    for line in fd:
        if line.startswith('['):
            pid, time_string, cmd = line.split(None, 3)[1:]
            pid = int(pid[:-1])
        else:
            pid = 0
            time_string, cmd = line.split(None, 1)

        cmd = cmd.strip()

        # FIXME: vfork system calls are skipped for now.
        if cmd.startswith('vfork'):
            continue

        cur_time = ptime(time_string) - zero_time

        # Execute a syscall in the current process (save its start time).
        if cmd.startswith('execve') or cmd.startswith('<... execve resumed>'):
            syscall = Syscall(cur_time, cmd)
            if pid not in syscalls:
                syscalls[pid] = []
            syscalls[pid].append(syscall)
        # A syscall is finished, calculate its duration (using end time).
        elif cmd.startswith('exit_group'):
            syscall = syscalls[pid][-1]
            assert syscall.duration == 0
            syscall.end = cur_time
            syscall.duration = cur_time - syscall.start

    processes = {}

    for pid, calls in syscalls.iteritems():
        type = parse_syscall_type(calls)
        parent = 0
        start = calls[0].start
        end = calls[-1].end
        duration = end - start

        if duration < duration_threshold:
            continue

        processes[pid] = {'type': type, 'parent': parent, 'syscalls': calls,
                'start': start, 'end': end, 'duration': duration}

    processes['length'] = len(processes)

    return processes


def parse_syscall_type(syscalls):
    pos = 1
    syscall = syscalls[-pos]
    syscall_count = len(syscalls)

    while pos < syscall_count \
            and syscall.cmd.startswith('<... execve resumed>'):
        pos += 1
        syscall = syscalls[-pos]

    if '/usr/bin/make' in syscall.cmd:
        syscall_type ='make'
    else:
        syscall_type = 'unknown'

    return syscall_type


def dump_json(processes):
    json = JSONSyscallEncoder().encode({'version': 100, 'processes': processes})
    print json


if __name__ == '__main__':
    import sys
    duration_threshold = 0.1 * 1000
    processes = parse_strace_output(sys.stdin, duration_threshold)
    dump_json(processes)

    #for pid, tasks in syscalls.iteritems():
    #    if pid == 0:
    #        continue

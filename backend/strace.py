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
        self.children = []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<Syscall duration=%d cmd=%s>' % (self.duration, self.cmd)

    def to_dict(self):
        return {'cmd': self.cmd, 'duration': self.duration,
                'start': self.start, 'end': self.end, 
                'children': self.children}


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
    Transform the strace log file into processes and a timeline. Processes are
    returned as a dictionary, which maps pids to their corresponding process
    structure. The timeline is a list of pids, sorted by start time of the
    process.

    The first line of the given file descriptor should contain the absolute
    start time (format in ``%H:%M:%S.%f``) of the master Make process, followed
    by a space and the complete ``execve`` system call.
    """
    zero_line = fd.readline().split(None, 1)
    zero_time = ptime(zero_line[0])
    zero_pid = 0
    origin = Syscall(zero_pid, zero_line[1].strip())

    # Convert threshold in seconds to milliseconds.
    duration_threshold = duration_threshold * 1000

    syscalls = {zero_pid: [origin]}

    for line in fd:
        if line.startswith('['):
            pid, time_string, cmd = line.split(None, 3)[1:]
            pid = int(pid[:-1])
        elif line.startswith('Process '):
            # exit_group system calls are followed by a Process status line.
            continue
        elif line.startswith(') '):
            # vfork system calls are followed by a line starting with a closing
            # parentheis, followed by an equal sign and the syscall's exit code.
            continue
        else:
            pid = zero_pid
            time_string, cmd = line.split(None, 1)

        cmd = cmd.strip()

        try:
            cur_time = ptime(time_string) - zero_time
        except ValueError:
            print 'line = ', line
            raise

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
        elif cmd.startswith('vfork') or cmd.startswith('<... vfork resumed>'):
            # Make sure the vfork call is not unfinished.
            pos = cmd.find(') = ')
            if pos > -1:
                print cmd
                child_pid = cmd[pos+4:]
                syscalls[pid][-1].children.append(child_pid)



    processes = {}
    timeline = []

    for pid, calls in syscalls.iteritems():
        type = parse_syscall_type(calls)
        parent = 0
        start = calls[0].start
        end = calls[-1].end
        duration = end - start

        if duration < duration_threshold:
            continue

        timeline.append((pid, calls[0].start))
        processes[pid] = {'type': type, 'parent': parent, 'syscalls': calls,
                'start': start, 'end': end, 'duration': duration}

    processes['length'] = len(processes)

    # Sort processes by start time.
    sorted(timeline, key=lambda x: x[1])
    timeline = map(lambda x: x[0], timeline)

    return processes, timeline


def parse_syscall_type(syscalls):
    pos = 1
    syscall = syscalls[-pos]
    syscall_count = len(syscalls)

    while pos < syscall_count \
            and syscall.cmd.startswith('<... execve resumed>'):
        pos += 1
        syscall = syscalls[-pos]

    pos = syscall.cmd.find('", [')
    if pos > -1:
        cmd = syscall.cmd[8: pos]  # 8 = 'execve("'
    else:
        cmd = syscall.cmd

    if '/make' in cmd or '/gmake' in cmd:
        syscall_type ='make'
    elif '/g++' in cmd or '/c++' in cmd or '/cc1plus' in cmd:
        syscall_type ='cpp'
    elif '/gcc' in cmd or '/cc1' in cmd:
        syscall_type ='cc'
    elif '/sh' in cmd:
        syscall_type ='sh'
    else:
        syscall_type = 'unknown'

    return syscall_type


def dump_json(fd, processes, timeline, properties):
    obj = {'version': 100, 'processes': processes, 'timeline': timeline,
           'properties': properties}
    json = JSONSyscallEncoder().encode(obj)
    print >>fd, json


def main(args):
    properties = {'threshold': args.threshold}
    processes, timeline = parse_strace_output(args.input, args.threshold)
    dump_json(args.output, processes, timeline, properties)

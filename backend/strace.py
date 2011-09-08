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
        return str(self.to_dict())

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
    Transform the strace log file into processes and a timeline. Processes are
    returned as a dictionary, which maps pids to their corresponding process
    structure. The timeline is a list of pids, sorted by start time of the
    process.

    The lines of the given file descriptor should contain the process id, a
    space, the absolute start time (format in ``%H:%M:%S.%f``) of the event,
    followed by a space and the complete ``execve`` system call.
    """
    # Convert threshold in seconds to milliseconds.
    duration_threshold = duration_threshold * 1000

    syscalls = {}
    parents = {}
    zero_time = 0
    zero_pid = 0

    for line in fd:
        pid, time_string, cmd = line.split(None, 2)
        pid = int(pid)
        cmd = cmd.strip()

        try:
            cur_time = ptime(time_string) - zero_time
        except ValueError:
            print 'line = ', line
            raise
        
        # First line is the master Make process, which defines the zero time.
        if zero_time == 0:
            zero_time = cur_time
            zero_pid = pid
            syscall = Syscall(0, cmd)
            syscalls[pid] = [syscall]
            continue

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
        elif cmd.startswith('vfork') or cmd.startswith('<... vfork resumed>') \
                or cmd.startswith('clone') \
                or cmd.startswith('<... clone resumed>'):
            
            # Make sure the vfork call is not unfinished.
            if '<unfinished ...>' in cmd:
                continue
        
            # FIXME: what to do with these ERESTARTNOINTR kernel signals?
            if ' ERESTARTNOINTR ' in cmd:
                continue

            pos = cmd.find(' = ')
            assert pos > -1
            child_pid = int(cmd[pos+3:])
            parents[child_pid] = pid
            syscalls[pid][-1].children.append(child_pid)

    processes = {}

    for pid, calls in syscalls.iteritems():
        process_type = parse_syscall_type(calls)

        if pid == zero_pid:
            parent = 0
        else:
            parent = parents[pid]

        start = calls[0].start
        end = calls[-1].end
        duration = end - start

        try:
            assert not any(c.children for c in calls[:-1])
            assert parent > 0 or pid == zero_pid
            assert start > 0 or pid == zero_pid
            assert end > 0
            assert duration > 0
        except AssertionError:
            print pid, len(calls)
            print calls
            raise

        #if duration < duration_threshold:
        #   continue

        processes[pid] = {'type': process_type, 'parent': parent, 
                'syscalls': calls, 'start': start, 'end': end, 
                'duration': duration, 'children': calls[-1].children}

    processes['root'] = zero_pid

    return processes


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


def dump_json(fd, processes, properties):
    obj = {'version': 100, 'processes': processes, 'properties': properties}
    json = JSONSyscallEncoder().encode(obj)
    print >>fd, json


def main(args):
    properties = {'threshold': args.threshold}
    processes = parse_strace_output(args.input, args.threshold)
    dump_json(args.output, processes, properties)

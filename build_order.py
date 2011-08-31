#!/usr/bin/env python
"""
Construct a build order diagram from a Make build system. In order to get all
required information (start time, end time, arguments) about the invoked sub
processes, strace is used.

To use this utility, a filtered strace log file of Make is required:

  strace -ftts 1024 make -Bsj12 2>&1|egrep exit_group\|vfork\|execve > make.log
  cat make.log | ./build_order.py

"""

# TODO: strace does not output the date (only the time), so strace logs
# containing time string from two or more days will result in garbage.

import simplejson as json


class Process(object):
    def __init__(self, start_time, cmd):
        self.cmd = cmd
        self.duration = 0
        self.end = 0
        self.start = start_time

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<Process duration=%d cmd=%s>' % (self.duration, self.cmd)

    def to_dict(self):
        return {'cmd': self.cmd, 'duration': self.duration,
                'start': self.start, 'end': self.end}


class JSONProcessEncoder(json.JSONEncoder):

    def default(self, process):
        if isinstance(process, Process):
            return process.to_dict()
        return json.JSONEncoder.default(self, process)

def ptime(x):
    """
    Convert an ISO time string into milliseconds.
    
    >>> ptime('16:09:18.502932')
    332
    """
    h, m, s, micro = int(x[0:2]), int(x[3:5]), int(x[6:8]), int(x[9:15])
    return (micro / 1000) + 1000 * (s + 60 * (m + 60 * h))


def parse_strace_output(fd):
    """
    The first line of the given file descriptor should contain the absolute start
    time (format in ``%H:%M:%S.%f``) of the master Make process, followed by a
    space and the complete ``execve`` function call.
    """
    zero_line = fd.readline().split(None, 1)
    zero_time = ptime(zero_line[0])
    zero_process = Process(0, zero_line[1].strip())

    processes = {0: [zero_process]}

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
        #print '%d | %s | %s' %  (pid, cur_time, cmd)

        # Execute a command in the current process (save its start time).
        if cmd.startswith('execve') or cmd.startswith('<... execve resumed>'):
            process = Process(cur_time, cmd)
            if pid not in processes:
                processes[pid] = []
            processes[pid].append(process)
        # A command is finished, calculate its duration (using end time).
        elif cmd.startswith('exit_group'):
            process = processes[pid][-1]
            assert process.duration == 0
            process.end = cur_time
            process.duration = cur_time - process.start

    return processes


def parse_process_type(tasks):
    pos = 1
    task = tasks[-pos]
    task_count = len(tasks)

    while pos < task_count and task.cmd.startswith('<... execve resumed>'):
        pos += 1
        task = tasks[-pos]

    if '/usr/bin/make' in task.cmd:
        process_type ='make'
    else:
        process_type = 'unknown'

    return process_type


if __name__ == '__main__':
    import sys
    processes = parse_strace_output(sys.stdin)

    render_html(processes)

    #for pid, tasks in processes.iteritems():
    #    if pid == 0:
    #        continue

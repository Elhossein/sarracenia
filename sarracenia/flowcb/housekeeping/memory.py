#!/usr/bin/python3
"""
Default `on_heartbeat` handler that restarts components to deal with memory leaks.

Setting `MemoryMax` in the config overrides the following:

The plugin processes the first `MemoryBaseLineFile` items to reach a steady state before setting the threshold
(messages-in for subscribers, messages-posted for posting programs).
Once processed, the `MemoryMax` threshold is set to `MemoryMultiplier` * current memory in use.

If memory use ever exceeds the `MemoryMax` threshold, then the plugin triggers a restart, which should reduce the memory consumption.



Parameters
----------

MemoryMax : size (default: none)
    Hard coded maximum for tolerable memory consumption.
    Must be suffixed with k/m/g for Kilo/Mega/Giga byte values.
    If not set then the following options will have an effect:

MemoryBaseLineFile : int, optional (default: 100)
    How many files to process before measuring to establish the baseline memory usage.
    (how many files are expected to process before a steady state is reached)

MemoryMultiplier : int, optional (default: 3)
    How many times past the steady state memory footprint you want to allow the component to grow before considering it a memory leak.
    It could be normal for memory usage to grow, especially if plugins store data in memory.


Returns
-------
    Nothing, restarts components if memory usage is outside of configured thresholds.
"""

import logging
from pickle import TRUE
import humanize
import os
import psutil
from sarracenia.config import chunksize_from_str
from sarracenia.flowcb import FlowCB
from sarracenia.sr import sr_GlobalState
import sys

logger = logging.getLogger(__name__)


class Memory(FlowCB):

    def __init__(self, options):
        self.o = options
        # Set option to neg value to determine if user set in config
        self.o.add_option('MemoryMax', 'size', '-1k')
        self.o.add_option('MemoryBaseLineFile', 'count', 100)
        self.o.add_option('MemoryMultiplier', 'float', 3)

        self.threshold = None
        ''' Per-process maximum memory footprint that is considered too large, forcing a process restart.'''
        self.transferCount = 0
        self.msgCount = 0

    def on_housekeeping(self):
        logger.info(f"According to sys.argv:\n\t{sys.argv}")
        mem = psutil.Process().memory_info().vms
        # TODO: Should this be instead in logger? Why does it exist here?
        # Change this class to resources so it encapsulates more appropriately.
        ost = os.times()
        logger.info(f"Current Memory cpu_times: user={ost.user} system={ost.system} elapse={ost.elapsed}")

        # We must set a threshold **after** the config file has been parsed.
        if self.threshold is None:
            # If the config set something, use it. 
            if self.o.MemoryMax != -1024:
                self.threshold = self.o.MemoryMax

            if self.threshold is None:
                # No user input set, now to figure out what our baseline memory usage is at a steady state
                #   Process at least MemoryBaseLineFile(s) then get a memory reading before actually setting our memory threshold to trigger restart. 
                if (self.transferCount < self.o.MemoryBaseLineFile) and (self.msgCount < self.o.MemoryBaseLineFile):
                    # Not enough files processed for steady state, continue to wait..
                    logger.info(f"Current mem usage: {humanize.naturalsize(mem, binary=True)}, accumulating count ({self.transferCount} or {self.msgCount}/{self.o.MemoryBaseLineFile} so far) before self-setting threshold")
                    return True

                self.threshold = int(self.o.MemoryMultiplier * mem)

            logger.info(f"Memory threshold set to: {humanize.naturalsize(self.threshold, binary=True)}")

        logger.info(f"Current Memory usage: {humanize.naturalsize(mem, binary=True)} / {humanize.naturalsize(self.threshold, binary=True)} = {(mem/self.threshold):.2%}")

        if mem > self.threshold:
            self.restart()
        # self.restart()

        return True

    def restart(self):
        """
        """
        # Do an in-place restart (keeps pid)
        logger.info(f"Memory threshold surpassed! Triggering a restart for '{sys.executable}' with '{sys.argv}'")
        # FIXME Verify this actually works in Windows...
        os.execl(sys.executable, sys.executable, * sys.argv)

        # cmd_list = []

        # program_name == poll|post|sarra|sender|shovel|subscribe|watch
        # cmd_list.append(self.o.program_name)

        # We essentially want to run : sr3 <options> restart <config>.. I think?
        # cmd_list.append('sr3')
        # sys.argv == ['/.../sr3/sarracenia/instance.py', '--no', '1', 'start|restart|stop', 'poll|post|sarra|sender|shovel|subscribe|watch/<configFileName>']
        # cmd_list.extend(sys.argv[1:])
        # cmd_list[cmd_list.index('start')] = 'restart'

        # logger.info(f"Memory threshold surpassed! Triggering a restart with '{cmd_list}'")
        # sr_GlobalState.run_command(self, cmd_list)

        # Do an in-place restart (keeps pid)

    def after_work(self, worklist):
        self.transferCount += len(worklist.ok)
        # if self.threshold is not None:
        #    TODO: Remove this callback when isue #444 is implemented

    def after_accept(self, worklist):
        self.msgCount += len(worklist.incoming)
        # if self.threshold is not None:
        #    TODO: Remove this callback when isue #444 is implemented

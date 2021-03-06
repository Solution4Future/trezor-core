import utime

from uheapq import heappop, heappush, heapify
from .utils import type_gen
from . import msg
from . import log

if __debug__:
    # for performance stats
    import array
    log_delay_pos = 0
    log_delay_rb_len = const(10)
    log_delay_rb = array.array('i', [0] * log_delay_rb_len)

paused_tasks = {}  # {message interface: [task]}
schedule_counter = 0
scheduled_tasks = []  # heap: [(time, counter, task, value)]
MAX_SELECT_DELAY = const(1000000)

# message interfaces:
# 0-255  - USB HID
# 256    - touch event interface

TOUCH = const(256)  # interface
TOUCH_START = const(1)  # event
TOUCH_MOVE = const(2)  # event
TOUCH_END = const(4)  # event


def schedule_task(task, value=None, time=None):
    global schedule_counter
    if time is None:
        time = utime.ticks_us()
    heappush(scheduled_tasks, (time, schedule_counter, task, value))
    schedule_counter += 1


def unschedule_task(task):
    global scheduled_tasks
    scheduled_tasks = [t for t in scheduled_tasks if t[1] is not task]
    heapify(scheduled_tasks)


def pause_task(task, iface):
    paused_tasks.setdefault(iface, []).append(task)


def unpause_task(task):
    for iface in paused_tasks:
        if task in paused_tasks[iface]:
            paused_tasks[iface].remove(task)


def run_task(task, value):
    try:
        if isinstance(value, Exception):
            result = task.throw(value)
        else:
            result = task.send(value)
    except StopIteration as e:
        log.debug(__name__, '%s finished', task)
    except Exception as e:
        log.exception(__name__, e)
    else:
        if isinstance(result, Syscall):
            result.handle(task)
        elif result is None:
            schedule_task(task)
        else:
            log.error(__name__, '%s is unknown syscall', result)


def handle_message(message):
    if not paused_tasks:
        return
    iface, *value = message
    tasks = paused_tasks.pop(iface, ())
    for task in tasks:
        run_task(task, value)


def handle_timeout():
    if not scheduled_tasks:
        return
    _, _, task, value = heappop(scheduled_tasks)
    run_task(task, value)


def run_forever():
    if __debug__:
        global log_delay_pos
    while True:
        if scheduled_tasks:
            t, _, _, _ = scheduled_tasks[0]
            delay = t - utime.ticks_us()
        else:
            delay = MAX_SELECT_DELAY
        if __debug__:
            # add current delay to ring buffer for performance stats
            log_delay_rb[log_delay_pos] = delay
            log_delay_pos = (log_delay_pos + 1) % log_delay_rb_len
        message = msg.select(delay)
        if message:
            handle_message(message)
        else:
            handle_timeout()


class Syscall():

    def __iter__(self):
        return (yield self)


class Sleep(Syscall):

    def __init__(self, delay_us):
        self.time = delay_us + utime.ticks_us()

    def handle(self, task):
        schedule_task(task, self, self.time)


class Select(Syscall):

    def __init__(self, iface):
        self.iface = iface

    def handle(self, task):
        pause_task(task, self.iface)


NO_VALUE = ()


class Future(Syscall):

    def __init__(self):
        self.value = NO_VALUE
        self.task = None

    def handle(self, task):
        self.task = task
        if self.value is not NO_VALUE:
            self._deliver()

    def resolve(self, value):
        if self.value is NO_VALUE:
            self.value = value
            if self.task is not None:
                self._deliver()

    def _deliver(self):
        schedule_task(self.task, self.value)


class Wait(Syscall):

    def __init__(self, children, wait_for=1, exit_others=True):
        self.children = children
        self.wait_for = wait_for
        self.exit_others = exit_others
        self.scheduled = []
        self.finished = []
        self.callback = None

    def handle(self, task):
        self.callback = task
        self.scheduled = [self._wait(c) for c in self.children]
        for ct in self.scheduled:
            schedule_task(ct)

    def exit(self):
        for task in self.scheduled:
            if task not in self.finished:
                unschedule_task(task)
                unpause_task(task)
                task.close()

    def _wait(self, child):
        try:
            if isinstance(child, type_gen):
                result = yield from child
            else:
                result = yield child
        except Exception as e:
            self._finish(child, e)
        else:
            self._finish(child, result)

    def _finish(self, child, result):
        self.finished.append(child)
        if self.wait_for == len(self.finished) or isinstance(result, Exception):
            if self.exit_others:
                self.exit()
            schedule_task(self.callback, result)

    def __iter__(self):
        try:
            return (yield self)
        except:
            self.exit()
            raise

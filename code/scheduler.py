import sys
from usr.threading import Thread, Condition, AsyncTask
from usr.datetime import DateTime, TimeDelta


class HeapAlgorithm(object):

    @classmethod
    def __siftdown(cls, heap, startpos, pos):
        newitem = heap[pos]
        while pos > startpos:
            parentpos = (pos - 1) >> 1
            parent = heap[parentpos]
            if newitem < parent:
                heap[pos] = parent
                pos = parentpos
                continue
            break
        heap[pos] = newitem

    @classmethod
    def __siftup(cls, heap, pos):
        endpos = len(heap)
        startpos = pos
        newitem = heap[pos]
        childpos = 2 * pos + 1
        while childpos < endpos:
            rightpos = childpos + 1
            if rightpos < endpos and not heap[childpos] < heap[rightpos]:
                childpos = rightpos
            heap[pos] = heap[childpos]
            pos = childpos
            childpos = 2 * pos + 1
        heap[pos] = newitem
        cls.__siftdown(heap, startpos, pos)

    @classmethod
    def heapify(cls, sequence):
        if not isinstance(sequence, list):
            raise TypeError("`sequence` must be instance of list")
        n = len(sequence)
        for i in reversed(range(n // 2)):
            cls.__siftup(sequence, i)

    @classmethod
    def pop(cls, heap):
        lastelt = heap.pop()  # raise IndexError if heap is empty
        if heap:
            returnitem = heap[0]
            heap[0] = lastelt
            cls.__siftup(heap, 0)
            return returnitem
        return lastelt

    @classmethod
    def push(cls, heap, item):
        heap.append(item)
        cls.__siftdown(heap, 0, len(heap) - 1)

    @classmethod
    def poppush(cls, heap, item):
        """more efficient than pop() followed by push()"""
        returnitem = heap[0]  # raise IndexError if heap is empty
        heap[0] = item
        cls.__siftup(heap, 0)
        return returnitem

    @classmethod
    def pushpop(cls, heap, item):
        """more efficient than push() followed by pop()"""
        if heap and heap[0] < item:
            item, heap[0] = heap[0], item
            cls.__siftup(heap, 0)
        return item


class BaseTrigger(object):
    MAX_CALIBRATION_TIMEOUT = 600

    def __init__(self):
        self.next_run_time = None

    def get_remaining_seconds(self):
        # WARN: max remaining is TimeDelta(seconds=0x20C49B)
        value = (self.next_run_time - DateTime.now()).total_seconds()
        # time calibration
        return value if value <= self.MAX_CALIBRATION_TIMEOUT else self.MAX_CALIBRATION_TIMEOUT

    def update(self):
        """overwritten to set self.next_run_time, if valid return True else False"""
        raise NotImplementedError("BaseTrigger.update must be overwritten by subclass")


class IntervalTrigger(BaseTrigger):

    def __init__(self, interval, start_time=None, end_time=None):
        self.interval = interval
        self.start_time = start_time
        self.end_time = end_time
        super().__init__()

    def update(self):
        self.next_run_time = DateTime.now() + TimeDelta(seconds=self.interval)
        if self.start_time is not None and self.start_time > self.next_run_time:
            self.next_run_time = self.start_time
        return True if self.end_time is None else self.next_run_time <= self.end_time


class DateTimeTrigger(BaseTrigger):

    def __init__(self, datetime):
        self.datetime = datetime
        super().__init__()

    def update(self):
        self.next_run_time = self.datetime
        return self.next_run_time > DateTime.now()


class CronTrigger(BaseTrigger):

    def __init__(self, hour, minute):
        self.hour = hour
        self.minute = minute
        super().__init__()

    def update(self):
        current_time = DateTime.now()
        clock_time = current_time.replace(hour=self.hour, minute=self.minute, second=0)
        if clock_time > current_time:
            self.next_run_time = clock_time
        else:
            self.next_run_time = clock_time + TimeDelta(days=1)
        return True


class TriggerFactory(object):

    @staticmethod
    def create(interval=None, datetime=None, cron=(), start_time=None, end_time=None):
        if all([interval, datetime, cron]):
            raise ValueError("can only choose one from [interval, datetime, cron]")
        if isinstance(interval, int) and interval > 0:
            trigger = IntervalTrigger(interval, start_time=start_time, end_time=end_time)
        elif isinstance(datetime, DateTime):
            trigger = DateTimeTrigger(datetime)
        elif isinstance(cron, (tuple, list)):
            trigger = CronTrigger(hour=cron[0], minute=cron[1])
        else:
            raise ValueError("can not build trigger object according to params!!!")
        return trigger


class Task(object):

    def __init__(self, title="N/A", target=None, args=(), kwargs=None, sync=True, trigger=None):
        if not callable(target):
            raise TypeError("`target` must be callable")
        if not isinstance(trigger, (IntervalTrigger, DateTimeTrigger, CronTrigger)):
            raise TypeError("`trigger` must be instance of (IntervalTrigger, DateTimeTrigger, CronTrigger)")
        self.title = title
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs or {}
        self.trigger = trigger
        self.sync = sync

    def __str__(self):
        return "{}(title={})".format(type(self).__name__, repr(self.title))

    def __lt__(self, other):
        return self.trigger.next_run_time < other.trigger.next_run_time

    def run(self):
        try:
            if self.sync:
                self.__target(*self.__args, **self.__kwargs)
            else:
                AsyncTask(target=self.__target, args=self.__args, kwargs=self.__kwargs).delay()
        except Exception as e:
            sys.print_exception(e)
            return False
        else:
            return True


class Scheduler(object):

    def __init__(self):
        self.__heap = []
        self.__cond = Condition()
        self.__executor_thread = Thread(target=self.__executor_thread_worker)

    def __task_processing(self):
        task = HeapAlgorithm.pop(self.__heap)
        remaining = task.trigger.get_remaining_seconds()
        if remaining <= 0:
            task.run()
            if task.trigger.update():
                HeapAlgorithm.push(self.__heap, task)
            return
        else:
            HeapAlgorithm.push(self.__heap, task)
            return remaining

    def __executor_thread_worker(self):
        while True:
            with self.__cond:
                try:
                    remaining = self.__task_processing()
                    if remaining is not None:
                        self.__cond.wait(remaining)
                except IndexError:  # heap empty
                    self.__cond.wait()

    def start(self):
        self.__executor_thread.start()

    def reload(self):
        with self.__cond:
            for task in self.__heap:
                if task.trigger.update():
                    continue
                self.__heap.remove(task)
            HeapAlgorithm.heapify(self.__heap)
            self.__cond.notify()

    def cancel(self, task):
        if not isinstance(task, Task):
            raise TypeError("`task` must be instance of Task")
        with self.__cond:
            if task in self.__heap:
                self.__heap.remove(task)
                HeapAlgorithm.heapify(self.__heap)
                self.__cond.notify()

    def update(self, task, **kwargs):
        if not isinstance(task, Task):
            raise TypeError("`task` must be instance of Task")
        with self.__cond:
            task.trigger = TriggerFactory.create(**kwargs)
            if task.trigger.update() and task in self.__heap:
                HeapAlgorithm.heapify(self.__heap)
                self.__cond.notify()

    def add(self, task):
        if not isinstance(task, Task):
            raise TypeError("`task` must be instance of Task")
        with self.__cond:
            if task in self.__heap:
                raise ValueError("task {} already scheduled".format(task))
            if task.trigger.update():
                HeapAlgorithm.push(self.__heap, task)
                self.__cond.notify()

    def submit(self, title="N/A", target=None, args=(), kwargs=None, sync=True, interval=None, datetime=None, cron=(), 
               start_time=None, end_time=None):
        task = Task(
            title=title,
            target=target,
            args=args,
            kwargs=kwargs,
            sync=sync,
            trigger=TriggerFactory.create(
                interval=interval,
                datetime=datetime,
                cron=cron,
                start_time=start_time,
                end_time=end_time
            )
        )
        self.add(task)
        return task

    def task(self, title="N/A", args=(), kwargs=None, sync=True, interval=None, datetime=None, cron=(), start_time=None, end_time=None):
        def wrapper(target):
            return self.submit(
                title=title,
                target=target,
                args=args,
                kwargs=kwargs,
                sync=sync,
                interval=interval,
                datetime=datetime,
                cron=cron,
                start_time=start_time,
                end_time=end_time
            )
        return wrapper

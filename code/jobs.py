import net
from usr import pypubsub as pub
from usr.datetime import DateTime
from usr.scheduler import Scheduler


# 任务调度器
scheduler = Scheduler()


@scheduler.task(interval=10)
def update_signal():
    result = net.csqQueryPoll()  # 0~31
    csq = 0 if result == 99 or result == -1 else result
    pub.publish("update_signal", level=csq // 6)


@scheduler.task(interval=5)
def update_time():
    now = DateTime.now()
    pub.publish("update_time", time="{:02d}:{:02d}".format(now.hour, now.minute))

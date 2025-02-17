import sim
from usr.ui import SelectWindow, ChatWindow
from usr.jobs import scheduler
from usr import pypubsub as pub

import dataCall
import utime as time
import TiktokRTC
import atcmd
import _thread

from machine import Pin

PA = Pin.GPIO39

from machine import ExtInt
from queue import Queue

def key1(args):
    global rtc_queue
    rtc_queue.put(1)

def key2(args):
    global rtc_queue
    rtc_queue.put(2)

def enable_pid2():
    resp = bytearray(50)
    atcmd.sendSync('AT+qicsgp=2,1,3gnet,"","",0\r\n',resp,'',20)
    atcmd.sendSync('at+cgact=1,2\r\n',resp,'',20)

def ai_callback(args):
    global GPIO39
    event = args[0]
    msg = args[1]
    global chat_win
    if event == 1:
        print('TIKTOK_RTC_EVENT_START')
        GPIO39.write(1)
        chat_win.update_status("Please speak to me")
    elif event == 2:
        print('TIKTOK_RTC_EVENT_STOP')
        GPIO39.write(0)
    elif event == 3:
        #chat_win.update_status("AI speaking . . .")
        print('TIKTOK_RTC_EVENT_TTS_TEXT {}'.format(msg))
        #call.stopAudioService()
    elif event == 4:
        #chat_win.update_status("AI listening . . .")
        print('TIKTOK_RTC_EVENT_ASR_TEXT {}'.format(msg))
        #call.stopAudioService()
    elif event == 5:
        print('TIKTOK_RTC_EVENT_ERROR {}'.format(msg))
    else:
        print('TIKTOK_RTC_EVENT UNKNOWN {}'.format(event))

def update_status_with_animation(chat_win, base_message, steps=3, delay_ms=400, final_wait=2):
    # 更新动画
    for i in range(steps + 1):
        chat_win.update_status(base_message + " " + " ." * i)
        time.sleep_ms(delay_ms)
    time.sleep(final_wait)

def perform_initialization(chat_win, tiktok):
    # 初始化动画加载状态
    print('start rtc') 
    chat_win.show()
    tiktok.active(True)

    # 需要展示的状态列表
    status_list = [
        "Connecting to the server",
        "Building the AI engine",
        "Joining the AI room",
        "Loading AI personality",
        "Creating AI characters"
    ]

    # 依次遍历状态并显示动画
    for status in status_list:
        update_status_with_animation(chat_win, status)
def ai_task():
    global rtc_queue
    global extint1
    global extint2
    global tiktok
    global chat_win
    global selsct_win
    while True:
        lte = dataCall.getInfo(1, 0)
        if lte[2][0] == 1:
            print('lte network normal')
            #pub.publish('update_status', status="ready")
            break
        print('wait lte network normal...')
        pub.publish('update_status', status="connect network")
        time.sleep(3)

    extint1.enable()
    extint2.enable()
    print('ai task running')
    while True:
        data = rtc_queue.get()
        print('rtc_queue key event {}'.format(data))
        if data == 1:
            perform_initialization(chat_win, tiktok)
        elif data == 2:
            print('stop rtc')
            selsct_win.show()
            tiktok.active(False)
            

if __name__ == "__main__":

    enable_pid2()
    
    # 使能sim卡热插拔
    sim.setSimDet(1, 1)

    # 设置按键中断
    extint1 = ExtInt(ExtInt.GPIO13, ExtInt.IRQ_FALLING, ExtInt.PULL_PU, key1, filter_time=50)
    extint2 = ExtInt(ExtInt.GPIO12, ExtInt.IRQ_FALLING, ExtInt.PULL_PU, key2, filter_time=50)

    rtc_queue = Queue()

    # 初始化界面
    selsct_win = SelectWindow()
    selsct_win.show()
    
    chat_win = ChatWindow()
    
    # 启动后台任务调度器
    scheduler.start()
    
    print('window show over')

    tiktok = TiktokRTC(300000, ai_callback)
    GPIO39 = Pin(PA, Pin.OUT, Pin.PULL_DISABLE, 0)
    tiktok.config(volume=6)
    print('volume: {}'.format(tiktok.config('volume')))

    _thread.start_new_thread(ai_task, ())


    


import dataCall
import utime as time
import TiktokRTC
import atcmd
import _thread

from machine import Pin

PA = Pin.GPIO39

def enable_pid2():
    resp = bytearray(50)
    atcmd.sendSync('AT+qicsgp=2,1,3gnet,"","",0\r\n',resp,'',20)
    atcmd.sendSync('at+cgact=1,2\r\n',resp,'',20)

def ai_callback(args):
    global GPIO39
    event = args[0]
    msg = args[1]
    if event == 1:
        print('TIKTOK_RTC_EVENT_START')
        GPIO39.write(1)
    elif event == 2:
        print('TIKTOK_RTC_EVENT_STOP')
        GPIO39.write(0)
    elif event == 3:
        print('TIKTOK_RTC_EVENT_TTS_TEXT {}'.format(msg))
        #call.stopAudioService()
    elif event == 4:
        print('TIKTOK_RTC_EVENT_ASR_TEXT {}'.format(msg))
        #call.stopAudioService()
    elif event == 5:
        print('TIKTOK_RTC_EVENT_ERROR {}'.format(msg))
    else:
        print('TIKTOK_RTC_EVENT UNKNOWN {}'.format(event))


if __name__ == '__main__':
    while True:
        lte = dataCall.getInfo(1, 0)
        if lte[2][0] == 1:
            print('lte network normal')
            enable_pid2()
            break
        print('wait lte network normal...')
        time.sleep(3)
    
    tiktok = TiktokRTC(3000000, ai_callback)
    GPIO39 = Pin(PA, Pin.OUT, Pin.PULL_DISABLE, 0)
    time.sleep(2)
    
    tiktok.config(volume=6)
    print('volume: {}'.format(tiktok.config('volume')))
    
    tiktok.active(True)

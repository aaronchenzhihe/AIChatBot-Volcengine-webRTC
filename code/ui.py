from usr import pypubsub as pub
import lvgl as lv
from machine import LCD
from usr.lcd_config import *
from usr.jobs import update_signal, update_time


# init lcd
lcd = LCD()
lcd.lcd_init(INIT_DATA, 240, 320, 26000, 1, 4, 0, INVALID_DATA, DISPLAY_ON_DATA, DISPLAY_OFF_DATA, None)

# init lvgl
lv.init()
# init display driver
disp_buf = lv.disp_draw_buf_t()
buf_length = LCD_WIDTH * LCD_HEIGHT * 2
disp_buf.init(bytearray(buf_length), None, buf_length)
# disp_buf1.init(bytearray(buf_length), bytearray(buf_length), buf_length)  # 双buffer缓冲，占用过多RAM
disp_drv = lv.disp_drv_t()
disp_drv.init()
disp_drv.draw_buf = disp_buf
disp_drv.flush_cb = lcd.lcd_write
disp_drv.hor_res = LCD_WIDTH
disp_drv.ver_res = LCD_HEIGHT
# disp_drv.sw_rotate = 1  # 此处设置是否需要旋转
# disp_drv.rotated = lv.DISP_ROT._270  # 旋转角度
disp_drv.register()
# image cache
lv.img.cache_invalidate_src(None)
lv.img.cache_set_size(50)
# start lvgl thread
lv.tick_inc(5)
lv.task_handler()


# 创建字体
arial_12_style = lv.style_t()
arial_12_style.init()
arial_12_style.set_text_color(lv.color_white())
arial_12_style.set_text_font_v2("arial_12.bin", 18, 0)


arial_16_style = lv.style_t()
arial_16_style.init()
arial_16_style.set_text_color(lv.color_white())
arial_16_style.set_text_font_v2("arial_16.bin", 24, 0)

arial_22_style = lv.style_t()
arial_22_style.init()
arial_22_style.set_text_color(lv.color_white())
arial_22_style.set_text_font_v2("arial_22.bin", 33, 0)


class SelectWindow(object):

    def __init__(self):
        self.obj = lv.obj(None)
        self.obj.set_style_bg_color(lv.color_black(), lv.PART.MAIN)

        self.batt = lv.img(self.obj)
        self.batt.set_src("U:/img/battery/bat_09.png")
        self.batt.align(lv.ALIGN.TOP_RIGHT, -10, 10)

        self.signal = lv.img(self.obj)
        self.signal.set_size(16, 16)
        self.signal.set_src("U:/img/signal/signal_00.png")
        self.signal.align(lv.ALIGN.TOP_LEFT, 10, 10)
        self.signal.set_offset_y(-20 * 0)
        pub.subscribe("update_signal", lambda level: self.set_signal_level(level))
        update_signal.run()  # first update signal

        self.time = lv.label(self.obj)
        self.time.set_text("00:00")
        self.time.add_style(arial_16_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.time.align(lv.ALIGN.TOP_MID, 0, 10)
        pub.subscribe("update_time", lambda time: self.time.set_text(time))
        update_time.run()  # first update time

        self.main_icon = lv.img(self.obj)
        self.main_icon.set_src("U:/img/image1_80.png")
        self.main_icon.set_size(80, 80)
        self.main_icon.align(lv.ALIGN.TOP_RIGHT, -20, 85)

        self.main_icon1 = lv.img(self.obj)
        self.main_icon1.set_src("U:/img/image2_80.png")
        self.main_icon1.set_size(80, 80)
        self.main_icon1.align(lv.ALIGN.TOP_LEFT, 20, 85)

        self.name = lv.label(self.obj)
        self.name.add_style(arial_22_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.name.set_style_text_color(lv.palette_main(lv.PALETTE.BLUE), lv.PART.MAIN | lv.STATE.DEFAULT)
        self.name.set_text("Ding")
        self.name.align_to(self.main_icon, lv.ALIGN.OUT_TOP_MID, 0, -10)

        self.name = lv.label(self.obj)
        self.name.add_style(arial_22_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.name.set_style_text_color(lv.palette_main(lv.PALETTE.RED), lv.PART.MAIN | lv.STATE.DEFAULT)
        self.name.set_text("Wei")
        self.name.align_to(self.main_icon1, lv.ALIGN.OUT_TOP_MID, 0, -10)

        self.choose = lv.label(self.obj)
        self.choose.add_style(arial_22_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.choose.set_style_text_color(lv.palette_main(lv.PALETTE.YELLOW), lv.PART.MAIN | lv.STATE.DEFAULT)
        self.choose.set_text("Choose her")
        self.choose.align_to(self.main_icon1, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

        self.content = lv.label(self.obj)
        self.content.add_style(arial_22_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.content.set_text("")
        self.content.align_to(self.main_icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

        pub.subscribe("update_status", self.update_status)

    def update_status(self, status):
        self.content.set_text(status)
        self.content.align_to(self.main_icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

    def show(self):
        lv.scr_load(self.obj)

    def set_signal_level(self, level):
        """level 分 6 档, [0, 5], 其中 0 表示无信号, 5表示满信号"""
        self.signal.set_src("U:/img/signal/signal_{:02d}.png".format(level))

    def set_batt_level(self, level):
        """level 分 10 档, [0, 9], 其中 0 表示电池异常馈电, 8表示满电池, 9表示电池充电"""
        self.batt.set_src("U:/img/battery/bat_{:02d}.png".format(level))
    def update_status(self, status):
        self.content.set_text(status)
        self.content.align_to(self.main_icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

    def show(self):
        lv.scr_load(self.obj)

    def set_signal_level(self, level):
        """level 分 6 档, [0, 5], 其中 0 表示无信号, 5表示满信号"""
        self.signal.set_src("U:/img/signal/signal_{:02d}.png".format(level))

    def set_batt_level(self, level):
        """level 分 10 档, [0, 9], 其中 0 表示电池异常馈电, 8表示满电池, 9表示电池充电"""
        self.batt.set_src("U:/img/battery/bat_{:02d}.png".format(level))


class ChatWindow(object):

    def __init__(self):
        self.obj = lv.obj(None)
        self.obj.set_style_bg_color(lv.color_black(), lv.PART.MAIN)

        self.batt = lv.img(self.obj)
        self.batt.set_src("U:/img/battery/bat_09.png")
        self.batt.align(lv.ALIGN.TOP_RIGHT, -10, 10)

        self.signal = lv.img(self.obj)
        self.signal.set_size(16, 16)
        self.signal.set_src("U:/img/signal/signal_00.png")
        self.signal.align(lv.ALIGN.TOP_LEFT, 10, 10)
        self.signal.set_offset_y(-20 * 0)
        pub.subscribe("update_signal", lambda level: self.set_signal_level(level))
        update_signal.run()  # first update signal

        self.time = lv.label(self.obj)
        self.time.set_text("00:00")
        self.time.add_style(arial_16_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.time.align(lv.ALIGN.TOP_MID, 0, 10)
        pub.subscribe("update_time", lambda time: self.time.set_text(time))
        update_time.run()  # first update time

        self.main_icon = lv.img(self.obj)
        self.main_icon.set_src("U:/img/image2.png")
        self.main_icon.set_size(128, 128)
        self.main_icon.align(lv.ALIGN.CENTER, 0, 10)

        self.name = lv.label(self.obj)
        self.name.add_style(arial_22_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.name.set_style_text_color(lv.palette_main(lv.PALETTE.ORANGE), lv.PART.MAIN | lv.STATE.DEFAULT)
        self.name.set_text("Wei")
        self.name.align_to(self.main_icon, lv.ALIGN.OUT_TOP_MID, 0, -10)

        self.content = lv.label(self.obj)
        self.content.add_style(arial_22_style, lv.PART.MAIN | lv.STATE.DEFAULT)
        self.content.set_text("")
        self.content.align_to(self.main_icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

        pub.subscribe("update_status", self.update_status)

    def update_status(self, status):
        self.content.set_text(status)
        self.content.align_to(self.main_icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

    def show(self):
        lv.scr_load(self.obj)

    def set_signal_level(self, level):
        """level 分 6 档, [0, 5], 其中 0 表示无信号, 5表示满信号"""
        self.signal.set_src("U:/img/signal/signal_{:02d}.png".format(level))

    def set_batt_level(self, level):
        """level 分 10 档, [0, 9], 其中 0 表示电池异常馈电, 8表示满电池, 9表示电池充电"""
        self.batt.set_src("U:/img/battery/bat_{:02d}.png".format(level))
    def update_status(self, status):
        self.content.set_text(status)
        self.content.align_to(self.main_icon, lv.ALIGN.OUT_BOTTOM_MID, 0, 10)

    def show(self):
        lv.scr_load(self.obj)

    def set_signal_level(self, level):
        """level 分 6 档, [0, 5], 其中 0 表示无信号, 5表示满信号"""
        self.signal.set_src("U:/img/signal/signal_{:02d}.png".format(level))

    def set_batt_level(self, level):
        """level 分 10 档, [0, 9], 其中 0 表示电池异常馈电, 8表示满电池, 9表示电池充电"""
        self.batt.set_src("U:/img/battery/bat_{:02d}.png".format(level))


if __name__ == '__main__':
    selsct_win = SelectWindow()
    chat_win = ChatWindow()
    selsct_win.show()
    chat_win.show()
import time
import cv2
import numpy as np
from ok import color_range_to_bound
from src.char.BaseChar import BaseChar, Priority


class Ciaccona(BaseChar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attribute = 0
        self.in_liberation = False
        self.cartethyia = None

    def skip_combat_check(self):
        return self.time_elapsed_accounting_for_freeze(self.last_liberation) < 2

    def reset_state(self):
        super().reset_state()
        self.attribute = 0
        self.cartethyia = None

    def do_perform(self):
        self.in_liberation = False
        #e接r，重击接r要等0.3秒等伤害出来
        wait = False
        #进场直接重击，a4接重击要跳取消动作
        #闪避相比跳很容易被吞
        jump = True
        if self.attribute == 0:
            self.decide_teammate()
        if self.has_intro:
            self.continues_normal_attack(0.8)
            if not self.need_fast_perform():
                self.continues_normal_attack(0.7)
        self.click_echo()
        if not self.has_intro and not self.need_fast_perform() and not self.is_forte_full():
            self.click_jump_with_click(0.4)
            self.continues_normal_attack(1.2)
        if self.click_resonance()[0]:
            jump = False
            wait = True     
        if self.judge_forte() >= 3:
            if jump:
                self.continues_click(key='SPACE', duration=0.2)
            self.heavy_attack(0.7)
            wait = True
        if self.liberation_available(): 
            if wait:
                self.sleep(0.4)
            if self.click_liberation():
                self.in_liberation = True
                if self.attribute == 2:
                    self.continues_click_a(0.6)
        self.switch_next_char()

    def do_get_switch_priority(self, current_char: BaseChar, has_intro=False, target_low_con=False):
        if self.attribute == 2 and self.in_liberation and self.time_elapsed_accounting_for_freeze(self.last_liberation) < 20:
            return Priority.MIN
        if self.attribute == 3:
            self.logger.debug(f'ciaccona cond: {self.cartethyia.is_cartethyia}')
        if self.attribute == 3 and self.in_liberation and (self.time_elapsed_accounting_for_freeze(self.last_liberation) < 8 or not self.cartethyia.is_cartethyia):
            return Priority.MIN
        return super().do_get_switch_priority(current_char, has_intro)

    def click_jump_with_click(self, delay=0.1):
        start = time.time()
        click = 1
        while True:
            if time.time() - start > delay:
                break
            if click == 0:
                self.task.send_key('SPACE')
            else:
                self.click()
            click = 1 - click
            self.check_combat()
            self.task.next_frame()
            
    def continues_click_a(self, duration=0.6):
        start = time.time()
        while time.time() - start < duration:
            self.task.send_key(key='a')

    def judge_forte(self):
        if self.is_forte_full():
            return 3
        box = self.task.box_of_screen_scaled(3840, 2160, 1612, 1987, 2188, 2008, name='ciaccona_forte', hcenter=True)
        forte = self.calculate_forte_num(ciaccona_forte_color, box, 3, 12, 14, 37)
        if forte == 0:
            forte = self.calculate_forte_num(ciaccona_forte_color1, box, 3, 12, 14, 37)
        return forte

    def decide_teammate(self):
        from src.char.Phoebe import Phoebe
        from src.char.Zani import Zani
        from src.char.Cartethyia import Cartethyia
        for i, char in enumerate(self.task.chars):
            self.logger.debug(f'ciaccona teammate char: {char.char_name}')
            if isinstance(char, (Cartethyia)):
                self.logger.debug('ciaccona set attribute: wind dot')
                self.cartethyia = char
                self.attribute = 3
                return
            if isinstance(char, (Phoebe, Zani)):
                self.logger.debug('ciaccona set attribute: light dot')
                self.attribute = 2
                return
        self.logger.debug('ciaccona set attribute: wind dot')
        self.attribute = 1
        return

    def judge_frequncy_and_amplitude(self, gray, min_freq, max_freq, min_amp):
        height, width = gray.shape[:]
        if height == 0 or width < 64 or not np.array_equal(np.unique(gray), [0, 255]):
            return 0
        profile = np.sum(gray == 255, axis=0).astype(np.float32)
        profile -= np.mean(profile)
        n = np.abs(np.fft.fft(profile))
        amplitude = 0
        frequncy = 0
        i = 1
        while i < width:
            if n[i] > amplitude:
                amplitude = n[i]
                frequncy = i
            i += 1
        self.logger.debug(f'forte with freq {frequncy} & amp {amplitude}')
        return (min_freq <= frequncy <= max_freq) or amplitude >= min_amp

    def calculate_forte_num(self, forte_color, box, num=1, min_freq=39, max_freq=41, min_amp=50):
        cropped = box.crop_frame(self.task.frame)
        lower_bound, upper_bound = color_range_to_bound(forte_color)
        image = cv2.inRange(cropped, lower_bound, upper_bound)

        forte = 0
        height, width = image.shape
        step = int(width / num)
        left = 0
        fail_count = 0
        warning = False
        while left + step < width:
            gray = image[:, left:left + step]
            score = self.judge_frequncy_and_amplitude(gray, min_freq, max_freq, min_amp)
            if fail_count == 0:
                if score:
                    forte += 1
                else:
                    fail_count += 1
            else:
                if score:
                    warning = True
                else:
                    fail_count += 1
            left += step
        if warning:
            self.logger.info('Frequncy analysis error, return the forte before mistake.')
        self.logger.info(f'Frequncy analysis with forte {forte}')
        return forte

    # 回路条不满时的颜色


ciaccona_forte_color = {
    'r': (70, 100),  # Red range
    'g': (240, 255),  # Green range
    'b': (180, 210)  # Blue range
}

# 回路条满时的颜色
ciaccona_forte_color1 = {
    'r': (120, 220),  # Red range
    'g': (240, 255),  # Green range
    'b': (240, 255)  # Blue range
}

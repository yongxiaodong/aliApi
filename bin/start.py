# -*- coding: utf-8 -*-
# @Author: BigHead


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.buyinstance_new import *




if __name__ == "__main__":
    # 获取剩余的坑位
    pit = get_pit()
    #模拟剩余坑位
    # pit = 60
    while True:
        if pit < settings.red_line:
            buy_pit = settings.green_line - pit
            buy_count = math.ceil(buy_pit / settings.base_num)
            logger.info("当前剩余坑位%s,需要购买%s台机器" % (pit, buy_count))
            buy_machine(buy_count)
        else:
            logger.info(f"当前剩余坑位{pit},资源充足，跳过购买")
        time.sleep(settings.check_interval)



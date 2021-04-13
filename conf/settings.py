# -*- coding: utf-8 -*-
# @Author: BigHead

db_file = './db/db'
# 名称前缀
machine_prefix = 'dtk-wechat-'

# sleep_time周期内只购买buy_num_mini数量的机器
buy_num_min = 5

# 坑位红线值
red_line = 50
# 坑位绿线值
green_line = 100

# 余额红线值
money_yello = 2000
money_red = 300

# 单笔金额
buy_money = 266.25

# 每台机器的坑位数，用于计算应该购买多少机器
base_num = 7

# 阿里云
key = 'xxxx'
secre = 'xxxx'
zone = 'cn-beijing'

# 模式debug or prod
level = "debug"

# 购买机器后延迟检查时间
sleep_time = 60
# 检查时间间隔
check_interval = 20
# 检查次数
check_count = 15


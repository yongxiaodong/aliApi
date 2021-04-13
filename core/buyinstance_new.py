#coding=utf-8
#
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
import time
import math
import json
import requests
from lib import common_log
from conf import settings
from lib import dingdingwebhook

logger = common_log.get_logger(__name__)


# 如果db文件不存在, 初始化db结构
def init_db():
    with open(settings.db_file, 'w', encoding="utf-8") as f:
        data = {
            "init_name": 491,
            "money": 25000
        }
        with open(settings.db_file, 'a', encoding='utf-8') as f:
            json.dump(data, f)


def update_db(data):
    with open(settings.db_file, 'w', encoding="utf-8") as f:
        json.dump(data, f)
    logger.info("db更新完成")


def read_db():
    try:
        with open(settings.db_file, 'r', encoding="utf-8") as f:
            pass
    except FileNotFoundError:
        init_db()
    finally:
        with open(settings.db_file, 'r', encoding="utf-8") as f:
            data = json.load(f)
            return data


# 获取剩余坑位
def get_pit():
    try:
        url = "http://spiderman.ffquan.cn/api/wechat/sre/quota"
        r = json.loads(requests.get(url).text)
        pit = r.get("data").get("slot")
        if pit:
            return pit
        else:
            raise Exception("pit为空")
    except Exception as e:
        logger.error(f"爬虫接口对接失败,{e},{r.text}")


# 检查服务器注册状态
def check_registry(machine_name):
    try:
        url = f"http://spiderman.ffquan.cn/api/wechat/sre/worker?hostname={machine_name}"
        r = json.loads(requests.get(url).text)
        if r.get("status") == 1:
            message = f"{machine_name}注册成功"
            logger.info(message)
            dingdingwebhook.alert(message)
            return 1
        else:
            logger.error(f"{machine_name}注册失败")
            return None
    except Exception as e:
        logger.error(f"爬虫接口对接失败,{e}")
        return None


# 重启实例
def restart_machine(machine_names):
    pass


def ali_buy_machine(machine_name):
    client = AcsClient(settings.key, settings.secre, 'cn-beijing')
    request = RunInstancesRequest()
    request.set_accept_format('json')

    request.set_InstanceName(machine_name)
    request.set_HostName(machine_name)
    # 购买数量
    request.set_Amount(settings.buy_num_min)
    #最低购买数量
    request.set_MinAmount(settings.buy_num_min)
    # 模板名
    request.set_LaunchTemplateName("dtk-wechat-20210119-a")
    # 模板版本，如果不写则默认
    # request.set_LaunchTemplateVersion("2")

    # 购买时长
    request.set_Period(1)
    request.set_PeriodUnit("Month")

    response = client.do_action_with_exception(request)
    # python2:  print(response)
    # print(str(response, encoding='utf-8'))
    return str(response, encoding='utf-8')


def buy_machine(buy_count):
    while buy_count > 0:
        # 读取DB数据
        data = read_db()
        money = data.get("money")
        logger.info(f"当前余额{money}")
        #if money < settings.money_yello and money > settings.money_red:
        if money < settings.money_yello:
            message = f"余额过低，请注意,当前余额{money}"
            logger.error(message)
            dingdingwebhook.alert(message)
        elif money < settings.money_red:
            message = f"余额不足,放弃购买,当前余额{money}"
            logger.error(message)
            dingdingwebhook.alert(message)
            return Exception("余额不足")
        init_name = int(data.get("init_name"))
        current_time = str(time.strftime('%Y-%m-%d %H:%M:%S'))
        machine_name = "%s[%s,4]" % (settings.machine_prefix, init_name)
        machine_names = [settings.machine_prefix + str("%04d" % i) for i in range(init_name, init_name + settings.buy_num_min)]
        message = """开始购买机器:
        开始序号：%s,
        操作时间：%s
        本轮购买台数:%s
        机器名字组:%s
        """ % (init_name, current_time, settings.buy_num_min, machine_names)
        logger.info(message)
        dingdingwebhook.alert(message)
        # 买机器逻辑
        if settings.level == "prod":
            aliyun_return_info = ali_buy_machine(machine_name)
        else:
            logger.info("当前模式跳过真实购买")
            aliyun_return_info = {}
        # 买机器逻辑结束

        # 更新还应该购买的机器数量
        buy_count -= settings.buy_num_min
        # 减钱
        money = money - settings.buy_money
        # 本轮购买完成后重置下一次购买机器时的开始序号
        init_name += settings.buy_num_min
        data["init_name"] = init_name
        data["money"] = money
        logger.info("本轮购买完成，开始更新db,下次开始序号:%s" % init_name)
        update_db(data)
        logger.info(f"休眠{settings.sleep_time}秒,等待延时检测")
        time.sleep(settings.sleep_time)
        # 检查机器是否注册成功
        for count in range(0, settings.check_count):
            logger.info(f"开始第{count}次检测")
            for machine_name in machine_names[:]:
                r = check_registry(machine_name)
                if r:
                    machine_names.remove(machine_name)
            if len(machine_names) == 0:
                logger.info("本批次机器全部注册成功")
                break
            logger.info(f"第{count}次检测完成，休眠{settings.check_interval}秒，等待下一次检测")
            time.sleep(settings.check_interval)
        else:
            message = f"本批次注册失败的机器列表: {machine_names}"
            logger.error(message)
            dingdingwebhook.alert(message)
            # 重启注册失败的实例
            logger.info("开始尝试重启注册失败的实例!!!")
            for machine_name in machine_names:
                restart_machine(machine_name)
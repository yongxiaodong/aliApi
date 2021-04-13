import json
import logging
import math
import datetime
import sys
import os
import requests
import hmac
import hashlib
import base64
import urllib.parse
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526.DescribeInstanceAutoRenewAttributeRequest import \
    DescribeInstanceAutoRenewAttributeRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.ModifyInstanceAutoRenewAttributeRequest import \
    ModifyInstanceAutoRenewAttributeRequest
from aliyunsdkecs.request.v20140526.RenewInstanceRequest import RenewInstanceRequest
from aliyunsdkbssopenapi.request.v20171214.QueryAvailableInstancesRequest import QueryAvailableInstancesRequest
from aliyunsdkbssopenapi.request.v20171214.SetRenewalRequest import SetRenewalRequest
from conf import settings
from core import DescribeRenewalPrice
import time
from lib import common_log
logger = common_log.get_logger(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
clt = client.AcsClient(settings.key, settings.secre, settings.zone)



# 根据hostname获取实例的id
def hostname_to_instanceid(hostname):
    request = DescribeInstancesRequest()
    request.set_accept_format('json')

    request.set_InstanceName(hostname)
    request.set_Tags([])
    request.set_AdditionalAttributess([])

    response = clt.do_action_with_exception(request)
    # python2:  print(response)
    # print(str(response, encoding='utf-8'))
    j_response = json.loads(str(response, encoding='utf-8'))
    instance_info = j_response.get("Instances").get("Instance")
    if instance_info:
        return instance_info[0].get("InstanceId")
    else:
        return None


# 查询实例的续费状态[手动续费、自动续费、不续费]
def query_instance_renewstatus(instance_id):
    request = QueryAvailableInstancesRequest()
    request.set_accept_format('json')

    # request.set_Region("")
    # request.set_PageNum(1)
    # request.set_PageSize(1)
    request.set_InstanceIDs(instance_id)

    response = clt.do_action_with_exception(request)
    # python2:  print(response)
    # print(str(response, encoding='utf-8'))
    j_response = json.loads(str(response, encoding='utf-8'))
    return j_response


# 设置实例的续费状态[手动续费、自动续费、不续费]
# AutoRenewal：自动续费。
# ManualRenewal：手动续费。
# NotRenewal：不续费。
def set_instance_renewstatus(instance_id, status):
    request = SetRenewalRequest()
    request.set_accept_format('json')

    request.set_InstanceIDs(instance_id)
    request.set_ProductCode("ecs")
    request.set_RenewalStatus(status)

    response = clt.do_action_with_exception(request)
    j_response = json.loads(str(response, encoding='utf-8'))
    return j_response


# 续费任务
def renew_job(page_size=100, page_number=1, check_need_renew=True, security_group_id=None):
    response = describe_need_renew_instance(page_size=page_size, page_number=page_number, check_need_renew=check_need_renew, security_group_id=security_group_id)
    response_list = response.get('Instances').get('Instance')
    logging.info("%s instances need to renew", str(response.get('TotalCount')))
    if len(response_list) > 0:
        instance_ids = ''
        for item in response_list:
            instance_id = item.get('InstanceId')
            instance_ids += instance_id + ','
            # 获取实例的续费状态，如果为不续费则不处理
            r = query_instance_renewstatus(instance_id)
            renewstatus = r.get("Data").get("InstanceList")[0].get("RenewStatus")
            if renewstatus == 'NotRenewal':
                pass
            elif renewstatus == 'ManualRenewal':
                # 查询实例续费价格开关
                renew_instance(instance_id=instance_id)

            # if instance_id != 'i-2zecy74s6v6az3doridl':
            #     # 续费开关
            #     renew_instance(instance_id=instance_id)
            # time.sleep(0.5)
        logging.info("%s execute renew action ready", instance_ids)


# 查询任务
def query_job(page_size=100, page_number=1, check_need_renew=True, security_group_id=None, continue_execute=True):
    response = describe_need_renew_instance(page_size=page_size, page_number=page_number, check_need_renew=check_need_renew, security_group_id=security_group_id)
    response_list = response.get('Instances').get('Instance')
    logging.info("%s instances need to renew", str(response.get('TotalCount')))
    # 用于返回需要续费的机器数量
    if continue_execute is not True:
        machine_total = int(response.get('TotalCount'))
        return machine_total
    if len(response_list) > 0:
        instance_ids = ''
        for item in response_list:
            hostname = item.get("HostName")
            instance_id = item.get('InstanceId')
            instance_ids += instance_id + ','
            # 获取实例的续费状态，如果为不续费则不处理
            r = query_instance_renewstatus(instance_id)
            renewstatus = r.get("Data").get("InstanceList")[0].get("RenewStatus")
            # 不续费的
            if renewstatus == 'NotRenewal':
                pass
            # 需要续费的
            elif renewstatus == 'ManualRenewal':
                logging.debug(f"{instance_id}的续费方式是{renewstatus}")
                # 查询实例续费价格
                query_price(instance_id, hostname)
            # time.sleep(1)
        logging.info("%s execute renew action ready", instance_ids)


# 查询实例价格
def query_price(instance_id, hostname=None):
    r = DescribeRenewalPrice.get_price(instance_id)
    price = r.get("PriceInfo").get("Price").get("TradePrice")
    prices[instance_id] = price
    logging.info(f"{instance_id} 的续费价格是{price}, 主机名是{hostname}")


def describe_need_renew_instance(page_size=100, page_number=1, instance_id=None, check_need_renew=True, security_group_id=None):
    request = DescribeInstancesRequest()
    if check_need_renew is True:
        request.set_Filter3Key("ExpiredStartTime")
        request.set_Filter3Value(INSTANCE_EXPIRED_START_TIME_IN_UTC_STRING)
        request.set_Filter4Key("ExpiredEndTime")
        request.set_Filter4Value(INSTANCE_EXPIRE_END_TIME_IN_UTC_STRING)
    if instance_id is not None:
        request.set_InstanceIds(json.dumps([instance_id]))
    if security_group_id:
        request.set_SecurityGroupId(security_group_id)
    request.set_PageNumber(page_number)
    request.set_PageSize(page_size)
    return _send_request(request)


def describe_instance_auto_renew_setting(instance_ids, expected_auto_renew=True):
    describe_request = DescribeInstanceAutoRenewAttributeRequest()
    describe_request.set_InstanceId(instance_ids)
    response_detail = _send_request(request=describe_request)
    failed_instance_ids = ''
    if response_detail is not None:
        attributes = response_detail.get('InstanceRenewAttributes').get('InstanceRenewAttribute')
        if attributes:
            for item in attributes:
                auto_renew_status = item.get('AutoRenewEnabled')
                if auto_renew_status != expected_auto_renew:
                    failed_instance_ids += item.get('InstanceId') + ','
    if len(failed_instance_ids) > 0:
        logging.error("instance %s auto renew not match expect %s.", failed_instance_ids,
                      expected_auto_renew)


def setting_instance_auto_renew(instance_ids, auto_renew=True):
    logging.info('execute enable auto renew ' + instance_ids)
    request = ModifyInstanceAutoRenewAttributeRequest();
    request.set_Duration(1);
    request.set_AutoRenew(auto_renew);
    request.set_InstanceId(instance_ids)
    _send_request(request)
    describe_instance_auto_renew_setting(instance_ids, auto_renew)


def check_instance_need_renew(instance_id):
    response = describe_need_renew_instance(instance_id=instance_id)
    if response is not None:
        return response.get('TotalCount') == 1
    return False


def renew_instance(instance_id, period='1'):
    need_renew = check_instance_need_renew(instance_id)
    if need_renew:
        _renew_instance_action(instance_id, period)
        # describe_need_renew_instance(instance_id=instance_id, check_need_renew=False)


def _renew_instance_action(instance_id, period='1'):
    request = RenewInstanceRequest()
    request.set_Period(period)
    request.set_InstanceId(instance_id)
    response = _send_request(request)
    logging.info('renew %s ready, output is %s ', instance_id, response)


def _send_request(request):
    request.set_accept_format('json')
    try:
        response_str = clt.do_action(request)
        logging.info(response_str)
        response_detail = json.loads(response_str)
        return response_detail
    except Exception as e:
        logging.error(e)

def get_pagetotal():
    machine_total = query_job(page_size=1, page_number=1, continue_execute=False)
    page_total = math.ceil(machine_total / 100)
    logging.info(f"需要续费的机器台数为:{machine_total}, 机器总页数为{page_total}")
    return page_total


def run_query():
    # 查询
    page_total = get_pagetotal()
    for page in range(1, page_total + 1):
        query_job(page_number=page)
    # 查询结果写文件，用来提交OA申请
    # with open('./query1.txt', 'w', encoding='utf-8') as f:
    #     json.dump(prices, f)


def run_renew():
    # 老的续费规则
    # page_total = get_pagetotal()
    # for page in range(1, page_total + 1):
    #     renew_job(page_number=page)
    # with open('./renew1.txt', 'w', encoding='utf-8') as f:
    #     json.dump(prices, f)

    # 修改为先查询再续费，续费时直接从查询结果文件中获取需要续费的实例ID
    if prices:
        renew_count = len(prices)
        logging.info(f"开始续费，续费的机器总数为{renew_count}")
        logging.info(f"续费的机器列表{prices}")
        for instance_id in prices:
            logging.info(f"当前续费机器{instance_id}")
            renew_instance(instance_id)
    else:
        logging.info("没有需要续费的机器")




if __name__ == '__main__':
    logging.info("Renew ECS Instance by OpenApi!")
    # 查询在指定的时间范围内是否有需要续费的实例。
    # r = describe_need_renew_instance()
    # 续费

    # 自動獲取時間
    # machine_end_time = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%MZ")
    # machine_start_time = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%MZ")
    # logging.info(f"开始时间：{machine_start_time}，结束时间：{machine_end_time}")
    #
    # INSTANCE_EXPIRED_START_TIME_IN_UTC_STRING = machine_start_time
    # INSTANCE_EXPIRE_END_TIME_IN_UTC_STRING = machine_end_time
    INSTANCE_EXPIRED_START_TIME_IN_UTC_STRING = '2021-04-14T00:00Z'
    INSTANCE_EXPIRE_END_TIME_IN_UTC_STRING = '2021-04-21T23:59Z'


    global prices
    prices = {}
    run_query()
    # run_renew()
    # ding()

    # a = query_instance_renewstatus("i-2zebcdfzd6526yuddzds")
    # print(a)



    # 续费实例, 直接执行费用扣除。
    # renew_instance('i-bp1aet7s13lfpjop****')
    # 查询实例自动续费的状态。
    # describe_instance_auto_renew_setting('i-bp1aet7s13lfpjop****,i-bp13uh1twnfv7vp8****')
    # 设置实例自动续费。
    # setting_instance_auto_renew('i-bp1aet7s13lfpjop****,i-bp13uh1twnfv7vp8****')

    # 查询实例续费价格
    # https://help.aliyun.com/document_detail/127117.html?spm=a311a.7996332.0.0.55c23080nO6Tm5

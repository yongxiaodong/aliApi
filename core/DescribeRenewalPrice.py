#!/usr/bin/env python
#coding=utf-8

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526.DescribeRenewalPriceRequest import DescribeRenewalPriceRequest
import json
from conf import settings

def get_price(instanceid):
    client = AcsClient(settings.key, settings.secre, settings.zone)

    request = DescribeRenewalPriceRequest()
    request.set_accept_format('json')

    request.set_ResourceType("instance")
    request.set_ResourceId(instanceid)
    request.set_Period(1)
    request.set_PriceUnit("Month")

    response = client.do_action_with_exception(request)
    # python2:  print(response)
    # print(str(response, encoding='utf-8'))

    j_s = json.loads(str(response, encoding='utf-8'))
    return j_s

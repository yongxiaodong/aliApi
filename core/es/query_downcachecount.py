import requests
import json
import time
from lib import common_log
from lib.cachedown import dingdingwebhook
logger = common_log.get_logger(__name__)


def query(logfilepath):
    message = ""
    url = 'http://k8ses.haojiequ.com'
    prefix = '/in-nginx-proxy-*/_doc/_search?timeout=100ms'
    data = {
        "query": {
            "bool": {
                "filter": [
                    {
                        "term": {
                            "log.file.path": logfilepath
                        },
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gt": "now-1m"
                            }
                        }
                    }
                ]
            }
        }
    }
    try:
        r = requests.post(url + prefix, json=data)
        logger.info(f"接收到数据{r.text}")
        return r
    except requests.exceptions.ConnectTimeout as e:
        message = f"es链接超时,{e}"
    except requests.exceptions.ReadTimeout as e:
        message = f"es读取超时,{e}"
    except Exception as e:
        message = f"获取es数据错误,{e}"
    finally:
        if message:
            logger.error(message)
            dingdingwebhook.alert(f"查询es错误，信息：{message}")


def alert(logfilepath, count):
    message = f'留意!!!{logfilepath}正在查询缓存, 1分钟内查询缓存{str(count)}次'
    dingdingwebhook.alert(message)

def alert2(logfilepath, count):
    message = f'恢复通知.{logfilepath}查询缓存状态已恢复, 1分钟内查询缓存{str(count)}次'
    dingdingwebhook.alert(message)


alertdb = []
monitor_list = [
    "/var/log/nginx/downcache.www.dataoke.com.access.log",
    "/var/log/nginx/downcache.dtkapi.dataoke.com.access.log",
]
while True:
    try:
        logger.info(f"alerdb：{alertdb}")
        for logfilepath in monitor_list:
            r = query(logfilepath)
            j_r = json.loads(r.text)
            downcache_count = j_r.get("hits").get("total").get("value")
            if downcache_count >= 10:
                alert(logfilepath, downcache_count)
                if logfilepath not in alertdb:
                    alertdb.append(logfilepath)
            else:
                logger.info(f"正常,{logfilepath} 1分钟内查询缓存:{downcache_count}")
                if logfilepath in alertdb:
                    alertdb.remove(logfilepath)
                    logger.info(f"{logfilepath}恢复告警")
                    alert2(logfilepath, downcache_count)
        time.sleep(60)
    except Exception as e:
        logger.error("不管，反正异常了")

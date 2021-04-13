import requests
from lib import common_log

logger = common_log.get_logger(__name__)


def alert(message):
    url = 'https://oapi.dingtalk.com/robot/send?access_token=06548d838596b21bb1fecec09d1deb08d2c7318a3ad8f963b8610e1f51074bc9'
    headers = {
        'Content-Type': 'application/json'
    }

    data = {
    "msgtype": "text",
    "text": {
        "content": message
    }
}
    r = requests.post(url, json=data, headers=headers)
    logger.info(r.text)



if __name__ == "__main__":
    alert('你好')

from flask import Flask, Response
from flask import request
import json
import threading
import time
from core import ecsrenew
from lib import common_log
logger = common_log.get_logger(__name__)


app = Flask(__name__)

response_data = {
    "message": None,
    "status": True

}


@app.route('/', methods=['GET'])
def home():
    try:
        renew_status_list = ['AutoRenewal', 'ManualRenewal', 'NotRenewal']
        hostname = request.args.get("hostname")
        renewstatus = request.args.get("renewstatus")
        if hostname and renewstatus in renew_status_list:
            instanceid = ecsrenew.hostname_to_instanceid(hostname)
            if instanceid:
                r = ecsrenew.set_instance_renewstatus(instanceid, renewstatus)
                response_data["message"], response_data["status"] = r, True
                return Response(json.dumps(response_data), mimetype='application/json;charset=utf-8')
            else:
                raise Exception(f"{hostname}转换为instance_id失败,可能不存在{hostname}这台服务器,请检查hostname是否正确")
        else:
            raise Exception("请检查输入的hostname或renewstatus参数,hostname不能为空,renewstatus只能为['AutoRenewal', 'ManualRenewal', 'NotRenewal']")
    except Exception as e:
        response_data["message"], response_data["status"] = e.args[0], False
        logger.error(f"{hostname}")
        return Response(json.dumps(response_data), mimetype='application/json;charset=utf-8')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

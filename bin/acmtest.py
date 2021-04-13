# https://help.aliyun.com/document_detail/66727.html
#pip install acm-sdk-python
import acm
from conf import settings

ENDPOINT = "acm.aliyun.com"
NAMESPACE = "dc764327-1e4e-4c22-96ec-5b3370a3385f"
AK = settings.key
SK = settings.secre
DATA_ID= "config1"
GROUP= "app1"

# Initialize ACM client.
c = acm.ACMClient(ENDPOINT, NAMESPACE, AK, SK)


# Get plain content from ACM.
print(c.get(DATA_ID, GROUP))
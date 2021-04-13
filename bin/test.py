import json


init = 0
count = 0
with open("../core/query1.txt", 'r',encoding='utf-8') as f:
    j = json.loads(f.read())
    for k, v in j.items():
        init += v
        count += 1
    print(init)
    print(count)




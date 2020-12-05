'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 18:18:41
'''
import json, time
from elasticsearch import Elasticsearch
es = Elasticsearch()

def filter_msg(msg):
    body = {
        "size": 100,
        "query": {
            "match": {
                "sentence":msg
            }
        }
    }
    res = es.search(index='corpus', body=body)
    return json.dumps((res['hits']), indent=4, ensure_ascii=False)
    # return res['hits']

if __name__ == '__main__':
    t1=time.time()
    print(filter_msg('你好'))
    print(time.time()-t1)
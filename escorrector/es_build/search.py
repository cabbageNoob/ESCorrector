'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 18:18:41
'''
import json, time
from elasticsearch import Elasticsearch
es = Elasticsearch()


def filter_msg(msg,index_name=''):
    body = {
        "size": 20,
        "query": {
            "match": {
                "sentence":msg
            }
        }
    }
    res = es.search(index=index_name, body=body)
    return json.dumps((res['hits']['hits']), indent=4, ensure_ascii=False)
    # return res['hits']['hits']

def filter_phrase_msg(msg,index_name=''):
    body = {
        "size": 20,
        "query": {
            "match_phrase": {
                "sentence":msg
            }
        },
        # "aggs": {
        #     "uid_aggs": {
        #         "terms": {
        #             "field": "sentence.keyword",
        #             "size": 1
        #         },
        #         "aggs": {
        #             "uid_top": {
        #                 "top_hits": {
        #                     "size": 5
        #                 }
        #             }
        #         }
        #     }
        # }
    }
    res = es.search(index=index_name, body=body)
    return json.dumps((res['hits']['hits']), indent=4, ensure_ascii=False)

def filter_msg_regexp(msg, index_name=''):
    body = {
        "size": 20,
        "query": {
            "regexp":{
                "keyword": msg
            }
        }
    }
    res = es.search(index=index_name, body=body)
    return json.dumps((res['hits']['hits']), indent=4, ensure_ascii=False)


if __name__ == '__main__':
    t1=time.time()
    # print(filter_msg('你好'))
    # print(time.time() - t1)
    # print(filter_phrase_msg('忙',index_name='no_genera_sighan_test'))
    # print(filter_phrase_msg('很忙',index_name='no_genera_people14_sighan_test'))
    print(filter_msg_regexp('.*很忙..*', index_name='no_genera_people14_sighan_test'))
    # print(filter_phrase_msg('工作很忙', index_name='no_genera_people14_sighan_test'))
    print(time.time() - t1)
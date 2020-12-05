'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 16:53:47
'''
import os, sys
sys.path.insert(0, os.getcwd())
import codecs, time
from escorrector.es_build import config
from escorrector.utils.text_utils import split_2_short_text
from elasticsearch import Elasticsearch, helpers
es = Elasticsearch()
print(es.ping())

def read_file(file_path):
    segments=[]
    with codecs.open(file_path, 'r', encoding='utf8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            segments.extend([seg[0] for seg in split_2_short_text(line)])
    return segments

def set_mapping():
    body = {
        "mappings": {
            "doc": {
                "properties": {
                    "sentence": {
                        "type": "text"
                    }
                }
            }
        }
    }
    if not es.indices.exists(index='corpus'):
        print(es.indices.create(index='corpus', body=body))

def set_datas(file_path):
    data_corpus=read_file(file_path)
    action = (
        {
            "_index": "corpus",
            "_type": "doc",
            "_source": {
                "sentence": i,
            }
        } for i in data_corpus)
    t1 = time.time()
    helpers.bulk(es, action)
    print(time.time()-t1)
    return data_corpus

if __name__ == '__main__':
    set_mapping()
    set_datas(config.people2014_path)
    # print(read_file(config.people2014_path))
    

    
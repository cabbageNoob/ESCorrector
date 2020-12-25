'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 16:53:47
'''
import os, sys
sys.path.insert(0, os.getcwd())
import codecs, time
from escorrector.es_build import config
from escorrector.utils.text_utils import split_2_short_text, string_generalization
from elasticsearch import Elasticsearch, helpers
es = Elasticsearch()
print(es.ping())

def read_file(file_path):
    segments=[]
    with codecs.open(file_path, 'r', encoding='UTF-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            segments.extend([seg[0] for seg in split_2_short_text(line)])
    return segments

def set_mapping(index_name=''):
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
    if not es.indices.exists(index=index_name):
        print(es.indices.create(index=index_name, body=body))

def set_datas(file_path,index_name=''):
    data_corpus = read_file(file_path)
    action = []
    action = (
        {
            "_index": index_name,
            "_type": "doc",
            "_source": {
                "sentence": i,#''.join(string_generalization(i))
            }
        } for i in data_corpus)
    t1 = time.time()
    helpers.bulk(es, action)
    print(time.time()-t1)
    return data_corpus

if __name__ == '__main__':
    set_mapping(index_name='no_genera_sighan_test')
    set_datas(index_name='no_genera_sighan_test', file_path=config.sighan15_path)
    # print(read_file(config.people2014_path))

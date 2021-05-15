
import sys, os, codecs, time, docx, json
sys.path.insert(0, os.getcwd())
pwd_path = os.path.abspath(os.path.dirname(__file__))

from utils.text_utils import split_2_short_text, is_chinese_string
from escorrector import config
from corrector_dict.detector_dict import DetectorDict
detector_dict = DetectorDict()
detector_dict.check_detector_dict_initialized()
tokenizer = detector_dict.tokenizer

from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from collections.abc import Iterable

import warnings
warnings.filterwarnings('ignore')
es = Elasticsearch(timeout=30)

from utils.logger import get_logger
import datetime
if not os.path.exists(os.path.join(pwd_path, '../log/')):
    os.makedirs(os.path.join(pwd_path, '../log/'))

time_now = datetime.datetime.now()
today_log = os.path.join(pwd_path, '../log/' + str(time_now.year) + '-' + str(time_now.month) + '-' + str(time_now.day) + '.log')
mylogger = get_logger(__name__, today_log)


def read_file(file_path, n=4):
    segments={}
    if file_path.endswith('docx'):
        docx_file = docx.Document(file_path)
        datas = docx_file.paragraphs
    elif file_path.endswith('txt'):
        datas = codecs.open(file_path, 'r', encoding='UTF-8')
    for line in datas:
        if file_path.endswith('docx'):
            line = line.text.strip()
        elif file_path.endswith('txt'):
            line = line.strip()
        if line == '' or line.startswith('#'):
            continue
        blocks = split_2_short_text(line)
        for blk, idx in blocks:
            blk=' '.join(tokenizer.jieba_cut(blk.replace(' ', '')))
            words = blk.split()
            for i in range(len(words) - n + 1):
                words_blk = ''.join(words[i:i + n])
                if not is_chinese_string(words_blk):
                    continue
                if segments.get(words_blk) == None:
                    segments[words_blk] = 1
                else:
                    segments[words_blk] += 1
            for j in range(n - 1):
                if len(words) > j:
                    words_blk = ''.join(words[-j - 1:])
                    if not is_chinese_string(words_blk):
                        continue
                    if segments.get(words_blk) == None:
                        segments[words_blk] = 1
                    else:
                        segments[words_blk] += 1
    return segments

def read_line(line, n=4):
    segments={}
    line = line.strip()
    blocks = split_2_short_text(line)
    for blk, idx in blocks:
        blk=' '.join(tokenizer.jieba_cut(blk.replace(' ', '')))
        words = blk.split()
        for i in range(len(words) - n + 1):
            words_blk = ''.join(words[i:i + n])
            if not is_chinese_string(words_blk):
                continue
            if segments.get(words_blk) == None:
                segments[words_blk] = 1
            else:
                segments[words_blk] += 1
        for j in range(n - 1):
            if len(words) > j:
                words_blk = ''.join(words[-j - 1:])
                if not is_chinese_string(words_blk):
                    continue
                if segments.get(words_blk) == None:
                    segments[words_blk] = 1
                else:
                    segments[words_blk] += 1
    return segments

def set_mapping(index_name=''):
    body = {
        "mappings": {
            "doc": {
                "properties": {
                    "keyword": {
                        "type":"keyword"
                    },
                    "count": {
                        "type": "integer"
                    }
                }
            }
        }
    }
    if not es.indices.exists(index=index_name):
        print(es.indices.create(index=index_name, body=body))

def bulk_set_datas(file_path,n=4,index_name=''):
    '''
    使用ES批量插入更新
    '''
    segments = read_file(file_path, n=n)
    t1 = time.time()
    actions=(
        {
            "_op_type":"update",
            "_index":index_name,
            "_type":"doc",
            "_id":segment,
            "script":{
                "inline":"ctx._source.count += params.msg_count",
                "params":{
                    "msg_count":msg_count
                }
            },
            "upsert": {
                "keyword": segment,
                "count":msg_count
            }
        } for segment, msg_count in segments.items()
    )
    helpers.bulk(es,actions=actions)
    mylogger.info('index ' + file_path +'size: ' + str(os.path.getsize(file_path)) + ' byte spend  ' + str(time.time() - t1))
    print(file_path,' finish ', time.time() - t1)
    return time.time() - t1

def bulk_set_line(line,n=4,index_name=''):
    segments=read_line(line,n=n)
    t1 = time.time()
    actions=(
        {
            "_op_type":"update",
            "_index":index_name,
            "_type":"doc",
            "_id":segment,
            "script":{
                "inline":"ctx._source.count += params.msg_count",
                "params":{
                    "msg_count":msg_count
                }
            },
            "upsert": {
                "keyword": segment,
                "count":msg_count
            }
        } for segment, msg_count in segments.items()
    )
    helpers.bulk(es,actions=actions)
    return time.time() - t1

def filter_msg_regexp(msg, index_name=''):
    body = {
        "size": 100,
        "query": {
            "regexp":{
                "keyword": msg
            }
        },
        'sort': [
            {'count': 'desc'},
            {'_score': 'desc'}
        ],
    }
    res = es.search(index=index_name, body=body)
    return json.dumps((res['hits']['hits']), indent=4, ensure_ascii=False)

def index_corpus(data_dirs,index_name=''):
    if isinstance(data_dirs, str):
        for root, dirs, files in os.walk(data_dirs):
            for file in files:
                if file.endswith('.docx') or file.endswith('.txt'):
                    file_path = root + '/' + file
                    try:
                        bulk_set_datas(file_path=file_path,index_name=index_name)
                    except Exception as e:
                        mylogger.error(file_path + ' error: ' + str(e))
                        continue
    elif isinstance(data_dirs, Iterable):
        for data_dir in data_dirs:
            index_corpus(data_dir,index_name=index_name)


if __name__ == '__main__':
    set_mapping(index_name='test')
    line='今天突然冷了起来，妈妈从箱子里翻出一件旧棉衣让我穿上。我不愿意。在妈妈的说服教育下，我终于穿上那件棉衣哼着歌儿上学去了。'
    print(bulk_set_line(line=line,index_name='test'))
    # 建立索引
    index_corpus(config.index_data_dir, index_name='test')

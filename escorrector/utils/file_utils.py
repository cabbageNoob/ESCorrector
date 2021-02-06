'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-11 21:43:04
'''
import sys, os, json
sys.path.insert(0, os.getcwd())
from escorrector.utils.math_utils import find_all_idx

pwd_path = os.path.abspath(os.path.dirname(__file__))
sighan13_path = os.path.join(pwd_path, '../data/cn/sighan/sighan_2013_test.txt')
sighan14_path = os.path.join(pwd_path, '../data/cn/sighan/sighan_2014_test.txt')
sighan15_path = os.path.join(pwd_path, '../data/cn/sighan/sighan_2015_test.txt')
bcmi_path = os.path.join(pwd_path, '../data/cn/sighan/bcmi.txt')

sighan13_right_path = os.path.join(pwd_path, '../data/cn/sighan_right/sighan_2013_test_right.txt')
sighan14_right_path = os.path.join(pwd_path, '../data/cn/sighan_right/sighan_2014_test_right.txt')
sighan15_right_path = os.path.join(pwd_path, '../data/cn/sighan_right/sighan_2015_test_right.txt')
bcmi_right_path = os.path.join(pwd_path, '../data/cn/sighan_right/bcmi_test_right.txt')
def get_bcmi_corpus(line, left_symbol='（（', right_symbol='））'):
    """
    转换原始文本为encoder-decoder列表
    :param line: 王老师心（（性））格温和，态度和爱（（蔼）），教学有方，得到了许多人的好平（（评））。
    :param left_symbol:
    :param right_symbol:
    :return: ["王老师心格温和，态度和爱，教学有方，得到了许多人的好平。" , "王老师性格温和，态度和蔼，教学有方，得到了许多人的好评。"]
    """
    error_sentence, correct_sentence = '', ''
    # 错误词index列表
    index_list = list()
    if left_symbol not in line or right_symbol not in line:
        return line, line, index_list

    left_ids = find_all_idx(line, left_symbol)
    right_ids = find_all_idx(line, right_symbol)
    if len(left_ids) != len(right_ids):
        return error_sentence, correct_sentence,index_list
    begin = 0
    index = line.find('（（')
    while (index != -1):
        index_list.append(index - 5*len(index_list)-1)
        index = line.find('（（', index + 1)
    for left, right in zip(left_ids, right_ids):
        correct_len = right - left - len(left_symbol)
        correct_word = line[(left + len(left_symbol)):right]
        error_sentence += line[begin:left]
        correct_sentence += line[begin:(left - correct_len)] + correct_word
        begin = right + len(right_symbol)
    error_sentence += line[begin:]
    correct_sentence += line[begin:]
    return error_sentence, correct_sentence, index_list

def convert_data(data_path, target_path):
    target_f = open(target_path, 'w+', encoding='utf8')
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            error_sentence=''
            try:
                error_sentence, right_sentence, index_list = get_bcmi_corpus(line)
                target_f.writelines(right_sentence + '\n')
            except Exception as e:
                print(e)

def writejson2file(data, filename):
    with open(filename, 'w',encoding='utf8') as outfile:
        data = json.dumps(data, indent=4, ensure_ascii=False)
        outfile.write(data)

def readjson(filename):
    with open(filename,'rb') as outfile:
        return json.load(outfile)

def get_right(filename):
    datas = readjson(filename)
    with open(os.path.join(pwd_path,'../data/cn/test_set/test_right.txt'),'w',encoding='utf8') as f:
        for data in datas:
            right_data = data['right_text']
            f.writelines(right_data + '\n')
        

if __name__ == '__main__':
    convert_data(bcmi_path,bcmi_right_path)
    # get_right(os.path.join(pwd_path, '../data/cn/test_set/test-a.json'))
    
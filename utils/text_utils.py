'''
@Descripttion: 
@Author: cjh (492795090@qq.com)
Date: 2021-05-10 20:57:48
'''
# -*- coding: utf-8 -*-
# Brief: 汉字处理的工具:判断unicode是否是汉字，数字，英文，或者其他字符。以及全角符号转半角符号。
import re, json

import  operator
import six

re_han = re.compile("([\u4E00-\u9FD5a-zA-Z0-9+#&]+)", re.U)
_re_han = re.compile("([,?!，。？！;；、]+)", re.U)
from utils.langconv import Converter


def convert_to_unicode(text):
    """Converts `text` to Unicode (if it's not already), assuming utf-8 input."""
    if six.PY3:
        if isinstance(text, str):
            return text
        elif isinstance(text, bytes):
            return text.decode("utf-8", "ignore")
        else:
            raise ValueError("Unsupported string type: %s" % (type(text)))
    elif six.PY2:
        if isinstance(text, str):
            return text.decode("utf-8", "ignore")
        elif isinstance(text, str):
            return text
        else:
            raise ValueError("Unsupported string type: %s" % (type(text)))
    else:
        raise ValueError("Not running on Python2 or Python 3?")


def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if '\u4e00' <= uchar <= '\u9fa5':
        return True
    else:
        return False


def is_chinese_string(string):
    """判断是否全为汉字"""
    for c in string:
        if not is_chinese(c):
            return False
    return True


def is_number(uchar):
    """判断一个unicode是否是数字"""
    if u'u0030' <= uchar <= u'u0039':
        return True
    else:
        return False


def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (u'u0041' <= uchar <= u'u005a') or (u'u0061' <= uchar <= u'u007a'):
        return True
    else:
        return False


def is_alphabet_string(string):
    """判断是否全部为英文字母"""
    for c in string:
        if c < 'a' or c > 'z':
            return False
    return True


def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
        return True
    else:
        return False


def B2Q(uchar):
    """半角转全角"""
    inside_code = ord(uchar)
    if inside_code < 0x0020 or inside_code > 0x7e:  # 不是半角字符就返回原来的字符
        return uchar
    if inside_code == 0x0020:  # 除了空格其他的全角半角的公式为:半角=全角-0xfee0
        inside_code = 0x3000
    else:
        inside_code += 0xfee0
    return chr(inside_code)


def Q2B(uchar):
    """全角转半角"""
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0
    if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
        return uchar
    return chr(inside_code)


def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([Q2B(uchar) for uchar in ustring])


def uniform(ustring):
    """格式化字符串，完成全角转半角，大写转小写的工作"""
    return stringQ2B(ustring).lower()


def remove_punctuation(strs):
    """
    去除标点符号
    :param strs:
    :return:
    """
    return re.sub("[\s+\.\!\/<>“”,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+", "", strs.strip())


def traditional2simplified(sentence):
    """
    将sentence中的繁体字转为简体字
    :param sentence: 待转换的句子
    :return: 将句子中繁体字转换为简体字之后的句子
    """
    sentence = Converter('zh-hans').convert(sentence)
    return sentence


def split_2_short_text(text, include_symbol=False):
    """
    长句切分为短句
    :param text: str
    :param include_symbol: bool
    :return: (sentence, idx)
    """
    result = []
    blocks = _re_han.split(text)
    start_idx = 0
    for blk in blocks:
        if not blk:
            continue
        if include_symbol:
            result.append((blk, start_idx))
        else:
            if not _re_han.match(blk):
                result.append((blk, start_idx))
        start_idx += len(blk)
    return result


def _check_contain_error(maybe_err, details=[]):
    """
    检测错误集合(maybe_errors)是否已经包含该错误位置（maybe_err)
    :param maybe_err: [error_word, begin_pos, end_pos, error_type]
    :param details:[err_word, correct_word, begin_idx, end_idx, ErrorType]
    :return:
    """
    for err in details:
        if (maybe_err[1] >= err[2] and maybe_err[1] < err[3]) or \
            (maybe_err[2] > err[2] and maybe_err[2] <= err[3]):
            return True
    return False


def get_correct_text(src_text, details):
    '''
    Descripttion: 根据src_text与details获取纠正后的文本
    param {src_text} 
    param {details} [err_word, correct_word, begin_idx, end_idx, ErrorType]
    return {text_new} 
    '''    
    correct_word = 1
    begin_idx = 2
    end_idx = 3
    text_new = ''
    # 错误word的结束pos
    wrong_index = 0
    details = sorted(details, key=operator.itemgetter(2))
    for detail in details:
        sub_right_text = src_text[wrong_index:detail[begin_idx]]
        sub_correct_text = detail[correct_word]
        wrong_index = detail[end_idx]
        text_new += sub_right_text
        text_new += sub_correct_text
    left = src_text[wrong_index:]
    text_new += left
    return text_new


def find_index_tokens(tokens, begin_idx, end_idx):
    '''
    Descripttion: 找到idx对应tokens的index
    param {tokens} 列表
        'begin': 0,
        'end': 1,
        'pos': 'c',
        'text': '但'
    return {*}
    '''
    if tokens == None:
        return None
    for _index, item in enumerate(tokens):
        if begin_idx >= item['begin'] and begin_idx < item['end']:
            begin_index = _index
            end_index = begin_index
        elif end_idx > item['begin'] and end_idx <= item['end']:
            end_index = _index
    return begin_index, end_index


def find_index_tokens_jieba(tokens, begin_idx, end_idx):
    '''
    Descripttion: 
    param {tokens}
        token, 
        begin_idx, 
        end_idx
    return {*}
    '''
    if tokens == None:
        return None
    for _index, item in enumerate(tokens):
        if begin_idx >= item[1] and begin_idx < item[2]:
            begin_index = _index
            end_index = begin_index
        elif end_idx > item[1] and end_idx <= item[2]:
           end_index = _index
    return begin_index, end_index


def writejson2file(data, filename):
    with open(filename, 'w',encoding='utf8') as outfile:
        data = json.dumps(dict(data), indent=4, ensure_ascii=False)
        outfile.write(data)


def readjson(filename):
    with open(filename,'rb') as outfile:
        return json.load(outfile)


def load_diction(diction):
    with open(diction, 'r', encoding='utf8') as f:
        lines = f.readlines()
        lines = [l.strip() for l in lines]
    return set(lines)


if __name__ == "__main__":
    # a = 'nihao'
    # print(a, is_alphabet_string(a))
    # # test Q2B and B2Q
    # for i in range(0x0020, 0x007F):
    #     print(Q2B(B2Q(chr(i))), B2Q(chr(i)))
    # # test uniform
    # ustring = '中国 人名ａ高频Ａ  扇'
    # ustring = uniform(ustring)
    # print(ustring)
    # print(is_other(','))
    # print(uniform('你干么！ｄ７＆８８８学英 语ＡＢＣ？ｎｚ'))
    # print(is_chinese('喜'))
    # print(is_chinese_string('喜,'))
    # print(is_chinese_string('丽，'))
    print(split_2_short_text('发行人说明'))

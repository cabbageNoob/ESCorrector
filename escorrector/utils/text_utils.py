'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 18:31:46
'''
import sys, os, re
sys.path.insert(0, os.getcwd())
from escorrector.utils.nlpir_tokenizer import tokenizer4IR
import operator

re_han = re.compile("([\u4E00-\u9FD5a-zA-Z0-9+#&]+)", re.U)
_re_han = re.compile("([,?!，。？！;；、]+)", re.U)
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

# def split_2_short_text(text, include_symbol=False):
#     """
#     长句切分为短句
#     :param text: str
#     :param include_symbol: bool
#     :return: (sentence, idx)
#     """
#     result = []
#     blocks = re_han.split(text)
#     start_idx = 0
#     for blk in blocks:
#         if not blk:
#             continue
#         if include_symbol:
#             result.append((blk, start_idx))
#         else:
#             if re_han.match(blk):
#                 result.append((blk, start_idx))
#         start_idx += len(blk)
#     return result

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

def transformer_details(detail):
    return [detail[0], '', detail[1], detail[2], detail[3]]

def is_alphabet_string(string):
    """判断是否全部为英文字母"""
    for c in string:
        if c < 'a' or c > 'z':
            return False
    return True

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

def string_generalization(ustring):
    '''
    Descripttion: 字符串泛化，泛化其中的人名、地名、以及时间数字
        人名：[nr,nr1,nr2,nrj,nrf] NR
        地名：[ns, nsf] NS
        时间：[t,tg] T
        数字：[m,mq] M
    param {*}
    return {*}
    '''
    if isinstance(ustring, bytes):
        ustring = ustring.decode("utf-8", "ignore")
    after_generalization = []
    tokens = tokenizer4IR(ustring)
    if tokens == None:
        return []
    for item in tokens:
        if item['pos'] in ['nr', 'nr1', 'nr2', 'nrj', 'nrf']:
            item['text'] = 'NR'
        elif item['pos'] in ['ns', 'nsf']:
            item['text'] = 'NS'
        elif item['pos'] in ['t', 'tg']:
            item['text'] = 'T'
        elif item['pos'] in ['m', 'mq']:
            item['text'] = 'M'
        after_generalization.append(item['text'])
    return after_generalization

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
    

if __name__ == '__main__':
    # test = '《活着》是余华写的一本让人不忍卒读的书，赞誉很高'
    # split_2_short_text(test)
    print(string_generalization('”ACDF'))
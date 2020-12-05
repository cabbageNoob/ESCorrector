'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 18:31:46
'''
import re

re_han = re.compile("([\u4E00-\u9FD5a-zA-Z0-9+#&]+)", re.U)
_re_han = re.compile("([,?!，。？！]+)", re.U)
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

if __name__ == '__main__':
    test = '《活着》是余华写的一本让人不忍卒读的书，赞誉很高'
    split_2_short_text(test)
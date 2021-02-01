'''
@Descripttion: 评测代码，使用sighan测试集
@Author: cjh (492795090@qq.com)
@Date: Do not edit
'''
import os
import sys, time
sys.path.insert(0, os.getcwd())
from escorrector.corrector_regexp import Corrector
from escorrector.utils.math_utils import find_all_idx
from escorrector.utils.text_utils import get_correct_text
"""
泛化语料建立的索引：
    sighan测试集：sighan_test
    人民日报语料：corpus_generalization
    人民日报语料 + sighan数据集：people14_sighan_test

未泛化语料建立的索引：
    sighan测试集：no_genera_sighan_test
    人民日报语料：corpus
    人民日报语料 + sighan数据集：no_genera_people14_sighan_test
"""
corrector = Corrector(is_word_error_detect=True,is_char_correct=False, is_word_correct=True,index_name='no_genera_people14_sighan_test')

pwd_path = os.path.abspath(os.path.dirname(__file__))

sighan_2013 = os.path.join(pwd_path, './data/cn/sighan/sighan_2013_test.txt')
sighan_2014 = os.path.join(pwd_path, './data/cn/sighan/sighan_2014_test.txt')
sighan_2015 = os.path.join(pwd_path, './data/cn/sighan/sighan_2015_test.txt')

eval_result = os.path.join(pwd_path,'./data/cn/test_set/sighan13_eval(加入jieba分词检错).txt')
# sighan_2014_eval = os.path.join(pwd_path, './data/cn/sighan_eval/people14/sighan_2014_eval.txt')
# sighan_2015_eval = os.path.join(pwd_path, './data/cn/sighan_eval/sighan_people14/sighan_2015_eval.txt')

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

def eval_bcmi_data(data_path, eval_result, verbose=False):
    sentence_size = 0
    sentence_error_size = 0 # 错误sent数目
    char_error_size = 0 # 错误char数目

    right_result = dict()
    wrong_result = dict()
    # 其他数据
    word_count = 0
    sentence_detec_size = 0  # detec sentence数目
    char_detec_size = 0

    word_detec_count_char = 0  # 预测出字的数目
    word_detec_count_miss = 0   # 预测少字的数目
    word_detec_count_redundancy = 0  # 预测多字的数目
    word_detec_count_error = 0  #预测词错数目
    word_detec_count_confusion=0  #困惑集数目

    char_detec_right = 0  # char detect正确
    sentence_detec_right = 0  # sentence detec正确
    
    char_correct_right = 0  # char correct正确
    sentence_correct_right=0 # sentence correct正确

    eval_file = open(eval_result, 'w', encoding='utf8')
    t1=time.time()
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            error_sentence = ''
            try:
                error_sentence, right_sentence, index_list = get_bcmi_corpus(line)
            except Exception as e:
                print(e)
            if not error_sentence:
                continue
            # pred_sentence, pred_detail = bertCorrector.bert_correct_ssc_origin(error_sentence)
            pred_detail = corrector.correct(error_sentence, details=[])
            pred_sentence = get_correct_text(error_sentence, pred_detail)
            if verbose:
                print('input sentence:', error_sentence)
                print('pred sentence:', pred_sentence, pred_detail)
                print('right sentence:', right_sentence)
                print('wrong_index', index_list)
                eval_file.write('input sentence:' + error_sentence + '\n')
                eval_file.write('pred sentence:'+ pred_sentence+ str(pred_detail)+'\n')
                eval_file.write('right sentence:'+right_sentence+'\n')
                eval_file.write('wrong_index'+ str(index_list)+'\n\n')
            sentence_size += 1
            if pred_detail:  # detect出错误
                sentence_detec_size += 1
                if index_list:
                    sentence_detec_right += 1
            if index_list:
                char_error_size += len(index_list)  # 错误字数
                sentence_error_size += 1
            char_detec_size += len(pred_detail)  # 预判错误个数
            # 预测的错误字词
            pred_index_list = list()
            for detail in pred_detail:
                temp = detail[2]
                while(temp < detail[3]):
                    pred_index_list.append(temp)
                    temp += 1

            for i, index in enumerate(index_list):
                if index in pred_index_list:
                    char_detec_right += 1 # char detect正确 
                    try:
                        if(pred_sentence[index] == right_sentence[index]):
                            char_correct_right += 1  # char correct正确
                    except Exception as e:
                        print(e)

            if index_list and right_sentence == pred_sentence:
                sentence_correct_right += 1
                right_result[error_sentence] = [right_sentence, pred_sentence]
            else:
                wrong_result[error_sentence] = [right_sentence, pred_sentence]
    eval_file.close()
    if verbose:
        sent_detec_r = sentence_detec_right / (sentence_error_size * 1.0)
        sent_detec_p = sentence_detec_right / (sentence_detec_size * 1.0)
        sent_correct_r = sentence_correct_right / (sentence_error_size * 1.0)
        sent_correct_p = sentence_correct_right / (sentence_detec_size * 1.0)
        print('sentence size:', sentence_size, '; senence_error_size:', sentence_error_size)
        print('检测出错误句子数目', sentence_detec_size, ';正确检测出句子错误数目:', sentence_detec_right,'; 正确correct句子数目：',sentence_correct_right)
        print('sent_detec_r:', str(sent_detec_r),';sent_detec_p:', str(sent_detec_p))
        print('sent_correct_r:', str(sent_correct_r),';sent_correct_p:', str(sent_correct_p))
        print('sent_detec_F1:', str((2 * sent_detec_r * sent_detec_p) / (sent_detec_r + sent_detec_p)))
        print('sent_correct_F1:', str((2 * sent_correct_r * sent_correct_p) / (sent_correct_r + sent_correct_p)))

        char_detec_r = char_detec_right / (char_error_size * 1.0)
        char_detec_p = char_detec_right / (char_detec_size * 1.0)
        char_correct_r = char_correct_right / (char_error_size * 1.0)
        char_correct_p = char_correct_right / (char_detec_size * 1.0)
        print('词错误数量:', char_error_size, ';预判字词错误总数量:', char_detec_size)
        print('预测错误词位置正确数目: ', char_detec_right)
        print('准确预测错误，并成功纠错数目:', char_correct_right)
        print('char_detec_r:', str(char_detec_r),';char_detec_p:', str(char_detec_p))
        print('char_correct_r:', str(char_correct_r),';char_correct_p:', str(char_correct_p))
        print('char_detec_F1:', str((2 * char_detec_r * char_detec_p) / (char_detec_r + char_detec_p)))
        print('char_correct_F1:', str((2 * char_correct_r * char_correct_p) / (char_correct_r + char_correct_p)))
        print('spend total time:{}'.format(time.time() - t1))
        print('average time:{}'.format((time.time() - t1)/(sentence_size*1.0)))

if __name__ == "__main__":
    # get_gcmi_cor_test()
    # eval_bcmi_data_test()
    eval_bcmi_data(sighan_2013, eval_result=eval_result, verbose=True)
    # get_confusion_、dict()

'''
@Descripttion: 
@Author: cjh (492795090@qq.com)
@Date: Do not edit
'''
import os
import sys, time
sys.path.insert(0, os.getcwd())
from escorrector.corrector_regexp import Corrector
from escorrector import config
from escorrector.utils.text_utils import get_correct_text
from escorrector.utils.file_utils import writejson2file, readjson

pwd_path = os.path.abspath(os.path.dirname(__file__))
eval_result = os.path.join(pwd_path,'./data/cn/test_set/sighan13(未加入jieba分词检错).txt')
corrector = Corrector(is_word_error_detect=False,is_char_correct=False, is_word_correct=True,index_name='no_genera_people14_sighan_test')

def eval_test(data_path, eval_result, verbose=False):
    # 错误字总数
    char_error_size = 0
    # 正确检错字数
    char_detec_right = 0
    # 检错字数
    char_detec_size = 0
    # 正确校对字数
    char_correct_right = 0

    eval_file = open(eval_result, 'w', encoding='utf8')
    t1=time.time()
    test_datas = readjson(data_path)
    for item in test_datas:
        error_sentence = item['wrong_text']
        right_sentence = item['right_text']
        index_list = item['detail']
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
            eval_file.write('wrong_index' + str(index_list) + '\n\n')
        if index_list:
            char_error_size += len(index_list)  # 错误字数
        char_detec_size += len(pred_detail)  # 预判错误个数
        # 预测的错误字词
        pred_index_list = list()
        for detail in pred_detail:
            temp = detail[2]
            while(temp < detail[3]):
                pred_index_list.append(temp)
                temp += 1
        
        for wrong_char, right_char, start_idx, end_idx in index_list:
            if start_idx in pred_index_list:
                char_detec_right += 1 # char detect正确 
                try:
                    if(pred_sentence[start_idx] == right_sentence[start_idx]):
                        char_correct_right += 1  # char correct正确
                except Exception as e:
                    print(e)
    if verbose:
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
        print('average time:{}'.format((time.time() - t1) / (sentence_size * 1.0)))

        eval_file.write('char_detec_r:'+ str(char_detec_r)+';char_detec_p:'+ str(char_detec_p)+'\n')
        eval_file.write('char_correct_r:'+ str(char_correct_r)+';char_correct_p:'+ str(char_correct_p)+'\n')
        eval_file.write('char_detec_F1:'+ str((2 * char_detec_r * char_detec_p) / (char_detec_r + char_detec_p))+'\n')
        eval_file.write('char_correct_F1:'+ str((2 * char_correct_r * char_correct_p) / (char_correct_r + char_correct_p))+'\n')
        eval_file.write('spend total time:{}'.format(time.time() - t1)+'\n')
        eval_file.write('average time:{}'.format((time.time() - t1) / (sentence_size * 1.0))+'\n')
    eval_file.close()
        
if __name__ == '__main__':
    eval_test(data_path=config.sighan_2013, eval_result=eval_result, verbose=True)
    
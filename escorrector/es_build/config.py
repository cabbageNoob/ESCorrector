'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 18:05:16
'''
import os

pwd_path = os.path.abspath(os.path.dirname(__file__))
# 人民日报2014语料
people2014_path = os.path.join(pwd_path, '../data/people2014.txt')

# sighan语料
sighan13_path = os.path.join(pwd_path, '../data/cn/sighan_right/sighan_2013_test_right.txt')
sighan14_path = os.path.join(pwd_path, '../data/cn/sighan_right/sighan_2014_test_right.txt')
sighan15_path = os.path.join(pwd_path, '../data/cn/sighan_right/sighan_2015_test_right.txt')

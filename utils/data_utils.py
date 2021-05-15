'''
@Descripttion: 
@Author: cjh (492795090@qq.com)
Date: 2021-05-10 21:18:46
'''
import docx, re
import sys, os
sys.path.insert(0, os.getcwd())
from escorrector import config

def doc_parse(dir_path):
    for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('docx'):
                    file_path = root + '/' + file
                    docx_file = docx.Document(file_path)
                    for line in docx_file.paragraphs:
                        print(line.text)

def main():
    doc_parse(config.word1_path)

if __name__ == '__main__':
    main()

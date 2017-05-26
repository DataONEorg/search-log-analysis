#!/usr/bin/python

import apache_log_parser
import os
from pprint import pprint
import sys

def process(baseDir):
    line_parser = apache_log_parser.make_parser("%v %h %l %u %t \"%r\" %>s %b")
    for root, subFolders, files in os.walk(baseDir):
        for file in files:
            with open(os.path.join(root, file), 'r') as logFile:
                for line in logFile:
                    log_line_data = line_parser(line)
                    pprint(log_line_data);



if __name__ == "__main__":
    baseDir = sys.argv[1]
    baseDir = os.path.abspath(baseDir)
    process(baseDir)




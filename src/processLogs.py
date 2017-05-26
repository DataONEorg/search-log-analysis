#!/usr/bin/python

import apache_log_parser
import dateutil.parser
import json
from luqum.parser import parser
from luqum.parser import ParseError
from luqum.pretty import prettify
import MySQLdb
import os
from pprint import pprint
import re
import sys
import urllib

#Connect to the database and return a connection object
class dbConn(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host="localhost",
            user="dataoneuser",
            passwd="aA7tjWxwqTqJFXTSe5d5",
            db="dataone")
    def __enter__(self):
        return self.conn
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()


#Check the database lookup table to see if an IP address has
#been stored there.  If it has, return its anonymized ID; if
#it hasn't, insert it into the table and return its new
#anonymized ID
def getHostId(ip):
    with dbConn() as conn:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        sql = "SELECT id FROM dataone.ipAddr WHERE ip = (%s)"
        cursor.execute(sql, [ip])
        if cursor.rowcount == 0:
            sql = "INSERT INTO dataone.ipAddr (ip) VALUES (%s)"
            cursor.execute(sql, [ip])
            conn.commit()
            return cursor.lastrowid

        elif cursor.rowcount == 1:
            return cursor.fetchone()['id']

        else:
            print 'found too many hostIds'


#Check the database lookup table to see if a user ID has
#been stored there.  If it has, return its anonymized ID; if
#it hasn't, insert it into the table and return its new
#anonymized ID
def getUserId(requestPath):
    userId = requestPath.replace('/cn/v2/accounts/', '')
    userId = userId.replace('pendingmap/', '')
    userId = urllib.unquote(userId)
    if userId == '':
        return 0
    #print userId
    with dbConn() as conn:
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        sql = "SELECT id FROM dataone.userId WHERE userId = (%s)"
        cursor.execute(sql, [userId])
        if cursor.rowcount == 0:
            sql = "INSERT INTO dataone.userId (userId) VALUES (%s)"
            cursor.execute(sql, [userId])
            conn.commit()
            return cursor.lastrowid

        elif cursor.rowcount == 1:
            return cursor.fetchone()['id']

        else:
            print 'found too many userIds'


#Based upon the log event data, build a data structure
#to represent all the values that will be stored in the
#database.  Lookup remote host IPs and user IDs to
#anonymize them.  Mark unparseable queries, strip out
#illegal characters, and take a stab at identifying the
#query term.
def constructPayload(lineId, logData):
    activity = ''
    querySolr = None
    searchKey = None
    userId = 0
    querySolr4 = ''
    requestPath = logData.get('request_url_path', '')
    queryDict = logData.get('request_url_query_dict', '')

    if requestPath.startswith('/cn/v2/accounts/'):
        activity = 'login'
        userId = getUserId(requestPath)
        #print userId
        
        #obscure the request path because it contains the userid
        requestPath = '/cn/v2/accounts/'
    
    elif requestPath.startswith('/cn/v2/query/solr/'):
        activity = 'search'
        querySolr = queryDict.get('q', '')
        if len(querySolr) > 0:
            querySolr = querySolr[0]
        else:
            querySolr = ''

        if querySolr and querySolr != '':
            try:
                q = parser.parse(querySolr)
            except ParseError as e:
                print lineId, e.message
                q = ''
                searchKey = 'unparseable'
                querySolr = 'unparseable'

            q = repr(q)
            regex = "Phrase\('([^']+)'\)"
            m = re.search(regex, q)
            if m:
                if m.group(1):
                    searchKey = m.group(1)[1:-1]
    
    else:
        activity = 'other'
    
    queryDict = json.dumps(queryDict, ensure_ascii=False)

    payload = {'id': lineId,
                'hostId': getHostId(logData['remote_host']),
                'userId': userId,
                'activity': activity,
                'path': requestPath,
                'queryDict': queryDict,
                'querySolr': querySolr,
                'searchKey': searchKey,
                'status': logData.get('status', ''),
                'responseSize': logData.get('response_bytes_clf', ''),
                'timeStamp': dateutil.parser.parse(logData.get('time_received_utc_isoformat', ''))
              }
    
    return payload


#Iterate over log files and log lines, constructing
#a database payload for each line.  Insert the payload
#into the database.
def process(baseDir):
    ips = []
    lineParser = apache_log_parser.make_parser("%h %l %u %t \"%r\" %>s %b")

    with dbConn() as conn:
        cursor = conn.cursor()
        for root, subFolders, files in os.walk(baseDir):
            for file in files:
                with open(os.path.join(root, file), 'r') as logFile:
                    for line in logFile:
                        sql = "INSERT INTO dataone.rawLog (line) VALUES (%s)"
                        cursor.execute(sql, [line])
                        
                        lineId = cursor.lastrowid
                        #if lineId == 20934:
                        #    print line

                        logData = lineParser(line)
                        payload = constructPayload(lineId, logData)

                        sql = (
                            "INSERT INTO dataone.logData"
                            " (id, hostId, userId, activity, path, queryDict,"
                            " querySolr, searchKey, status, responseSize, timeStamp)"
                            " VALUES (%(id)s, %(hostId)s, %(userId)s, %(activity)s, %(path)s, %(queryDict)s,"
                            " %(querySolr)s, %(searchKey)s, %(status)s, %(responseSize)s, %(timeStamp)s)"
                        )
                        cursor.execute(sql, payload)
        conn.commit()



#Entry point to the program.  Use the command line
#argument as the base directory in which to look
#for log files.
if __name__ == "__main__":
    baseDir = sys.argv[1]
    baseDir = os.path.abspath(baseDir)
    process(baseDir)
    print 'done'


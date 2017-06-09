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


#Get the event logs from the database, sorted in
#hostId and timeStamp order.  Assign each event
#a session ID based upon how close in time it is
#to the previous event.
def populateSessions():
    sql = '''
    SELECT id, hostId, timeStamp, sessionId
     FROM dataone.logData
     WHERE activity = 'search' AND status = '200'
     ORDER BY hostId ASC, timeStamp ASC;
    '''

    with dbConn() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        session = -1
        hostId = -1
        timeStamp = -1
        for row in results:
            if (hostId != row[1]):
                session += 1
            elif (timeStamp + datetime.timedelta(minutes=15) <= row[2]):
                session += 1
            sql = "UPDATE dataone.logData SET sessionId = %s WHERE id = %s"
            eventId = row[0]
            updateCursor = conn.cursor()
            updateCursor.execute(sql % (session, eventId))
            conn.commit()
            hostId = row[1]
            timeStamp = row[2]



#Get the CSV download logs from baseDir and
#parse them into dicts, then insert them into
#the database
def processDownloadLogs(baseDir):
    sql = (
        "INSERT INTO dataone.downloadLog"
        " (eventId, pid, ipAddress, event, dateLogged, nodeId, formatId,"
        " formatType, country, region, city, inPartialRobotList, inFullRobotList)"
        " VALUES (%(eventId)s, %(pid)s, %(ipAddress)s, %(event)s, %(dateLogged)s, %(nodeId)s, %(formatId)s,"
        " %(formatType)s, %(country)s, %(region)s, %(city)s, %(inPartialRobotList)s, %(inFullRobotList)s)"
    )

    with dbConn() as conn:
        cursor = conn.cursor()
        count = 0
        for root, subFolders, files in os.walk(baseDir):
            for file in files:
                with open(os.path.join(root, file), 'r') as logFile:
                    logDict = csv.DictReader(logFile)
                    for record in logDict:
                        payload = {
                            'eventId': record.get('id', ''),
                            'pid': record.get('pid', ''),
                            'ipAddress': record.get('ipAddress', ''),
                            'event': record.get('event', ''),
                            'dateLogged': dateutil.parser.parse(record['dateLogged']),
                            'nodeId': record.get('nodeId', ''),
                            'formatId': record.get('formatId', ''),
                            'formatType': record.get('formatType', ''),
                            'country': record.get('country', ''),
                            'region': record.get('region', ''),
                            'city': record.get('city', ''),
                            'inPartialRobotList': record.get('inPartialRobotList', ''),
                            'inFullRobotList': record.get('inFullRobotList', '')
                        }
                        cursor.execute(sql, payload)
                        count += 1
            conn.commit()
            print count



#Entry point to the program.  Use the command line
#argument as the base directory in which to look
#for log files.
if __name__ == "__main__":
    baseDir = sys.argv[1]
    baseDir = os.path.abspath(baseDir)
    process(baseDir)
    populateSessions()
    print 'done'


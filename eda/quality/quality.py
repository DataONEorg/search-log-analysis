
from xml.etree import ElementTree as ET
import csv
import MySQLdb
import os
import requests
import urllib

class dbConn(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host="localhost",
            user="dataoneuser",
            passwd="aA7tjWxwqTqJFXTSe5d5",
            db="dataone",
            use_unicode=True,
            charset="utf8")
    def __enter__(self):
        return self.conn
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()


def getDataPids(metadataPid):
    dataPids = []
    baseUrl = "http://cn.dataone.org/cn/v2/query/solr/?q=id:%22"
    endUrl = "%22&fl=documents"
    pid = urllib.quote(metadataPid)

    fullUrl = baseUrl + pid + endUrl

    root = ET.parse(urllib.urlopen(fullUrl)).getroot()

    for doc in root.findall('result/doc/arr[@name="documents"]'):
        for pid in doc.findall('str'):
            dataPids.append(pid.text)
    
    return dataPids


def getPidLists():
    with open('/workspace/search-log-analysis/eda/quality/sample10k.csv', 'rb') as f:
        r = csv.reader(f)
        downloadedPids = list(r)

    metadataOnlyPids = []
    metadataDataPids = []
    i = 0
    for row in downloadedPids:
        print (i)
        i = i + 1
        downloadedPid = row[1]
        dataPids = getDataPids(downloadedPid)
        if len(dataPids) == 0:
            metadataOnlyPids.append(downloadedPid)
        else:
            for dataPid in dataPids:
                metadataDataPids.append([downloadedPid, dataPid])

    with open('/workspace/search-log-analysis/eda/quality/metadataDataPids10k.csv', 'wb') as csvfile:
        w = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        w.writerows(metadataDataPids)
    with open('/workspace/search-log-analysis/eda/quality/metadataOnlyPids10k.csv', 'wb') as csvfile:
        w = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        w.writerows(metadataOnlyPids)
    print ('done getting pids')



def getMetadata():
    with open('/workspace/search-log-analysis/eda/quality/sample10k.csv', 'rb') as f:
        r = csv.reader(f)
        dlTable = list(r)
    
    done = []
    baseUrl = "http://cn.dataone.org/cn/v2/object/"
    path = '/workspace/search-log-analysis/eda/quality/metadata/'

    for item in dlTable:
        pid = urllib.quote(item[1])
        print (pid)
        if pid not in done:
            done.append(pid)
            fullUrl = baseUrl + pid
            pid = pid.replace('/', '%2F')
            u = urllib.URLopener()
            try:
                u.retrieve(fullUrl, path + pid)
            except Exception as e:
                print (e.message)
                continue

    print ('done getting metadata')



def getScores():
    path = '/workspace/search-log-analysis/eda/quality/metadata/'
    baseUrl = "https://quality.nceas.ucsb.edu/quality/suites/ACDD_Discovery_ACDD_ISO/run"
    results = []
    files = []
    for filename in os.listdir(path):
        files.append(filename)
    random.shuffle(files)

    for filename in files:
        with open(path + filename, 'rb') as f:
            r = requests.post(baseUrl, files={'document': f})
            #print (r.text)
            s = r.text.count('"status":"SUCCESS"')
            f = r.text.count('"status":"FAILURE"')
            e = r.text.count('"status":"ERROR"')
            results.append([filename, s, f, e])

    with open('/workspace/search-log-analysis/eda/quality/scores10k.csv', 'wb') as csvfile:
        w = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        w.writerows(results)
    print('done getting scores')


getMetadata()
getScores()
getPidLists()


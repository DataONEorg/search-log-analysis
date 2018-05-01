'''
Echo DataONE aggregated logs to disk

Requires python 3

This script reads records from the aggregated logs solr index and writes
each record to a log file on disk, one record per line. Each line is formatted as:

  JSON_DATA

where:

  JSON_DATA = JSON representation of the record as retrieved from solr

Output log files are rotated based on size, with rotation scheduled at 1GB. A
maximum of 150 log files are kept, so the log directory should not exceed
about 150GB.

JSON loading benchmarks: http://artem.krylysov.com/blog/2015/09/29/benchmark-python-json-libraries/
Note performance difference under python3 are much reduced.

One particular challenge is that the dateLogged time in the log records
has precision only to the second. This makes restarting the harvest
challenging since there may be multiple records on the same second.

The strategy employed here is to retrieve the last set of n records (100 or so)
and ignore any retrieved records that are present in the last set.

Each log record is on the order of 500-600 bytes, assume 1000bytes / record. The
last 100 or so records would be the last 100k bytes of the log record.

'''

import os
import argparse
import logging
import logging.handlers
import urllib
import requests
import datetime
import json
import re
import time


DEFAULT_LOG = "d1logagg.log"
BASEURL = "http://localhost:8983/solr"
LOG_NAME = "logagg"
APP_LOG = "app"
PAGE_SIZE = 10000 #Number of records to reetrieve per request
DEFAULT_CORE = "event_core" #name of the solr core to query
MAX_LOGFILE_SIZE = 1073741824 #1GB
MAX_LOG_BACKUPS = 250 #max of about 200GB of log files stored
#LOGMATCH_PATTERN = '^(\d*\-\d*\-\d*T\d*\:\d*\:\d*([0-9\.])*Z) logagg INFO: {'  #used to match lines to a log entry
LOGMATCH_PATTERN = '^{'
LOG_DATE_FIELD = "dateLogged" #Name of field in record used as log entry time stamp


#========================
#==== Client implementing an iterator for paging over Solr results

SOLR_RESERVED_CHAR_LIST = [
  '+', '-', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*',
  '?', ':'
]


def escapeSolrQueryTerm(term):
  term = term.replace('\\', '\\\\')
  for c in SOLR_RESERVED_CHAR_LIST:
    term = term.replace(c, '\{}'.format(c))
  return term


class SolrSearchResponseIterator(object):
  """Performs a search against a Solr index and acts as an iterator to retrieve
  all the values."""

  def __init__(self, select_url, q, fq=None, fields='*', page_size=PAGE_SIZE, max_records=None, sort=None, **query_args):
    self.logger = logging.getLogger(APP_LOG)
    self.client = requests.Session()
    self.select_utl = select_url
    self.q = q
    self.fq = fq
    self.fields = fields
    self.query_args = query_args
    if max_records is None:
      max_records = 9999999999
    self.max_records = max_records
    self.sort = sort
    self.c_record = 0
    self.page_size = page_size
    self.res = None
    self.done = False
    self._next_page(self.c_record)
    self._num_hits = 0
    if self.res['response']['numFound'] > 1000:
      self.logger.warning("Retrieving %d records...", self.res['response']['numFound'])


  def _next_page(self, offset):
    """Retrieves the next set of results from the service."""
    self.logger.debug("Iterator c_record=%d", self.c_record)
    start_time = time.time()
    page_size = self.page_size
    if (offset + page_size) > self.max_records:
      page_size = self.max_records - offset
    query_dict = {
      'q': self.q,
      'start': str(offset),
      'rows': str(page_size),
      'fl': self.fields,
      'wt': 'json',
    }
    if self.fq is not None:
      query_dict['fq'] = self.fq
    if self.sort is not None:
      query_dict['sort'] = self.sort
    params = urllib.parse.urlencode(query_dict) #, quote_via=urllib.parse.quote)
    self.logger.debug("request params = %s", str(params))
    response = self.client.get(self.select_utl, params=params)
    self.res = json.loads(response.text)
    self._num_hits = int(self.res['response']['numFound'])
    end_time = time.time()
    self.logger.debug("Page loaded in %.4f seconds.", end_time - start_time)

  def __iter__(self):
    return self


  def process_row(self, row):
    """Override this method in derived classes to reformat the row response."""
    return row


  def __next__(self):
    if self.done:
      raise StopIteration()
    if self.c_record > self.max_records:
      self.done = True
      raise StopIteration()
    idx = self.c_record - self.res['response']['start']
    try:
      row = self.res['response']['docs'][idx]
    except IndexError:
      self._next_page(self.c_record)
      idx = self.c_record - self.res['response']['start']
      try:
        row = self.res['response']['docs'][idx]
      except IndexError:
        self.done = True
        raise StopIteration()
    self.c_record = self.c_record + 1
    return row

# =============================
# === Logging setup
# One logger is used for reporting on actions of this application, the
# other is used to write the records retrieved from solr to disk.
# Using the file rotation feature to keep on disk files to a reasonable size

class LogFormatter(logging.Formatter):
  converter = datetime.datetime.fromtimestamp
  def formatTime(self, record, datefmt=None):
    ct = self.converter(record.created)
    if datefmt is not None:
      s = ct.strftime(datefmt)
    else:
      t = ct.strftime("%Y-%m-%d %H:%M:%S")
      s = "%s,%03d" % (t, record.msecs)
    return s


def setupLogger(level=logging.WARN):
  '''
  Logger used for application logging

  :param level:
  :return:
  '''
  logger = logging.getLogger()
  for handler in logger.handlers:
    logger.removeHandler(handler)
  logger.setLevel(logging.DEBUG)
  formatter = LogFormatter(fmt='%(asctime)s %(name)s %(levelname)s: %(message)s',
                           datefmt='%Y%m%dT%H%M%S.%f%z')
  logger = logging.getLogger(APP_LOG)
  l2 = logging.StreamHandler()
  l2.setFormatter(formatter)
  l2.setLevel(level)
  logger.addHandler(l2)


# ===

class OutputLogFormatter(logging.Formatter):
  converter = datetime.datetime.fromtimestamp
  def formatTime(self, record, datefmt=None):
    try:
      data = json.loads(record.message)
      return data[LOG_DATE_FIELD]
    except KeyError:
      #no dateAggregated value
      pass
    except ValueError:
      #invalid json
      pass
    ct = self.converter(record.created)
    if datefmt is not None:
      s = ct.strftime(datefmt)
    else:
      t = ct.strftime("%Y-%m-%dT%H:%M:%S")
      s = "%s,%03d" % (t, record.msecs)
    return s


def getOutputLogger(log_file, log_level=logging.INFO):
  '''
  Logger used for emitting the solr records as JSON blobs, one record per line.

  Only really using logger for this to take advantage of the file rotation capability.

  :param log_file:
  :param log_level:
  :return:
  '''
  logger = logging.Logger(name=LOG_NAME)
  #Just emit the JSON
  formatter = logging.Formatter('%(message)s')
  #formatter = OutputLogFormatter(fmt='%(asctime)s %(name)s %(levelname)s: %(message)s',
  #                               datefmt='%Y-%m-%dT%H%M%S.%f%z')
  l1 = logging.handlers.RotatingFileHandler(filename=log_file,
                                            mode='a',
                                            maxBytes=MAX_LOGFILE_SIZE,
                                            backupCount=MAX_LOG_BACKUPS
                                            )
  l1.setFormatter(formatter)
  l1.setLevel(log_level)
  logger.addHandler(l1)
  return logger

# ===

def getLastLinesFromFile(fname, seek_back=100000, pattern=LOGMATCH_PATTERN, lines_to_return=100):
  '''
  Returns the last lines matching pattern from the file fname

  Args:
    fname: name of file to examine
    seek_back: number of bytes to look backwards in file
    pattern: Pattern lines must match to be returned
    lines_to_return: maximum number of lines to return

  Returns:
    last n log entries that match pattern
  '''
  L = logging.getLogger(APP_LOG)
  #Does file exist?
  if not os.path.exists(fname):
    L.warning("Log file not found. Starting from zero.")
    return []
  #Do we have any interesting content in the file?
  fsize = os.stat(fname).st_size
  if fsize < 100:
    L.warning("No records in log. Starting from zero.")
    return []
  #Reduce the seek backwards if necessary
  if fsize < seek_back:
    seek_back = fsize-1
  #Get the last chunk of bytes from the file as individual lines
  with open(fname, "rb") as f:
    f.seek(-seek_back, os.SEEK_END)
    lines = f.readlines()
  #Find lines that match the pattern
  i = len(lines)-1
  if i > lines_to_return:
    i = lines_to_return
  results = []
  while i >= 0:
    line = lines[i].decode().strip()
    if re.match(pattern, line) is not None:
      results.insert(0, line)
    i = i-1
  return results


def trimLogEntries(records, field):
  '''
  Shrink the list so only entries that match the last record are returned
  Args:
    records: records to test
    field: field to evaluate

  Returns: records that match the field of the last record

  '''
  L = logging.getLogger(APP_LOG)
  L.debug("Trimming from %d entries.", len(records))
  result = []
  if len(records) == 0:
    return result
  #data = json.loads(records[len(records)-1].split("INFO: ")[1])
  data = json.loads(records[len(records) - 1])
  last_record = data
  result = [data, ]
  i = len(records)-2
  while i >= 0:
    #data_str = records[i].split("INFO: ")[1]
    try:
      data = json.loads(records[i])
      if data[field] == last_record[field]:
        result.insert(0, data)
    except ValueError:
      L.debug("Bad json: %s", records[i])
      pass
    i = i-1
  return result


def logRecordInList(record_list, record):
  '''
  Returns True if record is in record_list
  Args:
    record_list:
    record:

  Returns:
    Boolean
  '''
  for rec in record_list:
    if rec['id'] == record['id']:
      return True
  return False


def getQuery(src_file=DEFAULT_LOG, tstamp=None):
  '''
  Returns a query that would retrieve the last entry in the log file

  Args:
    src_file: name of the log file to examine
    tstamp: timestamp of last point for query. Defaults to the value of utcnow if not set

  Returns:
    A solr query string that returns at least the last record from the index and
    the record data that was retrieved from the log
  '''
  L = logging.getLogger(APP_LOG)
  fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
  if tstamp is None:
    tstamp = datetime.datetime.utcnow()
  date_to = tstamp.strftime(fmt)
  date_from = datetime.datetime(year=2012, month=7, day=1, hour=0, minute=0, second=0)
  log_entries = getLastLinesFromFile(src_file)
  # trim the entries, note that only the log data is returned in the list
  log_entries = trimLogEntries(log_entries, LOG_DATE_FIELD)
  if len(log_entries) > 0:
    record = log_entries[-1]
    dstring = record[LOG_DATE_FIELD]
    try:
      date_from = datetime.datetime.strptime(dstring, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
      date_from = datetime.datetime.strptime(dstring, "%Y-%m-%dT%H:%M:%SZ")
  date_str = date_from.strftime(fmt)
  L.warning("Start date = %s", date_str)
  query = "{}:[{} TO {}]".format(LOG_DATE_FIELD, date_str, date_to)
  return query, log_entries


def getRecords(log_file_name, core_name, base_url=BASEURL, test_only=False):
  '''
  Main method. Retrieve records from solr and save them to disk.

  Args:
    log_file_name: Name of the destination log file
    core_name: Name of the solr core to query
    base_url: Base URL of the solr service

  Returns:
    Nothing
  '''
  log_file_name = os.path.abspath(log_file_name)
  L = logging.getLogger(APP_LOG)
  logger = getOutputLogger(log_file_name)
  query_str, last_records = getQuery(src_file=log_file_name)
  rid = ''
  if len(last_records) > 0:
    rid = last_records[-1]['id']
  url = "{}/{}/select".format(base_url, core_name)
  loader = SolrSearchResponseIterator(url, "*:*", fq=query_str, sort='{} ASC'.format(LOG_DATE_FIELD))
  if test_only:
    for row in last_records:
      L.info(str(row))
    return
  counter = 0
  num_last_records = len(last_records)
  for record in loader:
    if counter < num_last_records:
      if logRecordInList(last_records, record):
        L.info("Ignoring record: %s", str(record))
      else:
        logger.info(json.dumps(record))
    else:
      logger.info(json.dumps(record))
    counter += 1
  return


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-l', '--log_level',
                      action='count',
                      default=0,
                      help='Set logging level, multiples for more detailed.')
  parser.add_argument('-f', '--log_dest',
                      default=DEFAULT_LOG,
                      help="Log destination")
  parser.add_argument('-c','--core_name',
                      default=DEFAULT_CORE,
                      help="Name of solr core to query")
  parser.add_argument('-B','--base_url',
                      default=BASEURL,
                      help="Base URL of solr service")
  parser.add_argument('-t','--test',
                      default=False,
                      action='store_true',
                      help="Show the starting point and number of records to retrieve but don't download.")

  args = parser.parse_args()
  # Setup logging verbosity
  levels = [logging.WARNING, logging.INFO, logging.DEBUG]
  level = levels[min(len(levels) - 1, args.log_level)]
  setupLogger(level=level)
  getRecords(args.log_dest, args.core_name, args.base_url, test_only=args.test)

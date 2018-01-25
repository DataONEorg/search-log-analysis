#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticsearch5 import Elasticsearch

import argparse
import json
import sys

ES = Elasticsearch()

def get_session_info(indexname, sessionid, qtype):
  # set up the basic query -- this default configuration
  # returns the chronological first event in the session
  searchbody = {
    "from": 0, "size": 1,
    "query": {
      "bool": {
        "must": [
          {
            "term": {"_type": "logevent"}
          },
          {
            "exists": {
              "field": "sessionid"
            }
          },
          {
            "term": {"sessionid": sessionid}
          }
        ],
        "should": [ {
            "term": {"beat.name": "search"}
          },
          {
            "term": {"beat.name": "eventlog"}
          }
        ],
      }
    },
    "sort": [ 
      {
        "@timestamp": {
          "order": "asc",
          "unmapped_type": "date"
        }
      }
    ]
  }

  # if querytype is 'end', we want the chronological last event
  # so reverse the sort order to descending over timestamp
  if qtype == 'end':
    searchbody["sort"][0]["@timestamp"]["order"] = "desc"

  events = ES.search(index=indexname, body=searchbody)

  result = None
  
  if not events["hits"]["hits"]:
    return None

  # grab start or end time
  if qtype == 'start' or qtype == 'end':
    result = events["hits"]["hits"][0]["_source"]["@timestamp"]
  
  # grab the geoip info
  if qtype == 'geoip':
    result = events["hits"]["hits"][0]["_source"]["geoip"]

  return result


def parse_args(args):
  helpdescription = """
  This program provides session information for DataONE sessions
  stored in elasticsearch. 
  """

  parser = argparse.ArgumentParser(description=helpdescription)
  parser.add_argument('--indexname', action='store', required=True,
                      help='name of the elasticsearch index to be queried')
  parser.add_argument('--sessionid', action='store', required=True,
                      help='id of the session to be queried')
  
  return parser.parse_args()


if __name__ == "__main__":
  args = parse_args(sys.argv)

  indexname = args.indexname
  sessionid = args.sessionid

  ES.indices.refresh(indexname)
  
  session_start = get_session_info(indexname, sessionid, 'start')
  session_end = get_session_info(indexname, sessionid, 'end')
  session_geoip = get_session_info(indexname, sessionid, 'geoip')
  
  session_info = {
    "sessionid": sessionid,
    "start": session_start,
    "end": session_end,
    "geoip": session_geoip
  }
  print json.dumps(session_info, indent=2)
  exit(0)

  




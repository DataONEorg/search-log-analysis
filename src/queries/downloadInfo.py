#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticsearch5 import Elasticsearch
from elasticsearch5 import helpers

import argparse
import json
import sys

ES = Elasticsearch()


def get_download_info(indexname, sessionid=None):
  # set up the query. we're using the scan helper here,
  # so for performance reasons, we don't bother sorting --
  # it would require setting preserve_order on the scan,
  # and the docs describe that as 'extremely expensive'
  searchbody = {
    "query": {
      "bool": {
        "must": [
          {
            "term": {"_type": "logevent"}
          },
          {
            "term": { "beat.name": "eventlog" }
          },
          {
            "term": { "formatType": "data" }
          },
          {
            "term": { "event": "read" }
          },
          {
            "exists": { "field": "sessionid" }
          }
        ]
      }
    }
  }

  # add a sessionid section to the 'must' if requested
  if sessionid is not None:
    sessionid_search = {"term": {"sessionid": sessionid}}
    searchbody["query"]["bool"]["must"].append(sessionid_search)

  results = helpers.scan(ES, query=searchbody)

  download_info = []
  event_count = 0

  for event in results:
    event_count += 1
    download = {}
    download["timestamp"] = event["_source"]["@timestamp"]
    download["nodeId"] = event["_source"]["nodeId"]
    download["pid"] = event["_source"]["pid"]
    download["sessionid"] = event["_source"]["sessionid"]
    download["ip"] = event["_source"]["geoip"].get("ip") or None
    download["eventid"] = event["_id"]
    download["count"] = event_count
    download_info.append(download)

  return download_info


def parse_args(args):
  helpdescription = """
  This program provides download information for DataONE sessions
  stored in elasticsearch. 
  """

  parser = argparse.ArgumentParser(description=helpdescription)
  parser.add_argument('--indexname', action='store', required=True,
                      help='name of the elasticsearch index to be queried')
  parser.add_argument('--sessionid', action='store', required=False,
                      help='id of the session to be queried')
  
  return parser.parse_args()


if __name__ == "__main__":
  args = parse_args(sys.argv)

  indexname = args.indexname
  sessionid = args.sessionid

  ES.indices.refresh(indexname)
  
  download_info = get_download_info(indexname, sessionid)
  
  print json.dumps(download_info, indent=2)
  exit(0)

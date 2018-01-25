#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticsearch5 import Elasticsearch
from elasticsearch5 import helpers

#import apache_log_parser
import argparse
import json
import sys

ES = Elasticsearch()


def get_search_info(indexname, sessionid=None):
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
            "term": { "beat.name": "search" }
          },
          {
            "exists": { "field": "sessionid" }
          },
          {
            "query_string": {
              "default_field": "message",
              "query": "\/cn\/v2\/query\/solr\/"
            }
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

  search_info = []
  event_count = 0

  for event in results:
    event_count += 1
    search = {}
    search["timestamp"] = event["_source"]["@timestamp"]
    search["message"] = event["_source"]["message"]
    search["response"] = event["_source"]["response"]
    search["sessionid"] = event["_source"]["sessionid"]
    search["ip"] = event["_source"]["geoip"].get("ip") or None
    search["eventid"] = event["_id"]
    search["count"] = event_count
    search_info.append(search)

  return search_info


def parse_args(args):
  helpdescription = """
  This program provides search information for DataONE sessions
  stored in elasticsearch. 
  """

  parser = argparse.ArgumentParser(description=helpdescription)
  parser.add_argument('--indexname', action='store', required=True,
                      help='name of the elasticsearch index to be queried')
  parser.add_argument('--sessionid', action='store', required=False,
                      help='id of the session to be queried')
  
  return parser.parse_args()


def process_message_field(download_info):
  return download_info


if __name__ == "__main__":
  args = parse_args(sys.argv)

  indexname = args.indexname
  sessionid = args.sessionid

  ES.indices.refresh(indexname)
  
  download_info = get_search_info(indexname, sessionid)
  
  download_info = process_message_field(download_info)

  print json.dumps(download_info, indent=2)
  exit(0)

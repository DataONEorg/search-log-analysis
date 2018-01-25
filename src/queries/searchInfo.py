#!/usr/bin/env python
# -*- coding: utf-8 -*-

from elasticsearch5 import Elasticsearch
from elasticsearch5 import helpers
from luqum.parser import parser
from luqum.parser import ParseError

import apache_log_parser
import argparse
import json
import luqum
import re
import shlex
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


def process_query(download_info):
  lineParser = apache_log_parser.make_parser("%h %l %u %t \"%r\" %>s %b")
  
  for event in download_info:
    # first, parse the apache message into a dict
    apache_line = lineParser(event["message"])
    
    # these datetime objects interfere with serialization and are redundant
    del apache_line["time_received_datetimeobj"]
    del apache_line["time_received_tz_datetimeobj"]
    del apache_line["time_received_utc_datetimeobj"]
    #print json.dumps(apache_line, indent=2)

    solr_query_dict = {}

    q = apache_line["request_url_query_dict"].get("q", None)
    if q:
      solr_query_dict["querywords"] = []
      solr_query_dict["unhandled"] = []
      
      # copy the items from the parsed querystring
      for item in apache_line["request_url_query_dict"]:
        solr_query_dict[item] = apache_line["request_url_query_dict"][item]

      # parse the solr query 
      solr_query = q[0].strip()
      try:
        tree = parser.parse(solr_query)
      except ParseError as e:
        # alert for unparseable queries?
        continue
      
      # the solr query tree can be complex.
      # rather than parse the whole tree, we try to get
      # the parts we're most interested in.
      # most basic kvps are SearchFields
      # Words and Phrases are bare strings, usually search terms
      # Prohibits are often the -obsoletedBy:*
      for child in tree.children:
        if child.__class__ is luqum.tree.SearchField:
          solr_query_dict[child.name] = str(child.expr).replace('"', '')
        
        elif child.__class__ is luqum.tree.Word:
          solr_query_dict["querywords"].append(child.value.replace('"', ''))
        
        elif child.__class__ is luqum.tree.Phrase:
          solr_query_dict["querywords"].append(child.value.replace('"', ''))
        
        elif child.__class__ is luqum.tree.Prohibit:
          op = child.op
          child = child.children[0]
          if child.__class__ is luqum.tree.SearchField:
            solr_query_dict[op+child.name] = str(child.expr).replace('"', '')
        
        else:
          # alert for unhandled cases?
          solr_query_dict["unhandled"].append(repr(child))
          #print 'unhandled case: ', child.__class__
          #print 'child', child
      #print json.dumps(solr_query_dict, indent=2)

    event["solr_query"] = solr_query_dict

  return download_info


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


if __name__ == "__main__":
  args = parse_args(sys.argv)

  indexname = args.indexname
  sessionid = args.sessionid

  ES.indices.refresh(indexname)
  
  download_info = get_search_info(indexname, sessionid)

  download_info = process_query(download_info)

  print json.dumps(download_info, indent=2)
  exit(0)

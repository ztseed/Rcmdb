#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sys
import json
import requests
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from requests_kerberos import HTTPKerberosAuth, REQUIRED
import urllib3

urllib3.disable_warnings()

# This is Class using to query cmdb from nnitcmdb

class Rcmdb:

    def __init__(self,urls,payloads):
        self.url = urls
        self.payload = payloads
        self.cis_dics = {}


    def setParams(self,p_action,p_parameters):
        self.payload['action'] = p_action
        self.payload['parameters'] = p_parameters

    def getParams(self):
        print(self.payload)

    def getCmdbReport(self):
        r_josn = requests.get(self.url, auth=HTTPKerberosAuth(),params=self.payload,verify=False)
        cis_dic_object=r_josn.content.decode("utf-8")
        cis_dic = json.loads(cis_dic_object)
        self.cis_dics = cis_dic
        return cis_dic

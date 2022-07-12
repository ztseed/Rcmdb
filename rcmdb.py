#!/usr/bin/env python3


import sys
import json
import getopt
import os
import argparse
import subprocess
import re
import requests
import datetime
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth, REQUIRED
from requests.auth import HTTPDigestAuth
import urllib3
import Get_Report_Cmdb
from multiprocessing import Pool
import threading

def query_55_output(items):
    CI_DICS = []
    for server_item in items:
        CI_DIC = {}
        for server_info1 in server_item['properties']:


            for key,value in server_info1.items():
                if key != "type":
                    title = (key).replace('custom_','').replace('operation_parameter_','')
                    CI_DIC[title] = (value if value else "N/A").replace('\r','')
                    
            

        for server_info2 in server_item['related']:
            
            title2 = server_info2['cit'].replace('custom_','')
            value2 = server_info2['properties'][0]['name']
            if title2 != 'service_level_objective':
                
                CI_DIC[title2] = (value2 if value2 else "N/A").replace('\r','')

        CI_DICS.append(CI_DIC)

    return(CI_DICS)

def query_60_output(items):
    CI_DICS = []
    for server_item in items:
        CI_DIC = {}
        for server_info1 in server_item['properties']:
            for key,value in server_info1.items():
                if key != "type":
                    title = (key).replace('custom_','').replace('operation_parameter_','')
                    CI_DIC[title] = (value if value else "N/A").replace('\r','')
        CI_DICS.append(CI_DIC)

    return(CI_DICS)

def query_59_output(items):
    CI_DICS = []
    for server_item in items:
        CI_DIC = {}
        soft = {}
        for server_info1 in server_item['properties']:


            for key,value in server_info1.items():
                if key != "type":
                    title = (key).replace('custom_','').replace('operation_parameter_','')
                    CI_DIC[title] = (value if value else "N/A").replace('\r','')
                    
            

        for server_info2 in server_item['related']:
            sname = server_info2['properties'][0]['display_label']
            sver = server_info2['properties'][2]['version']
            soft[sname] = sver

        CI_DIC['running_software'] = soft      

        CI_DICS.append(CI_DIC)

    return(CI_DICS)



def query_55_59_60_output(items1,items2,items3):

    new_item = []
    main_item = query_55_output(items1)
    local_item = query_60_output(items2)
    soft_item = query_59_output(items3)
    for server1 in main_item:
        for server2 in local_item:
            if server1['name'] == server2['name']:
                server1['calculated_location'] = server2['calculated_location']
        for server3 in soft_item:
            if server1['name'] == server3['name']:
                server1['running_software'] = server3['running_software']
        new_item.append(server1)
             
    return new_item




if __name__=='__main__':

    urllib3.disable_warnings()

    parser = argparse.ArgumentParser()
    parser.add_argument('server_name', type=str, nargs='+', help='Server to query')
    args = parser.parse_args()

    fields = []


    server_name = args.server_name[0]

    query_info_act = "queryid=55|Status=Active|Name=%{0}%".format(server_name)
    query_info_local = "queryid=60|Status=Active|Name=%{0}%".format(server_name)
    query_info_ret = "queryid=55|Status=Retired|Name=%{0}%".format(server_name)
    query_info_sof = "queryid=59|Status=Active|Name=%{0}%".format(server_name)
    
    url = "https://nnitcmdb.nnitcorp.com/services/webapi/executeget"

    payload_act = {'action':'getqueryresults', 'parameters':query_info_act}
    payload_local = {'action':'getqueryresults', 'parameters':query_info_local}
    payload_ret = {'action':'getqueryresults', 'parameters':query_info_ret}
    payload_sof = {'action':'getqueryresults', 'parameters':query_info_sof}
    

    nnitcmdb_act = Get_Report_Cmdb.Rcmdb(url,payload_act)
    nnitcmdb_local = Get_Report_Cmdb.Rcmdb(url,payload_local)
    nnitcmdb_ret = Get_Report_Cmdb.Rcmdb(url,payload_ret)
    nnitcmdb_sof = Get_Report_Cmdb.Rcmdb(url,payload_sof)

    item_act = nnitcmdb_act.getCmdbReport()
    item_local = nnitcmdb_local.getCmdbReport()
    item_ret = nnitcmdb_ret.getCmdbReport()
    item_sof = nnitcmdb_sof.getCmdbReport()

    items_server_act = item_act['cis']
    items_server_local = item_local['cis']
    items_server_ret = item_ret['cis']
    items_server_sof = item_sof['cis']

    ret = query_55_output(items_server_ret)
    tol = query_55_59_60_output(items_server_act,items_server_local,items_server_sof)


    for it_server in tol:
        print("\n============= {0} ==============\n".format(it_server['name']))
        for key,value in it_server.items():
            key_i = key.ljust(30,' ')
            if key == "running_software":
                print("{0}:\n".format(key_i))
                for skey,svalue in value.items():
                    print("  {0}:  {1}".format(skey.ljust(20,' '),svalue))
            else:
                print("{0}:{1}".format(key_i,value))
            


    for it_server in ret:
        print("\n------------- {0} ----------------\n".format(it_server['name']))
        for key,value in it_server.items():
            key_i = key.ljust(30,' ')
            print("{0}:{1}".format(key_i,value))

    print("\n-------------")    
    print("Active server : {}".format(item_act['message']))
    print("Retired server : {}".format(item_ret['message']))




#!/usr/local/bin/python3

import sys
import json
import getopt
import os
import argparse
import subprocess
import re
import requests
import datetime
from requests_kerberos import HTTPKerberosAuth, REQUIRED
import urllib3
import Get_Report_Cmdb
import rcmdb
import pymssql
import time

from subprocess import Popen, PIPE

def createKerberostgt(kuser,kpasswd,realm):
    password=str.encode(kpasswd+"\n")
    kinit = '/usr/bin/kinit'
    kinit_args = [ kinit, '%s@%s' % (kuser,realm) ]
    kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    kinit.stdin.write(password)
    kinit.communicate()

def destoryKerberostgt():
    kdestroy = '/usr/bin/kdestroy'
    kinit_args = [kdestroy]
    kdes = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    kdes.communicate()

if __name__=='__main__':

    fields = []

    Time_now = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime())
    print("==================================={}========================================\n".format(Time_now))
        
    query_info_act = "queryid=55|Status=Active|Name=%"
    query_info_local = "queryid=60|Status=Active|Name=%"
    #query_info_ret = "queryid=55|Status=Retired|Name=%"
    query_info_sof = "queryid=59|Status=Active|Name=%"
    
    url = "https://nnitcmdb.nnitcorp.com/services/webapi/executeget"

    print("Creating Kerberos TGT......\n")
    createKerberostgt("tzg","Coltm1873!","NNITCORP.COM")
    print("Creating Kerberos TGT done.\n")

    payload_act = {'action':'getqueryresults', 'parameters':query_info_act}
    payload_local = {'action':'getqueryresults', 'parameters':query_info_local}
    #payload_ret = {'action':'getqueryresults', 'parameters':query_info_ret}
    payload_sof = {'action':'getqueryresults', 'parameters':query_info_sof}
    
    print("Export data from NNITCMDB.....\n")

    nnitcmdb_act = Get_Report_Cmdb.Rcmdb(url,payload_act)
    nnitcmdb_local = Get_Report_Cmdb.Rcmdb(url,payload_local)
    #nnitcmdb_ret = Get_Report_Cmdb.Rcmdb(url,payload_ret)
    nnitcmdb_sof = Get_Report_Cmdb.Rcmdb(url,payload_sof)
    
   
    item_act = nnitcmdb_act.getCmdbReport()
    item_local = nnitcmdb_local.getCmdbReport()
    #item_ret = nnitcmdb_ret.getCmdbReport()
    item_sof = nnitcmdb_sof.getCmdbReport()

    items_server_act = item_act['cis']
    items_server_local = item_local['cis']
    #items_server_ret = item_ret['cis']
    items_server_sof = item_sof['cis']

    #ret = rcmdb.query_55_output(items_server_ret)
    tol = rcmdb.query_55_59_60_output(items_server_act,items_server_local,items_server_sof)

    print("Export data from NNITCMDB.....done!\n")

    print("Starting import data from nnitcmdb......\n")

    db = pymssql.connect(host="heping",user="sa",password="Zt810112zt!",database="nnitcmdb_mssql")
    cursor = db.cursor()
    
    print("Deleted old data.......\n")

    cursor.execute("IF (OBJECT_ID('unix_linux_act_full_old','U') IS NOT NULL) drop TABLE [unix_linux_act_full_old];")
    cursor.callproc("sp_rename",('unix_linux_act_full','unix_linux_act_full_old'))
    db.commit()
    
    print("create new table.......\n")

    sql = """CREATE TABLE unix_linux_act_full (
            id INT PRIMARY KEY identity,
            name VARCHAR(50) NOT NULL,
            discovered_os_name VARCHAR(50),
            host_osinstalltype VARCHAR(100),
            environment VARCHAR(50),
            status VARCHAR(20),
            operation_location_limited_to VARCHAR(50),
            ExternalStorage VARCHAR(10),
            os_description VARCHAR(50),
            host_osrelease VARCHAR(20),
            impact_classification VARCHAR(50),
            time_zone VARCHAR(250),
            housing_only VARCHAR(20),
            "backup" VARCHAR(10),
            time_server VARCHAR(200),
            backup_environment VARCHAR(50),
            patch_group VARCHAR(50),
            asset_owner VARCHAR(50),
            compliance_classification VARCHAR(50),
            support_contract_identifier VARCHAR(50),
            primary_dns_name VARCHAR(100),
            password_owner VARCHAR(20),
            discovered_model VARCHAR(50),
            serial_number VARCHAR(200),
            reporting VARCHAR(20),
            antivirus VARCHAR(10),
            discovered_os_version VARCHAR(50),
            last_discovery_time VARCHAR(20),
            service_level_agreement VARCHAR(10),
            assignment_group VARCHAR(50),
            business_application VARCHAR(150),
            customer VARCHAR(50),
            calculated_location VARCHAR(250),
            running_software VARCHAR(250)
           )"""
    try:
        cursor.execute(sql)
        db.commit()
    except:
        print("create table failed!")
    server_num = len(tol)

    print("Starting import data to MYSQL.....\n")

    for server in tol:
        sql2 = "INSERT INTO unix_linux_act_full ("
        sql3 = " VALUES ("
        sql1 = ""
        server["running_software"] = "N/A"
        server_col = server.keys()
        server_len = len(server)
        i = 1
        for key,value in server.items():
            
            if i == server_len:
                sql2 = sql2 + "{}) ".format(key)
                sql1 = sql1 + "'{}')".format(value)

            else:
                sql2 = sql2 + "{},".format(key)
                sql1 = sql1 + "'{}',".format(value.replace('\'',""))
                    
            i = i + 1
        sql = sql2 + sql3 + sql1

        sql = sql.replace('backup,','\"backup\",')
        #print(sql)

        try:
                cursor.execute(sql)
                db.commit()
                #print("instert data done!")
        except:
                db.rollback()
                print("Below server insert failed! ： \n")
                print(sql)
                print("Restore last table and delete new table....")
                cursor.execute("IF (OBJECT_ID('unix_linux_act_full','U') IS NOT NULL) drop TABLE [unix_linux_act_full];")
                cursor.callproc("sp_rename",('unix_linux_act_full_old','unix_linux_act_full'))
                cursor.commit()
                print("Exit process now...")
                exit()
        
    print("{} server imported successfully !\n".format(server_num))

    db.close()

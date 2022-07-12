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
import pymysql
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

def insert_data(table,data_n):

    for server in data_n:
        sql2 = "INSERT INTO {0} (".format(table)
        sql3 = " VALUES ("
        sql1 = ""
        if "running_software" in server.keys():
            server["running_software"] = "N/A"
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

        try:
                cursor.execute(sql)
                db.commit()
                #print("instert data done!")
        except:
                db.rollback()
                print("below server insert failed! ： \n")
                print(sql)
                print("Exit process now...")
                exit()   


if __name__=='__main__':

    fields = []

    Time_now = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime())
    print("==================================={}========================================\n".format(Time_now))
        
    query_info_act = "queryid=55|Status=Active|Name=%"
    query_info_local = "queryid=60|Status=Active|Name=%"
    query_info_ret = "queryid=55|Status=Retired|Name=%"
    query_info_sof = "queryid=59|Status=Active|Name=%"
    
    url = "https://nnitcmdb.nnitcorp.com/services/webapi/executeget"

    print("Creating Kerberos TGT......\n")
    createKerberostgt("tzg","Coltm1873!","NNITCORP.COM")
    print("Creating Kerberos TGT done.\n")

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

    print("Export data from NNITCMDB.....\n")

    ret = rcmdb.query_55_output(items_server_ret)
    tol = rcmdb.query_55_59_60_output(items_server_act,items_server_local,items_server_sof)

    print("Export data from NNITCMDB.....done!\n")

    print("Starting import data from nnitcmdb......\n")

    db = pymysql.connect(host="127.0.0.1",user="root",password="initial",database="nnitcmdb",charset='utf8')
    cursor = db.cursor()
    
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()
    print ("connected Database version : %s \n" % data)

    print("Deleted old data.......\n")

    cursor.execute("DROP TABLE IF EXISTS unix_linux_act_full_new")
    cursor.execute("DROP TABLE IF EXISTS unix_linux_ret_full_new")


    print("create new table.......\n")

    sql = """CREATE TABLE unix_linux_act_full_new (
            id INT(5) PRIMARY KEY AUTO_INCREMENT,
            name CHAR(50) NOT NULL,
            discovered_os_name CHAR(50),
            host_osinstalltype CHAR(100),
            environment CHAR(50),
            status CHAR(20),
            operation_location_limited_to CHAR(50),
            ExternalStorage CHAR(10),
            os_description CHAR(50),
            host_osrelease CHAR(20),
            impact_classification CHAR(50),
            time_zone CHAR(250),
            housing_only CHAR(20),
            backup CHAR(10),
            time_server CHAR(200),
            backup_environment CHAR(50),
            patch_group CHAR(50),
            asset_owner CHAR(50),
            compliance_classification CHAR(50),
            support_contract_identifier CHAR(50),
            primary_dns_name CHAR(100),
            password_owner CHAR(20),
            discovered_model CHAR(50),
            serial_number CHAR(200),
            reporting CHAR(20),
            antivirus CHAR(10),
            discovered_os_version CHAR(50),
            last_discovery_time CHAR(20),
            service_level_agreement CHAR(10),
            assignment_group CHAR(50),
            business_application CHAR(150),
            customer CHAR(50),
            calculated_location CHAR(250),
            running_software CHAR(250)
           )"""

    sql_ret = """CREATE TABLE unix_linux_ret_full_new (
            id INT(5) PRIMARY KEY AUTO_INCREMENT,
            name CHAR(50) NOT NULL,
            discovered_os_name CHAR(50),
            host_osinstalltype CHAR(100),
            environment CHAR(50),
            status CHAR(20),
            operation_location_limited_to CHAR(50),
            ExternalStorage CHAR(10),
            os_description CHAR(50),
            host_osrelease CHAR(20),
            impact_classification CHAR(50),
            time_zone CHAR(250),
            housing_only CHAR(20),
            backup CHAR(10),
            time_server CHAR(200),
            backup_environment CHAR(50),
            patch_group CHAR(50),
            asset_owner CHAR(50),
            compliance_classification CHAR(50),
            support_contract_identifier CHAR(50),
            primary_dns_name CHAR(100),
            password_owner CHAR(20),
            discovered_model CHAR(50),
            serial_number CHAR(200),
            reporting CHAR(20),
            antivirus CHAR(10),
            discovered_os_version CHAR(50),
            last_discovery_time CHAR(20),
            service_level_agreement CHAR(10),
            assignment_group CHAR(50),
            business_application CHAR(150),
            customer CHAR(50)
           )"""

    cursor.execute(sql)
    cursor.execute(sql_ret)

    server_num_act = len(tol)
    server_num_ret = len(ret)

    print("Starting import data to MYSQL.....\n")
    
    # for server in tol:
    #     sql2 = "INSERT INTO unix_linux_act_full ("
    #     sql3 = " VALUES ("
    #     sql1 = ""
    #     server["running_software"] = "N/A"
    #     server_col = server.keys()
    #     server_len = len(server)
    #     i = 1
    #     for key,value in server.items():
            
    #         if i == server_len:
    #             sql2 = sql2 + "{}) ".format(key)
    #             sql1 = sql1 + "'{}')".format(value)

    #         else:
    #             sql2 = sql2 + "{},".format(key)
    #             sql1 = sql1 + "'{}',".format(value.replace('\'',""))
                    
    #         i = i + 1
    #     sql = sql2 + sql3 + sql1

    #     try:
    #             cursor.execute(sql)
    #             db.commit()
    #             #print("instert data done!")
    #     except:
    #             db.rollback()
    #             print("below server insert failed! ： \n")
    #             print(sql)
    #             print("Exit process now...")
    #             exit()

    insert_data("unix_linux_act_full_new",tol)
    insert_data("unix_linux_ret_full_new",ret)

    cursor.execute("DROP TABLE IF EXISTS unix_linux_act_full_old")
    cursor.execute("DROP TABLE IF EXISTS unix_linux_ret_full_old")
    cursor.execute("alter table unix_linux_act_full rename to unix_linux_act_full_old")      
    cursor.execute("alter table unix_linux_ret_full rename to unix_linux_ret_full_old")
    cursor.execute("alter table unix_linux_act_full_new rename to unix_linux_act_full")      
    cursor.execute("alter table unix_linux_ret_full_new rename to unix_linux_ret_full")   
        
    print("{} active server imported successfully !\n".format(server_num_act))
    print("{} retired server imported successfully !\n".format(server_num_ret))
    db.close()

#!/usr/bin/env python3


import sys
import json
import getopt
import os
import argparse
import subprocess
import getpass
import re
import requests
import xlwt
import xlrd
import time
from xlutils.copy import copy
from requests.auth import HTTPBasicAuth
from requests_kerberos import HTTPKerberosAuth, REQUIRED
from requests.auth import HTTPDigestAuth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import urllib3
import Get_Report_Cmdb

def output_to_xls(item,status,filename):

    serverlist=[]
    serveritem={}

    for server in item :
        
            serveritem = {
                            'name':server['properties'][0]['name'],
                            'os':server['properties'][7]['os_description'],
                            'compliance':server["properties"][17]['custom_compliance_classification'],
                            'serialnumber':server["properties"][22]['serial_number'],
                            'model':server['properties'][21]['discovered_model'],
                            'custom_environment':server['properties'][3]['custom_environment'],
                            'custom_status':server['properties'][4]['custom_status']}

            for related_item in server['related']:

                    if related_item['cit'] == 'custom_customer':

                            serveritem['customer'] = related_item['properties'][0]['name']

            if server['properties'][19]['primary_dns_name']:

                    serveritem['FQDN'] = server['properties'][19]['primary_dns_name']
            else:
                    serveritem['FQDN'] = "NULL"

            serverlist.append(serveritem)

    if os.path.isfile(filename):

        workbook_tmp=xlrd.open_workbook(filename)
        workbook = copy(workbook_tmp)

    else:

        workbook = xlwt.Workbook(encoding = 'utf-8')

    worksheet = workbook.add_sheet(status)
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.bold = True
    style.font = font

    worksheet.col(0).width = 5000
    worksheet.col(1).width = 10000
    worksheet.col(2).width = 6000
    worksheet.col(3).width = 5000
    worksheet.col(4).width = 8000
    worksheet.col(5).width = 5000
    worksheet.col(6).width = 5000
    worksheet.col(7).width = 10000
    worksheet.col(8).width = 13000

    worksheet.write(0,0,'server name', style)
    worksheet.write(0,1,'FQDN', style)
    worksheet.write(0,2,'compliance', style)
    worksheet.write(0,3,'customer', style)
    worksheet.write(0,4,'serialnumber', style)
    worksheet.write(0,5,'custom_environment', style)
    worksheet.write(0,6,'custom_status', style)
    worksheet.write(0,7,'OS', style)
    worksheet.write(0,8, 'model', style)

    x=1

    for server_i in serverlist:

            if server_i:
                    
#                    print("{0},{1},{2},{3},{4},{5},{6},{7},{8}".format(server_i['name'],server_i['FQDN'],server_i['compliance'],server_i['customer'],server_i['serialnumber'],server_i['custom_environment'],server_i['custom_status'],server_i['os'],server_i['model']))
                    
                    worksheet.write(x,0, server_i['name'])
                    worksheet.write(x,1, server_i['FQDN'])
                    worksheet.write(x,2, server_i['compliance'])
                    worksheet.write(x,3, server_i['customer'])
                    worksheet.write(x,4, server_i['serialnumber'])
                    worksheet.write(x,5, server_i['custom_environment'])
                    worksheet.write(x,6, server_i['custom_status'])
                    worksheet.write(x,7, server_i['os'])
                    worksheet.write(x,8, server_i['model'])

            x = x+1



    workbook.save(filename)


def send_mail(mail_adress,attachment):

    sender = 'nnitcmdb@nnit.com'
    receivers = [mail_adress]

    message = MIMEMultipart()
    message['From'] = Header("nnitcmdb@nnit.com", 'utf-8')
    message['To'] =  Header(mail_adress, 'utf-8')
    subject = 'unix_server_list_full'
    message['Subject'] = Header(subject, 'utf-8')

    message.attach(MIMEText('{0}'.format(attachment), 'plain', 'utf-8'))

    att1 = MIMEText(open(attachment, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'

    att1["Content-Disposition"] = 'attachment; filename={0}'.format(attachment)
    message.attach(att1)
    

    try:
        smtpObj = smtplib.SMTP('mail1.csn.nnithosting.com')
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("send mail done!")
    except smtplib.SMTPException:
        print("Error: failed send mail!")



if __name__=='__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('mail_adress', type=str, nargs='+', help='your mail adress!')
    args = parser.parse_args()  

    urllib3.disable_warnings()

    url = "https://nnitcmdb.nnitcorp.com/services/webapi/executeget"

    query_info_act = "queryid=55|Status=Active|Name=%"
    query_info_unm = "queryid=55|Status=Unmanaged|Name=%"
    query_info_ret = "queryid=55|Status=Retired|Name=%"

    payload1 = {'action':'getqueryresults', 'parameters':query_info_act}
    payload2 = {'action':'getqueryresults', 'parameters':query_info_unm}
    payload3= {'action':'getqueryresults', 'parameters':query_info_ret}

    nnitcmdb_act = Get_Report_Cmdb.Rcmdb(url,payload1)
    nnitcmdb_unm = Get_Report_Cmdb.Rcmdb(url,payload2)
    nnitcmdb_ret = Get_Report_Cmdb.Rcmdb(url,payload3)


    item1 = nnitcmdb_act.getCmdbReport()
    item2 = nnitcmdb_unm.getCmdbReport()
    item3 = nnitcmdb_ret.getCmdbReport()

    items_server1 = item1['cis']
    items_server2 = item2['cis']
    items_server3 = item3['cis']

    times = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) 
    filename = "unix_server_list_full_{0}.xls".format(times)

    output_to_xls(items_server2,"Unmanaged",filename)
    output_to_xls(items_server3,"Retired",filename)
    output_to_xls(items_server1,"active",filename)

    send_mail(args.mail_adress[0],filename)

    if os.path.isfile(filename):
        os.remove(filename)

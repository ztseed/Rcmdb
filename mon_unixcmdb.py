#!/usr/local/bin/python3

import time
from numpy.lib.twodim_base import _trilu_indices_form_dispatcher
from sqlalchemy import create_engine
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


def send_mail(mail_adress, mail_body):

    sender = 'unixcmdb@nnit.com'
    receivers = [mail_adress]

    message = MIMEText(mail_body, 'html', 'utf-8')
    subject = 'Daily report from UNIXCMDB'

    message['From'] = Header("unixcmdb@nnit.com", 'utf-8')
    message['To'] = Header(mail_adress, 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP('mail1.csn.nnithosting.com')
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("send mail done!")
    except smtplib.SMTPException:
        print("Error: failed send mail!")


def create_mailbody(df_1, df_2, num):

    mail_msg1 = '''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
　  <head>
　　<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
　　<title>Daily report from UNIXCNDB</title>
　　<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
　  </head>
    <body style="margin: 0; padding: 0;">

    <style type="text/css">
    table.tftable {font-size:12px;color:#333333;width:100%;border-width: 1px;border-color: #9dcc7a;border-collapse: collapse;}
    table.tftable th {font-size:15px;background-color:#abd28e;border-width: 1px;padding: 8px;border-style: solid;border-color: #9dcc7a;text-align:left;}
    table.tftable tr {background-color:#ffffff;}
    table.tftable td {font-size:14px;border-width: 1px;padding: 8px;border-style: solid;border-color: #9dcc7a;}
    </style>'''+ "<p>This is repot from unixcmdb, so far we have <b>{0}</b> unix/linux server! more information please see <a href=http://heping/serverinout/>UNIXCMDB</a></p>".format(num)

    if not df_1.empty:
        mail_msg2 = '''
        <br>
        <p>new server:
        <br>
        <table id="tfhover" class="tftable" border="1">
        <tr><th>name</th><th>customer</th><th>OS_Description</th><th>status</th><th>change_date</th></tr>'''
        for row in df_1.itertuples():
            mail_msg2 = mail_msg2 + "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(row[1],row[2],row[3],row[4],row[5])
        mail_msg2 = mail_msg2 + "</table>"
    else:
        mail_msg2 = "<p>no new server </p>"

    if not df_2.empty:
        mail_msg3 = '''
        <br>
        <p>retired server:
        <br>
        <table id="tfhover" class="tftable" border="1">
        <tr><th>name</th><th>customer</th><th>OS_Description</th><th>status</th><th>change_date</th></tr>'''
        for row in df_2.itertuples():
            mail_msg3 = mail_msg3 + "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(row[1],row[2],row[3],row[4],row[5])
        mail_msg3 = mail_msg3 + "</table>"
    else:
        mail_msg3 = "<p>no retired server </p>"

    mail_msg4 = '''
    </body>
    </html>'''

    return mail_msg1+mail_msg2+mail_msg3+mail_msg4


time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

print(time_stamp)

engine = create_engine('mysql+pymysql://root:initial@heping:3306/nnitcmdb')

sql = "select name,customer,OS_Description from unix_linux_act_full where OS_Description <> 'N/A';"
sql2 = "select name,customer,OS_Description from unix_linux_act_full_old where OS_Description <> 'N/A';"

#sql = "select name,customer,OS_Description from test_unix_linux_act_full;"
#sql2 = "select name,customer,OS_Description from test_unix_linux_act_full_old;"

df = pd.read_sql_query(sql, engine)
df2 = pd.read_sql_query(sql2, engine)

print(df2)

print(df)

df_new = pd.merge(df['name'], df2['name'], indicator='status',how='left').loc[lambda x: x['status'] != 'both']
df_removed = pd.merge(df2['name'], df['name'], indicator='status',how='left').loc[lambda x: x['status'] != 'both']

timestamp = pd.to_datetime(time_stamp)

df_new1 = pd.DataFrame()
df_removed1 = pd.DataFrame()


if not df_new.empty:

    df_new1 = pd.merge(df_new['name'], df, indicator='status',how='left').loc[lambda x: x['status'] != 'left_only']
    df_new1['change_date'] = timestamp
    df_new1['status'] = 'new'
    print(df_new1)
    df_new1.to_sql('server_in_out', engine, index=False, if_exists='append')


if not df_removed.empty:

    df_removed1 = pd.merge(df_removed['name'], df2, indicator='status',how='left').loc[lambda x: x['status'] != 'left_only']
    df_removed1['change_date'] = timestamp
    df_removed1['status'] = 'reomved'
    print(df_removed1)
    df_removed1.to_sql('server_in_out', engine,index=False, if_exists='append')


mailb = create_mailbody(df_new1, df_removed1, df.shape[0])


send_mail("IO_IS_UNIX_LINUX_ALL@nnit.com", mailb)
#send_mail("tzg@nnit.com", mailb)


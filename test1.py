#!/bin/python
import csv
import pandas as pd
import numpy as np
import time
import sys
import random
import os
import glob
import paramiko
import getpass
import scpclient
import md5
import subprocess
from pandas import DataFrame
from sqlalchemy import create_engine


# Golbal Variable
datenow=(time.strftime("%Y-%m-%d"))
COS_LIST='/opt/automateams/var/cos_list.csv'
DL_LIST='/opt/automateams/var/dl_list.csv'
filename=sys.argv[1]
ADEX_FILE='/opt/output/adexchange.csv'
ZM_FILE='/opt/output/adzimbra.csv'
TMP_ZM='/opt/output/tmpzimbra.csv'
IMPORT_DB='/opt/output/importdb.csv'

# Index COS file
cos_list = pd.read_csv(COS_LIST,sep=',|;', engine='python').apply(lambda x: x.astype(str).str.lower())
# Index Distribution List file
dl_list = pd.read_csv(DL_LIST,sep=',|;', engine='python').apply(lambda x: x.astype(str).str.lower())

#Global Column MANDATORY
df = pd.read_csv(filename, usecols=['EMP_NO','USERNAME','FIRST_NAME','LAST_NAME','EMAIL','AD','EXCHANGE','MANAGER','POSITION','CITY','SUPERVISOR','PASSWORD','WORK_LOCATION','COST_CENTER','MOBILE_PHONE','TICKET','COS','EMPLOYEE_NAME'], sep=',|;', engine='python')


## Split email address to sAMAccountName and limit just 20 Char in there because of AD limitation

# Purpose 1 : split dari almat email dan di batasi 20 Char
#sAMAccountName_field = df.EMAIL.str.split("@").str[0].str.slice(0, 20).str.lower()
#df['sAMAccountName'] = sAMAccountName_field.str.slice(0, 20).str.lower()
#print(sAMAccountName_field)

# ------------- Modif Kolom AD  / remove special char-------------------------------------
# Purpose 2 : gabung dari FNAME(1 char) + LNAME

sAMAccountName_fname = df.FIRST_NAME.str.slice(0, 1).str.lower().str.replace(",","").str.replace("-","").str.replace("\'","")
sAMAccountName_lname = df.LAST_NAME.str.slice(0, 18).str.lower().str.replace(",","").str.replace("-","").str.replace("\'","")
df['sAMAccountName'] = sAMAccountName_fname+'.'+sAMAccountName_lname
df['FIRST_NAME'] = df.FIRST_NAME.str.replace(',','').str.replace("-","").str.replace("\'","")
df['LAST_NAME'] = df.LAST_NAME.str.replace('\,',"").str.replace("\-","").str.replace("\'","")
df['EMAIL'] = df.EMAIL.str.lower().str.replace(",","").str.replace("-","").str.replace("\'","")
df['USERNAME'] = df.USERNAME.str.lower().str.replace(",","").str.replace("-","").str.replace("\'","")

## Domain name
domain_field = df.EMAIL.str.split("@").str[1]
df['domain_name'] = domain_field

#Add date Created column
date_field = datenow
df['date_created'] = date_field

#convert to lowercase for spesific column
df['COS']=df['COS'].str.lower()
df['CITY']=df['CITY'].str.lower()

#Add colom for insert to database by default value
df['status_employee']='0'
df['status_email']='0'
df['id_lync_stts_ftime']='0'
df['id_mobile_stts_ftime']='0'

#Add new column for zimbra mandatory
df['createAccount']='createAccount'
df['displayName']='displayName'
df['givenName']='givenName'
df['sn']='sn'
df['pager']='pager'
df['telephoneNumber']='telephoneNumber'
df['zimbraCOSid']='zimbraCOSid'
df['alias']='aaa'
df['adlm']='adlm'
#--
df['ZEMP_NO']="'"+df['EMP_NO'].astype('str')+"'"
df['alias_domain']=df['USERNAME']+'@'+df['domain_name']
df['ZFIRST_NAME']="'"+df['FIRST_NAME']+"'"
df['ZLAST_NAME']="'"+df['LAST_NAME']+"'"
df['Zphone']="'"+df['MOBILE_PHONE'].astype('str')+"'"



# DECIDE Field by feature and Position
AD_EXCHANGE = df.loc[(df.AD.str.lower() == 'y') & (df.EXCHANGE.str.lower() == 'y')]
AD_ZIMBRA = df.loc[(df.AD.str.lower() == 'y') & (df.EXCHANGE.str.lower() == 'n')]
zimbraonly = df.loc[(df.AD.str.lower() == 'n') & (df.EXCHANGE.str.lower() == 'n')]

AD_EXCHANGE.head()

# Khusus untuk Create Zimbra Join table antara AD_ZIMBRA dan zimbraonly
zm_create = AD_ZIMBRA.append(zimbraonly)

#---------- Join table 1 for zimbra------------------
cos_join = cos_list.merge(zm_create, how = 'inner', on = ['COS'])


#--

#---------- Join table 2 for zimbra DL------------------
#dl_df = conv_dl_list.merge(cos_join, how = 'inner', on = ['COS','CITY'])
dl_df = dl_list.merge(cos_join, how = 'inner', on = ['COS','CITY'])


#Global Table AD Format
tbl_adex=['EmployeeNo','FirstName','LastName','DisplayName','UserLogonName','JobTitle','City','Office','Department','EnableMailbox']

# Export to csv Untuk AD format dengan Exchange
#CONV_AD_EXCHANGE = AD_EXCHANGE.astype('str').replace('\.0', '', regex=True)
#CONV_AD_EXCHANGE = AD_EXCHANGE.astype('str').replace('\.0', '', regex=True)
CONV_AD_EXCHANGE = AD_EXCHANGE.astype('str').replace('\.0', '', regex=True)
CONV_AD_EXCHANGE.to_csv(ADEX_FILE, sep=',', encoding='utf-8', index = None, header=tbl_adex,columns=['EMP_NO','FIRST_NAME','LAST_NAME','EMPLOYEE_NAME','sAMAccountName','POSITION','CITY','WORK_LOCATION','COST_CENTER','EXCHANGE'])

# EXPORT TO CSV FOR untuk  AD_ONLY
CONV_AD_ONLY = AD_ZIMBRA.astype('str').replace('\.0', '', regex=True)
CONV_AD_ONLY.to_csv(ADEX_FILE, mode = 'a' ,sep=',', encoding='utf-8', index = None, header=None,columns=['EMP_NO','FIRST_NAME','LAST_NAME','EMPLOYEE_NAME','sAMAccountName','POSITION','CITY','WORK_LOCATION','COST_CENTER','EXCHANGE'])

# EXPORT to csv create zimbra
# Generate file for creating file zimbra
#CONV_ZM = zm_create.astype('str').replace('\.0', '', regex=True)
CONV_ZM = zm_create.astype('str').replace('\.0', '', regex=True)

# FORMAT CREATE ZIMBRA
#zmfile = open(ZM_FILE,'w+')
CONV_ZM.to_csv(ZM_FILE,encoding='utf-8',sep=' ', index = None, header=None, columns=['createAccount','EMAIL','PASSWORD','displayName','EMPLOYEE_NAME','givenName','ZFIRST_NAME','sn','ZLAST_NAME','pager','ZEMP_NO','telephoneNumber','Zphone','zimbraCOSid','COS_ID'])

# ALIAS IN ZIMBRA
CONV_ZM.to_csv(ZM_FILE,encoding='utf-8',sep=' ', index = None, header=None, mode = 'a', columns=['alias','EMAIL','alias_domain'])

# DL IN ZIMBRA
dl_df.to_csv(ZM_FILE,encoding='utf-8',sep=' ', index = None, header=None, mode = 'a', columns=['adlm','dl_address','EMAIL'])

# ---------------- DB Segment ------------------------------
tbl_db=['nik','username','upn','password','f_name','l_name','d_name','email','position','department','office','status_employee','status_email','date_created','otrs_date_created','id_lync_stts','id_mobile_stts','mobile_phone']

#add domain @HCG.HOMECREDIT.NET
df['sAMAccountName_db']=df.sAMAccountName+'@HCG.HOMECREDIT.NET'

df.to_csv(IMPORT_DB,encoding='utf-8',sep=',',index = None, quotechar='"', header=tbl_db,columns=['EMP_NO','USERNAME','sAMAccountName_db','PASSWORD','FIRST_NAME','LAST_NAME','EMPLOYEE_NAME','EMAIL','POSITION','COST_CENTER','WORK_LOCATION','status_employee','status_email','date_created','TICKET','id_lync_stts_ftime','id_mobile_stts_ftime','MOBILE_PHONE'])


#------------------------------------- INSERT DB AMS
#-- DB AMS
engine = create_engine("mysql://root:paganini@localhost/homecredit")

insertdb = pd.read_csv(IMPORT_DB)
insertdb.to_sql(con=engine, index=False, name='tbl_users', if_exists='replace')



# ------------------------------------- SEND TO SSH
# http://code.activestate.com/recipes/576810-copy-files-over-ssh-using-paramiko/
try:
	connUser = 'root'
	connHost = '10.58.122.209' # remote hostname where SSH server is running
	connPath = '/tmp'
	ZMFILE = '/opt/output/adzimbra.csv'
	scp = subprocess.Popen(['scp', ZMFILE, '{}@{}:{}'.format(connUser, connHost, connPath)])
	print ("File success transfer to zimbra")

except CalledProcessError:
    print('ERROR: Connection to host failed!')

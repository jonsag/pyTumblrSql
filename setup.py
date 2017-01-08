#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from __future__ import print_function

import mysql.connector as MS
from mysql.connector import errorcode

import sys, getpass

from modules import (dbHost, dbPort, dbRootUser, 
                     dbName, dbUser, dbPass)

DB_NAME = dbName

TABLES = {}
TABLES['blog'] = (
    "CREATE TABLE `blog` ( "
    "`blogId` int(11) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`ts` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, "
    "`blog` varchar(255) NOT NULL, "
    "`title` varchar(255), "
    "`updated` int(10), "
    "`totalPosts` int(6) DEFAULT 0, "
    "`postsRetrieved` int(11) NOT NULL DEFAULT 0, "
    "`itemsRetrieved` int(11) NOT NULL DEFAULT 0, "
    "PRIMARY KEY (`blogId`) "
    ") ENGINE=InnoDB")

TABLES['media'] = (
    "CREATE TABLE `media` ( "
    "`mediaId` int(11) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`ts` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, "
    "`path` varchar(255) NOT NULL, "
    "`fileName` varchar(255) NOT NULL, "
    "`mediaTypeId` int(2) UNSIGNED NOT NULL, "
    "`fileSize` int(11), "
    "`width` int(4), "
    "`height` int(4), "
    "`duration` int(5), "
    "`format` varchar(7), "
    "`videoFormat` varchar(5), "
    "`audioFormat` varchar(5), "
    "`fps` int(5), "
    "PRIMARY KEY (`mediaId`) "
    ") ENGINE=InnoDB")

TABLES['mediaInBlog'] = (
    "CREATE TABLE `mediaInBlog` ( "
    "`id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`mediaId` int(11) UNSIGNED NOT NULL, "
    "`blogId` int(11) UNSIGNED NOT NULL, "
    "PRIMARY KEY (`id`) "
    ") ENGINE=InnoDB")

TABLES['mediaType'] = (
    "CREATE TABLE `mediaType` ( "
    "`mediaTypeId` int(2) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`mediaType` varchar(21) NOT NULL, "
    "PRIMARY KEY (`mediaTypeId`) "
    ") ENGINE=InnoDB")

TABLES['fileType'] = (
    "CREATE TABLE `fileType` ( "
    "`fileTypeId` int(2) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`fileType` varchar(5) NOT NULL, "
    "`mediaTypeId` int(2) NOT NULL, "
    "PRIMARY KEY (`fileTypeId`) "
    ") ENGINE=InnoDB")

createUserSql = "CREATE USER IF NOT EXISTS '%s'@'%s' IDENTIFIED BY '%s'" % (dbUser, dbHost, dbPass)
#grantPrivilegesSql = "GRANT ALL ON '%s'.* TO '%s'@'%s' IDENTIFIED BY '%s'" % (dbName, dbUser, dbHost, dbPass)
grantPrivilegesSql = "GRANT ALL ON %s.* TO '%s'@'%s'" % (dbName, dbUser, dbHost)

rootPass = getpass.getpass('Enter MySql root password:')

try:
    cnx = MS.connect(host = dbHost, 
                     port = dbPort, 
                     user = dbRootUser,
                     passwd = rootPass)
    
except MS.Error as err:
    if err.errno == MS.errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == MS.errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
    
    sys.exit(1)

cursor = cnx.cursor()

def create_database(cursor):
    print("\nCreating database '{}'...".format(DB_NAME))
    print("mysql> CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8';".format(DB_NAME))
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except MS.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)
    else:
        print("OK")

try:
    cnx.database = DB_NAME  
except MS.Error as err:
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        cnx.database = DB_NAME
    else:
        print(err)
        exit(1)
        
for name, ddl in TABLES.iteritems():
    print("\nCreating table '{}'...".format(name))
    print("mysql> {};".format(ddl))
    try:
        cursor.execute(ddl)
    except MS.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("%s already exists.\n" % name)
        else:
            print(err.msg)
    else:
        print("OK")
     
cursor.execute("use mysql")
        
print("\nCreating user '{}'...".format(dbUser))
print("mysql> {};".format(createUserSql))
try:
    cursor.execute(createUserSql)
except MS.Error as err:
    print(err.msg)
else:
    print("OK")
    
#print("\nGranting privileges to '{}'...".format(dbUser))
#print("mysql> {};".format(grantPrivilegesSql))
#try:
#    cursor.execute(createUserSql)
#except MS.Error as err:
#    print(err.msg)
#else:
#    print("OK")

cnx.commit()

cursor.close()
cnx.close()

print("\nRun the following command in terminal:")
print("echo GRANT ALL ON '%s'.* TO '%s'@'%s' | mysql -uroot -p mysql\n" % (dbName, dbUser, dbHost))


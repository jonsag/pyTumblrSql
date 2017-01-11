#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

from __future__ import print_function

import mysql.connector as MS
from mysql.connector import errorcode

import sys, getpass

from modules import (dbHost, dbPort, dbRootUser, 
                     dbName, dbUser, dbPass, 
                     mediaTypes, animatedTypes, videoTypes, pictureTypes, audioTypes)

##### define tables
DB_NAME = dbName

TABLES = {}
TABLES['blog'] = (
    "CREATE TABLE `blog` ( "
    "`blogId` int(11) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`ts` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, "
    "`blog` varchar(255) UNIQUE, "
    "`blogTitle` varchar(255), "
    "`blogUpdated` DATETIME, "
    "`totalPosts` int(6) DEFAULT 0, "
    "`postsRetrieved` int(11) DEFAULT 0, "
    "`itemsRetrieved` int(11) DEFAULT 0, "
    "PRIMARY KEY (`blogId`) "
    ") ENGINE=InnoDB")

TABLES['media'] = (
    "CREATE TABLE `media` ( "
    "`mediaId` int(11) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`ts` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, "
    "`path` varchar(255), "
    "`fileName` varchar(255) UNIQUE, "
    "`mediaTypeId` int(2) UNSIGNED, "
    "`fileSize` int(11), "
    "`width` int(4), "
    "`height` int(4), "
    "`duration` int(5), "
    "`format` varchar(7), "
    "`videoFormat` varchar(5), "
    "`audioFormat` varchar(5), "
    "`bitRate` int(5), "
    "PRIMARY KEY (`mediaId`) "
    ") ENGINE=InnoDB")

TABLES['mediaInBlog'] = (
    "CREATE TABLE `mediaInBlog` ( "
    "`id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`mediaId` int(11) UNSIGNED, "
    "`blogId` int(11) UNSIGNED, "
    "`postId` int(15) UNSIGNED, "
    "PRIMARY KEY (`id`) "
    ") ENGINE=InnoDB")

TABLES['mediaType'] = (
    "CREATE TABLE `mediaType` ( "
    "`mediaTypeId` int(2) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`mediaType` varchar(21) UNIQUE, "
    "PRIMARY KEY (`mediaTypeId`) "
    ") ENGINE=InnoDB")

TABLES['fileType'] = (
    "CREATE TABLE `fileType` ( "
    "`fileTypeId` int(2) UNSIGNED NOT NULL AUTO_INCREMENT, "
    "`fileType` varchar(5) UNIQUE, "
    "`mediaTypeId` int(2), "
    "PRIMARY KEY (`fileTypeId`) "
    ") ENGINE=InnoDB")

##### create user sql
createUserSql = "CREATE USER IF NOT EXISTS '%s'@'%s' IDENTIFIED BY '%s'" % (dbUser, dbHost, dbPass)
##### grant privileges sql
#grantPrivilegesSql = "GRANT ALL ON %s.* TO '%s'@'%s'" % (dbName, dbUser, dbHost)

##### get password for root
rootPass = getpass.getpass('Enter MySql root password:')

##### connect to database
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

##### create cursor
cursor = cnx.cursor()

def create_database(cursor): # create database
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

##### create database
try:
    cnx.database = DB_NAME  
except MS.Error as err:
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        cnx.database = DB_NAME
    else:
        print(err)
        exit(1)
        
##### create tables
for name, ddl in TABLES.iteritems():
    print("\nCreating table '{}'...".format(name))
    print("mysql> {};".format(ddl))
    try:
        cursor.execute(ddl)
    except MS.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("Table '%s' already exists.\n" % name)
        else:
            print(err.msg)
    else:
        print("OK")

##### create regular user     
print("\nCreating user '{}'...".format(dbUser))
print("mysql> {};".format(createUserSql))
try:
    cursor.execute(createUserSql)
except MS.Error as err:
    print(err.msg)
else:
    print("OK")
    
##### write values to tables
def add_media_type(cnx, cursor, dbName, mediaType): # add media type
    print("\nAdding media type '%s' to table '%s.mediaType'..." % (mediaType, 
                                                                   dbName))
    print("mysql> INSERT IGNORE INTO %s.mediaType (mediaType) VALUES ('%s');" % (dbName, 
                                                                                 mediaType))

    try:
        cursor.execute("INSERT IGNORE INTO %s.mediaType (mediaType) VALUES ('%s')" % (dbName, 
                                                                                      mediaType))
    except MS.Error as err:
        print(err)
    else:
        print("OK") 
       
    cnx.commit()
    
def queryDbforId(cnx, cursor, dbName, mediaType):  
    print("\nFinding media type id type for %s files..." % mediaType)
    print("mysql> SELECT mediaTypeId FROM %s.mediaType WHERE mediaType='%s';" % (dbName, 
                                                                                 mediaType))   
    try:
        cursor.execute("SELECT mediaTypeId FROM %s.mediaType WHERE mediaType='%s';" % (dbName, 
                                                                                       mediaType))
    except MS.Error as err:
        print(err)
     
    for line in cursor:
        rowId = line
        
    rowId = int(line[0])
    
    if rowId != 0:
        print("OK")
    else:
        print("Something wrong here\nId was 0")
        
    return rowId
    
def add_file_type(cnx, cursor, fileType, mediaType, mediaTypeId): # add file type
    print("\nAdding file type '%s' as '%s'..." % (fileType, 
                                                      mediaType))
    print("mysql> INSERT IGNORE INTO %s.fileType (fileType, mediaTypeId) VALUES ('%s', '%s');" % (dbName, 
                                                                                                  fileType, 
                                                                                                  mediaTypeId))

    try:
        cursor.execute("INSERT IGNORE INTO %s.fileType (fileType, mediaTypeId) VALUES ('%s', '%s')" % (dbName, 
                                                                                                       fileType, 
                                                                                                       mediaTypeId))
    except MS.Error as err:
        print(err)
    else:
        print("OK")

    cnx.commit()

##### add media types
print("\nAdding media types to table 'mediaType'...")
for mediaType in mediaTypes:
    data_mediaType = (dbName, mediaType)
    add_media_type(cnx, cursor, dbName, mediaType)
    
##### make sure changes are written
cnx.commit()

##### add animated types
print("\nAdding file types to table 'fileType'...")
animatedTypeId = queryDbforId(cnx, cursor, dbName, "animated")
for animatedType in animatedTypes:
    add_file_type(cnx, cursor, animatedType, "animated", animatedTypeId)
    
##### add video types
videoTypeId = queryDbforId(cnx, cursor, dbName, "video")
for videoType in videoTypes:
    add_file_type(cnx, cursor, videoType, "video", videoTypeId)
    
##### add picture types
pictureTypeId = queryDbforId(cnx, cursor, dbName, "picture")
for pictureType in pictureTypes:
    add_file_type(cnx, cursor, pictureType, "picture", pictureTypeId)

##### add audio types
audioTypeId = queryDbforId(cnx, cursor, dbName, "audio")
for audioType in audioTypes:
    add_file_type(cnx, cursor, audioType, "audio", audioTypeId)

##### close everything
cursor.close()
cnx.close()

##### instruct how to grant privileges
print("\nRun the following command in terminal:")
print("echo GRANT ALL ON '%s'.* TO '%s'@'%s' | mysql -uroot -p mysql\n" % (dbName, dbUser, dbHost))


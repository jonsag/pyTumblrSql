#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys

from urllib2 import urlopen, URLError, HTTPError

import mysql.connector as MS
from mysql.connector import errorcode

config = ConfigParser.ConfigParser()  # define config file
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__)))  # read config file

dbHost = config.get('mysql_options', 'dbHost').strip(" ")
dbPort = int(config.get('mysql_options', 'dbPort').strip(" "))
dbRootUser = config.get('mysql_options', 'dbRootUser').strip(" ")

dbName = config.get('mysql_options', 'dbname').strip(" ")
dbUser = config.get('mysql_options', 'dbUser').strip(" ")
dbPass = config.get('mysql_options', 'dbPass').strip(" ")

consumer_key = config.get('tumblr_api_keys', 'consumer_key').strip(" ")
consumer_secret = config.get('tumblr_api_keys', 'consumer_secret').strip(" ")
oauth_token = config.get('tumblr_api_keys', 'oauth_token').strip(" ")
oauth_secret = config.get('tumblr_api_keys', 'oauth_secret').strip(" ")

chunkSize = int(config.get('tumblr_options', 'chunkSize'))

defaultDownloadDir = config.get('directory_settings', 'defaultDownloadDir').lstrip(" ").rstrip(" ")
subDir = config.get('directory_settings', 'subDir').lstrip(" ").rstrip(" ")
animatedDir = config.get('directory_settings', 'animatedDir').lstrip(" ").rstrip(" ")
videoDir = config.get('directory_settings', 'videoDir').lstrip(" ").rstrip(" ")

tempFileExtension = config.get('directory_settings', 'tempFileExtension')
logFileName = config.get('directory_settings', 'logFileName')
logFileExtension = config.get('directory_settings', 'logFileExtension')

animatedTypes = config.get('file_types', 'animatedTypes').replace(" ", "").split(",")
videoTypes = config.get('file_types', 'videoTypes').replace(" ", "").split(",")

fileSizeSuffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

def onError(errorCode, extra):
    print "\nError %s" % errorCode
    if errorCode == 1:
        print extra
        usage(errorCode)
    elif errorCode == 2:
        print "No options given"
        usage(errorCode)
    elif errorCode in (3, 4, 5, 7, 8, 9):
        print extra
        sys.exit(errorCode)
    elif errorCode == 6:
        print extra
        return
        
def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -b <blog_name> " % sys.argv[0]
    print "\nMisc options:"
    print "-k    keep going on non fatal errors"
    print "-v    verbose output"
    print "-h    prints this"

    sys.exit(exitCode)
    
def numbering(number):
    if number == 1:
        text = "st"
    elif number == 2:
        text = "nd"
    elif number == 3:
        text = "rd"
    else:
        text = "th"
        
    return text

def dbConnect(verbose):
    cursor = False
    
    if verbose:
        print "Connecting to database '%s'@'%s' on port %s as user '%s' using password '%s'..." % (dbName, 
                                                                                                   dbHost, 
                                                                                                   dbPort, 
                                                                                                   dbUser, 
                                                                                                   dbPass)
    try:
        cnx = MS.connect(host = dbHost, 
                         port = dbPort, 
                         database = dbName, 
                         user = dbUser,
                         passwd = dbPass)
    
    except MS.Error as err:
        if err.errno == MS.errorcode.ER_ACCESS_DENIED_ERROR:
            print("*** Something is wrong with your user name or password")
        elif err.errno == MS.errorcode.ER_BAD_DB_ERROR:
            print("*** Database does not exist")
        else:
            print("*** %s" % err)
        
        onError(3, "Could not connect to database")

    cursor = cnx.cursor()

    return cnx, cursor

def queryDbforId(cnx, cursor, query, data, verbose):
    ids = 0
    
    if verbose:
        print "--- Executing sql..."
        print "    mysql> %s;" % query, data
        
    try:
        cursor.execute(query % data)
    except MS.Error as err:
        onError(9, "Statement: %s\n%s" % (cursor.statement, err))
        
    if verbose:
        print "--- SQL statement was:\n    %s" % cursor.statement
        
    for line in cursor:
        ids += 1
        rowId = line
        if verbose:
            print "RowId[%s]: %s" % (ids, rowId)
        
    if ids == 1:
        rowId = int(line[0])
    elif ids >=2:
        onError(10, "Multiple rows found.\nBetter look into this")
    else:
        rowId = 0
        
    return rowId

def writeToDb(cnx, cursor, sql, data, verbose):
    if verbose:
        print "--- Executing sql..."
        print "    mysql> %s;" % sql, data
    
    try:
        cursor.execute(sql, data)
    except MS.Error as err:
        onError(8, "Statement: %s\n%s" % (cursor.statement, err))
        
    if verbose:
        print "--- SQL statement was:\n    %s" % cursor.statement
        
    cnx.commit()
    
    return cursor

def checkDirectories(defaultDownloadDir, subDir, blog, animatedDir, videoDir, verbose):
    downloadDir = defaultDownloadDir
    
    if not downloadDir.startswith("/"):
        homeDir = os.path.expanduser('~')
        if verbose:
            print "Home directory: %s" % homeDir
        downloadDir = os.path.join(homeDir, downloadDir)
    if verbose:
        print "Download directory: %s" % downloadDir
        
    checkDirectory(downloadDir, verbose)
    
    mainDir = os.path.join(downloadDir, subDir)
    checkDirectory(downloadDir, verbose)
    
    downloadDir = os.path.join(mainDir, blog)
    checkDirectory(downloadDir, verbose)
    
    animatedDir = os.path.join(downloadDir, animatedDir)
    checkDirectory(animatedDir, verbose)
    
    videoDir = os.path.join(downloadDir, videoDir)
    checkDirectory(videoDir, verbose)
    
    return mainDir, downloadDir, animatedDir, videoDir

def checkDirectory(path, verbose):
    if os.path.isdir(path):
        if verbose:
            print "%s exists" % path
    else:
        onError(6, "%s does NOT exist!" % path)
        print "Creating it..."
        os.makedirs(path)

    if os.access(path, os.W_OK):
        if verbose:
            print "%s is writeable" % path
    else:
        onError(4, "%s is NOT writeable" % path)
        
    if verbose:
        print "Deleting .%s files..." % tempFileExtension
    oldTempFiles = [ f for f in os.listdir(path) if f.endswith(".%s" % tempFileExtension) ]
    for f in oldTempFiles:
        os.remove(os.path.join(path, f))
        
def checkFileExists(url, path, verbose):
    fileExists = False
    
    fileName = url.split('/')[-1]
    
    if verbose:
        print "Checking if %s exists at \n %s ..." % (fileName, path)
        
    filePath = os.path.join(path, fileName)
    
    if os.path.isfile(filePath):
        fileExists = True
        if verbose:
            print "File already downloaded"
        
    return fileExists, filePath, fileName
        
def downloadFile(url, path, verbose):
    downloadSuccess = False
    
    fileName = url.split('/')[-1]
    fullPath = os.path.join(path, fileName)
    
    if verbose:
        print
        print "Downloading \n%s \nto \n%s" % (url, fullPath)
    
    # Open the url
    print "Downloading..."
    try:
        f = urlopen(url)

        # Open our local file for writing
        with open("%s.%s" % (fullPath, tempFileExtension), "wb") as local_file:
            local_file.write(f.read())

    #handle errors
    except HTTPError, e:
        print "HTTP Error:", e.code, url
        downloadSuccess = False
    except URLError, e:
        print "URL Error:", e.reason, url
        downloadSuccess = False
    except:
        print "Error"
        downloadSuccess = False
        
    else:
        os.rename("%s.%s" % (fullPath, tempFileExtension), fullPath)
        downloadSuccess = True
        
    return downloadSuccess, fileName, fullPath
        
def humanFileSize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(fileSizeSuffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, fileSizeSuffixes[i])

def checkBlogExists(blog, verbose):
    blogExists = False
    
    tumblrUrl = 'http://%s.tumblr.com' % blog
    
    if verbose:
        print "--- Checking if blog %s exists..." % blog
        
    try:
        urlopen(tumblrUrl)
    except HTTPError, e:
        print "*** %s" % e
    else:
        blogExists = True
        if verbose:
            print "+++ %s exists" % tumblrUrl
     
    return blogExists



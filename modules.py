#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys, shlex

from urllib2 import urlopen, URLError, HTTPError
from subprocess import Popen, PIPE
from datetime import datetime
from time import sleep
from signal import SIGKILL

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

mediaTypes = config.get('file_types', 'mediaTypes').replace(" ", "").split(",")

animatedTypes = config.get('file_types', 'animatedTypes').replace(" ", "").split(",")
videoTypes = config.get('file_types', 'videoTypes').replace(" ", "").split(",")
pictureTypes = config.get('file_types', 'pictureTypes').replace(" ", "").split(",")
audioTypes = config.get('file_types', 'audioTypes').replace(" ", "").split(",")

fileSizeSuffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

timeOut = int(config.get('misc', 'timeOut'))

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
    ##### query example:
    ##### query = "SELECT <id column> FROM blog WHERE <column>='%s'"
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
        #if verbose:
        #    print "--- RowId[%s]: %s" % (ids, rowId)
        
    if ids == 1:
        rowId = int(line[0])
    elif ids >=2:
        onError(10, "Multiple rows found.\nBetter look into this")
    else:
        rowId = 0
        
    if verbose:
        print "--- Answer: %s" % rowId
        
    return rowId

def queryDbSingleAnswer(cnx, cursor, query, data, verbose):
    ##### query example:
    ##### query = "SELECT <column> FROM blog WHERE <column>='%s'"
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
        answer = line
        #if verbose:
        #    print "--- RowId[%s]: %s" % (ids, answer)
        
    if ids == 1:
        answer = line[0]
    elif ids >=2:
        onError(10, "Multiple rows found.\nBetter look into this")
    else:
        answer = ""
        
    if verbose:
        print "--- Answer: %s" % answer
         
    return answer

def writeToDb(cnx, cursor, sql, data, verbose):
    # add_blog = ("INSERT IGNORE INTO blog "
    #             "(blog, blogTitle, blogUpdated, totalPosts) "
    #             "VALUES (%s, %s, %s, %s)")
    # data_blog = (blog, blogTitle, blogUpdated, totalPosts)
    
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
        print "--- Will try to download \n    %s \n    to \n    %s" % (url, fullPath)
    
    print "--- Downloading %s..." % fileName
    try: # open the url
        f = urlopen(url)
    except HTTPError, e: # handle errors
        print "HTTP Error:", e.code, url
        downloadSuccess = False
    except URLError, e:
        print "URL Error:", e.reason, url
        downloadSuccess = False
    except:
        print "Error"
        downloadSuccess = False        
    else:
        print "--- Writing file..."
        # Open our local file for writing
        with open("%s.%s" % (fullPath, tempFileExtension), "wb") as local_file:
            local_file.write(f.read())
        if verbose:
            print "--- Renaming file..."
        os.rename("%s.%s" % (fullPath, tempFileExtension), fullPath)
        downloadSuccess = True
        
    return downloadSuccess, fileName, fullPath

def getMediaInfo(fullPath, mediaType, keepGoing, verbose):
    fileSize =0
    width = 0
    height = 0
    duration = 0
    format = ""
    videoFormat = ""
    audioFormat = ""
    bitRate =0
    
    if verbose:
        print "--- Getting media info..."
    
    ##### general info
    cmd = "mediainfo %s '%s'" % (("--Inform=General;"
                                  "%Format%,"
                                  "%FileSize%,"
                                  "%OverallBitRate%,"
                                  "%Duration%"), fullPath)
    
    output, error = executeCmd(cmd, verbose)
    if output == None and error == None:
        if keepGoing:
            print "*** Execution took too long"
        else:
            onError(13, "Execution took too long")
    
    answer = output.replace("\n", "").split(',')
    
    try: # format
        format = answer[0]
    except:
        format = ""
    try: # file size
        fileSize = int(answer[1])
    except:
        fileSize = 0
    try: # bit rate
        bitRate = int(answer[2])
    except:
        bitRate = 0
    try: # duration
        duration = int(answer[3])
    except:
        duration = 0
        
    if verbose:
        print "--- Media info:"
        print "    Format:\t\t%s" % format
        print "    File size:\t\t%s B" % fileSize
        print "    Bit rate:\t\t%s bps" % bitRate
        print "    Duration:\t\t%s ms" % duration
        
    ##### video info
    if mediaType == "video":
        cmd = "mediainfo %s '%s'" % (("--Inform=Video;"
                                      "%Width%,"
                                      "%Height%,"
                                      "%Format%"), fullPath)   
        
        output, error = executeCmd(cmd, verbose)
        if output == None and error == None:
            if keepGoing:
                print "*** Execution took too long"
            else:
                onError(13, "Execution took too long")
        
        answer = output.replace("\n", "").split(',')

        try: # width
            width = int(answer[0])
        except:
            width = 0
        try: # height
            height = int(answer[1])
        except:
            height = 0
        try: # format
            videoFormat = answer[2]
        except:
            videoFormat = ""
        
        if verbose:
            print "    Width:\t\t%s px" % width
            print "    Height:\t\t%s px" % height
            print "    Video format:\t%s" % videoFormat
            
    ##### image info
    if mediaType == "photo" or mediaType == "animated":
        cmd = "mediainfo %s '%s'" % (("--Inform=Image;"
                                      "%Width%,"
                                      "%Height%"), fullPath)   
        
        output, error = executeCmd(cmd, verbose)
        if output == None and error == None:
            if keepGoing:
                print "*** Execution took too long"
            else:
                onError(13, "Execution took too long")
        
        answer = output.replace("\n", "").split(',')
            
        try: # width
            width = int(answer[0])
        except:
            width = 0
        try: # height
            height = int(answer[1])
        except:
            height = 0
        
        if verbose:
            print "    Width:\t\t%s px" % width
            print "    Height:\t\t%s px" % height
    
    ##### audio
    if mediaType == "video" or mediaType == "audio":
        cmd = "mediainfo %s '%s'" % (("--Inform=Audio;"
                                      "%Format%"), fullPath)   
        
        output, error = executeCmd(cmd, verbose)
        if output == None and error == None:
            if keepGoing:
                print "*** Execution took too long"
            else:
                onError(13, "Execution took too long")
        
        answer = output.replace("\n", "").split(',')
            
        try: # audio format
            audioFormat = answer[0]
        except:
            audioFormat = ""
        
        if verbose:
            print "    Audio format:\t%s" % audioFormat
        
    return fileSize, width, height, duration, format, videoFormat, audioFormat, bitRate
        
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

def executeCmd(cmd, verbose):
    if verbose:
        print "--- Cmd:\n    %s" % cmd 
    args = shlex.split(cmd)
    
    start = datetime.now()
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    while proc.poll() is None:
        sleep(0.1)
        now = datetime.now()
        if (now - start).seconds > timeOut:
            os.kill(proc.pid, SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return (None, None)
    
    output, error = proc.communicate()
    
    return (output, error)

def whereToSaveFile(cnx, cursor, mediaTypeId, downloadDir, animatedDir, videoDir, verbose):
    if verbose:
        print "--- Looking up media type..."        
    query = "SELECT mediaType FROM mediaType WHERE mediaTypeId='%s'"
    mediaType = queryDbSingleAnswer(cnx, cursor, query, mediaTypeId, verbose)
    if verbose:
        print "--- Media type: %s" % mediaType
    if mediaType == "animated":
        savePath = animatedDir
    elif mediaType == "video":
        savePath = videoDir
    elif mediaType == "picture":
        savePath = downloadDir
    if verbose:
        print "--- Will save to:\n    %s" % savePath
        
    return savePath, mediaType

def writeMediaInfo(cnx, cursor, filePath, mediaType, keepGoing, fileName, savePath, mediaTypeId, verbose):
    if verbose:
        print "--- Adding to database..."
    (fileSize, width, height, duration, 
     format, videoFormat, audioFormat, 
     bitRate) = getMediaInfo(filePath, 
                             mediaType, keepGoing, verbose) # get media info
    ##### write media info to db
    add_media = ("INSERT IGNORE INTO media "
                 "(path, filename, mediaTypeId, fileSize, "
                 "width, height, duration, format, "
                 "videoFormat, audioFormat, bitRate) "
                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    data_media = (savePath, fileName, mediaTypeId, fileSize, 
                  width, height, duration, format, 
                  videoFormat, audioFormat, bitRate)
    cursor = writeToDb(cnx, cursor, add_media, data_media, verbose)
    mediaId = cursor.lastrowid
    
    return mediaId

def countUpItemsRetrieved(cnx, cursor, blog, verbose):
    if verbose:
        print "--- Adding to items retrieved..."
    count_up_items = ("UPDATE blog "
                     "SET itemsRetrieved=itemsRetrieved+1 "
                     "WHERE blog=%s")
    data_count_up_items = (blog, )
    cursor = writeToDb(cnx, cursor, count_up_items, data_count_up_items, verbose)

def isMediaInBlog(cnx, cursor, mediaId, blogId, postId, verbose):    
    #verbose = True
    if verbose:
        print "--- Checking if this media and post is registered to this blog..."
    # check if media is linked to this blog
    query_mediaInBlog = ("SELECT id FROM mediaInBlog WHERE "
                         "mediaId='%s' AND "
                         "blogid='%s'")
    data_mediaInBlog = (mediaId, blogId)
    isInTable = queryDbforId(cnx, cursor, query_mediaInBlog, data_mediaInBlog, verbose)

    return isInTable

def addMediaInBlog(cnx, cursor, mediaId, blogId, postId, postTime,verbose):
    if mediaId == 0:
        sys.exit(0)
    if verbose:
        print "--- Not in table\n    Adding..."
        
    add_media_in_blog = ("INSERT IGNORE INTO mediaInBlog "
                         "(mediaId, blogId, postId, postTime) "
                         "VALUES (%s, %s, %s, %s)")
    data_media_in_blog = (mediaId, blogId, postId, postTime)
    cursor = writeToDb(cnx, cursor, add_media_in_blog, data_media_in_blog, verbose)
    
def countUpMediaForBlog(cnx, cursor, mediaType, blog, verbose):        
    if mediaType == "animated":
        count_up_item = ("UPDATE blog "
                         "SET animatedItems=animatedItems+1 "
                         "WHERE blog=%s")
    elif mediaType == "video":
        count_up_item = ("UPDATE blog "
                         "SET videoItems=videoItems+1 "
                         "WHERE blog=%s")
    elif mediaType == "picture":
        count_up_item = ("UPDATE blog "
                         "SET photoItems=photoItems+1 "
                         "WHERE blog=%s")
    data_count_up_item = (blog, )
    cursor = writeToDb(cnx, cursor, count_up_item, data_count_up_item, verbose)

    
    
    
    
    
    
    
    
    
    
    
    
    


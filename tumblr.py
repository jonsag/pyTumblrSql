#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import math, os, sys
import pytumblr

from pprint import pprint

from datetime import datetime

from modules import (consumer_key, consumer_secret, oauth_token, oauth_secret, 
                     animatedTypes, videoTypes, 
                     queryDbforId, writeToDb, 
                     onError, numbering, checkFileExists, downloadFile, getMediaInfo)

def authenticateClient(verbose):
    
    print "\n--- Authenticating..."
    
    if verbose:
        print "Consumer key: '%s'" % consumer_key
        print "Consumer secret: '%s'" % consumer_secret
        print "OAuth token: '%s'" % oauth_token
        print "OAuth secret: '%s'" % oauth_secret

    # Authenticate via OAuth
    client = pytumblr.TumblrRestClient(
        consumer_key,
        consumer_secret, 
        oauth_token, 
        oauth_secret)
    
    # Make the request
    clientInfo = client.info()
    
    if verbose:
        print "̣\nClient info:\n--------------------"
        pprint(clientInfo)
        print "--------------------"
    
    return client

def getPosts(cnx, cursor, client, blog, mainDir, downloadDir, animatedDir, videoDir, keepGoing, verbose):
    
    from modules import chunkSize
    
    posts = []
    
    chunkNo = 0
    postNo = 0
    
    ##### parse blog
    print "\n--- Getting posts from '%s'" % blog   
    blogContents = client.posts(blog, limit=1)
    
    if verbose:
        print "\nBlog contents:\n--------------------"
        pprint(blogContents)
        print "--------------------"
        
    blogTitle = blogContents['blog']['title']
    blogUpdatedUnix = blogContents['blog']['updated']
    blogUpdated = datetime.fromtimestamp(int(blogUpdatedUnix)).strftime('%Y-%m-%d %H:%M:%S')
    totalPosts = blogContents['blog']['total_posts']
    
    ##### print report
    print "\n%s:\n--------------------" % blog 
    print "Address: %s" % blogContents['blog']['url']
    print "Title: %s" % blogTitle
    print "Last updated: %s" % blogUpdated
    print "Total posts: %s" % totalPosts
    
    if blogContents['blog']['is_nsfw']:
        print "\nBlog is NOT safe for work"
        
    print
    
    ##### create entry for blog in db
    if verbose:
        print "--- Creating entry in db for blog '%s'" % blog
    add_blog = ("INSERT IGNORE INTO blog "
                "(blog, blogTitle, blogUpdated, totalPosts) "
                "VALUES (%s, %s, %s, %s)")
    data_blog = (blog, blogTitle, blogUpdated, totalPosts)
    
    cursor = writeToDb(cnx, cursor, add_blog, data_blog, verbose)
    
    ##### get id for blog
    blogId = cursor.lastrowid
    if blogId == 0:
        if verbose:
            print "+++ Blog '%s' already exist"
        query = "SELECT blogId FROM blog WHERE blog='%s'"
        blogId = queryDbforId(cnx, cursor, query, blog, verbose)
    if verbose:
        print "--- BlogId: %s" % blogId
    
    ##### calculate how many chunks we will try to receive
    totalChunks = int(math.ceil(totalPosts / chunkSize))
    
    while True:
        print "--- Starting downloads..."
        if chunkNo * chunkSize >= totalPosts: # check if we reached the end
            print "*** No more posts"
            break
        else: 
            partNo = 0
            
            chunkNo += 1
            
            offset = totalPosts - chunkNo * chunkSize
            if offset < 0:
                chunkSize = chunkSize + offset
                offset = 0
            
            print "--- Getting %s%s chunk..." % (chunkNo, numbering(chunkNo))
            print "    Offset: %s" % offset
            print "    Chunk size: %s" % chunkSize
            print "    Post %s to %s of %s" % (totalPosts - chunkNo * chunkSize + 1, 
                                               totalPosts - (chunkNo -1) * chunkSize, 
                                               totalPosts)

            blogContents = client.posts(blog, # get posts from blog, start at offset and get chunkSize posts
                                        offset=offset, 
                                        limit=chunkSize)
            
            for line in blogContents['posts']:
                postNo += 1
                partNo += 1
                print "\n--- Blog: %s" % blog
                print "    Post: %s / %s" % (postNo, totalPosts)
                print "    Chunk: %s / %s" % (chunkNo, totalChunks)
                print "    Part: %s / %s" % (partNo, chunkSize)
                if verbose:
                    print "Post:\n----------"
                    pprint(line)
                    print "----------"
                posts.append(line)

                mediaList = findMedia(line, keepGoing, verbose)
                
                mediaId = 0
                downloadSuccess = False
                    
                if mediaList:
                    for line in mediaList:
                        downloadSuccess = False                    
                        url, savePath = checkMedia(line, downloadDir, animatedDir, videoDir, verbose)
                        
                        #fileExists, filePath, fileName = checkFileExists(url, savePath, verbose)
                        query = "SELECT blogId FROM blog WHERE blog='%s'"
                        fileName = url.split('/')[-1]
                        if verbose:
                            print "--- Checking if file is in database..."
                        mediaId = queryDbforId(cnx, cursor, query, fileName, verbose)
                        
                        if not mediaId:                        
                            downloadSuccess, fileName, filePath = downloadFile(url, savePath, verbose)
                            if downloadSuccess:
                                if verbose:
                                    print "--- Adding to database..."
                                getMediaInfo(filePath, verbose)
                            if verbose and not downloadSuccess:
                                print "*** Failed to download file"
                        else:
                            if verbose:
                                print "+++ Already exists\n    Adding to database for '%s'" % blog
                            else:
                                print "+++ Already exists. Skipping file..."
                            
                if downloadSuccess or mediaId:                
                    sys.exit(0)
                    
            print "\n--- Posts processed: %s" % len(posts)
    
    print len(posts)
    
    if verbose:
        print blogContents
    
    posts = blogContents
    return posts
    
def findMedia(post, keepGoing, verbose):
    mediaList = []
    
    if verbose:
        print "--- Searching for media in post..."
        
    if "photos" in post:
        for line in post["photos"]:
            print "--- Found photo"
            mediaList.append(line["original_size"]["url"])
    elif "video_url" in post:
        print "--- Found video"
        mediaList.append(post["video_url"])
    else:
        if verbose:
            print "+++ Did not find photos or video"
        if not keepGoing:
            onError(5, "Did not find photos or video")
        
    return mediaList   
    
def checkMedia(line, downloadDir, animatedDir, videoDir, verbose):
    url = line
    
    savePath = downloadDir
    
    for fileType in animatedTypes:
        if url.lower().endswith(fileType):
            if verbose:
                print "--- File is animated"
            savePath = animatedDir
            break
    
    if savePath != animatedDir:
        for fileType in videoTypes:
            if url.lower().endswith(fileType):
                if verbose:
                    print "--- File is video"
                savePath = videoDir
                break
    
    if verbose and savePath != animatedDir and savePath != videoDir:
        print "--- File is not animated and not video"
        
    return url, savePath



   
    
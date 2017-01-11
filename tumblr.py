#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import math, os, sys
import pytumblr

from pprint import pprint

from datetime import datetime

from urlparse import urlparse

from modules import (consumer_key, consumer_secret, oauth_token, oauth_secret, 
                     animatedTypes, videoTypes, 
                     queryDbforId, queryDbSingleAnswer, writeToDb, 
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
    if verbose:
        print "--- BlogId a: %s" % blogId
    if blogId == 0: # blog already exists
        if verbose:
            print "+++ Blog '%s' already exist"
        query = "SELECT blogId FROM blog WHERE blog='%s'"
        blogId = queryDbforId(cnx, cursor, query, blog, verbose)
        if verbose:
            print "--- BlogId b: %s" % blogId
        print "--- Updating blog info..."
        update_blog = ("UPDATE blog "
                       "SET blogUpdated=%s, totalPosts=%s "
                       "WHERE blog=%s")
        data_update_blog = (blogUpdated, totalPosts, blog)
        cursor = writeToDb(cnx, cursor, update_blog, data_update_blog, verbose)
        
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
            
            for post in reversed(blogContents['posts']): # run through posts in chunk
                postNo += 1
                partNo += 1
                print "\n--- Blog: %s" % blog
                print "    Post: %s / %s" % (postNo, totalPosts)
                print "    Chunk: %s / %s" % (chunkNo, totalChunks)
                print "    Part: %s / %s" % (partNo, chunkSize)
                
                for line in post['trail']:
                    postId = line['post']['id']
                print "\n--- Post id: %s" % postId
                
                postTime = post['date']
                print "--- Post time: %s" % postTime.rstrip(' GMT')
                if verbose:
                    print "Post:\n----------"
                    pprint(post)
                    print "----------"
                posts.append(post)
                
                mediaList = findMedia(cnx, cursor, post, keepGoing, verbose) # check if post contains any media
                
                mediaId = 0
                downloadSuccess = False
                    
                if mediaList:
                    for mediaUrl, mediaTypeId in mediaList:
                        downloadSuccess = False     
                          
                        ##### determine where to save file     
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
                            #sys.exit(0)
                        if verbose:
                            print "--- Will save to:\n    %s" % savePath

                        query = "SELECT mediaId FROM media WHERE fileName='%s'"
                        
                        ##### check if file already exists
                        fileName = mediaUrl.split('/')[-1]
                        if verbose:
                            print "--- Checking if file is in database..."
                        mediaId = queryDbforId(cnx, cursor, query, fileName, verbose) # returns >0 if media is in db
                        
                        downloadSuccess = True
                        if not mediaId:      
                            if verbose:
                                print "--- File is not in database"                  
                            downloadSuccess, fileName, filePath = downloadFile(mediaUrl, savePath, verbose)
                            if downloadSuccess:
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
                            if verbose and not downloadSuccess:
                                print "*** Failed to download file"
                        else:
                            if verbose:
                                print "+++ Already exists\n    Adding to database for '%s' if not already there..." % blog
                            else:
                                print "+++ Already exists. Skipping file..."
                        
                        if verbose:
                            print "--- Checking if this media and post is registered to this blog..."
                        query_mediaInBlog = ("SELECT id FROM mediaInBlog WHERE "
                                             "mediaId='%s' AND "
                                             "blogid='%s' AND "
                                             "postId='%s'")
                        data_mediaInBlog = (mediaId, blogId, postId)
                        isInTable = queryDbforId(cnx, cursor, query_mediaInBlog, data_mediaInBlog, verbose)
                        
                        if not isInTable and downloadSuccess:
                            if mediaId == 0:
                                sys.exit(0)
                            if verbose:
                                print "--- Not in table\n    Adding..."
                            add_media_in_blog = ("INSERT IGNORE INTO mediaInBlog "
                                                 "(mediaId, blogId, postId, postTime) "
                                                 "VALUES (%s, %s, %s, %s)")
                            data_media_in_blog = (mediaId, blogId, postId, postTime)
                            cursor = writeToDb(cnx, cursor, add_media_in_blog, data_media_in_blog, verbose)
                            
                #if downloadSuccess or not mediaId:                
                #    sys.exit(0)
                    
            print "\n--- Posts processed: %s" % len(posts)
    
    print len(posts)
    
    if verbose:
        print blogContents
    
    posts = blogContents
    return posts
    
def findMedia(cnx, cursor, post, keepGoing, verbose):
    mediaList = []
    mediaTypeId = 0
    
    query = "SELECT mediaTypeId FROM fileType WHERE fileType='%s'"
    
    if verbose:
        print "--- Searching for media in post..."
        
    postType = post['type']
        
    if postType == "photo":
        for line in post["photos"]:
            print "--- Found photo"
            photoUrl = line["original_size"]["url"]
            path = urlparse(photoUrl).path
            extension = os.path.splitext(path)[1].strip(".")
            if verbose:
                print "--- Looking up its extension, %s" % extension
            mediaTypeId = queryDbforId(cnx, cursor, query, extension, verbose)
            mediaList.append([photoUrl, mediaTypeId])
            if verbose:
                print "--- Adding it to media list..."
                print "    Url: %s" % photoUrl
                print "    Media type id: %s" % mediaTypeId
    elif postType == "video":
        print "--- Found video"
        videoUrl = post["video_url"]
        path = urlparse(videoUrl).path
        extension = os.path.splitext(path)[1].strip(".")
        if verbose:
            print "--- Looking up its extension, %s" % extension
        mediaTypeId = queryDbforId(cnx, cursor, query, extension, verbose)
        mediaList.append([videoUrl, mediaTypeId])
        if verbose:
            print "--- Adding it to media list..."
            print "    Url: %s" % videoUrl
            print "    Media type id: %s" % mediaTypeId
    else:
        print "--- Post type: %s -----------------------------------------------------" % postType
        if verbose:
            print "+++ Did not find photos or video"
        if not keepGoing:
            onError(5, "Did not find photos or video")
            
    if len(mediaList) == 1:
        print "--- Found 1 item"
    elif len(mediaList) >= 2:
        print "--- Found %s items" % len(mediaList)
        
    return mediaList   
    

















   
    
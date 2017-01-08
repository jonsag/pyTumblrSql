#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import math, os, sys
import pytumblr

from pprint import pprint

from modules import (consumer_key, consumer_secret, oauth_token, oauth_secret, 
                     animatedTypes, videoTypes, 
                     onError, numbering, checkFileExists, downloadFile)

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

def getPosts(cursor, client, blog, mainDir, downloadDir, gifDir, videoDir, keepGoing, verbose):
    
    from modules import chunkSize
    
    posts = []
    fileList = []
    
    chunkNo = 0
    postNo = 0
    
    print "\n--- Getting posts from '%s'" % blog
    
    blogContents = client.posts(blog, limit=1)
    
    if verbose:
        print "\nBlog contents:\n--------------------"
        pprint(blogContents)
        print "--------------------"
    
    print "\n%s:\n--------------------" % blog 
    print "Blog: %s" % blogContents['blog']['url']
    print "Total posts: %s" % blogContents['blog']['total_posts']
    
    if blogContents['blog']['is_nsfw']:
        print "\nBlog is NOT safe for work"
        
    print
    
    sys.exit(0)
    
    totalPosts = blogContents['total_posts']
    totalChunks = int(math.ceil(totalPosts / chunkSize))
    
    while True:
        
        if chunkNo * chunkSize >= totalPosts:
            print "*** No more posts"
            break
        else:   
            chunkNo += 1
            partNo = 0
                
            fileList = []
            
            print "--- Getting %s%s chunk..." % (chunkNo, numbering(chunkNo))
            print "    Post %s to %s of %s" % (totalPosts - chunkNo * chunkSize + 1, totalPosts - (chunkNo -1) * chunkSize, totalPosts)
            
            offset = totalPosts - chunkNo * chunkSize
            if offset < 0:
                chunkSize = chunkSize + offset
                offset = 0
            #print "    Offset: %s" % offset
            #print "    Chunk size: %s" % chunkSize
            blogContents = client.posts(blog, offset=offset, limit=chunkSize)
            
            for line in blogContents['posts']:
                postNo += 1
                partNo += 1
                print "\n--- Blog: %s" % blog
                print "    Post: %s / %s" % (postNo, totalPosts)
                print "    Chunk: %s / %s" % (chunkNo, totalChunks)
                print "    Part: %s / %s" % (partNo, chunkSize)
                #if verbose:
                #    print line
                posts.append(line)
                
                mediaList = findMedia(line, keepGoing, verbose)
                    
                for line in mediaList:
                    downloadSuccess = False
                    fileSize = 0
                    
                    url, savePath = checkMedia(line, downloadDir, gifDir, videoDir, verbose)
                    
                    fileExists, filePath, fileName = checkFileExists(url, savePath, verbose)
                    
                    if not fileExists:                        
                        downloadSuccess, fileName, filePath = downloadFile(url, savePath, verbose)
                    
                        if verbose and not downloadSuccess:
                            print "+++ Failed to download file"
                    else:
                        print "+++ Already exists. Skipping file..."
                    
            print "\n--- Posts processed: %s" % len(posts)
    
    print len(posts)
    
    if verbose:
        print blogContents
    
    posts = blogContents
    return posts
    
def findMedia(post, keepGoing, verbose):
    mediaList = []
    
    if verbose:
        print "Post:"
        print post
        
    if "photos" in post:
        for line in post["photos"]:
            print "Original size url: \n%s" % line["original_size"]["url"]
            if verbose:
                print "Width x height: %s x %s" % (line["original_size"]["width"], line["original_size"]["height"])
            mediaList.append(line["original_size"]["url"])
    elif "video_url" in post:
        print "Video url: \n %s" %  post["video_url"]
        mediaList.append(post["video_url"])
    else:
        if not keepGoing:
            onError(5, "Did not find photos or video")
        
    return mediaList   
    
def checkMedia(line, downloadDir, gifDir, videoDir, verbose):
    url = line
    
    savePath = downloadDir
    
    for fileType in animatedTypes:
        if url.lower().endswith(fileType):
            if verbose:
                print "File is animated"
            savePath = gifDir
            break
    
    if savePath != gifDir:
        for fileType in videoTypes:
            if url.lower().endswith(fileType):
                if verbose:
                    print "File is video"
                savePath = videoDir
                break
    
    if verbose and savePath != gifDir and savePath != videoDir:
        print "File is not animated and not video"
        
    return url, savePath



   
    
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import sys, getopt, os

from shutil import rmtree

from modules import (onError, usage, dbConnect, checkBlogExists, checkDirectories, 
                     defaultDownloadDir, subDir, animatedDir, videoDir, 
                     queryDbforId, deleteFromDb, queryDbSingleAnswer)

from tumblr import authenticateClient, processBlog

try:
    myopts, args = getopt.getopt(sys.argv[1:],
                                 'b:' 
                                 'k'
                                 'u'
                                 'd'
                                 'vh',
                                 ['blog:', 'keepgoing', 'update', 'delete', 'verbose', 'help'])

except getopt.GetoptError as e:
    onError(1, str(e))

if len(sys.argv) == 1:  # no options passed
    onError(2, 2)
    
blog = ""
updateBlogs = False
deleteBlog = False
verbose = False
keepGoing = False

for option, argument in myopts:
    if option in ('-b', '--blog'):
        blog = argument
    elif option in ('-k', '--keepgoing'):
        keepGoing = True
    elif option in ('-u', '--update'):
        updateBlogs = True
    elif option in ('-d', '--delete'):
        deleteBlog = True
    elif option in ('-v', '--verbose'):  # verbose output
        verbose = True
    elif option in ('-h', '--help'):  # display help text
        usage(0)

# connect to database
cnx, cursor = dbConnect(verbose)

# create tumblr API client
client = authenticateClient(verbose)

if updateBlogs:
    if verbose:
        print "--- Updating all blogs..."
        print "--- Getting list of blogs..."

    cursor.execute('SELECT blog FROM blog')
    blogs = row = cursor.fetchall()
    
    if verbose:
        print "--- Will update %s blogs..." % len(blogs)
    for row in blogs:
        blog = row[0]
        print "--- Updating %s..." % blog
        posts = processBlog(defaultDownloadDir, subDir, blog, animatedDir, videoDir, cnx, cursor, client, keepGoing, verbose)
elif deleteBlog:
    fileNames = []
    if not blog:
        onError(12, "No blog given")
    if verbose:
        print "--- Will try to delete %s with all of its content..." % blog
   
    # find blogId 
    query = "SELECT blogId FROM blog WHERE blog='%s'"
    blogId = queryDbforId(cnx, cursor, query, blog, verbose)
    if not blogId:
        onError(13, "%s does not exist in database" % blog)
    
    # delete blog
    sql = "DELETE FROM blog WHERE blogId='%s'" % blogId
    cursor = deleteFromDb(cnx, cursor, sql, verbose)
    
    # delete from mediaInBlog
    sql = "DELETE FROM mediaInBlog WHERE blogId='%s'" % blogId
    cursor = deleteFromDb(cnx, cursor, sql, verbose)
    
    # delete media
    sql = "DELETE FROM media WHERE mediaId NOT IN (SELECT mediaId FROM mediaInBlog)"
    cursor = deleteFromDb(cnx, cursor, sql, verbose)
    
    # delete files
    downloadDir = defaultDownloadDir
    if not downloadDir.startswith("/"):
        homeDir = os.path.expanduser('~')
        downloadDir = os.path.join(homeDir, downloadDir)
    blogDir = os.path.join(downloadDir, subDir, blog)

    if verbose:
        print "--- Deleting %s and all files in it..." % blogDir
    rmtree(blogDir)
        
    
else:
    if not checkBlogExists(blog, verbose): # check if the blog really exists
        onError(7, "Blog %s does not exist" % blog)
    posts = processBlog(defaultDownloadDir, subDir, blog, animatedDir, videoDir, cnx, cursor, client, keepGoing, verbose)






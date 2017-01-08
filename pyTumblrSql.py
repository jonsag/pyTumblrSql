#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import sys, getopt

from modules import (onError, usage, dbConnect, checkDirectories, checkBlogExists, 
                     defaultDownloadDir, subDir, gifDir, videoDir)

from tumblr import authenticateClient, getPosts

try:
    myopts, args = getopt.getopt(sys.argv[1:],
                                 'b:' 
                                 'k'
                                 'vh',
                                 ['blog:', 'keepgoing', 'verbose', 'help'])

except getopt.GetoptError as e:
    onError(1, str(e))

if len(sys.argv) == 1:  # no options passed
    onError(2, 2)
    
verbose = False
keepGoing = False

for option, argument in myopts:
    if option in ('-b', '--blog'):
        blog = argument
    elif option in ('-k', '--keepgoing'):
        keepGoing = True
    elif option in ('-v', '--verbose'):  # verbose output
        verbose = True
    elif option in ('-h', '--help'):  # display help text
        usage(0)
        
if not checkBlogExists(blog, verbose):
    onError(7, "Blog %s does not exist" % blog)

# connect to database
cursor = dbConnect(verbose)

mainDir, downloadDir, gifDir, videoDir = checkDirectories(defaultDownloadDir, subDir, blog, gifDir, videoDir, verbose)

client = authenticateClient(verbose)

posts = getPosts(cursor, client, blog, mainDir, downloadDir, gifDir, videoDir, keepGoing, verbose)



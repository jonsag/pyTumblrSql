# pyTumblrSql
A tool to dl tumblr pics and vids and log all files and progress to MySql db


MySql cheatsheet:
==============
# mysql -upyTumblr -ppyTumblrPass pyTumblr

count videos
mysql> SELECT "videos", COUNT(*) FROM media WHERE mediaTypeId=(SELECT mediaTypeId FROM mediaType WHERE mediaType='video');

# pyTumblrSql
A tool to dl tumblr pics and vids and log all files and progress to MySql db


MySql cheatsheet:
==============
# mysql -upyTumblr -ppyTumblrPass pyTumblr

view media
mysql> SELECT mediaTypeId, COUNT(*) FROM media GROUP BY mediaTypeId;

count videos
mysql> SELECT "videos", COUNT(*) FROM media WHERE mediaTypeId=(SELECT mediaTypeId FROM mediaType WHERE mediaType='video');

view blogs and items retrieved
mysql> SELECT blog, itemsRetrieved, animatedItems, videoItems, photoItems FROM blog;


# pyTumblrSql
A tool to download tumblr pics and vids and log all files and progress to MySql db


MySql cheatsheet:
==========================================
# mysql -upyTumblr -ppyTumblrPass pyTumblr

view media
==============
mysql> SELECT mediaType.mediaType, COUNT(*) 
FROM media 
LEFT JOIN mediaType ON mediaType.mediaTypeId=media.mediaTypeId 
GROUP BY mediaType;

count videos
==============
mysql> SELECT COUNT(*) AS 'number of videos' 
FROM media 
WHERE mediaTypeId=(SELECT mediaTypeId FROM mediaType WHERE mediaType='video');

view blogs and items retrieved
==============
mysql> SELECT blog, itemsRetrieved, animatedItems, videoItems, photoItems 
FROM blog;

view how many items each blog has
==============
mysql> SELECT blog.blog, COUNT(*) AS 'media items'
FROM mediaInBlog
LEFT JOIN blog ON mediaInBlog.blogId = blog.blogId 
GROUP BY blog.blog;

view all media downloaded yesterday
==============
mysql> SELECT ts, fileName 
FROM media 
WHERE ts >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND ts < CURDATE();

view all videos downloaded yesterday
==============
mysql> SELECT ts, fileName 
FROM media 
WHERE ts >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) 
AND ts < CURDATE() AND mediaTypeId = (SELECT mediaTypeID 
FROM mediaType 
WHERE mediaType = 'video');

list media posted in multiple blogs
==============
mysql> SELECT media.fileName, COUNT(*) c 
FROM mediaInBlog 
LEFT JOIN media ON media.mediaId = mediaInBlog.mediaId
GROUP BY media.fileName 
HAVING c > 1
ORDER BY c;

count all items retrieved
==============
mysql> SELECT SUM(itemsRetrieved) AS 'items retrieved' 
FROM blog;

number of files and disk space used
==========
mysql> SELECT COUNT(*) AS 'Number of files' , SUM(fileSize)/1024/1024/1024 AS 'GiB' 
FROM media;


some statistics of videos
==============
mysql> SELECT COUNT(*) AS 'number of videos', 
SEC_TO_TIME(ROUND(SUM(duration/1000))) AS 'total play time', 
SEC_TO_TIME(ROUND(SUM(duration)/1000/COUNT(*), 0)) as 'average video duration' 
FROM media 
WHERE mediaTypeId = (SELECT mediaTypeId FROM mediaType WHERE mediaType = 'video');

find longest video
==============
mysql> SELECT path, fileName, SEC_TO_TIME(duration/1000) 
FROM media 
WHERE mediaTypeId = (SELECT mediaTypeId FROM mediaType WHERE mediaType = 'video') 
ORDER BY duration\G;

list media and which blog it's downloaded to
==============
mysql> SELECT media.fileName, blog.blog
FROM mediaInBlog 
LEFT JOIN media on media.mediaId = mediaInBlog.mediaId 
LEFT JOIN blog ON blog.blogID = mediaInBlog.blogId 
ORDER By blog.blog;



   
		

		
		
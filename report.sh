#!/bin/bash

BLOGS="SELECT blog, itemsRetrieved, animatedItems, videoItems, photoItems FROM blog\G;"

MEDIA="SELECT mediaTypeId, COUNT(*) FROM media GROUP BY mediaTypeId;"

MEDIACOUNT="SELECT COUNT(*) AS mediaCount FROM media;"

echo

for QUERY in "$BLOGS", "$MEDIA", "$MEDIACOUNT"; do
	echo $QUERY | mysql -upyTumblr -ppyTumblrPass pyTumblr 2>/dev/null
	echo
done

SELECT i.influencerid, i.name, COUNT(ph.hashtag_id) AS hashtags_used
FROM influencers i
JOIN posts p
ON i.influencerid = p.ownerid 
join posts_hashtags ph
ON p.postid = ph.post_id
GROUP BY i.influencerid, i.name;
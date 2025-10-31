SELECT h.tag_name, COUNT(hashtagid) AS use_count
FROM hashtags h
JOIN posts_hashtags ph
    ON ph.hashtag_id = h.hashtagid
JOIN posts p
    ON p.postid = ph.post_id
JOIN influencers i
    ON i.influencerid = p.ownerid
WHERE i.username = 'inaseemshah'
GROUP BY h.tag_name
ORDER BY use_count DESC
LIMIT 5;

SELECT *
FROM influencers;

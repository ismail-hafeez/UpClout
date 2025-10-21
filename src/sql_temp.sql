SELECT 
    h.tag_name, 
    COUNT(ph.hashtag_id) AS usage_count
FROM 
    posts_hashtags ph
JOIN 
    hashtags h 
ON 
    ph.hashtag_id = h.hashtagid
GROUP BY 
    h.tag_name
ORDER BY 
    usage_count DESC
LIMIT 1;
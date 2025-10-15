SELECT p.caption
FROM posts p
JOIN influencers i
ON p.ownerid = i.influencerid
WHERE i.influencerid = 48096912

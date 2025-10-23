SELECT *
FROM influencers
WHERE followers = (
    SELECT MAX(followers)
    FROM influencers
)

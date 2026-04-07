UPDATE brands
SET
    profile_pic = 'https://upclout-profile-pics.s3.us-west-1.amazonaws.com/brand-profile-pics/' || username || '.jpg'

SELECT tu.username AS tagged_user, COUNT(*) AS tag_count
FROM
    influencers i
    JOIN posts p ON i.influencerid = p.ownerid
    JOIN posts_taggeduser ptu ON p.postid = ptu.postid
    JOIN taggeduser tu ON ptu.taggeduserid = tu.taggeduserid
WHERE
    i.username = 'isaa_akhn'
GROUP BY
    tu.username
ORDER BY tag_count DESC
LIMIT 10;

drop table brand_recommendations;

select * from brand_recommendations;

SELECT businesscategoryname, TRIM(
        REPLACE(
            businesscategoryname, 'None,', ''
        )
    ) AS cleaned
FROM brands
WHERE
    businesscategoryname LIKE 'None,%';

select count(username), businesscategoryname
from influencers
GROUP BY
    businesscategoryname
order by count(username) desc;

select username, businesscategoryname
from brands
where
    businesscategoryname = 'NaN';

SELECT DISTINCT
    businesscategoryname
FROM brands
WHERE
    businesscategoryname IS NOT NULL
    AND businesscategoryname NOT LIKE 'None,%'
    AND businesscategoryname != 'nan';

select * from influencer_recommendations limit 50

SELECT
    tu.username AS tagged_person,
    COUNT(*) AS tag_frequency
FROM
    influencers i
    JOIN posts p ON i.influencerid = p.ownerid
    JOIN posts_taggeduser ptu ON p.postid = ptu.postid
    JOIN taggeduser tu ON ptu.taggeduserid = tu.taggeduserid
WHERE
    i.username = 'nidarehmannn'
GROUP BY
    tu.username
ORDER BY tag_frequency DESC;
CREATE TABLE rising_stars (
	id BIGINT PRIMARY KEY,
	username VARCHAR(255) UNIQUE,
	followers_then BIGINT
	date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	
	
	FOREIGN KEY (id) REFERENCES influencers(influencerID)
);





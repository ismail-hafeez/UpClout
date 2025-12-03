--
-- PostgreSQL database dump
--

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: brands; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brands (
    brandid bigint NOT NULL,
    url character varying(255),
    name character varying(255),
    username character varying(255),
    postcount bigint,
    bio text,
    followers bigint,
    following bigint,
    profile_pic text,
    isverified boolean,
    isbusinessaccount boolean,
    businesscategoryname character varying(255),
    location character varying(255)
);


ALTER TABLE public.brands OWNER TO neondb_owner;

--
-- Name: hashtags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hashtags (
    hashtagid integer NOT NULL,
    tag_name character varying(255)
);


ALTER TABLE public.hashtags OWNER TO neondb_owner;

--
-- Name: hashtags_hashtagid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hashtags_hashtagid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hashtags_hashtagid_seq OWNER TO neondb_owner;

--
-- Name: hashtags_hashtagid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hashtags_hashtagid_seq OWNED BY public.hashtags.hashtagid;


--
-- Name: influencers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.influencers (
    influencerid bigint NOT NULL,
    url character varying(255),
    name character varying(255),
    username character varying(255),
    postcount bigint,
    bio text,
    followers bigint,
    following bigint,
    profile_pic text,
    isverified boolean,
    isbusinessaccount boolean,
    businesscategoryname character varying(255),
    location character varying(255)
);


ALTER TABLE public.influencers OWNER TO neondb_owner;

--
-- Name: posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.posts (
    postid bigint NOT NULL,
    type character varying(255),
    caption text,
    url character varying(255),
    commentscount integer,
    likescount integer,
    "timestamp" timestamp without time zone,
    issponsored boolean,
    ownerid bigint,
    ownerbrandid bigint
);


ALTER TABLE public.posts OWNER TO neondb_owner;

--
-- Name: posts_hashtags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.posts_hashtags (
    post_id bigint NOT NULL,
    hashtag_id integer NOT NULL
);


ALTER TABLE public.posts_hashtags OWNER TO neondb_owner;

--
-- Name: posts_taggeduser; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.posts_taggeduser (
    postid bigint NOT NULL,
    taggeduserid bigint NOT NULL
);


ALTER TABLE public.posts_taggeduser OWNER TO neondb_owner;

--
-- Name: reviews; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reviews (
    reviewid integer NOT NULL,
    review_date timestamp without time zone,
    comment text,
    reviewer_type character varying(255),
    reviewerid integer,
    reviewee_type character varying(255),
    revieweeid integer,
    rating integer
);


ALTER TABLE public.reviews OWNER TO neondb_owner;

--
-- Name: taggeduser; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.taggeduser (
    taggeduserid bigint NOT NULL,
    username character varying(255)
);


ALTER TABLE public.taggeduser OWNER TO neondb_owner;

--
-- Name: hashtags hashtagid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtags ALTER COLUMN hashtagid SET DEFAULT nextval('public.hashtags_hashtagid_seq'::regclass);


--
-- Name: brands brands_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brands
    ADD CONSTRAINT brands_pkey PRIMARY KEY (brandid);


--
-- Name: brands brands_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brands
    ADD CONSTRAINT brands_username_key UNIQUE (username);


--
-- Name: hashtags hashtags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtags
    ADD CONSTRAINT hashtags_pkey PRIMARY KEY (hashtagid);


--
-- Name: influencers influencers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.influencers
    ADD CONSTRAINT influencers_pkey PRIMARY KEY (influencerid);


--
-- Name: influencers influencers_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.influencers
    ADD CONSTRAINT influencers_username_key UNIQUE (username);


--
-- Name: posts_hashtags posts_hashtags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts_hashtags
    ADD CONSTRAINT posts_hashtags_pkey PRIMARY KEY (post_id, hashtag_id);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (postid);


--
-- Name: posts_taggeduser posts_taggeduser_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts_taggeduser
    ADD CONSTRAINT posts_taggeduser_pkey PRIMARY KEY (postid, taggeduserid);


--
-- Name: reviews reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (reviewid);


--
-- Name: taggeduser taggeduser_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.taggeduser
    ADD CONSTRAINT taggeduser_pkey PRIMARY KEY (taggeduserid);


--
-- Name: hashtags unique_tagname; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hashtags
    ADD CONSTRAINT unique_tagname UNIQUE (tag_name);


--
-- Name: posts fk_owner_influencer; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_owner_influencer FOREIGN KEY (ownerid) REFERENCES public.influencers(influencerid);


--
-- Name: posts fk_ownerbrandid; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_ownerbrandid FOREIGN KEY (ownerbrandid) REFERENCES public.brands(brandid);


--
-- Name: posts_hashtags posts_hashtags_hashtag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts_hashtags
    ADD CONSTRAINT posts_hashtags_hashtag_id_fkey FOREIGN KEY (hashtag_id) REFERENCES public.hashtags(hashtagid);


--
-- Name: posts_hashtags posts_hashtags_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts_hashtags
    ADD CONSTRAINT posts_hashtags_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(postid);


--
-- Name: posts_taggeduser posts_taggeduser_postid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts_taggeduser
    ADD CONSTRAINT posts_taggeduser_postid_fkey FOREIGN KEY (postid) REFERENCES public.posts(postid) ON DELETE CASCADE;


--
-- Name: posts_taggeduser posts_taggeduser_taggeduserid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts_taggeduser
    ADD CONSTRAINT posts_taggeduser_taggeduserid_fkey FOREIGN KEY (taggeduserid) REFERENCES public.taggeduser(taggeduserid) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--



--
-- PostgreSQL database dump
--

\restrict 1BccaGtvptffLxk9evpCMsEAe8A77VmNhS4rJF67mk2kQmrx2auWaYMAYo6Pp6G

-- Dumped from database version 15.18 (Debian 15.18-1.pgdg13+1)
-- Dumped by pg_dump version 17.9

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
-- Name: calibration_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.calibration_sessions (
    id integer NOT NULL,
    user_id integer,
    post_id integer,
    dut_serial character varying(64),
    origin_serial character varying(64),
    product_name character varying(64),
    dut_filename character varying(256),
    origin_filename character varying(256),
    tolerance_dbm double precision,
    overall_pass boolean,
    tx_total integer,
    tx_pass integer,
    tx_fail integer,
    tx_corrections integer,
    rx_total integer,
    rx_pass integer,
    rx_fail integer,
    avg_delta_dbm double precision,
    max_delta_dbm double precision,
    created_at timestamp(6) without time zone DEFAULT now() NOT NULL,
    notes character varying
);


ALTER TABLE public.calibration_sessions OWNER TO postgres;

--
-- Name: calibration_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.calibration_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.calibration_sessions_id_seq OWNER TO postgres;

--
-- Name: calibration_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.calibration_sessions_id_seq OWNED BY public.calibration_sessions.id;


--
-- Name: posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.posts (
    id integer NOT NULL,
    number integer NOT NULL,
    name character varying(32) NOT NULL,
    ip_address character varying(45),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.posts OWNER TO postgres;

--
-- Name: posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.posts_id_seq OWNER TO postgres;

--
-- Name: posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.posts_id_seq OWNED BY public.posts.id;


--
-- Name: rx_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rx_results (
    id integer NOT NULL,
    session_id integer NOT NULL,
    band character varying(16),
    block_number integer,
    freq_mhz integer,
    mcs character varying(32),
    bandwidth character varying(16),
    antenna_label character varying(8),
    origin_rssi double precision,
    dut_rssi double precision,
    origin_per double precision,
    dut_per double precision,
    status character varying(32)
);


ALTER TABLE public.rx_results OWNER TO postgres;

--
-- Name: rx_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rx_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rx_results_id_seq OWNER TO postgres;

--
-- Name: rx_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rx_results_id_seq OWNED BY public.rx_results.id;


--
-- Name: tx_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tx_results (
    id integer NOT NULL,
    session_id integer NOT NULL,
    band character varying(16),
    block_number integer,
    freq_mhz integer,
    modulation character varying(32),
    bandwidth character varying(16),
    antenna character varying(8),
    origin_dbm double precision,
    dut_dbm double precision,
    delta_dbm double precision,
    correction_dbm double precision,
    tx_target_dbm double precision,
    limit_lo double precision,
    limit_hi double precision,
    status character varying(32)
);


ALTER TABLE public.tx_results OWNER TO postgres;

--
-- Name: tx_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tx_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tx_results_id_seq OWNER TO postgres;

--
-- Name: tx_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tx_results_id_seq OWNED BY public.tx_results.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    matricule character varying(64) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(128),
    role character varying(32),
    created_at timestamp(6) without time zone,
    last_login timestamp(6) without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: calibration_sessions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calibration_sessions ALTER COLUMN id SET DEFAULT nextval('public.calibration_sessions_id_seq'::regclass);


--
-- Name: posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts ALTER COLUMN id SET DEFAULT nextval('public.posts_id_seq'::regclass);


--
-- Name: rx_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rx_results ALTER COLUMN id SET DEFAULT nextval('public.rx_results_id_seq'::regclass);


--
-- Name: tx_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tx_results ALTER COLUMN id SET DEFAULT nextval('public.tx_results_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: calibration_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.calibration_sessions (id, user_id, post_id, dut_serial, origin_serial, product_name, dut_filename, origin_filename, tolerance_dbm, overall_pass, tx_total, tx_pass, tx_fail, tx_corrections, rx_total, rx_pass, rx_fail, avg_delta_dbm, max_delta_dbm, created_at, notes) FROM stdin;
\.


--
-- Data for Name: posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.posts (id, number, name, ip_address, is_active, created_at) FROM stdin;
1	1	Caisson 1	\N	t	2026-06-06 18:28:18.672491
2	2	Caisson 2	\N	t	2026-06-06 18:28:18.672491
3	3	Caisson 3	\N	t	2026-06-06 18:28:18.672491
4	4	Caisson 4	\N	t	2026-06-06 18:28:18.672491
5	5	Caisson 5	\N	t	2026-06-06 18:28:18.672491
6	6	Caisson 6	\N	t	2026-06-06 18:28:18.672491
7	7	Caisson 7	\N	t	2026-06-06 18:28:18.672491
8	8	Caisson 8	\N	t	2026-06-06 18:28:18.672491
9	9	Caisson 9	\N	t	2026-06-06 18:28:18.672491
10	10	Caisson 10	\N	t	2026-06-06 18:28:18.672491
\.


--
-- Data for Name: rx_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rx_results (id, session_id, band, block_number, freq_mhz, mcs, bandwidth, antenna_label, origin_rssi, dut_rssi, origin_per, dut_per, status) FROM stdin;
\.


--
-- Data for Name: tx_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tx_results (id, session_id, band, block_number, freq_mhz, modulation, bandwidth, antenna, origin_dbm, dut_dbm, delta_dbm, correction_dbm, tx_target_dbm, limit_lo, limit_hi, status) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, matricule, password_hash, full_name, role, created_at, last_login) FROM stdin;
7	123456	$2b$10$xZOD0PNm/7zMvqsx3NUfnuvmoNfrPOGsekytCjwag719z2z0zHXsW	admin1	admin	\N	\N
8	0001	$2b$10$b/Msq38midh4Ql5lPcACZO06o9stGhSDDzWWITetU8ZfcJbJcFVIm	user1	operator	\N	2026-06-07 14:49:01.853714
\.


--
-- Name: calibration_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.calibration_sessions_id_seq', 1, true);


--
-- Name: posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.posts_id_seq', 10, true);


--
-- Name: rx_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rx_results_id_seq', 1, false);


--
-- Name: tx_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tx_results_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 8, true);


--
-- Name: calibration_sessions calibration_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calibration_sessions
    ADD CONSTRAINT calibration_sessions_pkey PRIMARY KEY (id);


--
-- Name: posts posts_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_number_key UNIQUE (number);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (id);


--
-- Name: rx_results rx_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rx_results
    ADD CONSTRAINT rx_results_pkey PRIMARY KEY (id);


--
-- Name: tx_results tx_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tx_results
    ADD CONSTRAINT tx_results_pkey PRIMARY KEY (id);


--
-- Name: users users_matricule_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_matricule_key UNIQUE (matricule);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

\unrestrict 1BccaGtvptffLxk9evpCMsEAe8A77VmNhS4rJF67mk2kQmrx2auWaYMAYo6Pp6G


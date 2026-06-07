--
-- PostgreSQL database dump
--

\restrict 0gQ4qoDupo7EDARBec450lfy1qVpiTKuTz3l72drJLbPwdctFQgtZwk9dZlKpp9

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
-- PostgreSQL database dump complete
--

\unrestrict 0gQ4qoDupo7EDARBec450lfy1qVpiTKuTz3l72drJLbPwdctFQgtZwk9dZlKpp9


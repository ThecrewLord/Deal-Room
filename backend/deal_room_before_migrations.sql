--
-- PostgreSQL database dump
--

\restrict y5QeQb4Tez08RfKAVEh0KLEP4od1g9nhnJPQuBQy6QYRlNZibbKvxVarLmIJa4F

-- Dumped from database version 15.18 (Homebrew)
-- Dumped by pg_dump version 15.18 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: accounts; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.accounts (
    account_id integer NOT NULL,
    account_name character varying(200) NOT NULL,
    industry character varying(100),
    website character varying(255),
    phone character varying(50),
    country character varying(100),
    state character varying(100),
    city character varying(100),
    address text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.accounts OWNER TO deekshithakarri;

--
-- Name: accounts_account_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.accounts_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.accounts_account_id_seq OWNER TO deekshithakarri;

--
-- Name: accounts_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.accounts_account_id_seq OWNED BY public.accounts.account_id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO deekshithakarri;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.audit_logs (
    audit_log_id integer NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id integer NOT NULL,
    action character varying(100) NOT NULL,
    description text,
    performed_by integer,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO deekshithakarri;

--
-- Name: audit_logs_audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.audit_logs_audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_audit_log_id_seq OWNER TO deekshithakarri;

--
-- Name: audit_logs_audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.audit_logs_audit_log_id_seq OWNED BY public.audit_logs.audit_log_id;


--
-- Name: contacts; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.contacts (
    contact_id integer NOT NULL,
    account_id integer NOT NULL,
    full_name character varying(150) NOT NULL,
    title character varying(100),
    email character varying(150),
    phone character varying(50),
    is_primary boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.contacts OWNER TO deekshithakarri;

--
-- Name: contacts_contact_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.contacts_contact_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.contacts_contact_id_seq OWNER TO deekshithakarri;

--
-- Name: contacts_contact_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.contacts_contact_id_seq OWNED BY public.contacts.contact_id;


--
-- Name: oem_partners; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.oem_partners (
    oem_partner_id integer NOT NULL,
    account_id integer NOT NULL,
    partner_name character varying(150) NOT NULL,
    product_name character varying(150) NOT NULL,
    contact_person character varying(150),
    email character varying(150),
    phone character varying(50),
    status character varying(50) NOT NULL,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.oem_partners OWNER TO deekshithakarri;

--
-- Name: oem_partners_oem_partner_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.oem_partners_oem_partner_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.oem_partners_oem_partner_id_seq OWNER TO deekshithakarri;

--
-- Name: oem_partners_oem_partner_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.oem_partners_oem_partner_id_seq OWNED BY public.oem_partners.oem_partner_id;


--
-- Name: opportunities; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.opportunities (
    opportunity_id integer NOT NULL,
    account_id integer NOT NULL,
    stage_id integer NOT NULL,
    opportunity_name character varying(200) NOT NULL,
    description text,
    estimated_value numeric(15,2),
    probability integer,
    expected_close_date date,
    status character varying(50) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.opportunities OWNER TO deekshithakarri;

--
-- Name: opportunities_opportunity_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.opportunities_opportunity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.opportunities_opportunity_id_seq OWNER TO deekshithakarri;

--
-- Name: opportunities_opportunity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.opportunities_opportunity_id_seq OWNED BY public.opportunities.opportunity_id;


--
-- Name: opportunity_team; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.opportunity_team (
    team_id integer NOT NULL,
    opportunity_id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(100) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.opportunity_team OWNER TO deekshithakarri;

--
-- Name: opportunity_team_team_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.opportunity_team_team_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.opportunity_team_team_id_seq OWNER TO deekshithakarri;

--
-- Name: opportunity_team_team_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.opportunity_team_team_id_seq OWNED BY public.opportunity_team.team_id;


--
-- Name: poc; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.poc (
    id integer NOT NULL,
    opportunity_id integer NOT NULL,
    objective text NOT NULL,
    success_metric text NOT NULL,
    target_date date NOT NULL,
    failure_condition text NOT NULL,
    stakeholder_signoff boolean NOT NULL,
    outcome character varying(20),
    outcome_notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.poc OWNER TO deekshithakarri;

--
-- Name: poc_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.poc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.poc_id_seq OWNER TO deekshithakarri;

--
-- Name: poc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.poc_id_seq OWNED BY public.poc.id;


--
-- Name: poc_tracker; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.poc_tracker (
    poc_id integer NOT NULL,
    opportunity_id integer NOT NULL,
    poc_name character varying(150) NOT NULL,
    start_date date,
    end_date date,
    status character varying(50) NOT NULL,
    remarks text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    objective text,
    success_metric text,
    target_date date,
    failure_condition text,
    stakeholder_signoff boolean DEFAULT false,
    outcome character varying(20),
    outcome_notes text
);


ALTER TABLE public.poc_tracker OWNER TO deekshithakarri;

--
-- Name: poc_tracker_poc_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.poc_tracker_poc_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.poc_tracker_poc_id_seq OWNER TO deekshithakarri;

--
-- Name: poc_tracker_poc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.poc_tracker_poc_id_seq OWNED BY public.poc_tracker.poc_id;


--
-- Name: stage_history; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.stage_history (
    history_id integer NOT NULL,
    opportunity_id integer NOT NULL,
    stage_id integer NOT NULL,
    changed_by integer,
    remarks text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.stage_history OWNER TO deekshithakarri;

--
-- Name: stage_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.stage_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stage_history_history_id_seq OWNER TO deekshithakarri;

--
-- Name: stage_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.stage_history_history_id_seq OWNED BY public.stage_history.history_id;


--
-- Name: stage_master; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.stage_master (
    stage_id integer NOT NULL,
    stage_name character varying(100) NOT NULL,
    display_order integer NOT NULL,
    requires_poc boolean NOT NULL,
    is_closed boolean NOT NULL,
    is_won boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.stage_master OWNER TO deekshithakarri;

--
-- Name: stage_master_stage_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.stage_master_stage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stage_master_stage_id_seq OWNER TO deekshithakarri;

--
-- Name: stage_master_stage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.stage_master_stage_id_seq OWNED BY public.stage_master.stage_id;


--
-- Name: stakeholders; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.stakeholders (
    stakeholder_id integer NOT NULL,
    opportunity_id integer NOT NULL,
    stakeholder_name character varying(150) NOT NULL,
    designation character varying(150),
    email character varying(150),
    phone character varying(50),
    influence_level character varying(50),
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.stakeholders OWNER TO deekshithakarri;

--
-- Name: stakeholders_stakeholder_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.stakeholders_stakeholder_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stakeholders_stakeholder_id_seq OWNER TO deekshithakarri;

--
-- Name: stakeholders_stakeholder_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.stakeholders_stakeholder_id_seq OWNED BY public.stakeholders.stakeholder_id;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.tags (
    tag_id integer NOT NULL,
    name character varying(100) NOT NULL,
    color character varying(20),
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.tags OWNER TO deekshithakarri;

--
-- Name: tags_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.tags_tag_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tags_tag_id_seq OWNER TO deekshithakarri;

--
-- Name: tags_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.tags_tag_id_seq OWNED BY public.tags.tag_id;


--
-- Name: token_blocklist; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.token_blocklist (
    id integer NOT NULL,
    jti character varying(255) NOT NULL,
    token_type character varying(20) NOT NULL,
    user_id integer NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    revoked_at timestamp without time zone NOT NULL
);


ALTER TABLE public.token_blocklist OWNER TO deekshithakarri;

--
-- Name: token_blocklist_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.token_blocklist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.token_blocklist_id_seq OWNER TO deekshithakarri;

--
-- Name: token_blocklist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.token_blocklist_id_seq OWNED BY public.token_blocklist.id;


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.user_roles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(50) NOT NULL
);


ALTER TABLE public.user_roles OWNER TO deekshithakarri;

--
-- Name: user_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.user_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_roles_id_seq OWNER TO deekshithakarri;

--
-- Name: user_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.user_roles_id_seq OWNED BY public.user_roles.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: deekshithakarri
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    full_name character varying(150) NOT NULL,
    email character varying(150) NOT NULL,
    password_hash character varying(255) NOT NULL,
    active boolean,
    manager_id integer,
    created_at timestamp without time zone,
    status character varying(20) DEFAULT 'PENDING'::character varying NOT NULL,
    last_login timestamp without time zone,
    approved_at timestamp without time zone,
    approved_by integer,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    auth_version integer DEFAULT 1
);


ALTER TABLE public.users OWNER TO deekshithakarri;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: deekshithakarri
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO deekshithakarri;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deekshithakarri
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: accounts account_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.accounts ALTER COLUMN account_id SET DEFAULT nextval('public.accounts_account_id_seq'::regclass);


--
-- Name: audit_logs audit_log_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN audit_log_id SET DEFAULT nextval('public.audit_logs_audit_log_id_seq'::regclass);


--
-- Name: contacts contact_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.contacts ALTER COLUMN contact_id SET DEFAULT nextval('public.contacts_contact_id_seq'::regclass);


--
-- Name: oem_partners oem_partner_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.oem_partners ALTER COLUMN oem_partner_id SET DEFAULT nextval('public.oem_partners_oem_partner_id_seq'::regclass);


--
-- Name: opportunities opportunity_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunities ALTER COLUMN opportunity_id SET DEFAULT nextval('public.opportunities_opportunity_id_seq'::regclass);


--
-- Name: opportunity_team team_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunity_team ALTER COLUMN team_id SET DEFAULT nextval('public.opportunity_team_team_id_seq'::regclass);


--
-- Name: poc id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.poc ALTER COLUMN id SET DEFAULT nextval('public.poc_id_seq'::regclass);


--
-- Name: poc_tracker poc_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.poc_tracker ALTER COLUMN poc_id SET DEFAULT nextval('public.poc_tracker_poc_id_seq'::regclass);


--
-- Name: stage_history history_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stage_history ALTER COLUMN history_id SET DEFAULT nextval('public.stage_history_history_id_seq'::regclass);


--
-- Name: stage_master stage_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stage_master ALTER COLUMN stage_id SET DEFAULT nextval('public.stage_master_stage_id_seq'::regclass);


--
-- Name: stakeholders stakeholder_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stakeholders ALTER COLUMN stakeholder_id SET DEFAULT nextval('public.stakeholders_stakeholder_id_seq'::regclass);


--
-- Name: tags tag_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.tags ALTER COLUMN tag_id SET DEFAULT nextval('public.tags_tag_id_seq'::regclass);


--
-- Name: token_blocklist id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.token_blocklist ALTER COLUMN id SET DEFAULT nextval('public.token_blocklist_id_seq'::regclass);


--
-- Name: user_roles id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.user_roles ALTER COLUMN id SET DEFAULT nextval('public.user_roles_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.accounts (account_id, account_name, industry, website, phone, country, state, city, address, is_active, created_at, updated_at) FROM stdin;
1	Dataeko Enterprise	Technology	https://dataeko.ai	\N	\N	\N	\N	\N	t	2026-08-04 11:54:15.030977	2026-08-04 11:54:15.030981
2	JFrog	DevSecOps	https://jfrog.com	\N	\N	\N	\N	\N	t	2026-08-04 11:54:15.030982	2026-08-04 11:54:15.030983
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.alembic_version (version_num) FROM stdin;
128d06af2ba3
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.audit_logs (audit_log_id, entity_type, entity_id, action, description, performed_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.contacts (contact_id, account_id, full_name, title, email, phone, is_primary, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: oem_partners; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.oem_partners (oem_partner_id, account_id, partner_name, product_name, contact_person, email, phone, status, notes, created_at, updated_at) FROM stdin;
1	1	JFrog	JFrog Platform	Partner Team	partner@jfrog.com	\N	Active	\N	2026-08-04 11:54:15.103035	2026-08-04 11:54:15.10304
2	1	IBM	IBM Instana	Partner Team	partner@ibm.com	\N	Active	\N	2026-08-04 11:54:15.103042	2026-08-04 11:54:15.103043
3	2	MeshIQ	MeshIQ Observe	Partner Team	partner@meshiq.com	\N	Active	\N	2026-08-04 11:54:15.103044	2026-08-04 11:54:15.103045
\.


--
-- Data for Name: opportunities; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.opportunities (opportunity_id, account_id, stage_id, opportunity_name, description, estimated_value, probability, expected_close_date, status, is_active, created_at, updated_at) FROM stdin;
1	2	2	JFrog Enterprise Rollout	Enterprise DevSecOps implementation	2500000.00	40	\N	Open	t	2026-08-04 11:54:15.043034	2026-08-04 11:54:15.043036
\.


--
-- Data for Name: opportunity_team; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.opportunity_team (team_id, opportunity_id, user_id, role, created_at, updated_at) FROM stdin;
1	1	2	Sales	2026-08-14 00:59:19.41684	2026-08-14 00:59:19.416846
\.


--
-- Data for Name: poc; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.poc (id, opportunity_id, objective, success_metric, target_date, failure_condition, stakeholder_signoff, outcome, outcome_notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: poc_tracker; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.poc_tracker (poc_id, opportunity_id, poc_name, start_date, end_date, status, remarks, created_at, updated_at, objective, success_metric, target_date, failure_condition, stakeholder_signoff, outcome, outcome_notes) FROM stdin;
\.


--
-- Data for Name: stage_history; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.stage_history (history_id, opportunity_id, stage_id, changed_by, remarks, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: stage_master; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.stage_master (stage_id, stage_name, display_order, requires_poc, is_closed, is_won, created_at, updated_at) FROM stdin;
2	Lead	1	f	f	f	2026-08-03 14:29:36.882644	2026-08-03 14:29:36.882644
\.


--
-- Data for Name: stakeholders; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.stakeholders (stakeholder_id, opportunity_id, stakeholder_name, designation, email, phone, influence_level, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.tags (tag_id, name, color, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: token_blocklist; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.token_blocklist (id, jti, token_type, user_id, expires_at, revoked_at) FROM stdin;
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.user_roles (id, user_id, role) FROM stdin;
1	1	Admin
2	3	Delivery
3	3	Solution Engineer
4	2	Sales
5	5	Sales
6	7	Sales Manager
7	8	Pre-Sales Manager
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: deekshithakarri
--

COPY public.users (user_id, full_name, email, password_hash, active, manager_id, created_at, status, last_login, approved_at, approved_by, updated_at, auth_version) FROM stdin;
4	luna	l.una@dataeko.ai	pbkdf2:sha256:1000000$u1Z1NMyis9sxGI3o$94eafcd059dc7a6fa39f10df4ebff47f44d5bade0b96b3c6f25dc12d6789440e	t	\N	2026-08-13 05:02:43.828376	PENDING	\N	\N	\N	2026-08-13 05:02:43.828384	1
3	deekshitha	d.karri@dataeko.ai	pbkdf2:sha256:1000000$7bHvhfMLCnSq8xPH$c0046239df8e8b7a55ff705e1a014fee7d280006fad2b88b7fb76f17a3304a81	t	\N	2026-08-12 18:38:28.151699	APPROVED	\N	\N	\N	2026-08-13 10:09:56.699256	1
7	Sales Manager	sales.manager@dealroom.local	pbkdf2:sha256:1000000$lDFOkddIoGzgMRDk$cc6e4f8fbab591506d4bb33faa665e0cceb3ca141ac4530aca5d0133ce4878c0	t	\N	2026-08-19 06:26:38.081125	APPROVED	2026-08-19 09:06:51.437197	2026-08-19 06:26:38.080205	\N	2026-08-19 09:06:51.439274	1
2	sam	s.am@dataeko.ai	pbkdf2:sha256:1000000$JlgRaCY2qgG2Mvcd$c4befa2e968fd11062978c22c4f01a0db5c729edc0ce3a418c75df4258c5823e	t	\N	2026-08-12 18:38:01.496164	APPROVED	2026-08-14 02:59:52.127296	\N	\N	2026-08-14 02:59:52.127951	1
1	deekshitha	kdeekshitha61261@gmail.com	pbkdf2:sha256:1000000$DGX8eXjTpwk4vzsx$49f69639286643dd9dd7e95ffd5684b90650c5b477b390d85e71924d198e2d7e	t	\N	2026-08-12 18:37:29.256287	APPROVED	2026-08-18 16:58:39.106046	2026-08-12 18:37:29.252173	\N	2026-08-18 16:58:39.106491	1
5	beta	beta@dataeko.ai	pbkdf2:sha256:1000000$cHwELRJTzFZsormf$c2e3795919911b3298375bf29c6225cd0660c692bff3b5d3da74b5a0ecd1edd7	t	\N	2026-08-13 10:12:11.633701	APPROVED	2026-08-19 05:32:57.074374	\N	\N	2026-08-19 05:32:57.075642	1
6	Test User	testuser123@dataeko.ai	pbkdf2:sha256:1000000$RWx36YP1wtSB3FHm$302bd2e0ceee8f0961790a37c64a7fc1a5cf8be36a9f5dc151801321c81a3aab	t	\N	2026-08-19 06:02:18.63435	PENDING	\N	\N	\N	2026-08-19 06:02:18.634896	1
8	Pre-Sales Manager	presales.manager@dealroom.local	pbkdf2:sha256:1000000$WbyUkM4Pcwwx5Acs$577256255d13164d6c8d817aff2ed3ab6f7be8bd1b4f00cfa972ccfbca71e17d	t	\N	2026-08-19 06:27:19.773511	APPROVED	\N	2026-08-19 06:27:19.772755	\N	2026-08-19 06:27:19.773513	1
\.


--
-- Name: accounts_account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.accounts_account_id_seq', 2, true);


--
-- Name: audit_logs_audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.audit_logs_audit_log_id_seq', 1, false);


--
-- Name: contacts_contact_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.contacts_contact_id_seq', 1, false);


--
-- Name: oem_partners_oem_partner_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.oem_partners_oem_partner_id_seq', 3, true);


--
-- Name: opportunities_opportunity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.opportunities_opportunity_id_seq', 1, true);


--
-- Name: opportunity_team_team_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.opportunity_team_team_id_seq', 1, true);


--
-- Name: poc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.poc_id_seq', 1, false);


--
-- Name: poc_tracker_poc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.poc_tracker_poc_id_seq', 1, false);


--
-- Name: stage_history_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.stage_history_history_id_seq', 1, false);


--
-- Name: stage_master_stage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.stage_master_stage_id_seq', 2, true);


--
-- Name: stakeholders_stakeholder_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.stakeholders_stakeholder_id_seq', 1, false);


--
-- Name: tags_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.tags_tag_id_seq', 1, false);


--
-- Name: token_blocklist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.token_blocklist_id_seq', 1, false);


--
-- Name: user_roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.user_roles_id_seq', 7, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: deekshithakarri
--

SELECT pg_catalog.setval('public.users_user_id_seq', 8, true);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (account_id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (audit_log_id);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (contact_id);


--
-- Name: oem_partners oem_partners_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.oem_partners
    ADD CONSTRAINT oem_partners_pkey PRIMARY KEY (oem_partner_id);


--
-- Name: opportunities opportunities_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_pkey PRIMARY KEY (opportunity_id);


--
-- Name: opportunity_team opportunity_team_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunity_team
    ADD CONSTRAINT opportunity_team_pkey PRIMARY KEY (team_id);


--
-- Name: poc poc_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.poc
    ADD CONSTRAINT poc_pkey PRIMARY KEY (id);


--
-- Name: poc_tracker poc_tracker_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.poc_tracker
    ADD CONSTRAINT poc_tracker_pkey PRIMARY KEY (poc_id);


--
-- Name: stage_history stage_history_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stage_history
    ADD CONSTRAINT stage_history_pkey PRIMARY KEY (history_id);


--
-- Name: stage_master stage_master_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stage_master
    ADD CONSTRAINT stage_master_pkey PRIMARY KEY (stage_id);


--
-- Name: stakeholders stakeholders_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stakeholders
    ADD CONSTRAINT stakeholders_pkey PRIMARY KEY (stakeholder_id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (tag_id);


--
-- Name: token_blocklist token_blocklist_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT token_blocklist_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: ix_accounts_account_name; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE UNIQUE INDEX ix_accounts_account_name ON public.accounts USING btree (account_name);


--
-- Name: ix_oem_partners_account_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_oem_partners_account_id ON public.oem_partners USING btree (account_id);


--
-- Name: ix_opportunities_account_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_opportunities_account_id ON public.opportunities USING btree (account_id);


--
-- Name: ix_opportunities_stage_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_opportunities_stage_id ON public.opportunities USING btree (stage_id);


--
-- Name: ix_opportunity_team_opportunity_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_opportunity_team_opportunity_id ON public.opportunity_team USING btree (opportunity_id);


--
-- Name: ix_opportunity_team_user_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_opportunity_team_user_id ON public.opportunity_team USING btree (user_id);


--
-- Name: ix_poc_tracker_opportunity_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_poc_tracker_opportunity_id ON public.poc_tracker USING btree (opportunity_id);


--
-- Name: ix_stage_history_opportunity_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_stage_history_opportunity_id ON public.stage_history USING btree (opportunity_id);


--
-- Name: ix_stage_history_stage_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_stage_history_stage_id ON public.stage_history USING btree (stage_id);


--
-- Name: ix_stage_master_stage_name; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE UNIQUE INDEX ix_stage_master_stage_name ON public.stage_master USING btree (stage_name);


--
-- Name: ix_stakeholders_opportunity_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_stakeholders_opportunity_id ON public.stakeholders USING btree (opportunity_id);


--
-- Name: ix_tags_name; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE UNIQUE INDEX ix_tags_name ON public.tags USING btree (name);


--
-- Name: ix_token_blocklist_jti; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE UNIQUE INDEX ix_token_blocklist_jti ON public.token_blocklist USING btree (jti);


--
-- Name: ix_token_blocklist_user_id; Type: INDEX; Schema: public; Owner: deekshithakarri
--

CREATE INDEX ix_token_blocklist_user_id ON public.token_blocklist USING btree (user_id);


--
-- Name: contacts contacts_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE CASCADE;


--
-- Name: oem_partners oem_partners_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.oem_partners
    ADD CONSTRAINT oem_partners_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(account_id);


--
-- Name: opportunities opportunities_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(account_id);


--
-- Name: opportunities opportunities_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.stage_master(stage_id);


--
-- Name: opportunity_team opportunity_team_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunity_team
    ADD CONSTRAINT opportunity_team_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(opportunity_id);


--
-- Name: opportunity_team opportunity_team_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.opportunity_team
    ADD CONSTRAINT opportunity_team_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: poc_tracker poc_tracker_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.poc_tracker
    ADD CONSTRAINT poc_tracker_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(opportunity_id);


--
-- Name: stage_history stage_history_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stage_history
    ADD CONSTRAINT stage_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(user_id);


--
-- Name: stage_history stage_history_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stage_history
    ADD CONSTRAINT stage_history_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(opportunity_id);


--
-- Name: stage_history stage_history_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stage_history
    ADD CONSTRAINT stage_history_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES public.stage_master(stage_id);


--
-- Name: stakeholders stakeholders_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.stakeholders
    ADD CONSTRAINT stakeholders_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(opportunity_id);


--
-- Name: token_blocklist token_blocklist_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.token_blocklist
    ADD CONSTRAINT token_blocklist_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: users users_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: deekshithakarri
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES public.users(user_id);


--
-- PostgreSQL database dump complete
--

\unrestrict y5QeQb4Tez08RfKAVEh0KLEP4od1g9nhnJPQuBQy6QYRlNZibbKvxVarLmIJa4F


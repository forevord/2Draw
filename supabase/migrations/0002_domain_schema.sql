-- ── brands ────────────────────────────────────────────────────────────────────
create table if not exists public.brands (
    id      uuid    primary key default gen_random_uuid(),
    name    text    not null unique,
    region  text    not null check (region in ('eu', 'cis', 'global')),
    url     text    null,
    active  boolean not null default true
);

comment on table  public.brands            is 'Paint manufacturers (Winsor & Newton, Liquitex, Nevskaya…).';
comment on column public.brands.region     is 'eu | cis | global — primary market for this brand.';
comment on column public.brands.url        is 'Brand shop homepage for the Search Agent.';

-- ── paints ────────────────────────────────────────────────────────────────────
create table if not exists public.paints (
    id           uuid           primary key default gen_random_uuid(),
    brand_id     uuid           not null references public.brands (id),
    name         text           not null,
    color_index  text           null,       -- pigment code e.g. "PB29"
    hex          text           not null,   -- "#1A2B3C"
    lab_l        numeric(6, 3)  not null,   -- L*  0.000–100.000
    lab_a        numeric(6, 3)  not null,   -- a* −128.000–127.000
    lab_b        numeric(6, 3)  not null,   -- b* −128.000–127.000
    region       text           not null check (region in ('eu', 'cis', 'global'))
);

comment on table  public.paints            is 'Individual paint products with LAB color data for delta-E CIE76 matching.';
comment on column public.paints.color_index is 'Pigment code (Color Index Name), e.g. PB29 for Ultramarine.';
comment on column public.paints.lab_l      is 'CIE L* lightness, 0–100.';
comment on column public.paints.lab_a      is 'CIE a* green-red axis, −128–127.';
comment on column public.paints.lab_b      is 'CIE b* blue-yellow axis, −128–127.';

-- Indexes for the Color Match Agent (PS-06)
create index if not exists paints_brand_id_idx     on public.paints (brand_id);
create index if not exists paints_region_idx        on public.paints (region);
create index if not exists paints_lab_idx           on public.paints (lab_l, lab_a, lab_b);

-- ── exports ───────────────────────────────────────────────────────────────────
create table if not exists public.exports (
    id                uuid        primary key default gen_random_uuid(),
    user_email        text        null,       -- set on Stripe checkout
    status            text        not null default 'pending'
                                  check (status in ('pending', 'processing', 'complete', 'failed', 'paid')),
    stripe_session_id text        unique,     -- for webhook idempotency
    pdf_url           text        null,       -- signed Cloudflare R2 URL after generation
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

comment on table  public.exports                   is 'One row per user PDF export — tracks payment and delivery.';
comment on column public.exports.user_email        is 'Collected at Stripe checkout; used for RLS and email delivery.';
comment on column public.exports.stripe_session_id is 'Stripe Checkout Session ID; unique index ensures idempotent webhook handling.';
comment on column public.exports.pdf_url           is 'Signed Cloudflare R2 URL, valid 24 h after generation.';
comment on column public.exports.status            is 'pending | processing | complete | failed | paid';

-- Reuse trigger function defined in 0001_initial_schema.sql
create trigger exports_set_updated_at
    before update on public.exports
    for each row
    execute function public.set_updated_at();

-- ── Row Level Security — exports ──────────────────────────────────────────────
alter table public.exports enable row level security;

-- Authenticated users see only their own exports (matched by email from JWT)
create policy "users see own exports"
    on public.exports
    for select
    using (auth.jwt() ->> 'email' = user_email);

-- Service role bypasses RLS by default — no additional policy needed.

-- ── No RLS on public catalog tables ──────────────────────────────────────────
-- brands and paints are read-only reference data; no RLS required.
-- The service role (FastAPI) will write to them during the seeding step (PS-03).

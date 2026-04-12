-- Enable the pgcrypto extension for gen_random_uuid()
create extension if not exists "pgcrypto";

-- ── jobs ──────────────────────────────────────────────────────────────────────
create table if not exists public.jobs (
    id          uuid        primary key default gen_random_uuid(),
    user_id     uuid        null,           -- nullable: anonymous users allowed
    status      text        not null default 'pending'
                            check (status in ('pending', 'processing', 'complete', 'failed')),
    settings    jsonb       not null default '{}',
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- Auto-update updated_at on any row modification
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger jobs_set_updated_at
    before update on public.jobs
    for each row
    execute function public.set_updated_at();

-- ── Row Level Security ────────────────────────────────────────────────────────
alter table public.jobs enable row level security;

-- Authenticated users can see only their own jobs
create policy "users see own jobs"
    on public.jobs
    for select
    using (auth.uid() = user_id);

-- Authenticated users can insert their own jobs (or anonymous with null user_id)
create policy "users insert own jobs"
    on public.jobs
    for insert
    with check (auth.uid() = user_id or user_id is null);

-- Service role bypasses RLS by default — no additional policy needed.

comment on table public.jobs is 'One row per paint-by-number generation job.';
comment on column public.jobs.settings is 'User-selected options: style, zone count, brand, language.';
comment on column public.jobs.status is 'pending | processing | complete | failed';

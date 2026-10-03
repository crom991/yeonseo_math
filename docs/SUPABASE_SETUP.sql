create table if not exists public.math_sessions (
  id text primary key,
  completed_at timestamptz not null,
  local_date date not null,
  domain text not null,
  start_level integer not null,
  final_level integer not null,
  recommended_level integer not null,
  attempted integer not null,
  correct integer not null,
  accuracy numeric not null,
  elapsed_seconds integer not null,
  feeling text not null default '',
  telegram_sent_at timestamptz,
  records jsonb not null default '[]'::jsonb
);

create index if not exists math_sessions_completed_at_idx
  on public.math_sessions (completed_at desc);

create table if not exists public.math_settings (
  id text primary key,
  settings jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.math_sessions enable row level security;
alter table public.math_settings enable row level security;

alter table sessions add column profile_id text not null default 'yeonseo'
  check (profile_id in ('yeonseo', 'haeun'));

create index if not exists sessions_profile_completed_at_idx
  on sessions (profile_id, completed_at desc);

insert into settings (id, settings_json, updated_at)
select 'yeonseo', settings_json, updated_at
from settings
where id = 'family'
on conflict(id) do nothing;

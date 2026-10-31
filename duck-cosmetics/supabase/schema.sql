-- Duck Connect private storage. Run once in the project's SQL Editor.
-- Public clients use the Vercel relay; no browser/mod receives a database key.
begin;
create schema if not exists duck_relay_private;
revoke all on schema duck_relay_private from public, anon, authenticated;
create table if not exists duck_relay_private.entries (
 key text primary key check (key like 'duck:%' and length(key)<=512),
 kind text not null check(kind in ('string','list','zset')),
 value jsonb not null,
 expires_at timestamptz
);
create index if not exists duck_relay_expiry on duck_relay_private.entries(expires_at) where expires_at is not null;
create table if not exists duck_relay_private.members (
 key text not null references duck_relay_private.entries(key) on delete cascade,
 member text not null check(length(member)<=128),score double precision not null,
 primary key(key,member)
);
create index if not exists duck_relay_scores on duck_relay_private.members(key,score);
alter table duck_relay_private.entries enable row level security;
alter table duck_relay_private.members enable row level security;
revoke all on all tables in schema duck_relay_private from public, anon, authenticated;

create or replace function public.duck_pipeline(p_commands jsonb) returns jsonb
language plpgsql security definer
set search_path = pg_catalog, duck_relay_private
as $function$
declare
 cmd jsonb; op text; k text; result jsonb; output jsonb:='[]'::jsonb;
 row_value jsonb; row_kind text; expiry timestamptz; expiry_value timestamptz;
 now_value timestamptz:=clock_timestamp(); option_name text; only_missing boolean;
 i int; n bigint; a int; b int; score_value double precision; member_value text;
 item jsonb; lower_score double precision; upper_score double precision;
begin
 if jsonb_typeof(p_commands) <> 'array' or jsonb_array_length(p_commands) not between 1 and 32 then raise exception 'Invalid command batch' using errcode='22023'; end if;
 -- Small atomic relay transactions. Never expose arbitrary SQL or Redis commands.
 perform pg_advisory_xact_lock(834709621442::bigint);
 delete from entries where key in (select key from entries where expires_at<=now_value limit 128);
 for cmd in select value from jsonb_array_elements(p_commands) loop
  if jsonb_typeof(cmd)<>'array' or jsonb_array_length(cmd) not between 1 and 40 then raise exception 'Invalid relay command' using errcode='22023'; end if;
  op:=upper(cmd->>0);result:='null'::jsonb;
  if op='PING' then result:='"PONG"'::jsonb;
  elsif op='MGET' then
   result:='[]'::jsonb;
   if jsonb_array_length(cmd)>33 then raise exception 'Too many profiles' using errcode='22023'; end if;
   for i in 1..jsonb_array_length(cmd)-1 loop
    k:=cmd->>i;
    if k is null or k not like 'duck:%' or length(k)>512 then raise exception 'Invalid key' using errcode='22023'; end if;
    select value into row_value from entries where key=k and kind='string' and (expires_at is null or expires_at>now_value);
    result:=result||jsonb_build_array(coalesce(row_value,'null'::jsonb));
   end loop;
  else
   k:=cmd->>1;
   if k is null or k not like 'duck:%' or length(k)>512 then raise exception 'Invalid key' using errcode='22023'; end if;
   delete from entries where key=k and expires_at<=now_value;
   row_value:=null;row_kind:=null;expiry:=null;
   select value,kind,expires_at into row_value,row_kind,expiry from entries where key=k;
   case op
   when 'SET' then
    only_missing:=false;expiry_value:=null;i:=3;
    if jsonb_array_length(cmd)<3 or length(cmd->>2)>16384 then raise exception 'Invalid value' using errcode='22023'; end if;
    while i<jsonb_array_length(cmd) loop
     option_name:=upper(cmd->>i);
     if option_name='NX' then only_missing:=true;
     elsif option_name in ('EX','PX') then
      i:=i+1;n:=(cmd->>i)::bigint;
      if n<1 or n>86400000 then raise exception 'Invalid expiry' using errcode='22023'; end if;
      expiry_value:=now_value+make_interval(secs=>n::double precision/(case when option_name='PX' then 1000 else 1 end));
     else raise exception 'Invalid option' using errcode='22023'; end if;
     i:=i+1;
    end loop;
    if not only_missing or row_kind is null then
     delete from members where key=k;
     insert into entries(key,kind,value,expires_at) values(k,'string',to_jsonb(cmd->>2),expiry_value)
      on conflict(key) do update set kind='string',value=excluded.value,expires_at=excluded.expires_at;
     result:='"OK"'::jsonb;
    end if;
   when 'GET','GETDEL' then
    if row_kind is not null and row_kind<>'string' then raise exception 'Wrong value type' using errcode='22023'; end if;
    result:=coalesce(row_value,'null'::jsonb);
    if op='GETDEL' then delete from entries where key=k; end if;
   when 'INCR' then
    if row_kind is not null and row_kind<>'string' then raise exception 'Wrong value type' using errcode='22023'; end if;
    n:=coalesce((row_value#>>'{}')::bigint,0)+1;
    insert into entries(key,kind,value,expires_at) values(k,'string',to_jsonb(n::text),null)
     on conflict(key) do update set value=excluded.value;
    result:=to_jsonb(n);
   when 'EXPIRE' then
    n:=(cmd->>2)::bigint;
    if n<1 or n>86400 then raise exception 'Invalid expiry' using errcode='22023'; end if;
    if row_kind is not null and (jsonb_array_length(cmd)=3 or (upper(cmd->>3)='NX' and expiry is null)) then
     update entries set expires_at=now_value+make_interval(secs=>n) where key=k;result:='1'::jsonb;
    else result:='0'::jsonb;end if;
   when 'ZADD' then
    if row_kind is not null and row_kind<>'zset' then raise exception 'Wrong value type' using errcode='22023'; end if;
    score_value:=(cmd->>2)::double precision;member_value:=cmd->>3;
    if member_value is null or length(member_value)>128 or score_value in ('Infinity'::float8,'-Infinity'::float8,'NaN'::float8) then raise exception 'Invalid member' using errcode='22023';end if;
    insert into entries(key,kind,value) values(k,'zset','{}') on conflict do nothing;
    perform 1 from members where key=k and member=member_value;
    result:=case when found then '0'::jsonb else '1'::jsonb end;
    insert into members(key,member,score) values(k,member_value,score_value)
     on conflict(key,member) do update set score=excluded.score;
   when 'ZREMRANGEBYSCORE' then
    lower_score:=case when cmd->>2='-inf' then '-Infinity'::float8 else (cmd->>2)::float8 end;
    upper_score:=case when cmd->>3='+inf' then 'Infinity'::float8 else (cmd->>3)::float8 end;
    delete from members where key=k and score between lower_score and upper_score;
    get diagnostics n=row_count;result:=to_jsonb(n);
   when 'ZCARD' then select count(*) into n from members where key=k;result:=to_jsonb(n);
   when 'LPUSH' then
    if row_kind is not null and row_kind<>'list' then raise exception 'Wrong value type' using errcode='22023'; end if;
    row_value:=jsonb_build_array(cmd->>2)||coalesce(row_value,'[]'::jsonb);
    if jsonb_array_length(row_value)>128 then raise exception 'List exceeds bound' using errcode='22023';end if;
    insert into entries(key,kind,value,expires_at) values(k,'list',row_value,null)
     on conflict(key) do update set value=excluded.value;
    result:=to_jsonb(jsonb_array_length(row_value));
   when 'LRANGE','LTRIM' then
    if row_kind is not null and row_kind<>'list' then raise exception 'Wrong value type' using errcode='22023';end if;
    a:=(cmd->>2)::int;b:=(cmd->>3)::int;
    if a<0 or b<a or b>127 then raise exception 'Invalid list range' using errcode='22023';end if;
    select coalesce(jsonb_agg(value order by ord),'[]'::jsonb) into result
     from jsonb_array_elements(coalesce(row_value,'[]'::jsonb)) with ordinality as e(value,ord) where ord between a+1 and b+1;
    if op='LTRIM' then
     if row_kind is not null then update entries set value=result where key=k;end if;result:='"OK"'::jsonb;
    end if;
   else raise exception 'Unsupported relay command' using errcode='22023';
   end case;
  end if;
  output:=output||jsonb_build_array(jsonb_build_object('result',result));
 end loop;
 return output;
end
$function$;
revoke all on function public.duck_pipeline(jsonb) from public, anon, authenticated;
grant execute on function public.duck_pipeline(jsonb) to service_role;
commit;

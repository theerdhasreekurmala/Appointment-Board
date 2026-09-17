import os
from sqlalchemy import create_engine, MetaData, Table, select

sqlite_url = 'sqlite:///appointments.db'
pg_url = os.environ.get('DATABASE_URL')

if not pg_url:
    print('ERROR: Set DATABASE_URL environment variable to your Postgres URL first.')
    print("Example: $env:DATABASE_URL = 'postgresql://appt_user:strongpassword@localhost:5432/appointmentdb'")
    raise SystemExit(1)

e_sql = create_engine(sqlite_url)
e_pg = create_engine(pg_url)

md_sql = MetaData()
md_pg = MetaData()

tbl_sql = Table('appointments', md_sql, autoload_with=e_sql)
tbl_pg = Table('appointments', md_pg, autoload_with=e_pg)

with e_sql.connect() as cs, e_pg.connect() as cp:
    rows = cs.execute(select(tbl_sql)).mappings().all()
    existing_ids = {r[0] for r in cp.execute(select(tbl_pg.c.id)).fetchall()}
    to_insert = [dict(r) for r in rows if r['id'] not in existing_ids]
    if not to_insert:
        print('No new rows to migrate.')
    else:
        print(f'Migrating {len(to_insert)} rows...')
        for r in to_insert:
            # remove SQLAlchemy Row mapping proxies if any
            cp.execute(tbl_pg.insert().values(**r))
        print('Migration complete.')

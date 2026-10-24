"""Non-destructive local upgrade. Original database and runtime config are retained."""
import json
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit

import psycopg
from psycopg import sql

root=Path(__file__).resolve().parents[1]
runtime_path=root/'.local/runtime.json'
config=json.loads(runtime_path.read_text())

def database_url(value,name):
    parsed=urlsplit(value)
    return urlunsplit(parsed._replace(path='/'+name))

with psycopg.connect(config['adminUrl'],client_encoding='utf8') as source:
    encoding=source.execute('SHOW server_encoding').fetchone()[0]
    old_name=source.execute('SELECT current_database()').fetchone()[0]
    if encoding=='UTF8':
        print('Database already uses UTF-8.');raise SystemExit(0)
    target_name='inkloom_utf8'
    with psycopg.connect(database_url(config['adminUrl'],'postgres'),autocommit=True) as control:
        if control.execute('SELECT 1 FROM pg_database WHERE datname=%s',(target_name,)).fetchone():
            raise RuntimeError('UTF-8 target already exists. Inspect it before retrying; no data was overwritten.')
        control.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'").format(sql.Identifier(target_name)))
    target_url=database_url(config['adminUrl'],target_name)
    with psycopg.connect(target_url,client_encoding='utf8') as dest:
        dest.execute((root/'services/api/app/schema.sql').read_text(encoding='utf-8'))
        dest.execute("CREATE TABLE schema_migrations (name text PRIMARY KEY,applied_at timestamptz NOT NULL DEFAULT now())")
        for migration in sorted((root/'services/api/migrations').glob('*.sql')):
            dest.execute(migration.read_text(encoding='utf-8'))
        dest.execute('SET CONSTRAINTS ALL DEFERRED')
        tables=['users','verification_tokens','sessions','organisations','memberships','invitations','guideline_versions','source_documents','structured_rules','audit_events','diagnostic_runs','drafts','draft_versions','ai_processing_consents','review_runs','review_events','ai_request_usage','approval_requests','approval_decisions','review_comments','brand_assets','schema_migrations']
        counts={}
        for table in tables:
            exists=source.execute('SELECT to_regclass(%s)',(table,)).fetchone()[0]
            if not exists:continue
            query=sql.SQL("COPY {} TO STDOUT WITH (FORMAT CSV,ENCODING 'UTF8')").format(sql.Identifier(table))
            write=sql.SQL("COPY {} FROM STDIN WITH (FORMAT CSV,ENCODING 'UTF8')").format(sql.Identifier(table))
            with source.cursor().copy(query) as outgoing,dest.cursor().copy(write) as incoming:
                for block in outgoing:incoming.write(block)
            count=source.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
            assert dest.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]==count
            counts[table]=count
    backup=root/'.local/runtime-before-utf8.json'
    if not backup.exists():backup.write_text(json.dumps(config,indent=2))
    config['adminUrl']=target_url
    config['databaseUrl']=database_url(config['databaseUrl'],target_name)
    runtime_path.write_text(json.dumps(config,indent=2))
    (root/'.local/test-results/utf8-migration.json').write_text(json.dumps({'source_retained':old_name,'target':target_name,'encoding':'UTF8','verified_row_counts':counts},indent=2))
    print('Copied all application records and verified row counts. Original database retained. Runtime now selects UTF-8.')

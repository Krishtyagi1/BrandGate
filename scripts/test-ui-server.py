"""Isolated UI test server. Explicit provider double, synthetic data, separate DB."""
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
runtime=json.loads((ROOT/'.local/runtime.json').read_text())
os.environ['DATABASE_URL']=runtime['databaseUrl'].rsplit('/',1)[0]+'/inkloom_test_utf8'
os.environ['DATABASE_ADMIN_URL']=runtime['adminUrl'].rsplit('/',1)[0]+'/inkloom_test_utf8'
os.environ['WEB_ORIGIN']='http://127.0.0.1:3001'
from app.main import app
from app.review_models import ReviewResponse,RewriteResponse
from app.rewrites import RewriteJudge
from providers import openrouter

def synthetic_complete(system,payload,schema,purpose='review',usage_callback=None):
    metadata={'model':'SYNTHETIC_TEST_DOUBLE','provider':'Offline UI fixture; no external AI request'}
    if schema is ReviewResponse:return ReviewResponse(findings=[]),metadata
    if schema is RewriteResponse:return RewriteResponse(minimal='daily',natural='gentle'),metadata
    if schema is RewriteJudge:return RewriteJudge(minimal_safe=True,natural_safe=True,reason='Synthetic UI fixture'),metadata
    raise AssertionError('Unexpected test schema')
openrouter.complete=synthetic_complete
openrouter.settings=lambda:{'OPENROUTER_API_KEY':'synthetic-test-key','OPENROUTER_MODEL':'synthetic/model:free'}
import uvicorn
uvicorn.run(app,host='127.0.0.1',port=8001,log_level='warning')

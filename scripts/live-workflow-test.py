"""Bounded live P0 validation using fictional material and two automated accounts."""
import json
import time
from pathlib import Path
from uuid import uuid4

import httpx

owner=httpx.Client(base_url='http://127.0.0.1:8000/api',headers={'X-Inkloom-CSRF':'1'},timeout=20)
report={'kind':'Synthetic live end-to-end workflow','checks':[],'provider_attempts':[],'human_feedback':'Two automated accounts; no independent human feedback or sign-off.'}
def post(client,path,data=None):
    response=client.post(path,json=data)
    response.raise_for_status();return response.json()
def record(name,passed):report['checks'].append({'name':name,'passed':bool(passed)})
def wait(run):
    for _ in range(200):
        run=owner.get(f"{base}/review-runs/{run['id']}").json()
        if run['status'] not in ('queued','running'):return run
        time.sleep(1)
    return run
def review(draft_id,version_id):
    for attempt in range(2):
        preview=owner.get(f'{base}/drafts/{draft_id}/ai-preview').json()
        run=wait(post(owner,f'{base}/drafts/{draft_id}/reviews',{'version_id':version_id,'preview_hash':preview['preview_hash'],'idempotency_key':str(uuid4())}))
        report['provider_attempts'].append({'run_id':run['id'],'kind':'review','status':run['status'],'error':run.get('error'),'metadata':run['result'].get('metadata')})
        if run['status']=='completed':return run,preview
        if attempt==0:time.sleep(10)
    raise RuntimeError(run.get('error') or 'Provider unavailable')
try:
    email=f'workflow-live-{uuid4().hex}@example.com';password='Synthetic workflow account 123!'
    post(owner,'/auth/register',{'email':email,'password':password,'name':'Synthetic Workflow Creator'});post(owner,'/auth/login',{'email':email,'password':password})
    org=post(owner,'/organisations',{'name':'Synthetic Live End-to-End'});base=f"/organisations/{org['id']}"
    v=post(owner,base+'/guidelines/versions')
    rules=[{'type':'approved_fact','rule_key':'price','value':'Cloudberry Daily Cleanser 150ml costs INR 799.','fact':{'kind':'price','entity':'Cloudberry Daily Cleanser','amount':'799','currency':'INR','unit':'150ml','effective_from':'2026-01-01'}},{'type':'tone','rule_key':'tone','value':'Use calm, precise language. Avoid exaggerated guarantees.'},{'type':'approved_fact','rule_key':'cleanser_claim','value':'Cloudberry Daily Cleanser removes surface oil. No clinical treatment claims are approved.'},{'type':'required_disclaimer','rule_key':'disclaimer','value':'Results vary.'}]
    for rule in rules:post(owner,f"{base}/guidelines/versions/{v['id']}/rules",{**rule,'approved':True})
    post(owner,f"{base}/guidelines/versions/{v['id']}/activate");post(owner,base+'/ai/consent',{'enabled':True,'policy_version':'openrouter-free-zdr-redacted-v1'})
    draft=post(owner,base+'/drafts',{'title':'Synthetic complete live workflow','text':'Cloudberry Daily Cleanser 150ml costs INR 499. Guaranteed to cure acne for everyone. Results vary.'})
    run,preview=review(draft['id'],draft['current_version_id'])
    record('Real AI review completed',run['result']['mode']=='live_ai' and bool(run['result'].get('metadata',{}).get('model')))
    record('Typed price error found with approved evidence',any(f['category']=='fact' and f['status']=='confirmed_mismatch' and f['evidence'] for f in run['result']['findings']))
    record('Promotional promise requests evidence',any(f['category']=='claim' and f['status']=='unverified' for f in run['result']['findings']))
    finding=next(f for f in run['result']['findings'] if f['category']=='fact' and f['status']=='confirmed_mismatch')
    rewrite=wait(post(owner,f"{base}/review-runs/{run['id']}/rewrites",{'finding_id':finding['id'],'preview_hash':preview['preview_hash'],'idempotency_key':str(uuid4())}))
    report['provider_attempts'].append({'run_id':rewrite['id'],'kind':'rewrite','status':rewrite['status'],'error':rewrite.get('error'),'metadata':rewrite['result'].get('metadata')})
    report['live_rewrite_status']=rewrite['status']
    if rewrite['result'].get('options'):
        option=rewrite['result']['options'][0]
        applied=post(owner,f"{base}/drafts/{draft['id']}/apply-rewrite",{'expected_current_version_id':draft['current_version_id'],'option_id':option['id']})
        record('Real correction applied to a new immutable revision','INR 799' in applied['text'] and applied['id']!=draft['current_version_id'])
        current_id=applied['id']
    else:
        current=owner.get(f"{base}/drafts/{draft['id']}").json()
        record('Unavailable rewrite preserved the original revision',current['current_version_id']==draft['current_version_id'])
        current_id=draft['current_version_id'];report['limitation']='Live rewrite did not pass; the creator used a manual correction. The failed output was not applied.'
    clean=post(owner,f"{base}/drafts/{draft['id']}/versions",{'expected_current_version_id':current_id,'text':'Cloudberry Daily Cleanser 150ml costs INR 799. It removes surface oil. Results vary.'})
    record('Earlier check became stale after edits',owner.get(f"{base}/review-runs/{run['id']}").json()['stale'])
    rechecked,_=review(draft['id'],clean['id'])
    record('Clean control has no findings',rechecked['result']['findings']==[])
    reviewer=httpx.Client(base_url=owner.base_url,headers={'X-Inkloom-CSRF':'1'},timeout=20)
    reviewer_email=f'workflow-reviewer-{uuid4().hex}@example.com'
    post(reviewer,'/auth/register',{'email':reviewer_email,'password':password,'name':'Synthetic Workflow Reviewer'});post(reviewer,'/auth/login',{'email':reviewer_email,'password':password})
    invitation=post(owner,base+'/invites',{'email':reviewer_email,'role':'reviewer'});post(reviewer,'/invitations/accept',{'token':invitation['token']})
    reviewer_id=reviewer.get('/auth/me').json()['id'];owner_id=owner.get('/auth/me').json()['id']
    denied=owner.post(f"{base}/drafts/{draft['id']}/approvals",json={'version_id':clean['id'],'reviewer_id':owner_id,'idempotency_key':str(uuid4())})
    record('Creator cannot request self approval',denied.status_code==409)
    request=post(owner,f"{base}/drafts/{draft['id']}/approvals",{'version_id':clean['id'],'reviewer_id':reviewer_id,'idempotency_key':str(uuid4())})
    decision=post(reviewer,f"{base}/approvals/{request['id']}/decision",{'expected_version_id':clean['id'],'artifact_sha256':clean['artifact_sha256'],'decision':'approved','comment':'Automated two-account fixture; not independent human feedback.'})
    record('Separate reviewer account approved exact saved hash',decision['artifact_sha256']==clean['artifact_sha256'])
    record('Approval persisted',owner.get(f"{base}/drafts/{draft['id']}").json()['status']=='approved')
    report['status']='passed' if all(c['passed'] for c in report['checks']) else 'failed'
    reviewer.close()
except Exception as error:
    report.update(status='blocked',reason=str(error) if isinstance(error,RuntimeError) else type(error).__name__)
finally:
    directory=Path('.local/test-results');directory.mkdir(parents=True,exist_ok=True)
    (directory/'live-workflow.json').write_text(json.dumps(report,indent=2))
    (directory/f'live-workflow-{uuid4().hex}.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));owner.close()

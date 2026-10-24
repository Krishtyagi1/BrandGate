"""User-authorised live pipeline check. Synthetic fixtures only; no real materials."""
import json
import time
from pathlib import Path
from uuid import uuid4

import httpx

client=httpx.Client(base_url='http://127.0.0.1:8000/api',headers={'X-Inkloom-CSRF':'1'},timeout=20)
report={'kind':'synthetic real-provider review smoke','checks':[]}
def post(path,body):
    result=client.post(path,json=body)
    result.raise_for_status()
    return result.json()
try:
    email=f'synthetic-live-{uuid4().hex}@example.com';password='Synthetic live test password 123!'
    post('/auth/register',{'email':email,'name':'Synthetic Live Tester','password':password})
    post('/auth/login',{'email':email,'password':password})
    org=post('/organisations',{'name':'Synthetic Live Review Test'})
    base=f"/organisations/{org['id']}"
    v=post(base+'/guidelines/versions',{})
    for rule in [
        {'type':'approved_fact','rule_key':'cloudberry_price','value':'Cloudberry Daily Cleanser 150ml costs INR 799.','fact':{'kind':'price','entity':'Cloudberry Daily Cleanser','amount':'799','currency':'INR','unit':'150ml','effective_from':'2026-01-01'}},
        {'type':'tone','rule_key':'tone','value':'Use calm, precise language. Avoid exaggerated guarantees.'},
        {'type':'approved_fact','rule_key':'approved_claim','value':'Cloudberry Daily Cleanser is a daily cleanser. No clinical treatment claims are approved.'},
        {'type':'required_disclaimer','rule_key':'disclaimer','value':'Results vary.'}]:
        post(f"{base}/guidelines/versions/{v['id']}/rules",{**rule,'approved':True})
    post(f"{base}/guidelines/versions/{v['id']}/activate",{})
    post(base+'/ai/consent',{'enabled':True,'policy_version':'openrouter-free-zdr-redacted-v1'})
    draft=post(base+'/drafts',{'title':'Synthetic live brand review','text':'Cloudberry Daily Cleanser 150ml costs INR 499. Guaranteed to cure acne for everyone. Results vary.'})
    preview=client.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    run=post(f"{base}/drafts/{draft['id']}/reviews",{'version_id':draft['current_version_id'],'preview_hash':preview['preview_hash'],'idempotency_key':str(uuid4())})
    for _ in range(100):
        run=client.get(f"{base}/review-runs/{run['id']}").json()
        if run['status'] not in ('queued','running'):break
        time.sleep(1)
    findings=run.get('result',{}).get('findings',[])
    report.update(run_id=run['id'],run_status=run['status'],status='passed' if run['status']=='completed' else 'blocked',reason=run.get('error'),metadata=run.get('result',{}).get('metadata'),findings=[{'category':f['category'],'status':f['status'],'origin':f['origin'],'evidence_ids':[e['id'] for e in f['evidence']]} for f in findings])
    report['checks'].append({'name':'Seeded typed price mismatch detected','passed':any(f['category']=='fact' and f['status']=='confirmed_mismatch' for f in findings)})
    report['checks'].append({'name':'Promotional promise flagged for evidence review','passed':any(f['category']=='claim' and f['status']=='unverified' for f in findings)})
    if run['status']=='completed':
        price_issue=next(f for f in findings if f['category']=='fact' and f['status']=='confirmed_mismatch')
        rewrite=post(f"{base}/review-runs/{run['id']}/rewrites",{'finding_id':price_issue['id'],'preview_hash':preview['preview_hash'],'idempotency_key':str(uuid4())})
        for _ in range(200):
            rewrite=client.get(f"{base}/review-runs/{rewrite['id']}").json()
            if rewrite['status'] not in ('queued','running'):break
            time.sleep(1)
        if not rewrite['result'].get('options'):
            report.update(status='blocked',reason=rewrite.get('error') or 'Rewrite did not complete.')
        else:
            option=rewrite['result']['options'][0]
            applied=post(f"{base}/drafts/{draft['id']}/apply-rewrite",{'expected_current_version_id':draft['current_version_id'],'option_id':option['id']})
            report['checks'].append({'name':'Real generated correction applied as a new revision','passed':applied['id']!=draft['current_version_id'] and 'INR 799' in applied['text']})
            stale=client.get(f"{base}/review-runs/{run['id']}").json()
            report['checks'].append({'name':'Previous check invalidated after correction','passed':stale['stale']})
            clean=post(f"{base}/drafts/{draft['id']}/versions",{'expected_current_version_id':applied['id'],'text':'Cloudberry Daily Cleanser 150ml costs INR 799. A daily cleanser that removes surface oil. Results vary.'})
            p=client.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
            rechecked=post(f"{base}/drafts/{draft['id']}/reviews",{'version_id':clean['id'],'preview_hash':p['preview_hash'],'idempotency_key':str(uuid4())})
            for _ in range(100):
                rechecked=client.get(f"{base}/review-runs/{rechecked['id']}").json()
                if rechecked['status'] not in ('queued','running'):break
                time.sleep(1)
            report['checks'].append({'name':'Live clean control completed without findings','passed':rechecked['status']=='completed' and rechecked['result'].get('findings')==[]})
            if rechecked['status']!='completed':
                report.update(status='blocked',reason=rechecked.get('error') or 'Recheck incomplete.')
            else:
                owner_id=client.get('/auth/me').json()['id']
                denied=client.post(f"{base}/drafts/{draft['id']}/approvals",json={'version_id':clean['id'],'reviewer_id':owner_id,'idempotency_key':str(uuid4())})
                report['checks'].append({'name':'Self approval request rejected','passed':denied.status_code==409})
                reviewer=httpx.Client(base_url=client.base_url,headers={'X-Inkloom-CSRF':'1'},timeout=20)
                reviewer_email=f'synthetic-reviewer-{uuid4().hex}@example.com'
                reviewer.post('/auth/register',json={'email':reviewer_email,'name':'Synthetic Reviewer','password':password}).raise_for_status()
                reviewer.post('/auth/login',json={'email':reviewer_email,'password':password}).raise_for_status()
                invitation=post(base+'/invites',{'email':reviewer_email,'role':'reviewer'})
                reviewer.post('/invitations/accept',json={'token':invitation['token']}).raise_for_status()
                reviewer_id=reviewer.get('/auth/me').json()['id']
                request=post(f"{base}/drafts/{draft['id']}/approvals",{'version_id':clean['id'],'reviewer_id':reviewer_id,'idempotency_key':str(uuid4())})
                approved=reviewer.post(f"{base}/approvals/{request['id']}/decision",json={'expected_version_id':clean['id'],'artifact_sha256':clean['artifact_sha256'],'decision':'approved','comment':'Synthetic automated workflow test; not independent human feedback.'})
                report['checks'].append({'name':'Separate reviewer account approved the exact checked artifact','passed':approved.status_code==200})
                report['human_feedback']='Two-account automated workflow validation only. No independent human sign-off or user feedback was collected.'
                reviewer.close()
                if not all(c['passed'] for c in report['checks']):report['status']='failed'
except Exception as error:
    report.update(status='error',reason=type(error).__name__)
finally:
    path=Path('.local/test-results/live-review-smoke.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));client.close()

"""Two bounded real-provider probes, using generated fictional material only."""
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from PIL import Image

from app.visual_review import evaluate_visual
from ingestion.knowledge_intake import analyse_chunk, chunks
from providers.openrouter import ProviderUnavailable

directory = Path('.local/test-results/simple-live').resolve()
directory.mkdir(parents=True, exist_ok=True)
report = {'kind': 'Real free-provider probes; fictional inputs only', 'intake': {}, 'vision': {}}
source_id = str(uuid4())
source = {'id': source_id, 'media_type': 'application/docx', 'locations': [
    {'location': 'Paragraph 1', 'text': 'Tone: use a calm, clear and helpful voice.'},
    {'location': 'Paragraph 2', 'text': 'Cloudberry Daily Cleanser 150ml costs INR 799. Effective from 2026-01-01.'}]}
try:
    proposals, metadata, invalid = analyse_chunk(next(chunks([source])), [source])
    report['intake'] = {'status': 'passed' if proposals and not invalid else 'partial', 'validated_proposals': len(proposals), 'invalid_proposals': invalid, 'metadata': metadata}
except ProviderUnavailable as error:
    report['intake'] = {'status': 'blocked', 'reason': str(error)}
(directory / 'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'intake': report['intake']}), flush=True)

reference, candidate = directory / 'reference.png', directory / 'candidate.png'
Image.new('RGB', (320, 180), '#167569').save(reference)
Image.new('RGB', (320, 180), '#be123c').save(candidate)
reference_id = str(uuid4())
refs = [{'id': reference_id, 'label': 'Fictional teal visual reference', 'private_path': str(reference),
         'sha256': hashlib.sha256(reference.read_bytes()).hexdigest(), 'source_document_id': source_id,
         'source_location': 'Reference image', 'source_excerpt': 'Approved fictional teal theme.'}]
output = evaluate_visual(candidate, [], refs, ['logos'])
report['vision'] = {'status': 'passed' if output['mode'] == 'live' else 'blocked', 'mode': output['mode'],
                    'check_coverage': output['check_coverage'], 'findings': len(output['findings']),
                    'metadata': output.get('metadata'), 'reason': output.get('error')}
(directory / 'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'vision': report['vision']}), flush=True)

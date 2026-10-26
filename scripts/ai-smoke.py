"""Explicit synthetic-only live smoke; outputs no credentials or company data."""
import json
from pathlib import Path

from providers.openrouter import ProviderUnavailable, complete, routing_policy, settings
from pydantic import BaseModel, ConfigDict


class Smoke(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answer: str


report = {'kind': 'synthetic live smoke', 'configured': bool(settings()['OPENROUTER_API_KEY']), 'routing_policy': routing_policy()}
try:
    parsed, meta = complete('Return the requested word in the required schema.', {'requested_word': 'inkloom'}, Smoke, 'synthetic_smoke')
    report.update(status='passed' if parsed.answer.lower() == 'inkloom' else 'failed', **meta)
except ProviderUnavailable as error:
    report.update(status='blocked', reason=str(error))
path = Path('.local/test-results/ai-smoke.json')
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))

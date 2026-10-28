"""Build a curated local source archive; exclude secrets, runtimes and private files."""

import hashlib
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
output = root / '.local' / 'releases'
output.mkdir(parents=True, exist_ok=True)
allowed_roots = {'apps', 'services', 'packages', 'scripts', 'docs', 'evals', '.agents', 'samples', 'deploy', '.github', 'tests'}
allowed_files = {'.gitignore', '.dockerignore', '.gcloudignore', 'Dockerfile', '.npmrc', '.env.example', '.env.deploy.example', 'AGENTS.md', 'INKLOOM_CODEX_IMPLEMENTATION_PLAN.md', 'EXTERNAL_COMPONENTS.md', 'LICENSE', 'README.md', 'package.json', 'package-lock.json', 'Sample Company Brand Rules.docx'}
blocked_parts = {'.git', '.local', '.cache', '.venv', 'node_modules', '__pycache__', '.next', '.next-ui-tests', 'vendor', '.ruff_cache'}
listing = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], check=True, capture_output=True).stdout.decode('utf-8')
files = []
for name in sorted(set(listing.split('\0')) - {''}):
    relative = Path(name)
    if relative.parts[0] not in allowed_roots and name not in allowed_files:
        continue
    if any(part in blocked_parts for part in relative.parts) or (relative.name.startswith('.env') and name not in {'.env.example', '.env.deploy.example'}):
        raise RuntimeError('Private path unexpectedly entered source selection: ' + name)
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.is_symlink():
        raise RuntimeError('Source path must remain inside this project: ' + name)
    files.append((name, path))

private_keys = []
env_file = root / '.env'
if env_file.exists():
    for line in env_file.read_text(encoding='utf-8-sig').splitlines():
        if line.strip().startswith('OPENROUTER_API_KEY='):
            value = line.split('=', 1)[1].strip().strip('\"\'')
            if len(value) >= 16:
                private_keys.append(value.encode())
manifest = []
archive = output / 'inkloom-source.zip'
with ZipFile(archive, 'w', ZIP_DEFLATED) as bundle:
    for name, path in files:
        data = path.read_bytes()
        if any(key in data for key in private_keys) or re.search(rb'sk-or-v1-[A-Za-z0-9]{20,}', data):
            raise RuntimeError('Credential detected in source file: ' + name)
        bundle.writestr(name, data)
        manifest.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest()})
report = {'status': 'passed', 'archive': archive.relative_to(root).as_posix(), 'files': manifest, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'scope': 'Curated source plus fictional sample only. No keys, private runtime/company files, dependencies, generated workers, reports or Git metadata. This is not a complete secret scanner or clean-machine installation test.'}
(output / 'source-manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'status': report['status'], 'archive': report['archive'], 'file_count': len(manifest), 'sha256': report['archive_sha256']}, indent=2))

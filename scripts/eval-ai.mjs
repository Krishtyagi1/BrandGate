import {spawn} from 'node:child_process';
import {resolve} from 'node:path';
const root=resolve('.');
const child=spawn(resolve(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python'),['evals/run.py',...process.argv.slice(2)],{cwd:root,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONUTF8:'1',TEMP:resolve(root,'.cache/tmp'),TMP:resolve(root,'.cache/tmp'),TMPDIR:resolve(root,'.cache/tmp')},stdio:'inherit'});
child.on('exit',code=>process.exit(code??1));

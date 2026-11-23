"""Release consistency for the nested modules not rewritten by static-file hashing."""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def test_yankson_manifest_fingerprints_match_release_files():
    source = Path('static/js/yankson/build.js').read_text()
    data = json.loads(re.search(r'window.YanksonBuild = (\{.*?\});', source, re.S).group(1))
    for name in ['boot.mjs','workbench.mjs','layout.mjs','electrical.mjs','guide.mjs','microphone.mjs','experiments.mjs','engine-stand.bundle.mjs','learning-guide.json','authenticated-starting-learning-guide.pdf']:
        assert data['sha256'][name] == hashlib.sha256(Path('static/js/yankson', name).read_bytes()).hexdigest()
    code = '''global.window={};require('node:vm').runInThisContext(require('node:fs').readFileSync('static/js/yankson/build.js','utf8'));
    const url=new URL(window.YanksonAssetURL('./workbench.mjs','https://lab.example/static/js/yankson/teaching.abc.mjs?v=old'));
    if(url.pathname!='/static/js/yankson/workbench.mjs'||url.searchParams.get('v')!==window.YanksonBuild.sha256['workbench.mjs'])process.exit(1);
    '''
    subprocess.run(['node','-e',code],capture_output=True,text=True,check=True)

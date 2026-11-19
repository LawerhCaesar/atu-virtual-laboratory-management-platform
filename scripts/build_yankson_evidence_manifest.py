"""Generate source hashes separately from Render's runtime deployment identity."""
from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parents[1]
names = ['engine.js','ui.js','practical.js','speech.js','evidence.js','teaching.mjs','workbench.mjs','microphone.mjs','devices.js','experiments.mjs']
build = {
    'scope': 'Reviewed source assets; runtime deployment commit is reported separately.',
    'baseCommit': '05d72ec5a4a626f35060b7ab0b334eed799b5b66',
    'sha256': {name: hashlib.sha256((root/'static/js/yankson'/name).read_bytes()).hexdigest() for name in names},
}
(root/'static/js/yankson/build.js').write_text('window.YanksonBuild = '+json.dumps(build,indent=2)+';\n')

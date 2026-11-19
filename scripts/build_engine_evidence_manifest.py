"""Identify actual calculation/controller source bytes; no invented deployment build hash."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
files=['reference.mjs','controller.mjs']
hashes={name:hashlib.sha256((root/'static/js/engine-live-data'/name).read_bytes()).hexdigest() for name in files}
build={'identifier':'engine-live-data-reference-'+hashes['reference.mjs'][:16], 'sourceSha256':hashes,'sourceContract':'EngineLab Master Prompt revision 2 and approved programmer guide, 25 October 2026','scope':'Reviewed source from baseline 05d72ec5a4a626f35060b7ab0b334eed799b5b66; runtime deployment identity is reported separately'}
build['canonicalSource']={'slxSha256':'d52420882756680f3523e9a61cb2edeee84fd41037418d03c261bf2720402d75','reviewDate':'2026-11-19','method':'Embedded-source review and five original browser CSV comparisons; not a MATLAB solver run'}
(root/'static/js/engine-live-data/build.mjs').write_text('export const ENGINE_BUILD = Object.freeze('+json.dumps(build,indent=2)+');\n')

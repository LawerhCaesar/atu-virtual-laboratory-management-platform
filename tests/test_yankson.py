import subprocess
from pathlib import Path
import hashlib
from django.urls import reverse

def test_yankson_reference():
 assert hashlib.sha256(Path('static/js/yankson/engine.js').read_bytes()).hexdigest()=='7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279'
 r=subprocess.run(['node','static/js/yankson/engine.js','--self-test'],capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr

def test_yankson_login(client):
 assert client.get(reverse('core:yankson')).status_code==302

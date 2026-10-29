import subprocess
from django.urls import reverse

def test_series_parallel_core():
 r=subprocess.run(['node','--test','tests/series-parallel/engine.test.mjs'],capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr

def test_series_parallel_requires_login(client):
 assert client.get(reverse('core:series_parallel')).status_code==302

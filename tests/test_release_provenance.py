import pytest
from apps.core.context_processors import deployment_metadata

def test_release_metadata_only_exposes_public_build_fields(monkeypatch):
    monkeypatch.setenv('RENDER','true')
    monkeypatch.setenv('RENDER_GIT_COMMIT','a'*40)
    monkeypatch.setenv('RENDER_GIT_BRANCH','main')
    monkeypatch.setenv('POSTGRES_PASSWORD','not-public')
    assert deployment_metadata()=={'commit':'a'*40,'branch':'main','environment':'render'}

def test_local_release_does_not_invent_commit(monkeypatch):
    for name in ['RENDER','RENDER_GIT_COMMIT','RENDER_GIT_BRANCH']:monkeypatch.delenv(name,raising=False)
    assert deployment_metadata()=={'commit':None,'branch':None,'environment':'local'}

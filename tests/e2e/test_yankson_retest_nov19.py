import csv,io,json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_yankson_practical import open_lab,contact,result
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

def test_custom_draft_practice_language_and_activation(page,demo_records,live_server):
 open_lab(page,demo_records,live_server)
 page.locator('#yp-command').fill('Yankson Start');page.locator('#yp-save').click()
 expect(page.locator('#yp-active-command')).to_contain_text('Hey Start')
 page.locator('#yp-language').select_option('en-GB')
 page.locator('#yp-test-phrase').click();assert page.evaluate('recognizers.at(-1).lang')=='en-GB'
 result(page,'yankson stats');expect(page.locator('#yp-phrase-check')).to_contain_text('NO MATCH')
 page.locator('#yp-save').click();expect(page.locator('#yp-active-command')).to_contain_text('Hey Start')
 page.locator('#yp-command').fill('Start my engine');page.locator('#yp-test-phrase').click();result(page,'START, MY ENGINE!')
 expect(page.locator('#yp-phrase-check')).to_contain_text('en-GB');page.locator('#yp-save').click()
 expect(page.locator('#yp-active-command')).to_contain_text('Start my engine')
 assert page.locator('#ys-output-pane #yp-phrase-check').count()==1
 page.locator('#yp-practice').check();contact(page,300);page.locator('#yp-listen').click();result(page,'Start my engine');page.clock.run_for(4000)
 expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 Path('test-results/corrections/nov19-screenshots').mkdir(parents=True,exist_ok=True)
 page.screenshot(path='test-results/corrections/nov19-screenshots/custom-phrase-software.png')

@pytest.mark.parametrize('wire',['match','contact'])
@pytest.mark.parametrize('kind',['short','long','held','mouse'])
def test_all_adapters_and_no_reconnection_replay(page,demo_records,live_server,wire,kind):
 open_lab(page,demo_records,live_server);page.locator('#yp-circuit').evaluate('e=>e.open=true');page.locator('#yp-practice').check()
 page.locator('#yp-wire-'+wire).uncheck()
 if kind in ['short','long']:page.locator('#ys-'+kind).click();page.clock.run_for(2000)
 elif kind=='held':page.locator('#ys-press').click();page.locator('#ys-run').click();page.clock.run_for(2000)
 else:
  target=page.locator('#yp-hold');target.scroll_into_view_if_needed();b=target.bounding_box();page.mouse.move(b['x']+30,b['y']+30);page.mouse.down();page.clock.run_for(1700);page.mouse.up()
 assert page.evaluate('YanksonLab.row[2]+YanksonLab.row[3]')==0
 page.locator('#yp-wire-'+wire).check();page.clock.run_for(2000)
 assert page.evaluate('YanksonLab.row[2]+YanksonLab.row[3]')==0
 if kind=='held':page.locator('#ys-release').click()


def test_export_reset_status_and_historical_trials(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);page.locator('#ys-short').click();page.clock.run_for(11000)
 expect(page.locator('#yp-reason')).to_contain_text('expired')
 page.locator('#ys-reset').click();expect(page.locator('#yp-reason')).to_contain_text('LOCKED')
 page.locator('#ys-long').click();page.clock.run_for(5000)
 with page.expect_download() as dl:page.locator('#ys-json').click()
 data=json.loads(Path(dl.value.path()).read_text());prior=data['evidence']['runId']
 with page.expect_download() as dl:page.locator('#ys-csv').click()
 rows=list(csv.reader(io.StringIO(Path(dl.value.path()).read_text())));assert rows[0]==data['columns'];assert len(rows)-1==len(data['rows'])
 assert all([float(v) for v in row]==saved for row,saved in zip(rows[1:],data['rows']))
 times=[r[0] for r in data['rows']];assert all(b>a for a,b in zip(times,times[1:]))
 assert data['evidence']['generation'] is not None;assert data['evidence']['build']['sha256']['engine.js']
 page.locator('#ys-reset').click()
 with page.expect_download() as dl:page.locator('#ys-json').click()
 data=json.loads(Path(dl.value.path()).read_text());assert data['evidence']['runId']!=prior
 assert not data['practical']['events'];assert not data['signalTrace']['events']
 assert data['evidence']['humanVoiceEvidence']['attestedTrials']==0
 assert data['evidence']['historicalReportedTrials']['customPhrase']['finalResults']==7
 assert page.locator('#ys-output-pane #ys-json').count()==1


def test_diagnostic_no_result_and_payload_are_explicit(page,demo_records,live_server):
 open_lab(page,demo_records,live_server)
 page.locator('#yp-command').fill('New clear phrase');page.locator('#yp-test-phrase').click()
 page.evaluate("recognizers.at(-1).onerror({error:'network'})")
 expect(page.locator('#yp-phrase-check')).to_contain_text('No final matching transcript')
 page.locator('#yp-save').click();expect(page.locator('#yp-active-command')).to_contain_text('Hey Start')
 page.locator('#ya-tab-signals').click();page.locator('#ys-run').click();page.clock.run_for(300)
 expect(page.locator('#ya-can')).to_contain_text('Received payload:')
 expect(page.locator('#ya-can')).to_contain_text('frame model time')
 expect(page.locator('#ya-can')).to_contain_text('not a Toyota or uaEFI DBC')

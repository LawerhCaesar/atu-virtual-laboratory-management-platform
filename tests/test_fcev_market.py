from unittest.mock import patch
import pytest
from django.core.cache import cache
from django.urls import reverse
from apps.accounts.models import User
from apps.core import fcev_market as market


def test_bog_mid_rate_and_dates_not_scrape_time():
    html='<table><tr><td>30 Oct 2026</td><td>US Dollar</td><td>USDGHS</td><td>11.6142</td><td>11.6258</td><td>11.6200</td></tr><tr><td>30 Oct 2026</td><td>Euro</td><td>EURGHS</td><td>12.9559</td><td>12.9678</td><td>12.9619</td></tr></table>'
    assert market.parse_bog(html)=={'usdGhs':11.62,'eurGhs':12.9619,'effectiveDate':'2026-10-30'}
    with pytest.raises(ValueError):market.parse_bog(html.replace('EURGHS','WRONG'))
    with pytest.raises(ValueError):market.parse_bog(html.replace('30 Oct 2026</td><td>Euro','29 Oct 2026</td><td>Euro'))


def test_diesel_effective_date_and_purc_energy_only_quote():
    assert market.parse_goil('NEW FUEL PRICES EFFECTIVE 17TH SEPTEMBER 2026. Diesel XP - Ghc 18.46')=={'value':18.46,'effectiveDate':'2026-09-17'}
    form='<input name="__VIEWSTATE" value="public-form"><input name="__EVENTVALIDATION" value="public-form">'
    response='<input id="MainContent_txtEnergyCharge" disabled="disabled" value="208.63"><input id="MainContent_txtETotalAmt" value="860.79">'
    with patch.object(market,'fetch',side_effect=[form,response]) as request:
        assert market.electricity()=={'value':2.0863}
        assert b'SLT+EV+Chg' in request.call_args.args[1]


def test_quote_failure_retains_dated_references_and_shared_cache():
    cache.clear()
    with patch.object(market,'fetch',side_effect=OSError('offline')) as fetch:
        book=market.market_book();again=market.market_book()
        assert book==again
        assert book['fx']['effectiveDate']=='2026-10-30'
        assert book['fx']['status']=='retained_reference'
        assert book['hydrogen']['status']!='online'
        assert all(q['value']>0 for k,q in book.items() if k!='fx')
        assert fetch.call_count==4
    cache.clear()


@pytest.mark.django_db
def test_private_quote_endpoint_and_hiace_scope(client):
    endpoint=reverse('core:fcev_market_prices')
    assert client.get(endpoint).status_code==302
    user=User.objects.create_user(email='fcev-price-test@example.test',password='DemoPass!742',role='STUDENT',approval_status='ACTIVE',full_name='QA')
    client.force_login(user)
    with patch.object(market,'market_book',return_value=market.seed_book()):
        r=client.get(endpoint);assert r.status_code==200;assert r.json()['fx']['usdGhs']==11.62
        assert 'private' in r['Cache-Control'] and 'no-store' in r['Cache-Control']
        assert client.post(endpoint).status_code==405
    html=client.get(reverse('core:bless')).content
    assert b'FCEV Range Extended System' in html and b'Bless Atisu' in html
    assert b'Toyota HiAce' in html and b'1GD-FTV' in html and b'3,860' in html
    assert b'GV70 scans' not in html and b'235/55R19' not in html
    user.approval_status='PENDING';user.save();assert client.get(endpoint).status_code==403

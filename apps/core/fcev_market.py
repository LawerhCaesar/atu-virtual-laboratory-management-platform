"""Bounded, fixed-source quotes for educational cost comparisons; never a price guarantee."""
import copy
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from django.core.cache import cache

BOG='https://www.bog.gov.gh/treasury-and-the-markets/daily-interbank-fx-rates/'
GOIL='https://www.goil.com.gh/new-fuel-prices/'
PURC='https://purcghapp.com/'
HYDROGEN='https://www.bundeswirtschaftsministerium.de/Redaktion/DE/Artikel/Energie/2021-08-pkw-energiekostenvergleich.html'
ALLOWED={'www.bog.gov.gh','bog.gov.gh','www.goil.com.gh','goil.com.gh','purcghapp.com','www.bundeswirtschaftsministerium.de','bundeswirtschaftsministerium.de'}
SEED={
 'fx':{'usdGhs':11.62,'eurGhs':12.9619,'effectiveDate':'2026-10-30','source':BOG,'label':'Bank of Ghana interbank mid rates'},
 'diesel':{'value':18.46,'currency':'GHS','unit':'L','effectiveDate':'2026-09-17','source':GOIL,'label':'GOIL Diesel XP published pump quote'},
 'electricity':{'value':2.0863,'currency':'GHS','unit':'kWh','effectiveDate':None,'source':PURC,'label':'PURC SLT EV Chg energy charge only; excludes taxes, operator margin and monthly service charge'},
 'hydrogen':{'value':15.56,'currency':'EUR','unit':'kg','effectiveDate':None,'source':HYDROGEN,'label':'Published German government international comparison benchmark; not a worldwide or Ghana delivery price'},
}
def seed_book():
 book=copy.deepcopy(SEED)
 for v in book.values():v.update(status='reference_snapshot',retrievedAt='2026-11-02',notice='Stored reference, not a fresh online quotation.')
 book['hydrogen']['notice']='Published benchmark; direct live verification may be unavailable. No universal international hydrogen price exists.'
 return book
class Redirect(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urlparse(newurl).scheme!='https' or urlparse(newurl).hostname not in ALLOWED:raise ValueError('Unsupported quote-source redirect')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url,data=None):
 if urlparse(url).hostname not in ALLOWED:raise ValueError('Unsupported source')
 request=Request(url,data=data,headers={'User-Agent':'ATU-Educational-Price-Reference/1.0','Accept':'text/html'})
 with build_opener(Redirect()).open(request,timeout=8) as response:
  payload=response.read(1500001)
  if len(payload)>1500000:raise ValueError('Quote source too large')
  return payload.decode('utf-8',errors='replace')
def text(html):return re.sub(r'\s+',' ',unescape(re.sub('<[^>]+>',' ',html)))
def positive(v):
 value=float(v)
 if not 0<value<100000:raise ValueError('Invalid price')
 return value
def parse_bog(html):
 t=text(html);out={}
 for symbol,key in [('USDGHS','usdGhs'),('EURGHS','eurGhs')]:
  m=re.search(r'(\d{1,2} [A-Za-z]{3} 20\d{2})[^\d]{0,60}'+symbol+r'\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)',t)
  if not m:raise ValueError('Bank rate table changed')
  date=datetime.strptime(m[1],'%d %b %Y').date().isoformat()
  if out.get('effectiveDate',date)!=date:raise ValueError('FX quote dates differ')
  out[key]=positive(m[4]);out['effectiveDate']=date
 return out
def parse_goil(html):
 t=text(html);m=re.search(r'Diesel\s+XP\s*[-–:]?\s*(?:Ghc|GHS|GH¢)\s*([\d.]+)',t,re.I)
 if not m:raise ValueError('Diesel quote unavailable')
 d=re.search(r'(\d{1,2})(?:ST|ND|RD|TH)?\s+([A-Z]+)\s+(20\d{2})',t,re.I)
 if not d:raise ValueError('Diesel effective date unavailable')
 return {'value':positive(m[1]),'effectiveDate':datetime.strptime(f'{d[1]} {d[2]} {d[3]}','%d %B %Y').date().isoformat()}
class Form(HTMLParser):
 def __init__(self):super().__init__();self.inputs={};self.ids={}
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='input':
   if a.get('id'):self.ids[a['id']]=a.get('value','')
   if a.get('name') and 'disabled' not in a:self.inputs[a['name']]=a.get('value','')
def electricity():
 p=Form();p.feed(fetch(PURC));d=p.inputs
 for key in ['__VIEWSTATE','__EVENTVALIDATION']:
  if key not in d:raise ValueError('Tariff form changed')
 d.update({'ctl00$MainContent$ddlCustomerType':'SLT EV Chg','ctl00$MainContent$ddlCompPref':'Consumption (kWh)','ctl00$MainContent$txtEConsmptn':'100','ctl00$MainContent$btnECalculate':'CALCULATE'})
 q=Form();q.feed(fetch(PURC,urlencode(d).encode()));return {'value':positive(q.ids['MainContent_txtEnergyCharge'])/100}
def hydrogen():
 t=text(fetch(HYDROGEN));m=re.search(r'Wasserstoff\s*\(?H\s*[₂2]\s*\)?\s*[:\-]?\s*([0-9]+[,.][0-9]+)\s*(?:Euro|€)',t,re.I)
 if not m:raise ValueError('Hydrogen benchmark not live-verifiable; retained published reference')
 return {'value':positive(m[1].replace(',','.'))}
def market_book():
 cached=cache.get('fcev-market:book:v1')
 if cached:return cached
 if not cache.add('fcev-market:refresh-lock:v1',True,40):return cache.get('fcev-market:last:v1') or seed_book()
 book=cache.get('fcev-market:last:v1') or seed_book()
 loaders={'fx':lambda:parse_bog(fetch(BOG)),'diesel':lambda:parse_goil(fetch(GOIL)),'electricity':electricity,'hydrogen':hydrogen}
 def load(item):
  key,fn=item
  try:return key,fn(),None
  except Exception:return key,None,'Online source unavailable or format changed; retained dated reference. Use an experiment override if needed.'
 with ThreadPoolExecutor(max_workers=4) as pool:
  for key,values,error in pool.map(load,loaders.items()):
   if values:book[key].update(values,status='online',retrievedAt=datetime.now(timezone.utc).isoformat(),notice='Latest successfully retrieved source quotation; check its effective date and tariff scope.')
   else:book[key].update(status='retained_reference',notice=error)
 cache.set('fcev-market:book:v1',book,900);cache.set('fcev-market:last:v1',book,7*86400);return book

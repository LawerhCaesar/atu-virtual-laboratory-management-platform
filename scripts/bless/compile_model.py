"""Build-time translation of the supplied, hash-verified graph; never evaluates user code."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'docs/reference/bless-battery'
OUT=ROOT/'static/js/bless'
import hashlib
manifest=json.loads((SRC/'manifest.json').read_text())
for name in ['model/native_model.json','model/parameter_catalog.json','model/output_contract.json']:
 assert hashlib.sha256((SRC/name).read_bytes()).hexdigest()==manifest['files'][name]['sha256'], 'Source integrity failure: '+name
m=json.loads((SRC/'model/native_model.json').read_text()); catalog=json.loads((SRC/'model/parameter_catalog.json').read_text()); contract=json.loads((SRC/'model/output_contract.json').read_text())
blocks={b['path']:b for b in m['blocks']}; edges={(e['destination'],e['destinationPort']):(e['source'],e['sourcePort']) for e in m['connections']}
params={p['source_path']:p for p in catalog['parameters'] if p['parameter']=='Value'}
mask=next(b['path'] for b in m['blocks'] if b['mask']['initialization'])
class Parser:
 def __init__(self,s,u='u'):
  self.tokens=re.findall(r'\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|[A-Za-z_]\w*|>=|<=|==|!=|~=|&&|\|\||[()+*/^,!<>-]',s); self.i=0; self.u=u
  if ''.join(self.tokens)!=re.sub(r'\s','',s): raise ValueError('Unrecognized expression '+s)
 def pop(self): t=self.tokens[self.i]; self.i+=1; return t
 def peek(self): return self.tokens[self.i] if self.i<len(self.tokens) else ''
 def expr(self,limit=0):
  t=self.pop()
  if t in ['-','+','!']: a=f'({t}{self.expr(7)})'
  elif t=='(': a=self.expr(); assert self.pop()==')'
  elif re.match(r'[\d.]',t): a=t
  elif self.peek()=='(':
   self.pop(); args=[self.expr()]
   while self.peek()==',': self.pop(); args.append(self.expr())
   assert self.pop()==')'
   if t in ['u','ocv_soc','ocv_cell_V']:
    assert len(args)==1; a=f'{self.u if t=="u" else "e."+t}[({args[0]})-1]'
   elif t=='rem': a=f'({args[0]}%{args[1]})'
   else:
    assert t in ['abs','atan','cos','sin','sqrt']; a=f'Math.{t}({",".join(args)})'
  else: a='Math.PI' if t=='pi' else 'e.'+t
  prec={'||':1,'&&':2,'==':3,'!=':3,'~=':3,'>':4,'<':4,'>=':4,'<=':4,'+':5,'-':5,'*':6,'/':6,'^':8}
  while self.peek() in prec and prec[self.peek()]>limit:
   op=self.pop(); b=self.expr(prec[op]-(op=='^'))
   if op=='^': a=f'Math.pow({a},{b})'
   elif op in ['||','&&','==','!=','~=','>','<','>=','<=']: a=f'Number({a}{"!=" if op=="~=" else op}{b})'
   else: a=f'({a}{op}{b})'
  return a
 def parse(self):
  a=self.expr(); assert self.i==len(self.tokens); return a

def expr(s,u='u'): return Parser(s,u).parse()
def canonical(path,port=1,seen=None):
 seen=set() if seen is None else seen
 assert (path,port) not in seen, path
 seen.add((path,port)); b=blocks[path]; typ=b['type']; p=b['parameters']
 if typ=='SubSystem':
  child=next(x for x in m['blocks'] if x['parent']==path and x['type']=='Outport' and int(x['parameters']['Port'])==port); return canonical(child['path'],1,seen)
 if typ=='Inport': return canonical(*edges[(b['parent'],int(p['Port']))],seen)
 if typ=='From':
  matches=[x for x in m['blocks'] if x['type']=='Goto' and x['parameters']['GotoTag']==p['GotoTag'] and x['parent']==b['parent']]
  assert len(matches)==1, path
  assert matches[0]['parameters']['TagVisibility']=='local'
  return canonical(matches[0]['path'],1,seen)
 if typ in ['Outport','Goto']: return canonical(*edges[(path,1)],seen)
 return path
active=[b for b in m['blocks'] if b['type'] not in ['SubSystem','From','Goto','Inport','Outport','Terminator','Display','Scope']]
index={b['path']:i for i,b in enumerate(active)}; states=[b for b in active if b['type']=='UnitDelay']; state_index={b['path']:i for i,b in enumerate(states)}
lines=[]; done=set(); visiting=set()
def emit(path):
 if path in done:return
 if path in visiting:raise ValueError('Algebraic loop '+path)
 visiting.add(path); b=blocks[path]; p=b['parameters']; t=b['type']; i=index[path]
 ins=[]
 if t not in ['UnitDelay','Constant','DigitalClock']:
  for n in range(1,b['inputCount']+1):
   src=canonical(*edges[(path,n)]); emit(src); ins.append(f'v[{index[src]}]')
 a=ins[0] if ins else ''
 if t=='Constant': val=f'p.{params[path]["key"]}' if path in params else expr(p['Value'])
 elif t=='DigitalClock': val='time_s'
 elif t=='UnitDelay': val=f'state[{state_index[path]}]'
 elif t=='Mux': val='['+','.join(ins)+'].flat()'
 elif t=='Fcn': val=expr(p['Expr'],f'vector({a})')
 elif t=='Abs': val=f'Math.abs({a})'
 elif t=='Gain': val=f'({a}*{expr(p["Gain"])})'
 elif t in ['Product','Sum']:
  ops=p['Inputs'].replace('|',''); assert len(ops)==len(ins)
  val=('1' if t=='Product' else '0')
  for op,x in zip(ops,ins): val=f'({val}{op}{x})'
 elif t=='MinMax': val=f'Math.{p["Function"]}({",".join(ins)})'
 elif t=='RelationalOperator': val=f'Number({ins[0]}{p["Operator"]}{ins[1]})'
 elif t=='Logic': assert p['Operator']=='AND'; val=f'Number({"&&".join(ins)})'
 elif t=='Switch': assert p['Criteria']=='u2 >= Threshold'; val=f'({ins[1]}>={expr(p["Threshold"])}?{ins[0]}:{ins[2]})'
 elif t=='Saturate': val=f'Math.min({expr(p["UpperLimit"])},Math.max({expr(p["LowerLimit"])},{a}))'
 elif t=='Lookup_n-D':
  assert p['NumberOfTableDimensions']=='1' and p['InterpMethod']=='Linear point-slope' and p['ExtrapMethod']=='Clip'; val=f'lookup({a},e.ocv_soc,e.ocv_cell_V)'
 else: raise ValueError(t)
 lines.append(f'  v[{i}]={val}; // SID {b["sid"]} {path}')
 visiting.remove(path);done.add(path)
for b in active:
 assert b['parameters'].get('SampleTime','-1') in ['-1','1','dt_s','inf'], 'Unsupported sample time: '+b['path']
 emit(b['path'])
nexts=[f'v[{index[canonical(*edges[(b["path"],1)])]}]' for b in states]
streams={k:[index[canonical(c['source_path'])] for c in v['columns']] for k,v in contract['streams'].items()}
code='''// Generated by scripts/bless/compile_model.py. Do not edit.
const vector=(x)=>Array.isArray(x)?x:[x];
export function lookup(x,bp,table){if(x<=bp[0])return table[0];for(let i=1;i<bp.length;i++){if(x<=bp[i])return table[i-1]+(table[i]-table[i-1])*((x-bp[i-1])/(bp[i]-bp[i-1]));}return table.at(-1);}
export function initialState(e){return '''+ '['+','.join(expr(b['parameters']['InitialCondition']) for b in states)+'''];}
export function calculate(time_s,state,p,e){const v=[];
'''+ '\n'.join(lines)+'\nreturn {nextState:['+','.join(nexts)+'],streams:{'+','.join(k+':['+','.join(f'v[{i}]' for i in ids)+']' for k,ids in streams.items())+'}};\n}\n'
(OUT/'graph.mjs').write_text(code)
(OUT/'catalog.mjs').write_text('export const parameters='+json.dumps(catalog['parameters'])+';\nexport const contract='+json.dumps(contract)+';\nexport const examples='+json.dumps(json.loads((SRC/'validation/scenarios.json').read_text())['scenarios'])+';\n')
report=[]
for b in m['blocks']:
 t=b['type']; target=f'graph.mjs v[{index[b["path"]]}]' if b['path'] in index else ('presentation only' if t in ['Scope','Display','Terminator'] else 'scoped graph routing')
 report.append({'path':b['path'],'sid':b['sid'],'type':t,'implementation':target})
(ROOT/'docs/reference/bless-battery/conversion-map.json').write_text(json.dumps(report,indent=2)+'\n')
print('Generated',len(active),'calculations;',len(states),'simultaneous states;',sum(map(len,streams.values())),'channels')

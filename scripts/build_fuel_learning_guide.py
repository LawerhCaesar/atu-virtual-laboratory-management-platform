from pathlib import Path
import json,html,re
from reportlab.platypus import SimpleDocTemplate,Paragraph,KeepTogether,Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'scripts/fuel-learning-content.json').read_text())
styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=15;styles['BodyText'].spaceAfter=8
for name in ['Title','Heading1','Heading2']:styles[name].textColor=colors.HexColor('#234e68')
def clean(t):
 for a,b in [('−','-'),('–','-'),('—','-'),('×','x'),('→','->'),('±','+/-'),('’',"'"),('“','"'),('”','"')]:t=str(t).replace(a,b)
 return html.escape(str(t))
def para(t,style='BodyText'):return Paragraph(clean(t),styles[style])
story=[para('Fuel Delivery Optimisation','Title'),para('Student learning guide | ICE laboratory | 31 October 2026'),para('Aziz Allotey | Supervisor: Professor Moro Adams'),para('From your first experiment to checking the equations. This guide matches the in-page learning guide and explains all inputs and calculated outputs.')]
for title,text in data['lessons']:story.append(KeepTogether([para(title,'Heading2'),para(text)]))
story +=[PageBreak(),para('Every input, in plain language','Heading1'),para('Suggested ranges guide classroom experiments. Only fuel scale, duration and calculation step have the named hard ranges shown below; other validation rules still apply.')]
for f in data['fields']:
 title=f['label']+(' ('+f['unit']+')' if f['unit'] else '')
 bounds='Allowed' if f['key'] in ['fuelOptimisationScale','simulationDurationS','timeStepS'] else 'Suggested'
 story.append(KeepTogether([para(title,'Heading2'),para(data['help'][f['key']]),para(f"Default: {f['value']}. {bounds} range: {f['min']} to {f['max']} {f['unit']}. Signal: {f['key']}.")]))
story +=[Spacer(1,16),para('Every calculated output','Heading1')]
for key,meaning in data['outputs'].items():story.append(KeepTogether([para(re.sub(r'([a-z])([A-Z])',r'\1 \2',key).capitalize(),'Heading2'),para(meaning)]))
def footer(c,doc):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#486477'));c.drawString(42,27,'ATU Virtual Laboratory | Fuel Delivery Optimisation');c.drawRightString(553,27,str(doc.page));c.setStrokeColor(colors.HexColor('#c1d3df'));c.line(42,39,553,39)
SimpleDocTemplate(str(ROOT/'static/guides/fuel-delivery-learning-guide.pdf'),leftMargin=42,rightMargin=42,topMargin=44,bottomMargin=54).build(story,onFirstPage=footer,onLaterPages=footer)

from pathlib import Path
import json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
ROOT=Path(__file__).resolve().parents[1];data=json.loads((ROOT/'scripts/battery-learning-content.json').read_text());styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=8
for key in ['Title','Heading1','Heading2']:styles[key].textColor=colors.HexColor('#234e68')
def p(text,style='BodyText'):
 for a,b in [('→','->'),('–','-'),('—','-'),('×','x'),('’',"'"),('−','-')]:text=str(text).replace(a,b)
 return Paragraph(html.escape(str(text)),styles[style])
story=[p('BEV Charge and Discharge System','Title'),p('Battery Energy Management | Student learning guide'),p('31 October 2026 | Local review'),p('From your first run to interpreting restrictions. The guide matches the on-page definitions. Geometry and calibration are educational.')]
for title,text in data['lessons']:story.append(KeepTogether([p(title,'Heading2'),p(text)]))
story.append(p('Every input and its reference default','Heading1'))
for key,text in data['help'].items():
 value=data['defaults']
 for part in key.split('.'):value=value[part]
 story.append(KeepTogether([p(key,'Heading2'),p(text),p('Reference default: '+str(value))]))
story.append(p('All 32 output channels','Heading1'))
for key,text in data['channels'].items():story.append(KeepTogether([p(key,'Heading2'),p(text)]))
def footer(c,doc):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#486477'));c.drawString(42,27,'ATU Virtual Laboratory | Battery Energy Management');c.drawRightString(553,27,str(doc.page));c.setStrokeColor(colors.HexColor('#c1d3df'));c.line(42,39,553,39)
(ROOT/'static/guides').mkdir(exist_ok=True)
SimpleDocTemplate(str(ROOT/'static/guides/battery-charge-learning-guide.pdf'),leftMargin=42,rightMargin=42,topMargin=44,bottomMargin=54).build(story,onFirstPage=footer,onLaterPages=footer)

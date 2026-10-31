from pathlib import Path
import json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,KeepTogether,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
ROOT=Path(__file__).resolve().parents[1];data=json.loads((ROOT/'scripts/motor-learning-content.json').read_text());styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=8
for key in ['Title','Heading1','Heading2']:styles[key].textColor=colors.HexColor('#234e68')
def p(text,style='BodyText'):
 for a,b in [('→','->'),('–','-'),('—','-'),('×','x'),('’',"'"),('²','^2')]:text=str(text).replace(a,b)
 return Paragraph(html.escape(str(text)),styles[style])
story=[p('Electric Motor Drive and Power Conversion','Title'),p('Student learning guide | Edward Selorm | BEV laboratory'),p('31 October 2026 | Local interface review'),p('Understand the inputs, follow the power path and verify the results. The guide matches the on-page learning section.')]
for title,text in data['lessons']:story.append(KeepTogether([p(title,'Heading2'),p(text)]))
for group,keys in data['fields'].items():
 story.append(p(group+' - all inputs','Heading1'))
 for key in keys:story.append(KeepTogether([p(data['labels'][key],'Heading2'),p(data['help'][key]),p('Default: '+str(data['defaults'][key])+'. Signal: '+key+'.')]))
story.append(p('Graph and legend glossary','Heading1'))
for title,text in data['legends'].items():story.append(KeepTogether([p(title,'Heading2'),p(text)]))
story.append(p('Complete 51-column CSV map','Heading1'))
for title,text in data['columns'].items():story.append(KeepTogether([p(title,'Heading2'),p(text)]))
def footer(c,doc):
 c.setFillColor(colors.HexColor('#486477'));c.setFont('Helvetica',8);c.drawString(42,27,'ATU Virtual Laboratory | Electric Motor Drive and Power Conversion');c.drawRightString(553,27,str(doc.page));c.setStrokeColor(colors.HexColor('#c1d3df'));c.line(42,39,553,39)
(ROOT/'static/guides').mkdir(exist_ok=True)
SimpleDocTemplate(str(ROOT/'static/guides/motor-drive-learning-guide.pdf'),leftMargin=42,rightMargin=42,topMargin=44,bottomMargin=54).build(story,onFirstPage=footer,onLaterPages=footer)

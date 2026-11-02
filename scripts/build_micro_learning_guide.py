"""Generate the downloadable guide from the same data used by the lab page."""
import json,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'static/js/micro-hybrid/learning-guide.json').read_text())
output=root/'output/pdf/micro-hybrid-learning-guide.pdf';output.parent.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet();styles.add(ParagraphStyle('Lead',fontName='Helvetica',fontSize=12,leading=18,textColor=colors.HexColor('#38576a'),spaceAfter=16));styles['BodyText'].fontSize=10;styles['BodyText'].leading=13.5;styles['BodyText'].spaceAfter=6;styles['Heading3'].spaceBefore=7;styles['Heading3'].spaceAfter=5;styles['Heading1'].fontSize=20;styles['Heading1'].leading=25;styles['Heading1'].textColor=colors.HexColor('#18394f');styles['Heading2'].textColor=colors.HexColor('#176b78');styles['Heading2'].spaceBefore=16;styles['Heading2'].spaceAfter=10
styles.add(ParagraphStyle('GlossaryName',fontName='Helvetica-Bold',fontSize=10,leading=14,spaceBefore=5,spaceAfter=3))
safe=lambda s:html.escape(s.replace('•','|').replace('→','to').replace('’',"'").replace('–','-').replace('—','-').replace('≥','>=').replace('Ω','ohm').replace('−','-').replace('×','x').replace('÷','/'))
p=lambda s,style='BodyText':Paragraph(safe(s),styles[style])
story=[p('ATU VIRTUAL LABORATORY','Heading2'),p(data['title'],'Heading1'),p('A Genesis-reference instrument cluster, electrical loads and reproducible stop-start experiments','Lead'),p('Local review | 2 November 2026'),p('A practical guide from first use to test design. The system is a browser-based educational simulation; physical stop-start and vehicle validation are separate activities.')]
for title,paragraphs in data['sections']:
 story.append(p(title,'Heading2'))
 for text in paragraphs:story.append(p(text))
story.append(p('Complete editable-input glossary','Heading2'))
for field in data['parameters']:
 name=field['title']+(' ('+field['unit']+')' if field['unit'] else '')+' | Default '+str(field['default'])
 story.append(KeepTogether([Paragraph('<b>'+safe(name)+'.</b> '+safe(field['help']),styles['BodyText'])]))
story.append(p('Analytical signal definitions','Heading2'))
for key,text in data['signals'].items():
 import re
 name,_,text=text.partition('. ')
 story.append(KeepTogether([Paragraph('<b>'+safe(name)+'.</b> '+safe(text),styles['BodyText'])]))
story.append(p('Photograph sources and licences','Heading2'))
for title,author,url,licence,licence_url in data['credits']:
 story.append(p(title+' | '+author+' | '+licence));story.append(p(url));story.append(p(licence_url))
story.append(p('Photographs are unmodified originals. The original cluster readings are masked by a browser teaching overlay. Speed and RPM are configured visual cues. The photograph does not supply model calibration. CC BY-SA images retain their stated licences. No manufacturer endorsement is implied.'))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#cbdce5'));canvas.line(48,43,547,43);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#38576a'));canvas.drawString(48,29,'ATU | 12 V micro-hybrid | Learning guide');canvas.drawRightString(547,29,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(output),pagesize=(595.28,841.89),rightMargin=48,leftMargin=48,topMargin=46,bottomMargin=58,title=data['title'],author='ATU Virtual Laboratory').build(story,onFirstPage=footer,onLaterPages=footer)
(root/'static/guides/micro-hybrid-learning-guide.pdf').write_bytes(output.read_bytes())
print(output)

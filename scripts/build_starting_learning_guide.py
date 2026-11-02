"""Generate the downloadable guide from the same data used by the lab page."""
import json,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'static/js/yankson/learning-guide.json').read_text())
output=root/'output/pdf/authenticated-starting-learning-guide.pdf';output.parent.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet();styles.add(ParagraphStyle('Lead',fontName='Helvetica',fontSize=12,leading=18,textColor=colors.HexColor('#38576a'),spaceAfter=16));styles['BodyText'].fontSize=10;styles['BodyText'].leading=15;styles['BodyText'].spaceAfter=11;styles['Heading1'].fontSize=20;styles['Heading1'].leading=25;styles['Heading1'].textColor=colors.HexColor('#18394f');styles['Heading2'].textColor=colors.HexColor('#176b78');styles['Heading2'].spaceBefore=16;styles['Heading2'].spaceAfter=10
safe=lambda s:html.escape(s.replace('•','|').replace('→','to').replace('’',"'").replace('–','-').replace('—','-').replace('≥','>=').replace('Ω','ohm'))
p=lambda s,style='BodyText':Paragraph(safe(s),styles[style])
story=[p('ATU VIRTUAL LABORATORY','Heading2'),p(data['title'],'Heading1'),p('Device verification, microphone commands, CAN feedback and electrical fault diagnosis','Lead'),p(data['version']),p('A practical guide from first use to test design. The system is a browser-based educational simulation; physical engine, ECU and biometric reader validation are separate activities.')]
for title,paragraphs in data['sections']:
 story.append(p(title,'Heading2'))
 for text in paragraphs:story.append(p(text))
for title,items in [('Controller parameter glossary',data['parameters']),('All 28 output signals',data['outputs'])]:
 story.append(p(title,'Heading2'))
 for item in items:
  story.append(KeepTogether([p(item[0]+(' | Default '+item[1] if len(item)==3 else ''),'Heading3'),p(item[-1])]))
story.append(p('Linked references','Heading2'))
for label,url in data['references']:story.append(Paragraph(f'<b>{safe(label)}</b><br/><link href="{url}" color="#176b78">{url}</link>',styles['BodyText']))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#cbdce5'));canvas.line(48,43,547,43);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#38576a'));canvas.drawString(48,29,'ATU | Authenticated Engine Starting | Local review');canvas.drawRightString(547,29,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(output),pagesize=(595.28,841.89),rightMargin=48,leftMargin=48,topMargin=46,bottomMargin=58,title=data['title'],author='ATU Virtual Laboratory').build(story,onFirstPage=footer,onLaterPages=footer)
(root/'static/js/yankson/authenticated-starting-learning-guide.pdf').write_bytes(output.read_bytes())
print(output)

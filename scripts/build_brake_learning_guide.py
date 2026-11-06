"""Generate the downloadable guide from the same data used by the lab page."""
import json,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'static/js/brakelab/learning-guide.json').read_text())
output=root/'output/pdf/brake-allocation-learning-guide.pdf';output.parent.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet();styles.add(ParagraphStyle('Lead',fontName='Helvetica',fontSize=12,leading=18,textColor=colors.HexColor('#38576a'),spaceAfter=16));styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=9;styles['Heading3'].spaceBefore=7;styles['Heading3'].spaceAfter=5;styles['Heading1'].fontSize=20;styles['Heading1'].leading=25;styles['Heading1'].textColor=colors.HexColor('#18394f');styles['Heading2'].textColor=colors.HexColor('#176b78');styles['Heading2'].spaceBefore=16;styles['Heading2'].spaceAfter=10
styles.add(ParagraphStyle('GlossaryName',fontName='Helvetica-Bold',fontSize=10,leading=14,spaceBefore=5,spaceAfter=3))
safe=lambda s:html.escape(s.replace('•','|').replace('→','to').replace('’',"'").replace('–','-').replace('—','-').replace('≥','>=').replace('Ω','ohm'))
p=lambda s,style='BodyText':Paragraph(safe(s),styles[style])
story=[p('ATU VIRTUAL LABORATORY','Heading2'),p(data['title'],'Heading1'),p('Wheel-driven hub generation, disc friction braking and editable calibration','Lead'),p('Local review | 2 November 2026'),p('A practical guide from first use to test design. The system is a browser-based educational simulation; physical hub-motor and vehicle stopping validation are separate activities.')]
for title,paragraphs in data['sections']:
 story.append(p(title,'Heading2'))
 for text in paragraphs:story.append(p(text))
for title,items in [('Operating input glossary',[(f['label']+' ('+f['unit']+')',f['purpose']) for f in data['inputs']]),('Advanced calibration glossary',[(f['title']+' | Default '+str(f['value']),f['help']) for f in data['calibration']]),('Output glossary',[(label+' ('+unit+')',data['outputHelp'][key]+' Export: '+key) for key,label,unit,*rest in data['outputs']])]:
 story.append(p(title,'Heading2'))
 for name,text in items:story.append(KeepTogether([Paragraph('<b>'+safe(name)+'.</b> '+safe(text),styles['BodyText'])]))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#cbdce5'));canvas.line(48,43,547,43);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#38576a'));canvas.drawString(48,29,'ATU | Braking allocation | Learning guide');canvas.drawRightString(547,29,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(output),pagesize=(595.28,841.89),rightMargin=48,leftMargin=48,topMargin=46,bottomMargin=58,title=data['title'],author='ATU Virtual Laboratory').build(story,onFirstPage=footer,onLaterPages=footer)
(root/'static/guides/brake-allocation-learning-guide.pdf').write_bytes(output.read_bytes())
print(output)

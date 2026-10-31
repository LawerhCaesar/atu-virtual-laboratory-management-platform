"""Generate the browser help data and PDF from one reviewed learning source."""
from pathlib import Path
import json
from html import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'static/js/ect/learning-content.json').read_text())
(root/'static/js/ect/learning-content.js').write_text('window.ECTLearningGuide = '+json.dumps(data,ensure_ascii=False)+';\n')
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='GuideBody',fontName='Helvetica',fontSize=10.5,leading=16,textColor=HexColor('#294052'),spaceAfter=10));styles['Title'].fontName='Times-Roman';styles['Title'].textColor=HexColor('#193a53');styles['Heading1'].textColor=HexColor('#1c5869');styles['Heading1'].fontSize=15;styles['Heading1'].leading=20;styles['Heading1'].spaceBefore=18
story=[Paragraph(escape(data['title']).replace('—','-'),styles['Title']),Paragraph(escape(data['subtitle']).replace('·',' | '),styles['GuideBody']),Spacer(1,14)]
for section in data['sections']:
 story.append(Paragraph(escape(section['title']),styles['Heading1']))
 for p in section['paragraphs']:story.append(Paragraph(escape(p).replace('→',' > ').replace('−','-').replace('–','-').replace('°',' deg '),styles['GuideBody']))
story.append(PageBreak());story.append(Paragraph('Complete input glossary',styles['Title']))
for key,(title,text) in data['fields'].items():
 story.append(KeepTogether([Paragraph(escape(title)+' <font size="9">('+key+')</font>',styles['Heading2']),Paragraph(escape(text).replace('°',' deg '),styles['GuideBody'])]))
story.append(Paragraph('Graph and output glossary',styles['Heading1']))
for term,text in data['legends'].items():story.append(KeepTogether([Paragraph(escape(term),styles['Heading2']),Paragraph(escape(text),styles['GuideBody'])]))
def footer(canvas,doc):
 canvas.setStrokeColor(HexColor('#cad9e2'));canvas.line(48,42,547,42);canvas.setFont('Helvetica',8);canvas.setFillColor(HexColor('#476172'));canvas.drawString(48,29,'ATU Virtual Laboratory | ECT learning guide | Educational reference');canvas.drawRightString(547,29,str(doc.page))
SimpleDocTemplate(str(root/'static/guides/ect-learning-guide.pdf'),pagesize=(595,842),leftMargin=48,rightMargin=48,topMargin=48,bottomMargin=60,title=data['title'],author='ATU Virtual Laboratory').build(story,onFirstPage=footer,onLaterPages=footer)

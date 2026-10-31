import json,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'static/guides/engine-live-data-learning-guide.pdf';p.parent.mkdir(exist_ok=True)
d=json.loads(ROOT.joinpath('scripts/engine-guide-content.json').read_text()); styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=15;styles['BodyText'].spaceAfter=9;styles['Heading1'].textColor=colors.HexColor('#193d58');styles['Heading2'].textColor=colors.HexColor('#245e78')
def para(t,style='BodyText'):return Paragraph(html.escape(str(t)),styles[style])
story=[para('Engine Live Data Demonstration','Title'),para('Student learning guide | ICE laboratory | Local interface review'),para('From your first sample to interpreting controller commands. Prepared 30 October 2026. This guide accompanies the section-based input/output workspace.')]
for title,text in d['sections']:story.append(KeepTogether([para(title,'Heading2'),para(text)]))
story +=[PageBreak(),para('Complete input and output glossary','Heading1'),para('Input limits and defaults are taken directly from the preserved module specification. Outputs are calculated or commanded values, rather than measured hardware behaviour.')]
for s in d['signals']:
 title=d['labels'].get(s['name'],s.get('label',s['name']));meaning=d['meanings'].get(s['name'],s.get('description',''))
 rows=[para(title,'Heading2'),para(meaning),para('Signal: '+s['name']+' | Unit: '+str(s.get('unit','')))]
 if 'default' in s:rows.append(para('Default: '+str(s['default'])+' | Accepted range: '+str(s.get('min',''))+' to '+str(s.get('max',''))))
 story.append(KeepTogether(rows))
story += [para('Additional derived signals','Heading2'),para('Imposed actual RPM (ActualRPM): mirrors the student-selected speed. Safe start condition (SafeStartCondition): includes the momentary start request and returns false after that request even during RUN.'),para('Reference evidence and verification','Heading1'),para('Preserved engineering metadata: '+d['source']+'. The module specification, pure reference equations, model and controller are the software evidence for the display. No new OEM or vehicle-specific calibration is claimed.'),para('A repeatable check: load warm defaults; Run; enable ignition and simulated authorisation; Start. At RUN, final injector pulse width is about 1.679 ms. Pause, change O2 voltage from 0.45 V to 0.10 V and Step once. Final pulse width becomes about 1.926 ms and STFT is about +14.7%. Restore the preset before the next independent experiment.'),para('Use a low-battery preset to verify inhibited starting. Use a sensor-disagreement preset to inspect both temperatures, their difference and full cooling commands. Export retained CSV samples for your report and record your inputs, selected preset, observed states and any deviations. Emergency stop remains latched across preset loads until explicitly cleared.'),para('The interface revision changes presentation and guidance only. Software tests establish the educational implementation behaviour; they are not experimental validation against an OEM controller or a physical vehicle.')]
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#c4d9e3'));c.line(42,39,553,39);c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#435e72'));c.drawString(42,26,'ATU Virtual Laboratory | Engine Live Data Demonstration');c.drawRightString(553,26,str(doc.page))
SimpleDocTemplate(str(p),rightMargin=42,leftMargin=42,topMargin=44,bottomMargin=54).build(story,onFirstPage=footer,onLaterPages=footer)

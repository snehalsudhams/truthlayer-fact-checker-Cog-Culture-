"""Create the intentionally mixed true/false sample PDF used for demos."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

BASE = Path(__file__).resolve().parent
OUT = BASE / "assets" / "sample_trap.pdf"
OUT.parent.mkdir(exist_ok=True)
ss = getSampleStyleSheet()
styles = {
    'title': ParagraphStyle('titlex', parent=ss['Title'], fontName='Helvetica-Bold',fontSize=21,leading=26,textColor=colors.HexColor('#163047'),spaceAfter=16),
    'subtitle': ParagraphStyle('subx',parent=ss['Normal'],fontSize=10,leading=16,textColor=colors.HexColor('#66788A'),spaceAfter=16),
    'body': ParagraphStyle('bodyx',parent=ss['Normal'],fontSize=12,leading=20,spaceAfter=13,textColor=colors.HexColor('#223A4F')),
}
doc = SimpleDocTemplate(str(OUT),pagesize=A4,topMargin=50,bottomMargin=45,leftMargin=55,rightMargin=55)
claims = [
    '1. The first iPhone was introduced by Apple in January 2007.',
    '2. Neil Armstrong first walked on the Moon in 1985.',
    '3. Mount Everest is exactly 6,500 metres above sea level.',
    '4. Microsoft announced its acquisition of LinkedIn in 2016 for approximately 26.2 billion US dollars.',
    '5. The chemical symbol for gold is Ag.',
    '6. Chandrayaan-3 landed on the Moon in August 2023.',
    '7. YouTube was founded in 2011.',
    '8. Amazon was founded in 2024.',
]
flow = [Paragraph('Claims for Fact-Checking', styles['title']),
        Paragraph('Sample test document containing a deliberate mix of accurate and incorrect statements. Intended to validate claim extraction, classification, corrections, and source citations.',styles['subtitle']),Spacer(1,8)]
flow.extend(Paragraph(claim,styles['body']) for claim in claims)
doc.build(flow)
print(OUT)

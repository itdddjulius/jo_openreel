from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
ROOT=Path(__file__).resolve().parent; DOCS=["README","USER-GUIDE","FUNCT-GUIDE","TESTS"]
BG=HexColor("#030504"); WHITE=HexColor("#F4FFF7"); GREEN=HexColor("#27EF78"); MUTED=HexColor("#ADC0B1")
pdfmetrics.registerFont(TTFont("DejaVu","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"));pdfmetrics.registerFont(TTFont("DejaVuBold","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
def page(c,d):
 c.saveState();c.setFillColor(BG);c.rect(0,0,A4[0],A4[1],fill=1,stroke=0);c.setStrokeColor(GREEN);c.line(36,32,A4[0]-36,32);c.setFillColor(MUTED);c.setFont("DejaVu",8);c.drawString(36,20,"OPENREELpy");c.drawRightString(A4[0]-36,20,f"Page {d.page}");c.restoreState()
def build(name):
 styles=getSampleStyleSheet();title=ParagraphStyle("title",parent=styles["Title"],fontName="DejaVuBold",fontSize=24,leading=29,textColor=GREEN,spaceAfter=16);h=ParagraphStyle("h",parent=styles["Heading2"],fontName="DejaVuBold",fontSize=14,leading=18,textColor=GREEN,spaceBefore=10,spaceAfter=7);body=ParagraphStyle("body",parent=styles["BodyText"],fontName="DejaVu",fontSize=10.3,leading=15,textColor=WHITE,spaceAfter=9);story=[]
 for line in (ROOT/"docs"/f"{name}.md").read_text(encoding="utf-8").splitlines():
  s=line.strip();safe=s.replace("—","-").replace("**","").replace("`","").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
  if s=="<!-- PAGE BREAK -->":story.append(PageBreak())
  elif not s:story.append(Spacer(1,5))
  elif s.startswith("# "):story.append(Paragraph(safe[2:],title))
  elif s.startswith("## "):story.append(Paragraph(safe[3:],h))
  else:story.append(Paragraph(safe,body))
 out=ROOT/"docs"/f"{name}.pdf";SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=44).build(story,onFirstPage=page,onLaterPages=page)
for doc in DOCS:build(doc)

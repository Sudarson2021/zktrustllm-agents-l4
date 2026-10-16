#!/usr/bin/env python3
"""Build an editable-Markdown reviewer response as a paginated PDF.

Requires reportlab; fonts are standard DejaVu TTF files on Linux.
"""
from pathlib import Path
import argparse,re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[3]
PAPER=ROOT/'paper/tnsm_revision_20261015'

def build(source,destination):
    font_roots=[Path('/usr/share/fonts/truetype/dejavu')]
    try:
        import matplotlib
        font_roots.append(Path(matplotlib.get_data_path())/'fonts/ttf')
    except ImportError:
        pass
    for name,file in [('Body','DejaVuSerif.ttf'),('Body-Bold','DejaVuSerif-Bold.ttf'),('Body-Italic','DejaVuSerif-Italic.ttf'),('Sans','DejaVuSans.ttf'),('Sans-Bold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:
        font=next((folder/file for folder in font_roots if (folder/file).is_file()),None)
        if font is None:raise FileNotFoundError('Install complete DejaVu TTF fonts or matplotlib: '+file)
        pdfmetrics.registerFont(TTFont(name,str(font)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Body-Bold',italic='Body-Italic',boldItalic='Body-Bold')
    navy=colors.HexColor('#173957');gray=colors.HexColor('#4a5660')
    body=ParagraphStyle('body',fontName='Body',fontSize=10.1,leading=13.8,spaceAfter=7)
    title=ParagraphStyle('title',fontName='Sans-Bold',fontSize=19,leading=24,textColor=navy,spaceAfter=14)
    heading=ParagraphStyle('heading',fontName='Sans-Bold',fontSize=11.7,leading=16,textColor=navy,spaceBefore=12,spaceAfter=8,keepWithNext=True)
    quote=ParagraphStyle('quote',parent=body,fontName='Body-Italic',fontSize=9.4,leading=13.1,textColor=gray,leftIndent=12,rightIndent=9,borderColor=colors.HexColor('#b7c8d7'),borderWidth=.5,borderPadding=7,backColor=colors.HexColor('#f3f6f8'),spaceBefore=3,spaceAfter=12)
    location=ParagraphStyle('location',parent=body,fontSize=9.1,leading=12,textColor=navy,spaceAfter=10)
    def inline(text):
        text=escape(text)
        text=re.sub(r'`([^`]+)`',r'<font name="Mono">\1</font>',text)
        text=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)
        return text
    def decorate(c,doc):
        c.saveState();w,h=A4
        c.setStrokeColor(colors.HexColor('#d6dde4'));c.setLineWidth(.5)
        c.line(48,h-37,w-48,h-37);c.line(48,37,w-48,37)
        c.setFont('Sans',8);c.setFillColor(gray)
        c.drawString(48,h-28,'TNSM-2026-12002 · Major revision R1')
        c.drawString(48,24,'16 October 2026 · Response to reviewers')
        c.drawRightString(w-48,24,str(doc.page));c.restoreState()
    story=[]
    for block in re.split(r'\n\s*\n',source.read_text().strip()):
        block=' '.join(block.splitlines())
        if block.startswith('# '):story.append(Paragraph(inline(block[2:]),title))
        elif block.startswith('## '):story.append(Paragraph(inline(block[3:]),heading))
        elif block.startswith('> '):story.append(Paragraph(inline(block[2:]),quote))
        elif block.startswith('**Locations:**'):story.append(Paragraph(inline(block),location))
        else:story.append(Paragraph(inline(block),body))
    destination.parent.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(destination),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=53,bottomMargin=52,title='Response to Reviewers — TNSM-2026-12002',author='Sudarson Karmaker et al.')
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=PAPER/'RESPONSE_TO_REVIEWERS.md')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();build(args.source,args.output)
    print(args.output)

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from datetime import datetime
from zoneinfo import ZoneInfo
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether

FONT_DIR=Path(reportlab.__file__).parent/'fonts'
for name,file in [('Vera','Vera.ttf'),('VeraBold','VeraBd.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
NAVY=colors.HexColor('#123450'); TEAL=colors.HexColor('#086b67'); LIGHT=colors.HexColor('#edf4f7'); RED=colors.HexColor('#df4051')
def euros(v): return f'{v:,.2f}'.replace(',', ' ').replace('.', ',')+' €'

def make_pdf(result, company, profile, advisor, contact, basis, assumptions):
    buf=BytesIO(); styles=getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName='VeraBold' if name.startswith('Heading') else 'Vera'
        styles[name].textColor=NAVY
    styles.add(ParagraphStyle('Label',fontName='VeraBold',fontSize=8,leading=12,textColor=TEAL))
    styles.add(ParagraphStyle('Fine',fontName='Vera',fontSize=7.5,leading=11,textColor=colors.HexColor('#536577')))
    styles.add(ParagraphStyle('White',fontName='VeraBold',fontSize=9,leading=13,textColor=colors.white))
    styles.add(ParagraphStyle('Number',fontName='VeraBold',fontSize=17,leading=24,textColor=NAVY))
    styles.add(ParagraphStyle('Gain',fontName='VeraBold',fontSize=25,leading=32,textColor=TEAL if result['gain']>=0 else NAVY))
    styles['Normal'].fontSize=9;styles['Normal'].leading=13
    styles['Heading2'].spaceBefore=8;styles['Heading2'].spaceAfter=6
    styles['Heading3'].spaceBefore=6;styles['Heading3'].spaceAfter=4
    p=lambda text,style='Normal':Paragraph(escape(str(text)),styles[style])
    logo=Path(__file__).resolve().parent.parent/'logo_cma_na_gironde.png'
    left=p('CMA Nouvelle-Aquitaine','Heading2')
    if logo.exists():
        from PIL import Image as PILImage
        with PILImage.open(logo) as im: w,h=im.size
        scale=min(180/w,60/h)
        left=Image(str(logo),width=w*scale,height=h*scale)
    header=Table([[left,p('PASS CMA LIBERTÉ\nVotre simulation personnalisée','Heading2')]],colWidths=[220,287])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('LINEBELOW',(0,0),(-1,-1),2,RED),('BOTTOMPADDING',(0,0),(-1,-1),14)]))
    story=[header,Spacer(1,10),p(company or 'Votre entreprise','Heading2'),p(f"{profile} · Comparaison en {basis} · Établie le {datetime.now(ZoneInfo('Europe/Paris')):%d/%m/%Y}"),Spacer(1,10)]
    gain=result['gain']; label='ÉCONOMIE ESTIMÉE SUR 12 MOIS' if gain>0 else ('COÛT SUPPLÉMENTAIRE SUR 12 MOIS' if gain<0 else 'BUDGET À L’ÉQUILIBRE')
    card=Table([[p(label,'Label')],[p(euros(abs(gain)),'Gain')],[p('Abonnement déduit · Selon les besoins renseignés','Fine')]],colWidths=[507])
    card.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e6f3ef')),('LEFTPADDING',(0,0),(-1,-1),16),('TOPPADDING',(0,0),(-1,0),12),('BOTTOMPADDING',(0,-1),(-1,-1),12)]))
    story += [card,Spacer(1,8)]
    totals=Table([[p('SANS PASS','Label'),p('AVEC PASS','Label')],[p(euros(result['before']),'Number'),p(euros(result['after']),'Number')]],colWidths=[253.5,253.5])
    totals.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('LEFTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,0),9),('BOTTOMPADDING',(0,-1),(-1,-1),6)]))
    story += [totals,Spacer(1,10),p('Le détail de votre comparaison','Heading2')]
    data=[[p('Prestations prévues','White'),p(f'Sans PASS ({basis})','White'),p(f'Avec PASS ({basis})','White')]]
    for name,a,b in result['rows']:
        if not a and not b and 'Abonnement' not in name:continue
        data.append([p(name),p(euros(a)),p('Inclus' if a>0 and b==0 and not name.startswith('Formation') else euros(b))])
    data.append([p('TOTAL SUR 12 MOIS'),p(euros(result['before'])),p(euros(result['after']))])
    table=Table(data,colWidths=[277,115,115],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white,LIGHT]),('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#dceeea')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),10)]))
    story += [table,Spacer(1,8),p('Et vos droits encore disponibles ?','Heading3'),p(f"{result['remaining_formalities']} formalité(s) et {result['remaining_hours']:g} heure(s) de conseil. Non comptabilisées dans l’économie annoncée.",'Fine'),Spacer(1,6),p('Hypothèses retenues','Heading3')]
    story += [p('• '+x,'Fine') for x in assumptions]
    story += [Spacer(1,6),KeepTogether([p('Votre conseiller CMA','Heading3'),p(advisor or 'Votre conseiller'),p(contact)]),Spacer(1,10),p('Estimation indicative sans valeur contractuelle. Engagement initial de 12 mois, puis reconduction mensuelle. Hors frais légaux et redevances. Économies conditionnées à l’utilisation des prestations.','Fine')]
    def footer(c,d):
        c.setStrokeColor(RED);c.line(44,35,551,35);c.setFont('Vera',7);c.setFillColor(NAVY);c.drawString(44,23,'CMA Nouvelle-Aquitaine · PASS CMA Liberté');c.drawRightString(551,23,f'{d.page}')
    SimpleDocTemplate(buf,rightMargin=38,leftMargin=38,topMargin=30,bottomMargin=48,title='Votre simulation PASS CMA Liberté').build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()

from io import BytesIO
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
FONT_DIR=Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera",str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("VeraBold",str(FONT_DIR / "VeraBd.ttf")))
from xml.sax.saxutils import escape
from datetime import date
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def euros(v): return f'{v:,.2f}'.replace(',', ' ').replace('.', ',')+' €'

def make_pdf(result, company, profile, advisor, contact, basis, assumptions):
    buf=BytesIO(); styles=getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName = "VeraBold" if name.startswith("Heading") or name=="Title" else "Vera"
    styles.add(ParagraphStyle('SmallPrint',parent=styles['Normal'],fontSize=8,leading=11,textColor=colors.HexColor('#526477')))
    styles.add(ParagraphStyle('BigGain',parent=styles['Heading1'],fontSize=25,leading=30,textColor=colors.HexColor('#125f60')))
    p=lambda text,style='Normal':Paragraph(escape(str(text)),styles[style])
    story=[p('CMA Nouvelle-Aquitaine','Heading2'),p('PASS CMA Liberté','Title'),p('Votre comparaison personnalisée sur 12 mois','Heading2'),p(company or 'Votre entreprise'),p(f'{profile} | Comparaison en {basis} | {date.today():%d/%m/%Y}'),Spacer(1,18)]
    gain=result['gain']
    label=f'{euros(gain)} d’économie estimée' if gain>0 else (f'{euros(-gain)} de coût supplémentaire' if gain<0 else 'Un budget à l’équilibre')
    story += [p(label,'BigGain'),p('Abonnement déduit. Calcul limité aux besoins renseignés.'),Spacer(1,18)]
    data=[[p('Prestations'),p('Sans PASS'),p('Avec PASS')]]
    data += [[p(name),p(euros(a)),p(euros(b))] for name,a,b in result['rows']]
    data += [[p('TOTAL'),p(euros(result['before'])),p(euros(result['after']))]]
    table=Table(data,colWidths=[275,100,100],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f0f5')),('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#dceeea')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d8e1e8'))]))
    story += [table,Spacer(1,16),p('Vos droits encore disponibles','Heading2'),p(f"{result['remaining_formalities']} formalité(s) et {result['remaining_hours']:g} heure(s) de conseil. Leur valeur n’est pas ajoutée au gain."),Spacer(1,10),p('Hypothèses de votre simulation','Heading2')]
    story += [p(x,'SmallPrint') for x in assumptions]
    story += [Spacer(1,14),p('Votre interlocuteur CMA','Heading2'),p(advisor or 'Votre conseiller'),p(contact),Spacer(1,10),p('Estimation indicative, sans valeur contractuelle. Engagement initial de 12 mois ; reconduction mensuelle. Hors frais légaux et redevances, identiques dans les deux scénarios. Les économies supposent l’utilisation effective des prestations.','SmallPrint')]
    def footer(c,d):
        c.setFont('Vera',8); c.setFillColor(colors.HexColor('#526477')); c.drawString(60,30,'PASS CMA Liberté | Simulation conseiller');c.drawRightString(535,30,str(d.page))
    SimpleDocTemplate(buf,rightMargin=60,leftMargin=60,topMargin=40,bottomMargin=50,title='Simulation PASS CMA Liberté').build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()

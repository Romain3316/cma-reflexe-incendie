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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, Flowable

FONT_DIR=Path(reportlab.__file__).parent/'fonts'
for name,file in [('Vera','Vera.ttf'),('VeraBold','VeraBd.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
NAVY=colors.HexColor('#123450'); TEAL=colors.HexColor('#103450'); LIGHT=colors.HexColor('#edf4f7'); RED=colors.HexColor('#ef4639')
def euros(v): return f'{v:,.2f}'.replace(',', ' ').replace('.', ',')+' €'

class RightsCard(Flowable):
    """Two annual rights, with a proportional remaining-rights bar."""
    def __init__(self, remaining, kind):
        Flowable.__init__(self)
        self.width=244; self.height=108
        self.remaining=float(remaining); self.kind=kind

    def draw(self):
        c=self.canv
        c.setFillColor(LIGHT if self.remaining else colors.HexColor('#f0f1f3'))
        c.roundRect(0,0,self.width,self.height,10,fill=1,stroke=0)
        c.setFillColor(NAVY);c.setFont('VeraBold',9)
        c.drawString(14,88,'VOS FORMALITÉS' if self.kind=='formalities' else 'VOTRE CONSEIL SUR MESURE')
        c.setFont('VeraBold',25)
        c.drawString(14,54,f'{self.remaining:g}'+(' h' if self.kind=='hours' else ''))
        c.setFont('Vera',8)
        label='disponible' if self.remaining==1 else 'disponibles'
        c.drawString(75,59,f'{label} sur 2'+(' h' if self.kind=='hours' else ''))
        c.setFillColor(colors.HexColor('#d5dfe6'))
        c.roundRect(14,34,216,7,3,fill=1,stroke=0)
        if self.remaining:
            c.setFillColor(RED);c.roundRect(14,34,216*min(1,self.remaining/2),7,3,fill=1,stroke=0)
        c.setFillColor(NAVY);c.setFont('Vera',7)
        c.drawString(14,15,'Pour vos prochains projets' if self.remaining else 'Entièrement prévu dans cette simulation')

def make_pdf(result, company, profile, advisor, contact, basis, assumptions, trainings=None):
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
    pass_logo=Image(str(Path(__file__).parent/'assets/pass-logo.png'),width=116,height=63)
    header=Table([[pass_logo,left]],colWidths=[287,220])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('LINEBELOW',(0,0),(-1,-1),2,RED),('BOTTOMPADDING',(0,0),(-1,-1),14)]))
    story=[header,Spacer(1,10),p('Votre métier. Vos projets. Votre PASS.','Heading1'),p(company or 'Votre entreprise','Heading2'),p(f"{profile} · Comparaison en {basis} · Établie le {datetime.now(ZoneInfo('Europe/Paris')):%d/%m/%Y}"),Spacer(1,10)]
    gain=result['gain']; label='ÉCONOMIE ESTIMÉE SUR 12 MOIS' if gain>0 else ('COÛT SUPPLÉMENTAIRE SUR 12 MOIS' if gain<0 else 'BUDGET À L’ÉQUILIBRE')
    card=Table([[p(label,'Label')],[p(euros(abs(gain)),'Gain')],[p('Abonnement déduit · Selon les besoins renseignés','Fine')]],colWidths=[335])
    card.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fff0ec')),('LEFTPADDING',(0,0),(-1,-1),16),('TOPPADDING',(0,0),(-1,0),12),('BOTTOMPADDING',(0,-1),(-1,-1),12)]))
    visual=Image(str(Path(__file__).parent/'assets/pass-card.png'),width=156,height=158)
    hero=Table([[card,visual]],colWidths=[339,168])
    hero.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
    story += [hero,Spacer(1,8)]
    totals=Table([[p('SANS PASS','Label'),p('AVEC PASS','Label')],[p(euros(result['before']),'Number'),p(euros(result['after']),'Number')]],colWidths=[253.5,253.5])
    totals.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('LEFTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,0),9),('BOTTOMPADDING',(0,-1),(-1,-1),6)]))
    story += [totals,Spacer(1,10),p('Le détail de votre comparaison','Heading2')]
    data=[[p('Prestations prévues','White'),p(f'Sans PASS ({basis})','White'),p(f'Avec PASS ({basis})','White')]]
    for name,a,b in result['rows']:
        if not a and not b and 'Abonnement' not in name:continue
        data.append([p(name),p(euros(a)),p('Inclus' if a>0 and b==0 and not name.startswith('Formation') else euros(b))])
    data.append([p('TOTAL SUR 12 MOIS'),p(euros(result['before'])),p(euros(result['after']))])
    table=Table(data,colWidths=[277,115,115],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white,LIGHT]),('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#ffe4de')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),10)]))
    rights=Table([[RightsCard(result['remaining_formalities'],'formalities'),'',RightsCard(result['remaining_hours'],'hours')]],colWidths=[244,19,244])
    rights.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('VALIGN',(0,0),(-1,-1),'TOP')]))
    rights_title='Vous pourrez aussi profiter de…' if result['remaining_formalities'] or result['remaining_hours'] else 'Vos droits sont entièrement mobilisés'
    story += [table,Spacer(1,8),KeepTogether([p(rights_title,'Heading3'),rights,Spacer(1,5),p('Droits restants après les besoins prévus dans cette simulation. Non comptabilisés dans l’économie présentée.','Fine')])]
    story += [PageBreak(),p('Plus de liberté pour votre métier.','Heading1'),p('Vous consacrez votre énergie à votre métier. Le PASS CMA Liberté vous aide à trouver les bons interlocuteurs pour vos démarches et vos décisions.'),Spacer(1,14)]
    if trainings:
        story += [p('Vos projets de formation','Heading2')]
        for training in trainings:
            content=[[p(training['title'],'Heading3')],[p(f"{training['days']:g} journée(s) prévue(s)",'Label')]]
            if training.get('summary'):
                content += [[p('Ce que vous allez apprendre','Label')],[p(training['summary'])]]
            if training.get('condition'):
                content += [[p('Condition PASS : '+training['condition'],'Fine')]]
            if training.get('source_url'):
                url=escape(training['source_url'],{'"':'&quot;'})
                content += [[Paragraph(f'<link href="{url}" color="#123450"><u>En savoir plus sur le site CMA</u></link>',styles['Fine'])]]
            block=Table(content,colWidths=[507])
            block.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('LINEBEFORE',(0,0),(0,-1),3,RED),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,0),8),('BOTTOMPADDING',(0,-1),(-1,-1),12)]))
            story += [KeepTogether([block,Spacer(1,10)])]
        story += [p('Votre PASS au quotidien','Heading2')]
    arguments=[('Un interlocuteur privilégié', 'Un point d’entrée à la CMA pour faire le point sur vos besoins et vous orienter vers l’expertise adaptée à votre entreprise.')]
    if any(a > b and not name.startswith(('Conseil', 'Formation', 'Abonnement')) for name,a,b in result['rows']):
        arguments.append(('Vos démarches, accompagnées', 'Pour les formalités retenues dans votre simulation, vous bénéficiez de l’appui de la CMA pour préparer et suivre votre dossier. Vous pouvez vous concentrer sur votre activité.'))
    if any(name.startswith('Conseil') and a > 0 for name,a,b in result['rows']):
        arguments.append(('Un regard extérieur sur vos décisions', 'Prix, organisation, développement commercial ou numérique : utilisez vos rendez-vous de conseil pour avancer sur les questions concrètes de votre entreprise. Deux rendez-vous d’une heure sont inclus par an.'))
    if any(name.startswith('Formation') and a > b for name,a,b in result['rows']):
        arguments.append(('Des compétences plus accessibles', 'Pour les journées éligibles de votre simulation, le PASS réduit votre reste à charge jusqu’à 70 € par jour. Un moyen de développer vos compétences tout en maîtrisant votre budget.'))
    benefit_cards=[]
    for title,body in arguments:
        block=Table([[p(title,'Heading3')],[p(body)]],colWidths=[247])
        block.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,0),8),('BOTTOMPADDING',(0,-1),(-1,-1),12)]))
        benefit_cards.append(block)
    for i in range(0,len(benefit_cards),2):
        pair=Table([[benefit_cards[i],'',benefit_cards[i+1] if i+1<len(benefit_cards) else '']],colWidths=[247,13,247])
        pair.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
        story += [KeepTogether([pair,Spacer(1,8)])]
    if gain>0:
        message=f'Avec les besoins identifiés ensemble, votre économie estimée atteint {euros(gain)} sur douze mois, abonnement déduit. Votre conseiller vous accompagne pour organiser l’utilisation de vos prestations.'
    else:
        message='Avec les seuls besoins renseignés, le PASS ne dégage pas d’économie financière à ce stade. Échangeons sur vos projets pour apprécier si les services inclus et le suivi correspondent réellement à vos attentes.'
    story += [p('Faisons le point sur vos projets','Heading2'),p(message),Spacer(1,12),p('Les bases de votre comparaison','Heading3')]
    story += [p('• '+x,'Fine') for x in assumptions]
    story += [Spacer(1,6),KeepTogether([p('Votre conseiller CMA','Heading3'),p(advisor or 'Votre conseiller'),p('Contactez votre CMA au 3006','Heading3')]),Spacer(1,10),p('Estimation indicative sans valeur contractuelle. Engagement initial de 12 mois, puis reconduction mensuelle. Hors frais légaux et redevances. Économies conditionnées à l’utilisation des prestations.','Fine')]
    def footer(c,d):
        c.setFillColor(NAVY);c.rect(0,0,596,40,fill=1,stroke=0);c.setFillColor(RED);c.roundRect(44,38,72,4,2,fill=1,stroke=0);c.setFont('Vera',7);c.setFillColor(colors.white);c.drawString(44,23,'CMA Nouvelle-Aquitaine · PASS CMA Liberté');c.drawRightString(551,23,f'{d.page}')
    SimpleDocTemplate(buf,rightMargin=38,leftMargin=38,topMargin=30,bottomMargin=48,title='Votre simulation PASS CMA Liberté').build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()

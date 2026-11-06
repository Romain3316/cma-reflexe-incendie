from pathlib import Path
import json
import streamlit as st
from calculator import calculate
from pdf_export import make_pdf, euros

st.set_page_config(page_title='PASS CMA | Simulateur conseiller',page_icon='🧮',layout='wide')
st.markdown('''<style>.stApp{background:#f5f7fa} h1,h2,h3{color:#153650} [data-testid="stMetric"]{background:white;border:1px solid #dce5ec;border-radius:12px;padding:18px} .block-container{padding-top:2rem} </style>''',unsafe_allow_html=True)
T=json.loads(Path(__file__).with_name('tariffs.json').read_text())
st.caption('CMA NOUVELLE-AQUITAINE · OUTIL CONSEILLER · PREMIÈRE VERSION')
st.title('Le PASS, chiffres à l’appui.')
st.write('Comparez les dépenses prévues sur douze mois et remettez une fiche personnalisée à votre client.')
with st.sidebar:
    st.header('L’entreprise')
    company=st.text_input('Nom de l’entreprise',max_chars=120)
    profile=st.selectbox('Forme juridique',['Micro-entreprise','EI au réel','Société'])
    basis=st.radio('Base de comparaison',['TTC','HT'],help='TTC si TVA non récupérée ; HT si récupération intégrale. Récupération partielle non gérée dans cette V1.')
    st.caption('Le statut ne détermine pas automatiquement la récupération de TVA.')
    free=st.checkbox('2 mois offerts : éligibilité confirmée',help='Souscription lors d’une prestation CMA d’assistance à l’immatriculation. Engagement de 12 mois maintenu.')
    advisor=st.text_input('Conseiller',max_chars=100)
    contact=st.text_input('Contact professionnel',max_chars=180)
left,right=st.columns([1.1,1],gap='large')
with left:
    st.subheader('01 · Les besoins réels')
    st.caption('Sélectionnez uniquement les prestations prévues dans les 12 prochains mois.')
    options=list(T['formalites'])
    if profile=='Micro-entreprise': options.remove("Contrat d'apprentissage")
    formalities=[]
    n=st.number_input('Nombre de formalités prévues',0,6,0)
    for i in range(n):
        with st.container(border=True):
            label=st.selectbox(f'Formalité {i+1}',options,key=f'kind_{i}_{profile}')
            tariff=T['formalites'][label]['societe' if profile=='Société' else 'ei']
            st.write(f'Prix catalogue : **{euros(tariff)} HT**')
            checked=st.checkbox('Prestation et tarif applicables confirmés',key=f'confirm_{i}_{profile}_{label}')
            covered=st.checkbox('Affecter au PASS',value=i<2,key=f'covered_{i}')
            formalities.append(dict(label=label,ht=tariff,covered=covered,confirmed=checked))
    hours=st.number_input('Heures de conseil nécessaires',0.0,20.0,0.0,.5)
    st.caption('79 € HT/heure · 2 heures maximum couvertes. Conseil Flash gratuit exclu du calcul.')
    st.subheader('02 · La formation')
    days=st.number_input('Jours de formation prévus',0,100,0)
    rac=st.number_input(f'Reste à charge par jour avant PASS ({basis})',0.0,10000.0,0.0,5.0)
    eligible=st.checkbox('Formation éligible et financement vérifiés')
    cap=st.number_input(f'Réduction journalière validée dans cette même base ({basis})',0.0,70.0,0.0,5.0,help='Saisir le montant validé par le service formation. Ne pas convertir automatiquement 70 € HT en 84 € TTC.')
    st.caption('Exclusions : e-learning, réglementaire, certifiant/qualifiant/diplômant et CPF. Formation courte de moins de 10 jours ; plusieurs sessions possibles. Une participation par session à tarif préférentiel.')
    st.subheader('03 · Validation conseiller')
    validated=st.checkbox('J’ai vérifié la grille tarifaire et les hypothèses de cette simulation')
with right:
    st.subheader('Votre comparaison annuelle')
    try:
        result=calculate(formalities,hours,days,rac,eligible,cap,basis,free)
    except ValueError as e:
        st.error(str(e)); st.stop()
    a,b=st.columns(2)
    a.metric(f'Sans PASS · {basis}',euros(result['before']))
    b.metric(f'Avec PASS · {basis}',euros(result['after']))
    gain=result['gain']
    if gain>0: st.success(f"Économie estimée : {euros(gain)} / an, abonnement déduit.")
    elif gain<0: st.info(f"Coût supplémentaire : {euros(-gain)} / an pour les besoins renseignés.")
    else: st.info('Budget à l’équilibre pour les besoins renseignés.')
    st.table([{'Prestation':name,f'Sans PASS ({basis})':euros(a),f'Avec PASS ({basis})':euros(b)} for name,a,b in result['rows']])
    st.caption(f"Abonnement : {euros(result['subscription'])} sur 12 mois. {'Deux mensualités offertes.' if free else 'Douze mensualités.'}")
    st.write(f"**Droits encore disponibles :** {result['remaining_formalities']} formalité(s), {result['remaining_hours']:g} h de conseil. Non valorisés dans le gain.")
    ready=validated and all(f['confirmed'] for f in formalities) and (not days or eligible)
    assumptions=[f"Profil : {profile}. Base {basis}, choisie selon récupération de TVA.",f"Conseil : 79 € HT/h ; {hours:g} h prévues, dont {min(hours,2):g} h couvertes.",f"Formation : {days} jours ; reste à charge {euros(rac)}/jour ; réduction validée {euros(cap)}/jour, limitée au reste à charge.",f"Grille publique relevée le {T['date_releve']}. Applicabilité confirmée par le conseiller pour cette simulation.", 'Deux mois offerts confirmés : souscription avec assistance CMA à l’immatriculation.' if free else 'Aucune gratuité d’abonnement retenue.', 'Les prestations affectées au PASS sont indiquées à zéro dans la colonne Avec PASS. Les frais légaux ne sont pas inclus.']
    if ready:
        st.download_button('Télécharger la fiche client PDF',make_pdf(result,company,profile,advisor,contact,basis,assumptions),'simulation_pass_cma.pdf','application/pdf',type='primary',use_container_width=True)
        st.caption('À joindre à votre mail habituel. Aucune donnée client enregistrée sur disque par cette application.')
    else: st.warning('Aperçu de travail : confirmez les tarifs et l’éligibilité avant de générer le PDF client.')
with st.expander('Grille tarifaire et sources — contrôle avant diffusion'):
    st.write('Tarifs publics relevés le 6 novembre 2026 ; validation interne non présumée. Modifiables dans tariffs.json sur GitHub. Conseil : 79 € HT/h fixé dans calculator.py.')
    st.table([{'Prestation':k,'EI / micro HT':v['ei'],'Société HT':v['societe']} for k,v in T['formalites'].items()])
    for name,v in T['formalites'].items():
        slug=v['source']
        if slug.endswith('-'):
            for suffix in ['ei-micro-entreprise-ou-reel','societe']: st.markdown(f"[{name} — {suffix}](https://cma-nouvelleaquitaine.fr/catalogue/{slug}{suffix})")
        else: st.markdown(f"[{name}](https://cma-nouvelleaquitaine.fr/catalogue/{slug})")
    st.markdown('[Conseil sur mesure](https://cma-nouvelleaquitaine.fr/catalogue/conseil-sur-mesure) · [Offre PASS](https://cma-nouvelleaquitaine.fr/pass-cma-liberte)')
st.caption('Simulation indicative · Engagement initial de 12 mois · Les avantages partenaires et le suivi ne sont pas monétisés. Usage conseiller ; cette V1 ne contient pas d’authentification intégrée.')

from pathlib import Path
import json
import base64
import streamlit as st
from calculator import calculate
from pdf_export import make_pdf, euros

# Sélection issue du catalogue CMA NA consulté le 10/11/2026.
# Durées converties sur 7 h/j ; cas ambigus et formations réglementaires exclus.
FORMATIONS = {
  "Numérique": {
    "Communication et outils numériques": [
      [
        "Bien débuter avec les IA génératives",
        1
      ],
      [
        "Développer sa communication digitale",
        2
      ],
      [
        "Mon entreprise sur Facebook : bien vendre",
        1
      ],
      [
        "Créer et développer son compte Instagram professionnel",
        1
      ],
      [
        "Instagram niveau intermédiaire",
        1
      ],
      [
        "Mon entreprise sur LinkedIn",
        1
      ],
      [
        "Communiquer avec son époque : TikTok",
        1
      ],
      [
        "Réaliser des visuels professionnels avec Canva",
        1
      ],
      [
        "Réussir ses photos pour valoriser ses produits et ses services",
        1
      ],
      [
        "Améliorer la visibilité de son entreprise en optimisant son référencement",
        1
      ]
    ]
  },
  "Gestion et développement": {
    "Gestion et prix": [
      [
        "Comment organiser et gérer ma micro-entreprise au quotidien ?",
        1
      ],
      [
        "Dépassement de seuil du CA, quel impact sur votre statut ?",
        1
      ],
      [
        "Gérer ma TVA",
        1
      ],
      [
        "Micro-entreprise : calculez vos tarifs",
        2
      ],
      [
        "Déterminer mes coûts de revient pour mieux fixer mes prix de vente",
        2
      ],
      [
        "Savoir rédiger vos Conditions Générales de Vente",
        2
      ],
      [
        "Passer à la facture électronique",
        1
      ],
      [
        "Maîtriser sa facturation électronique avec une solution de gestion et facturation",
        1
      ]
    ],
    "Vente et relation client": [
      [
        "Construire et développer mon offre commerciale",
        3
      ],
      [
        "Techniques de vente : les fondamentaux",
        2
      ],
      [
        "Augmenter ses ventes en magasin",
        2
      ],
      [
        "Augmentez vos ventes sur les foires, salons et marchés",
        2
      ],
      [
        "Accueil relation client",
        1
      ],
      [
        "Optimiser sa relation client digitale",
        1
      ],
      [
        "Excellence Client",
        1
      ],
      [
        "Gestion des conflits et des incivilités",
        1
      ],
      [
        "Savoir accueillir un client en situation de handicap",
        1
      ],
      [
        "Évènementiel : créer, promouvoir et valoriser un événement",
        2
      ],
      [
        "Optimiser ses revenus avec le yield management",
        2
      ]
    ]
  },
  "Management": {
    "Équipe et ressources humaines": [
      [
        "Manager une équipe au quotidien dans une TPE-PME",
        2
      ],
      [
        "Recruter ses collaborateurs",
        1
      ],
      [
        "Intégrer et former les nouveaux embauchés",
        1
      ],
      [
        "Fidéliser ses collaborateurs",
        1
      ],
      [
        "Manager au quotidien en hôtels, cafés, restaurants",
        2
      ]
    ]
  },
  "Technique": {
    "Beauté et bien-être": [
      [
        "Modelage ayurvédique",
        2
      ],
      [
        "Modelage singapourien",
        2
      ],
      [
        "Massage Deep Tissue",
        2
      ],
      [
        "Modelage japonais visage type Kobido",
        2
      ],
      [
        "Massage crânien",
        2
      ],
      [
        "Réflexologie plantaire",
        2
      ]
    ],
    "Métiers de bouche et restauration": [
      [
        "Snacking",
        3
      ],
      [
        "Snacking tradition — produits de saison",
        1
      ],
      [
        "Techniques pizza/crêpe",
        3
      ],
      [
        "Techniques créativité culinaire",
        3
      ],
      [
        "Les cuisines du monde",
        3
      ],
      [
        "Techniques de cuisson basse température, sous vide, à la vapeur et mixtes",
        3
      ],
      [
        "Techniques de cuissons sous-vide, à juste température et cuissons de nuit",
        2
      ],
      [
        "Pâtisseries",
        3
      ],
      [
        "Pains, viennoiseries",
        3
      ],
      [
        "Réalisations spécifiques à l’activité traiteur",
        3
      ],
      [
        "Nutrition diététique découverte",
        2
      ],
      [
        "Mettre en place les fiches techniques pour optimiser ses coûts et ratios",
        2
      ],
      [
        "Développer une gamme de produits secs en charcuterie",
        2
      ],
      [
        "Valoriser ses pâtés et terrines gastronomiques",
        2
      ],
      [
        "Savoir développer une gamme de conserves dans son entreprise",
        2
      ],
      [
        "Bouchées cocktail sucrées",
        1
      ],
      [
        "Bouchées cocktail salées",
        2
      ],
      [
        "Techniques — desserts en pots",
        1
      ],
      [
        "Développer une gamme de burger",
        1
      ],
      [
        "Prestations salle et réception",
        2
      ]
    ],
    "Automobile, réparation et atelier": [
      [
        "Maintenance de véhicules légers — train roulant et pneumatique",
        2
      ],
      [
        "Carrosserie et peinture — réparation des éléments en matière plastique",
        2
      ],
      [
        "Carrosserie et peinture — micro-réparation spot repair",
        2
      ],
      [
        "Carrosserie et peinture — raccords sur les teintes multicouches",
        2
      ],
      [
        "Carrosserie et peinture — méthodes de soudure de l’acier et de l’aluminium",
        2
      ],
      [
        "Maintenance petit matériel en jardins — espaces verts",
        3
      ],
      [
        "Techniques de soudage — initiation",
        2
      ]
    ]
  }
}

st.set_page_config(page_title='PASS CMA | Simulateur conseiller',page_icon='🧮',layout='wide')
st.markdown("""
<style>
.stApp {background:#f4f7fa;color:#123450}
h1,h2,h3 {color:#123450;letter-spacing:-.025em}
.block-container {padding-top:1.5rem;max-width:1450px}
[data-testid="stSidebar"] {background:#e9f0f5;border-right:1px solid #d5e1ea}
[data-testid="stSidebar"] h2 {color:#123450}
[data-testid="stMetric"] {background:white;border:1px solid #dce5ec;border-top:4px solid #ef4639;border-radius:14px;padding:20px}
[data-testid="stMetricValue"] {color:#123450}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;background:white}
[data-testid="stTable"] {background:white;border-radius:12px;overflow:hidden}
[data-testid="stTable"] th {background:#123450;color:white}
[data-testid="stTable"] tr:nth-child(even) {background:#edf3f7}
.stDownloadButton button[kind="primary"] {background:#d93429;border-color:#d93429;color:white;border-radius:10px;min-height:48px}
.stDownloadButton button[kind="primary"]:hover {background:#b92a21;border-color:#b92a21}
.pass-hero {display:flex;align-items:center;gap:28px;background:#123450;border-radius:20px;padding:30px 34px;margin:0 0 26px;border-bottom:5px solid #ef4639}
.pass-hero-logo {width:150px;flex-shrink:0;background:white;padding:16px;border-radius:12px}
.pass-hero h1 {color:white;font-size:2.2rem;line-height:1.15;margin:8px 0 12px;padding:0}
.pass-hero p {color:#e4edf4;margin:0;max-width:650px}
.pass-kicker {color:#ffc0b9;font-size:.75rem;letter-spacing:.12em;font-weight:700;text-transform:uppercase}
.pass-step {display:flex;align-items:center;gap:12px;margin:28px 0 14px}
.pass-step span {background:#ef4639;color:white;border-radius:10px;padding:7px 10px;font-weight:700;font-size:.9rem}
.pass-step h2 {font-size:1.35rem;margin:0;padding:0}
@media(max-width:700px) {
.pass-hero {padding:22px;gap:18px;align-items:flex-start;flex-direction:column}
.pass-hero-logo {width:110px;padding:10px}
.pass-hero h1 {font-size:1.8rem}
.block-container {padding-top:1rem}
}
</style>
""",unsafe_allow_html=True)
T=json.loads(Path(__file__).with_name('tariffs.json').read_text())
logo_path=Path(__file__).parent/'assets'/'pass-logo.png'
logo_html=''
if logo_path.exists():
    logo_data=base64.b64encode(logo_path.read_bytes()).decode('ascii')
    logo_html=f'<img class="pass-hero-logo" src="data:image/png;base64,{logo_data}" alt="PASS CMA Liberté">'
st.markdown(f"""
<div class="pass-hero">
{logo_html}
<div><div class="pass-kicker">CMA Nouvelle-Aquitaine · Espace conseiller</div>
<h1>Le PASS, chiffres à l’appui.</h1>
<p>Les projets de votre client. Un budget clair. Comparez ses dépenses sur 12 mois et préparez sa fiche personnalisée.</p>
</div></div>
""",unsafe_allow_html=True)
st.caption('SIMULATEUR PASS LIBERTÉ · VERSION 1.5 — 10/11/2026')
with st.sidebar:
    st.header('Votre client')
    st.caption('Personnalisez la simulation et les coordonnées de sa fiche.')
    company=st.text_input('Nom de l’entreprise',max_chars=120)
    profile=st.selectbox('Forme juridique',['Micro-entreprise','EI au réel','Société'])
    basis=st.radio('Base de comparaison',['TTC','HT'],help='TTC si TVA non récupérée ; HT si récupération intégrale. Récupération partielle non gérée dans cette V1.')
    st.caption('Le statut ne détermine pas automatiquement la récupération de TVA.')
    free=st.checkbox('2 mois offerts : éligibilité confirmée',help='Souscription lors d’une prestation CMA d’assistance à l’immatriculation. Engagement de 12 mois maintenu.')
    advisor=st.text_input('Conseiller',max_chars=100)
    contact=st.text_input('Contact professionnel',max_chars=180)
left,right=st.columns([1.1,1],gap='large')
with left:
    st.markdown('<div class="pass-step"><span>01</span><h2>Les besoins de l’entreprise</h2></div>',unsafe_allow_html=True)
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
            covered=st.checkbox('Affecter au PASS',value=i<2,key=f'covered_{i}')
            formalities.append(dict(label=label,ht=tariff,covered=covered))
    hours=st.number_input('Heures de conseil nécessaires',0.0,20.0,0.0,.5)
    st.caption('79 € HT/heure · 2 heures maximum couvertes. Conseil Flash gratuit exclu du calcul.')
    st.markdown('<div class="pass-step"><span>02</span><h2>Ses projets de formation</h2></div>',unsafe_allow_html=True)
    st.caption('Choisissez une catégorie, une spécialité puis une formation. Les cas à confirmer sont exclus de cette sélection. Durées : 7 heures par journée.')
    training_count=st.number_input('Nombre de formations prévues',0,20,0)
    selected_trainings=[]
    for i in range(training_count):
        with st.container(border=True):
            st.write(f'**Formation {i+1}**')
            category=st.selectbox('Catégorie',list(FORMATIONS),key=f'training_category_{i}')
            specialty=st.selectbox('Spécialité',list(FORMATIONS[category]),key=f'training_specialty_{i}_{category}')
            courses=dict(FORMATIONS[category][specialty])
            course=st.selectbox('Formation',['— Choisir une formation —']+list(courses),key=f'training_course_{i}_{category}_{specialty}')
            if course in courses:
                selected_trainings.append((course,courses[course]))
                st.caption(f'Durée : {courses[course]} journée(s) · {courses[course]*7} heures')
    days=sum(duration for _,duration in selected_trainings)
    training_complete=len(selected_trainings)==training_count
    st.write(f'**Total : {days} journée(s) de formation**')
    if selected_trainings:
        st.table([{'Formation':name,'Journées':duration} for name,duration in selected_trainings])
    if not training_complete:
        st.warning('Choisissez une formation dans chaque bloc pour finaliser la simulation.')
    st.caption('Le reste à charge journalier ci-dessous s’applique à toutes les formations sélectionnées. Si les montants diffèrent, réalisez des simulations distinctes.')
    rac=st.number_input(f'Reste à charge par jour avant PASS ({basis})',0.0,10000.0,0.0,5.0)
    eligible=st.checkbox('Formation éligible et financement vérifiés')
    cap=70.0
    st.info("Avantage formation : 70 € par jour éligible, automatiquement limité au reste à charge.")
    st.caption('Exclusions : e-learning, formations réglementaires, parcours qualifiants/diplômants et financement CPF. Les cas certifiants à confirmer ne sont pas proposés. Formation courte de moins de 10 jours ; plusieurs sessions possibles. Une participation par session à tarif préférentiel.')
    st.markdown('<div class="pass-step"><span>03</span><h2>Prêt à partager ?</h2></div>',unsafe_allow_html=True)
    validated=st.checkbox('J’ai vérifié la grille tarifaire et les hypothèses de cette simulation')
with right:
    st.markdown('<div class="pass-step"><span>12 mois</span><h2>Le PASS en chiffres</h2></div>',unsafe_allow_html=True)
    st.caption('Une estimation fondée sur les besoins renseignés, abonnement compris.')
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
    if days:
        if not eligible:
            st.warning('Réduction formation non appliquée : cochez « Formation éligible et financement vérifiés » après vérification.')
        elif cap == 0:
            st.warning('Réduction formation non appliquée : le montant journalier est réglé à 0 €.')
        elif rac == 0:
            st.info('Aucune économie formation : aucun reste à charge renseigné avant PASS.')
        else:
            st.caption(f'Réduction formation appliquée : {days} × {euros(min(rac, cap))} = {euros(days * min(rac, cap))}.')
    st.table([{'Prestation':name,f'Sans PASS ({basis})':euros(a),f'Avec PASS ({basis})':euros(b)} for name,a,b in result['rows']])
    st.caption(f"Abonnement : {euros(result['subscription'])} sur 12 mois. {'Deux mensualités offertes.' if free else 'Douze mensualités.'}")
    st.write(f"**Droits encore disponibles :** {result['remaining_formalities']} formalité(s), {result['remaining_hours']:g} h de conseil. Non valorisés dans le gain.")
    ready=validated and training_complete and (not days or eligible)
    assumptions=[f"Profil : {profile}. Base {basis}, choisie selon récupération de TVA.",f"Conseil : 79 € HT/h ; {hours:g} h prévues, dont {min(hours,2):g} h couvertes.",f"Formation : {days} jours ; reste à charge {euros(rac)}/jour ; plafond de réduction {euros(cap)}/jour, limitée au reste à charge.",f"Grille publique relevée le {T['date_releve']}. Applicabilité confirmée par le conseiller pour cette simulation.", 'Deux mois offerts confirmés : souscription avec assistance CMA à l’immatriculation.' if free else 'Aucune gratuité d’abonnement retenue.', 'Les prestations affectées au PASS sont indiquées à zéro dans la colonne Avec PASS. Les frais légaux ne sont pas inclus.']
    if ready:
        st.download_button('Télécharger la fiche client PDF',make_pdf(result,company,profile,advisor,contact,basis,assumptions),'simulation_pass_cma.pdf','application/pdf',type='primary',use_container_width=True)
        st.caption('À joindre à votre mail habituel. Aucune donnée client enregistrée sur disque par cette application.')
    else:
        missing=[]
        if not training_complete: missing.append('Complétez les sélections de formation (section 02).')
        if not validated: missing.append('Cochez la validation générale du conseiller (section 03).')
        if days and not eligible: missing.append('Confirmez l’éligibilité de la formation (section 02).')
        st.download_button('Télécharger la fiche client PDF',data=b'',file_name='simulation_pass_cma.pdf',mime='application/pdf',disabled=True,use_container_width=True)
        st.warning('Pour activer le PDF : ' + ' '.join(missing))
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

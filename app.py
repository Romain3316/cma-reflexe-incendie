from __future__ import annotations

import base64
import html
import io
import hashlib
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CMA Réflexe Incendie",
    page_icon="🔥",
    layout="wide",
)

CMA_BLUE = "#17365D"
CMA_RED = "#D8232A"
CMA_LIGHT = "#F5F7FA"
CMA_TEXT = "#263445"
CMA_MUTED = "#667085"
CMA_BORDER = "#DDE3EA"
CMA_GREEN = "#157F5B"
CMA_AMBER = "#B06B00"

CPSTI_FORM_URL = "https://secu-independants.fr/files/live/sites/ssi/files/mediatheque/Espace_telechargement/Formulaires/CPSTI-%20aide%20d'urgence%20CPSTI%20aux%20actifs%20victimes%20de%20catastrophe%20et%20d'intemp%c3%a9ries.pdf"

# Cellule d’Urgence Médico-Psychologique (CUMP)
CUMP_PHONE_DISPLAY = "0800 719 912"
CUMP_PHONE_LINK = "tel:+33800719912"

ACTIVITE_PARTIELLE_URL = "https://activitepartielle.emploi.gouv.fr/aparts/"
FAQ_INCENDIES_URL = (
    "https://travail-emploi.gouv.fr/faq-accompagnement-des-entreprises-"
    "dans-le-cadre-des-incendies-exceptionnels"
)
ATMO_FRANCE_URL = "https://www.atmo-france.org/"
PREFECTURE_EVACUATION_URL = (
    "https://www.gironde.gouv.fr/Actualites/Breves/"
    "Incendie-Foire-aux-questions/Foire-aux-questions-incendie"
)

PREFECTURE_WEEKEND_URL = "https://www.gironde.gouv.fr/Actualites/Communiques-de-presse/Communiques-de-presse-2026/Juillet-2026/Incendie-de-Saumos-point-de-situation-ce-samedi-1er-aout-a-20h"
LEGE_PORGE_REINTEGRATION_URL = "https://www.gironde.gouv.fr/Actualites/Communiques-de-presse/Communiques-de-presse-2026/Aout-2026/Incendie-de-Saumos-Reintegration-autorisee-dans-les-communes-de-Lege-Cap-Ferret-et-du-Porge"
PREFECTURE_FAQ_ENTREPRISES_URL = "https://www.gironde.gouv.fr/Actualites/Breves/Incendie-Foire-aux-questions/Foire-aux-questions-incendie"
CMA_FONDS_URL = "https://www.artisanat.fr/magazine/actus/entreprises-impactees-incendies-cma-se-mobilisent-cotes-artisans"
URSSAF_CPSTI_URL = "https://www.urssaf.org/accueil/espace-medias/communiques-et-dossiers-de-press/communiques-de-presse/2026/incendies-le-cpsti-et-l-urssaf-m.html"
MINISTERE_MESURES_URL = "https://www.economie.gouv.fr/actualites/incendies-les-mesures-pour-accompagner-les-sinistres-et-les-entreprises"

# Actualités visibles uniquement dans l'interface collaborateurs.
# Pour ajouter, masquer ou modifier une actualité, intervenir dans cette liste.
# Situation cartographique issue des communiqués et de la FAQ de la
# Préfecture de la Gironde. Mettre à jour à chaque nouveau communiqué.
CARTE_SITUATION_DATE = "3 août 2026 – réintégrations progressives du Porge et de Lège-Cap-Ferret"
CARTE_SOURCE_URL = LEGE_PORGE_REINTEGRATION_URL
PORTAIL_INCENDIE_GIRONDE_URL = (
    "https://www.gironde.gouv.fr/Actualites/Incendie-en-Gironde-toutes-les-informations-utile"
)

CARTE_FAQ_URL = (
    "https://www.gironde.gouv.fr/Actualites/Breves/"
    "Incendie-Foire-aux-questions/Foire-aux-questions-incendie"
)

# Coordonnées des centres-bourgs, suffisantes pour une carte d'aide aux appels.
# Statuts :
# - "evacuee" : évacuation maintenue selon la dernière situation consolidée ;
# - "reintegree" : retour autorisé par la Préfecture ;
# - "reintegree_partielle" : retour autorisé avec exclusions territoriales.
# Attestations officielles par commune.
# Les URL ci-dessous pointent directement vers les PDF publiés par
# la Préfecture de la Gironde.
ATTESTATIONS_COMMUNES = {
    "Andernos-les-Bains": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87859/661083/file/Attestation+-+Andernos.pdf",
        "direct": True,
    },
    "Arès": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87860/661088/file/Attestation+-+Ar%C3%A8s.pdf",
        "direct": True,
    },
    "Audenge": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87861/661093/file/Attestation+-+Audenge.pdf",
        "direct": True,
    },
    "Biganos": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87862/661098/file/Attestation+-+Biganos.pdf",
        "direct": True,
    },
    "Le Barp": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87863/661103/file/Attestation+-+Le+Barp.pdf",
        "direct": True,
    },
    "Cestas": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87864/661108/file/Attestation+-+Cestas.pdf",
        "direct": True,
    },
    "Eysines": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87865/661113/file/Attestation+-+Eysines.pdf",
        "direct": True,
    },
    "Le Haillan": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87867/661123/file/Attestation+-+Le+Haillan.pdf",
        "direct": True,
    },
    "Lacanau Océan": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87866/661118/file/Attestation+-+Lacanau+Oc%C3%A9an.pdf",
        "direct": True,
    },
    "Lacanau Sud": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87868/661128/file/Attestation+-+Sud+Lacanau.pdf",
        "direct": True,
    },
    "Lanton": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87869/661133/file/Attestation+-+Lanton.pdf",
        "direct": True,
    },
    "Lège-Cap-Ferret": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87870/661138/file/Attestation+-+L%C3%A8ge+-+Cap-Ferret.pdf",
        "direct": True,
    },
    "Marcheprime": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87871/661143/file/Attestation+-+Marcheprime.pdf",
        "direct": True,
    },
    "Martignas-sur-Jalle": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87872/661148/file/Attestation+-+Martignas-sur-Jalles.pdf",
        "direct": True,
    },
    "Mérignac extra-rocade": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87873/661153/file/Attestation+-+M%C3%A9rignac+%28extra-rocade%29.pdf",
        "direct": True,
    },
    "Mios": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87874/661158/file/Attestation+-+Mios.pdf",
        "direct": True,
    },
    "Le Porge": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87875/661163/file/Attestation+-+Le+Porge.pdf",
        "direct": True,
    },
    "Saint-Aubin-de-Médoc": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87876/661168/file/Attestation+-+Saint-Aubin-du-M%C3%A9doc.pdf",
        "direct": True,
    },
    "Saint-Jean-d'Illac": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87877/661173/file/Attestation+-+Saint-Jean-d%27Illac.pdf",
        "direct": True,
    },
    "Saint-Médard-en-Jalles": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87878/661178/file/Attestation+-+Saint-M%C3%A9dard-en-Jalles.pdf",
        "direct": True,
    },
    "Sainte-Hélène": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87879/661183/file/Attestation+-+Sainte-H%C3%A9l%C3%A8ne.pdf",
        "direct": True,
    },
    "Salaunes": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87884/661208/file/Attestation+-+Salaunes.pdf",
        "direct": True,
    },
    "Saumos": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87881/661193/file/Attestation+-+Saumos.pdf",
        "direct": True,
    },
    "Le Temple": {
        "url": "https://www.gironde.gouv.fr/contenu/telechargement/87882/661198/file/Attestation+-+Le+Temple.pdf",
        "direct": True,
    },
}


COMMUNES_INCENDIE = [
    # Évacuation maintenue
    {
        "commune": "Arès",
        "lat": 44.7658,
        "lon": -1.1397,
        "statut": "reintegree",
        "precision": "Réintégration autorisée depuis le 1er août 2026.",
    },
    {"commune": "Andernos-les-Bains", "lat": 44.7424, "lon": -1.1033, "statut": "evacuee"},
    {
        "commune": "Audenge",
        "lat": 44.6843,
        "lon": -1.0133,
        "statut": "reintegree",
        "precision": (
            "Toute la commune est réintégrée, y compris les quartiers "
            "de Lubec et de La Pointe."
        ),
    },
    {
        "commune": "Biganos",
        "lat": 44.6447,
        "lon": -0.9772,
        "statut": "reintegree",
        "precision": "Réintégration autorisée à compter du 31 juillet 2026 à 12 h.",
    },
    {"commune": "Lanton", "lat": 44.7044, "lon": -1.0357, "statut": "evacuee"},
    {
        "commune": "Lacanau – structures touristiques",
        "lat": 44.9778,
        "lon": -1.0785,
        "statut": "reintegree_partielle",
        "precision": (
            "Retour autorisé uniquement dans les campings, résidences de tourisme, "
            "villages vacances et parcs de loisirs de Lacanau."
        ),
    },
    {
        "commune": "Lège-Cap-Ferret",
        "lat": 44.7933,
        "lon": -1.1469,
        "statut": "reintegree_partielle",
        "precision": (
            "Réintégration progressive à compter du 3 août, selon les secteurs. "
            "Les campings et certaines zones restent exclus. Vérifier le communiqué "
            "avant tout déplacement."
        ),
    },
    {
        "commune": "Marcheprime",
        "lat": 44.6929,
        "lon": -0.8558,
        "statut": "reintegree",
        "precision": "Réintégration autorisée depuis le 1er août 2026.",
    },
    {
        "commune": "Le Porge",
        "lat": 44.8734,
        "lon": -1.0922,
        "statut": "reintegree_partielle",
        "precision": (
            "Réintégration progressive à compter du 3 août, selon les secteurs. "
            "Les campings et certaines zones restent exclus. Vérifier le communiqué "
            "avant tout déplacement."
        ),
    },
    {
        "commune": "Saumos",
        "lat": 44.9124,
        "lon": -0.9958,
        "statut": "reintegree",
        "precision": "Réintégration autorisée depuis le 1er août 2026.",
    },
    {
        "commune": "Le Temple",
        "lat": 44.8790,
        "lon": -0.9899,
        "statut": "reintegree",
        "precision": "Réintégration autorisée depuis le 1er août 2026.",
    },

    # Réintégration autorisée le 30 juillet 2026
    {"commune": "Mios", "lat": 44.6057, "lon": -0.9378, "statut": "reintegree"},
    {"commune": "Le Barp", "lat": 44.6081, "lon": -0.7697, "statut": "reintegree"},
    {"commune": "Cestas", "lat": 44.7449, "lon": -0.6813, "statut": "reintegree"},
    {"commune": "Saint-Jean-d'Illac", "lat": 44.8117, "lon": -0.7829, "statut": "reintegree"},
    {"commune": "Martignas-sur-Jalle", "lat": 44.8409, "lon": -0.7732, "statut": "reintegree"},
    {"commune": "Saint-Médard-en-Jalles", "lat": 44.8953, "lon": -0.7174, "statut": "reintegree"},
    {"commune": "Saint-Aubin-de-Médoc", "lat": 44.9111, "lon": -0.7245, "statut": "reintegree"},
    {"commune": "Salaunes", "lat": 44.9367, "lon": -0.8308, "statut": "reintegree"},
    {"commune": "Sainte-Hélène", "lat": 44.9657, "lon": -0.8848, "statut": "reintegree"},

    # Réintégration autorisée précédemment
    {"commune": "Eysines", "lat": 44.8845, "lon": -0.6510, "statut": "reintegree"},
    {"commune": "Mérignac", "lat": 44.8386, "lon": -0.6436, "statut": "reintegree"},
    {"commune": "Le Haillan", "lat": 44.8716, "lon": -0.6794, "statut": "reintegree"},
]


ACTUALITES = [
    {
        "date": "3 août 2026",
        "badge": "Réintégration",
        "titre": "Réintégration progressive du Porge et de Lège-Cap-Ferret",
        "resume": (
            "La Préfecture annonce une réintégration progressive à compter du lundi "
            "3 août, selon les secteurs. Les entreprises peuvent envisager une reprise "
            "progressive, sous réserve de vérifier l'accès effectif aux locaux et les "
            "restrictions qui restent applicables. Les campings et certains secteurs "
            "demeurent exclus."
        ),
        "source": "Préfecture de la Gironde",
        "url": LEGE_PORGE_REINTEGRATION_URL,
        "active": True,
        "featured": True,
    },
    {
        "date": "2 août 2026",
        "badge": "FAQ officielle",
        "titre": "Une FAQ regroupe les démarches et contacts utiles",
        "resume": (
            "La Préfecture met à disposition une foire aux questions consacrée aux "
            "incendies, avec les principales démarches, les contacts d'urgence et une "
            "rubrique spécifique pour les entreprises, autoentrepreneurs et travailleurs "
            "indépendants."
        ),
        "source": "Préfecture de la Gironde",
        "url": PREFECTURE_FAQ_ENTREPRISES_URL,
        "active": True,
    },
    {
        "date": "1er août 2026",
        "badge": "Aide CMA",
        "titre": "Jusqu'à 1 500 € d'aide d'urgence pour les artisans sinistrés",
        "resume": (
            "Le réseau des CMA mobilise son Fonds de calamités et des catastrophes "
            "naturelles. Une aide d'urgence pouvant atteindre 1 500 € peut être accordée "
            "aux entreprises artisanales dont les locaux, équipements ou matériels ont "
            "été endommagés ou détruits. La demande doit être déposée auprès de la CMA "
            "compétente dans un délai maximal de trois mois après le sinistre."
        ),
        "source": "CMA France",
        "url": CMA_FONDS_URL,
        "active": True,
    },
    {
        "date": "1er août 2026",
        "badge": "Assurances",
        "titre": "Les expertises d'assurance doivent être accélérées",
        "resume": (
            "France Assureurs, les compagnies et les experts se sont engagés auprès "
            "de la Préfecture à accélérer les passages d'expertise et à suivre chaque "
            "semaine l'avancement des dossiers. Pour les entreprises en attente, "
            "conseiller une relance écrite de l'assureur. Le délai exceptionnel de "
            "déclaration des sinistres reste fixé au 31 août 2026."
        ),
        "source": "Préfecture de la Gironde",
        "url": PREFECTURE_WEEKEND_URL,
        "active": True,
    },
    {
        "date": "1er août 2026",
        "badge": "Réintégration",
        "titre": "Arès, Marcheprime, Saumos, Le Temple et Audenge réintégrés",
        "resume": (
            "La Préfecture autorise la réintégration à Arès, Marcheprime, Saumos "
            "et Le Temple, ainsi que dans les quartiers de Lubec et de La Pointe à "
            "Audenge. Audenge est donc entièrement réintégrée. Vérifier malgré tout "
            "l'accès réel aux locaux et la possibilité effective de reprendre l'activité."
        ),
        "source": "Préfecture de la Gironde",
        "url": PREFECTURE_WEEKEND_URL,
        "active": True,
    },
    {
        "date": "31 juillet 2026",
        "badge": "Mesures entreprises",
        "titre": "Activité partielle, CFE, Urssaf et assurances : les mesures de référence",
        "resume": (
            "La page du ministère centralise les principales mesures : activité "
            "partielle, reports de cotisations Urssaf, remise des majorations, "
            "modulation des cotisations provisionnelles, accompagnement fiscal et "
            "dégrèvement possible de CFE pour les locaux devenus inutilisables."
        ),
        "source": "Ministère de l'Économie",
        "url": MINISTERE_MESURES_URL,
        "active": True,
    },
    {
        "date": "30 juillet 2026",
        "badge": "CPSTI",
        "titre": "Aide CPSTI renforcée pour les travailleurs indépendants",
        "resume": (
            "Le CPSTI prévoit une aide pouvant atteindre 2 000 € pour les indépendants "
            "empêchés d'exercer dans une zone évacuée et jusqu'à 8 000 € lorsque "
            "l'entreprise ou l'habitation principale a été directement touchée. "
            "La demande est à transmettre à l'Urssaf avec les justificatifs via la "
            "messagerie sécurisée, rubrique « situation exceptionnelle »."
        ),
        "source": "Urssaf / CPSTI",
        "url": URSSAF_CPSTI_URL,
        "active": True,
    },
]

LOGO_CANDIDATES = [
    Path("logo_cma_na_gironde.png"),
    Path("logo_cma_na_gironde.jpg"),
    Path("logo_cma.png"),
    Path("logo_cma.jpg"),
    Path("assets/logo_cma_na_gironde.png"),
    Path("assets/logo_cma_na_gironde.jpg"),
    Path("assets/logo_cma.png"),
    Path("assets/logo_cma.jpg"),
]


# ============================================================
# CONTENU MÉTIER
# ============================================================

ORGANISMES: dict[str, dict[str, Any]] = {
    "Assurance": {
        "icone": "🛡️",
        "sous_titre": "Déclaration du sinistre, expertise et indemnisation",
        "objectif": (
            "Ouvrir rapidement le dossier de sinistre, préserver les preuves, "
            "organiser l'expertise et préparer l'évaluation des dommages."
        ),
        "todo": [
            "Contacter sans délai l'assureur, le courtier ou l'agent général.",
            "Vérifier le délai et les modalités de déclaration prévus au contrat.",
            "Effectuer une déclaration écrite et demander un numéro de dossier.",
            "Identifier le gestionnaire du dossier et ses coordonnées directes.",
            "Photographier ou filmer les dommages avant nettoyage ou déplacement.",
            "Prendre les mesures conservatoires nécessaires sans se mettre en danger.",
            "Établir un premier inventaire des biens, matériels et stocks touchés.",
            "Demander les modalités et la date de passage de l'expert.",
            "Vérifier les garanties mobilisables, dont les pertes d'exploitation.",
            "Conserver les justificatifs de toutes les dépenses engagées en urgence.",
        ],
        "documents": [
            "Contrat d'assurance et conditions particulières.",
            "Numéro de contrat et coordonnées de l'assureur ou du courtier.",
            "Déclaration écrite avec date, lieu et circonstances connues.",
            "Photos et vidéos datées des locaux, matériels et marchandises.",
            "Inventaire détaillé des biens détruits ou détériorés.",
            "Factures, bons de commande et justificatifs de propriété.",
            "Devis de sécurisation, nettoyage, réparation ou remplacement.",
            "Rapport ou attestation d'intervention des secours, si disponible.",
            "Bilans, comptes de résultat et éléments de chiffre d'affaires.",
            "RIB de l'entreprise et coordonnées de l'expert-comptable.",
        ],
        "vigilance": [
            "Ne pas jeter les biens endommagés avant l'accord de l'assureur ou de l'expert.",
            "Distinguer les mesures conservatoires urgentes des réparations définitives.",
            "Vérifier franchises, plafonds, exclusions et durée d'indemnisation.",
            "Formaliser par écrit les échanges et conserver une copie de chaque pièce envoyée.",
        ],
        "contact": "Coordonnées figurant sur le contrat d'assurance de l'entreprise.",
        "source": "Informations générales à adapter aux garanties et conditions du contrat.",
    },
    "Assurances complémentaires": {
        "icone": "🔎",
        "sous_titre": "Garanties annexes et continuité de l'activité",
        "objectif": (
            "Vérifier avec l'assureur ou le courtier toutes les garanties susceptibles "
            "de limiter les conséquences financières et opérationnelles de l'incendie, "
            "au-delà de la seule indemnisation des biens endommagés."
        ),
        "todo": [
            "Demander à l'assureur la liste complète des garanties mobilisables au titre du contrat.",
            "Vérifier si une garantie pertes d'exploitation a été souscrite et son événement déclencheur.",
            "Identifier la période d'indemnisation, la franchise et le plafond de la perte d'exploitation.",
            "Demander si les frais de relogement, de réinstallation ou de location temporaire sont couverts.",
            "Vérifier la prise en charge des frais de démolition, déblai, gardiennage et mesures conservatoires.",
            "Contrôler l'existence d'une garantie perte d'usage ou perte de loyers selon le statut d'occupation.",
            "Vérifier la couverture du matériel loué, financé ou détenu en crédit-bail.",
            "Examiner les garanties relatives aux marchandises, au froid et aux frais supplémentaires d'exploitation.",
            "Vérifier si une protection juridique ou une garantie honoraires d'expert peut être mobilisée.",
            "Contrôler l'existence d'une assurance homme-clé ou d'une garantie couvrant l'indisponibilité d'une personne essentielle.",
            "Demander un écrit récapitulant les garanties acceptées, refusées ou restant à expertiser.",
        ],
        "documents": [
            "Contrat multirisque professionnelle et conditions particulières.",
            "Tableau des garanties, plafonds, franchises et exclusions.",
            "Avenants et attestations d'assurance en vigueur à la date du sinistre.",
            "Derniers bilans, comptes de résultat et situations comptables.",
            "Chiffre d'affaires mensuel des exercices précédents.",
            "Prévisionnel de trésorerie et estimation de la durée d'interruption.",
            "Baux, contrats de location et justificatifs des loyers.",
            "Contrats de crédit-bail, location financière ou prêt portant sur le matériel.",
            "Devis de relogement, location temporaire, gardiennage, déblai et réinstallation.",
            "Liste des salariés ou personnes indispensables à la continuité de l'activité.",
        ],
        "vigilance": [
            "Une garantie n'est mobilisable que si elle figure dans le contrat et si ses conditions sont remplies.",
            "La perte d'exploitation est souvent liée à un dommage matériel garanti : vérifier précisément le déclencheur.",
            "Ne pas engager de dépenses importantes sans demander l'accord préalable de l'assureur lorsqu'il est requis.",
            "Comparer les réponses de l'assureur avec les conditions particulières et conserver tous les échanges écrits.",
        ],
        "contact": (
            "Demander un rendez-vous dédié avec l'assureur, le courtier ou l'agent général "
            "afin de passer en revue l'intégralité du contrat."
        ),
        "source": (
            "Informations générales fondées sur les garanties professionnelles présentées "
            "par France Assureurs ; seule l'analyse du contrat permet de confirmer la couverture."
        ),
    },
    "URSSAF / CPSTI": {
        "icone": "🤝",
        "sous_titre": "Cotisations sociales et aide d'urgence aux indépendants",
        "objectif": (
            "Signaler rapidement les difficultés, demander un délai de paiement ou une "
            "modulation des cotisations et solliciter l'action sociale du CPSTI."
        ),
        "todo": [
            "Signaler l'incendie depuis la messagerie sécurisée de l'espace URSSAF.",
            "Demander un délai de paiement ou le report des échéances de cotisations.",
            "Vérifier la remise des pénalités et majorations liées au retard provoqué par le sinistre.",
            "Pour un travailleur indépendant, ajuster les cotisations provisionnelles si l'activité baisse.",
            "Déposer rapidement une demande d'action sociale CPSTI avec les justificatifs utiles.",
            "Conserver l'accusé de réception, les messages et la décision reçue.",
        ],
        "documents": [
            "SIRET, identité et coordonnées de l'entreprise.",
            "Explication synthétique du sinistre et de ses conséquences.",
            "Attestation de sinistre, photos ou document des secours.",
            "État des échéances sociales et difficultés de trésorerie.",
            "Éléments récents de chiffre d'affaires ou de revenu.",
            "RIB et justificatifs des dépenses ou pertes urgentes.",
        ],
        "vigilance": [
            "Toutes les démarches URSSAF et les offres de service sont gratuites.",
            "Les demandes sont examinées selon la situation et les justificatifs fournis.",
            "L’aide CPSTI peut atteindre 2 000 € en cas d’interruption liée à une évacuation et jusqu’à 8 000 € en cas de sinistre direct de l’entreprise ou de l’habitation principale, sous conditions.",
            "Le communiqué de juillet 2026 annonce un paiement sous 15 jours après réception d'un dossier recevable.",
        ],
        "contact": (
            "Employeurs : 3957 - Travailleurs indépendants : 3698 - "
            "Messagerie sécurisée de l'espace en ligne."
        ),
        "source": "Communiqué national Urssaf / CPSTI du 30 juillet 2026.",
        "form_url": CPSTI_FORM_URL,
        "form_label": "Télécharger le formulaire de demande d’aide CPSTI",
    },

    "DGFIP / SIE / CDED / CCSF": {
        "icone": "🏛️",
        "sous_titre": "Échéances fiscales et accompagnement des difficultés",
        "objectif": (
            "Informer rapidement l'administration fiscale, rechercher une solution amiable "
            "et, si nécessaire, coordonner les dettes publiques dans un plan d'apurement."
        ),
        "todo": [
            "Contacter le service des impôts des entreprises depuis l'espace professionnel.",
            "Utiliser l'e-contact pour signaler les difficultés de déclaration ou de paiement.",
            "Présenter de façon transparente l'impact de l'incendie sur l'entreprise.",
            "Demander les solutions possibles pour les échéances fiscales concernées.",
            "Solliciter l'orientation vers le CDED si les difficultés sont plus larges.",
            "Évaluer l'intérêt d'une saisine de la CCSF en présence de dettes fiscales et sociales.",
            "Préparer un dossier financier exposant la situation et les perspectives de reprise.",
            "Vérifier que les obligations déclaratives et les conditions d'accès sont respectées.",
        ],
        "documents": [
            "SIRET, identité et coordonnées de l'entreprise.",
            "Description du sinistre et de ses conséquences économiques.",
            "Échéancier des dettes fiscales et sociales.",
            "Dernières déclarations fiscales et sociales.",
            "Bilans, comptes de résultat et situation comptable récente.",
            "Prévisionnel de trésorerie et plan de reprise d'activité.",
            "Relevés bancaires ou éléments justifiant les tensions de trésorerie.",
            "Justificatifs du sinistre et dépenses déjà engagées.",
            "Dossier CCSF, lorsqu'une saisine est envisagée.",
        ],
        "vigilance": [
            "Prendre contact avant l'accumulation des impayés et rester transparent.",
            "La procédure CDED / CCSF est amiable et confidentielle.",
            "Le plan CCSF peut regrouper plusieurs créanciers publics sur une durée maximale de 36 mois.",
            "L'entreprise doit notamment être à jour de ses obligations déclaratives.",
        ],
        "contact": (
            "CDED / CCSF Gironde : codefi.ccsf33@dgfip.finances.gouv.fr - "
            "06 17 22 70 81."
        ),
        "source": "Note DGFIP Nouvelle-Aquitaine / Gironde du 24 juillet 2026.",
    },
    "Protection des salariés / fumées": {
        "icone": "😷",
        "sous_titre": "Santé, sécurité et organisation du travail pendant les épisodes de fumées",
        "objectif": (
            "Évaluer l'exposition aux fumées et mettre en place des mesures de prévention "
            "adaptées avant de maintenir ou de reprendre l'activité des salariés."
        ),
        "todo": [
            "Suivre l'évolution de la qualité de l'air et des recommandations des autorités.",
            "Évaluer les risques liés aux fumées selon les postes, les lieux et la durée d'exposition.",
            "Privilégier la délocalisation temporaire de l'activité dans un environnement non pollué.",
            "Mettre en place le télétravail lorsque les postes et l'organisation le permettent.",
            "Limiter les déplacements professionnels et les activités physiques en extérieur.",
            "En extérieur, supprimer les efforts physiques non indispensables et organiser des rotations.",
            "Maintenir portes et fenêtres fermées lorsque l'air extérieur est dégradé.",
            "Arrêter les systèmes faisant entrer de l'air extérieur non filtré lorsque cela est pertinent.",
            "Solliciter le médecin du travail pour les salariés particulièrement vulnérables.",
            "Fournir des masques FFP2 adaptés lorsque l'exposition extérieure prolongée ne peut être évitée.",
            "Former les salariés au bon ajustement, au retrait et au remplacement du masque.",
            "Mettre à disposition de l'eau et permettre un lavage régulier des mains et du visage.",
            "Mettre à jour l'évaluation des risques et conserver la trace des mesures décidées.",
        ],
        "documents": [
            "Évaluation des risques ou mise à jour du document unique.",
            "Informations locales sur la qualité de l'air et recommandations sanitaires.",
            "Liste des postes exposés et durée prévisible d'exposition.",
            "Consignes écrites communiquées aux salariés.",
            "Échanges avec le service de prévention et de santé au travail.",
            "Justificatifs d'achat et de remise des équipements de protection.",
            "Organisation du télétravail, des rotations ou de la délocalisation temporaire.",
            "Éléments démontrant les mesures prises avant une éventuelle demande d'activité partielle.",
        ],
        "vigilance": [
            "Il n'existe pas de seuil spécifique du Code du travail pour les particules fines liées aux fumées.",
            "Les protections collectives et les mesures d'organisation doivent être privilégiées.",
            "Le masque FFP2 complète les mesures de prévention mais ne remplace pas la réduction de l'exposition.",
            "Un masque doit être bien ajusté et remplacé lorsqu'il est humide, sale ou difficile à respirer.",
            "En intérieur, la priorité porte sur la limitation de l'entrée d'air pollué et l'organisation du travail.",
            "Les situations individuelles de santé doivent être traitées avec le médecin du travail.",
        ],
        "contact": (
            "Service de prévention et de santé au travail de l'entreprise ; "
            "suivi de la qualité de l'air sur Atmo France."
        ),
        "source": (
            "FAQ du ministère du Travail et des Solidarités : "
            "« Accompagnement des entreprises dans le cadre des incendies exceptionnels », juillet 2026."
        ),
        "action_url": FAQ_INCENDIES_URL,
        "action_label": "Consulter la FAQ officielle incendies",
        "action_caption": "Recommandations de prévention et modalités de recours à l'activité partielle.",
        "secondary_url": ATMO_FRANCE_URL,
        "secondary_label": "Consulter la qualité de l’air",
    },
    "Activité partielle / DREETS": {
        "icone": "👥",
        "sous_titre": "Réduction ou suspension temporaire de l'activité des salariés",
        "objectif": (
            "Préserver l'emploi lorsque l'incendie, une interdiction d'accès ou les conséquences "
            "directes de la crise empêchent temporairement les salariés de travailler."
        ),
        "todo": [
            "Rechercher d'abord les solutions permettant de poursuivre l'activité : télétravail, délocalisation ou adaptation des horaires.",
            "Identifier précisément la situation de l'entreprise : sinistre direct, zone évacuée, interdiction d'accès ou impact indirect.",
            "Pour une entreprise directement sinistrée, utiliser le motif « Sinistre ou intempéries de caractère exceptionnel ».",
            "Pour une entreprise en zone évacuée ou interdite d'accès sans dommage direct, utiliser le motif « Toute autre circonstance de caractère exceptionnel ».",
            "Si l'activité est impossible en raison des fumées, démontrer que les mesures de prévention recommandées ont été mises en œuvre.",
            "Pour un impact économique indirect, réunir les éléments prouvant la baisse significative d'activité.",
            "Déposer la demande sur le portail officiel de l'activité partielle.",
            "La demande peut être déposée rétroactivement dans les 30 jours suivant le placement des salariés en activité partielle.",
            "Indiquer la période, les salariés concernés et le nombre prévisionnel d'heures chômées.",
            "Conserver les arrêtés, preuves du sinistre, consignes sanitaires et justificatifs économiques.",
            "Informer les salariés des mesures prises et conserver les échanges avec l'administration.",
        ],
        "documents": [
            "SIRET et coordonnées de l'établissement concerné.",
            "Déclaration de sinistre, photos ou attestation établissant les dommages directs.",
            "Arrêté préfectoral ou municipal d'évacuation ou d'interdiction d'accès.",
            "Copie d'écran de la liste officielle des communes évacuées publiée par la Préfecture.",
            "SMS, courriels ou notifications d'évacuation reçus.",
            "Note expliquant le lien entre l'incendie et l'impossibilité ou la réduction d'activité.",
            "Mesures de prévention mises en œuvre lorsque les fumées empêchent la poursuite du travail.",
            "Liste des salariés concernés, apprentis compris le cas échéant.",
            "Période et nombre prévisionnel d'heures chômées.",
            "Éléments de paie nécessaires au dépôt et à l'indemnisation.",
            "Justificatifs de baisse d'activité, d'annulations ou de rupture d'approvisionnement.",
            "Avis du CSE lorsque l'entreprise est concernée.",
            "Décisions et échanges avec la DDETS ou l'administration.",
        ],
        "vigilance": [
            "L'activité partielle n'est pas automatique : la situation est appréciée au regard du motif invoqué et des justificatifs.",
            "Une entreprise directement sinistrée peut bénéficier d'une autorisation pouvant aller jusqu'à six mois, renouvelable selon la durée du sinistre.",
            "Pour une entreprise en zone évacuée ou interdite d'accès, l'autorisation initiale est limitée à trois mois, renouvelable dans la limite réglementaire.",
            "Une simple recommandation sanitaire ne suffit pas toujours : il faut démontrer que l'activité reste impossible malgré les mesures de prévention.",
            "Les entreprises seulement affectées indirectement sont examinées au cas par cas.",
            "Avant le dépôt, vérifier les alternatives possibles avec les salariés : télétravail, congés convenus ou récupération des heures perdues.",
            "Les taux d'indemnité et d'allocation doivent être vérifiés sur le portail officiel au moment du dépôt.",
        ],
        "contact": (
            "Portail officiel de l'activité partielle - "
            "Gironde : ddets-activite-partielle@gironde.gouv.fr."
        ),
        "source": (
            "FAQ du ministère du Travail et des Solidarités : "
            "« Accompagnement des entreprises dans le cadre des incendies exceptionnels », juillet 2026."
        ),
        "action_url": ACTIVITE_PARTIELLE_URL,
        "action_label": "Accéder au portail de l’activité partielle",
        "action_caption": "Déposer et suivre la demande sur le portail officiel de l’ASP.",
        "secondary_url": FAQ_INCENDIES_URL,
        "secondary_label": "Lire les conditions exceptionnelles incendies",
    },
}


# ============================================================
# ACTUALITÉS COLLABORATEURS
# ============================================================

def get_actualite_badge_class(badge: str) -> str:
    badge_normalise = (badge or "").lower()
    if "alerte" in badge_normalise:
        return "alert"
    if "évolution" in badge_normalise or "retour" in badge_normalise:
        return "evolution"
    return ""


def get_actualite_style(badge: str) -> tuple[str, str, str]:
    """Retourne une icône, une classe de couleur et un ton selon le type d'actualité."""
    normalized = (badge or "").lower()

    if "réintégration" in normalized:
        return "🗺️", "green", "Retour progressif"
    if "faq" in normalized:
        return "❓", "blue", "Ressource officielle"
    if "cma" in normalized:
        return "🤝", "red", "Soutien aux artisans"
    if "assurance" in normalized:
        return "🛡️", "amber", "Assurance"
    if "cpsti" in normalized or "urssaf" in normalized:
        return "💶", "violet", "Aide sociale"
    if "mesures" in normalized:
        return "🏛️", "blue", "Mesures publiques"

    return "📌", "blue", "Information"


def render_actualite_ligne(
    actualite: dict[str, Any],
    index: int,
    featured: bool = False,
) -> None:
    """Affiche une actualité sous forme de carte compacte et colorée."""
    icon, color, tone = get_actualite_style(actualite.get("badge", ""))

    with st.container(border=True):
        icon_col, info_col, action_col = st.columns(
            [0.7, 4.7, 1.15],
            vertical_alignment="center",
        )

        with icon_col:
            st.markdown(
                f"""
                <div class="news-icon news-icon-{color}">
                    {icon}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with info_col:
            st.markdown(
                f"""
                <div class="news-meta-line">
                    <span class="news-pill news-pill-{color}">
                        {html.escape(actualite.get("badge", "Actualité"))}
                    </span>
                    {html.escape(actualite.get("date", ""))} ·
                    {html.escape(actualite.get("source", ""))}
                </div>
                <div class="news-title-line">
                    {html.escape(actualite.get("titre", ""))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            resume = actualite.get("resume", "")
            if featured:
                resume_display = resume
            else:
                resume_display = resume if len(resume) <= 185 else resume[:182].rstrip() + "…"

            st.markdown(
                f"""
                <div class="news-summary-line">
                    {html.escape(resume_display)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with action_col:
            st.link_button(
                "Consulter",
                actualite["url"],
                use_container_width=True,
                key=f"actualite_compacte_{index}",
            )


def render_actualites() -> None:
    """Affiche un briefing court, coloré et réservé aux collaborateurs."""
    actualites_actives = [
        item for item in ACTUALITES if item.get("active", True) and item.get("url")
    ]
    if not actualites_actives:
        return

    actualite_principale = next(
        (item for item in actualites_actives if item.get("featured")),
        actualites_actives[0],
    )
    autres_actualites = [
        item for item in actualites_actives if item is not actualite_principale
    ]

    st.markdown(
        f"""
        <div class="briefing-banner">
            <div class="briefing-banner-kicker">Briefing collaborateurs</div>
            <div class="briefing-banner-title">
                Les informations à connaître avant les appels
            </div>
            <div class="briefing-banner-subtitle">
                {len(actualites_actives)} actualités actives · sources officielles et professionnelles
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_actualite_ligne(
        actualite_principale,
        index=0,
        featured=True,
    )

    for index, actualite in enumerate(autres_actualites[:2], start=1):
        render_actualite_ligne(
            actualite,
            index=index,
            featured=False,
        )

    actualites_masquees = autres_actualites[2:]
    if actualites_masquees:
        with st.expander(
            f"Afficher les {len(actualites_masquees)} autres actualités",
            expanded=False,
        ):
            for index, actualite in enumerate(actualites_masquees, start=3):
                render_actualite_ligne(
                    actualite,
                    index=index,
                    featured=False,
                )

    st.caption(
        "Cet espace est réservé aux collaborateurs et n'apparaît pas dans le PDF remis à l'entreprise."
    )



# ============================================================
# ATTESTATIONS OFFICIELLES D'ÉVACUATION
# ============================================================

def render_attestations_evacuation() -> None:
    """Page dédiée aux attestations officielles d'évacuation."""
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Attestations officielles d'évacuation</div>
            <p class="section-help">
                Sélectionnez une commune pour ouvrir l'attestation officielle
                dans un nouvel onglet.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    commune = st.selectbox(
        "Commune concernée",
        options=sorted(ATTESTATIONS_COMMUNES.keys()),
        index=None,
        placeholder="Sélectionner une commune",
        key="commune_attestation_evacuation",
    )

    if commune:
        attestation = ATTESTATIONS_COMMUNES[commune]
        url = attestation["url"]

        st.markdown(
            f"""
            <div style="
                background:#eef5fb;
                border:1px solid #cbdceb;
                border-left:5px solid #173b65;
                border-radius:12px;
                padding:14px 16px;
                margin:10px 0 14px 0;
            ">
                <div style="font-weight:800;color:#173b65;font-size:1rem;">
                    {html.escape(commune)}
                </div>
                <div style="color:#43566b;margin-top:5px;font-size:.9rem;">
                    Le lien mène directement au document officiel.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <a href="{url}" target="_blank" rel="noopener noreferrer"
               style="
                   display:block;
                   text-align:center;
                   background:#173b65;
                   color:white;
                   text-decoration:none;
                   font-weight:750;
                   padding:12px 16px;
                   border-radius:9px;
                   margin:6px 0 10px 0;
               ">
                Ouvrir / télécharger l'attestation — {html.escape(commune)}
            </a>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Le document s'ouvre dans un nouvel onglet. Selon les réglages du navigateur, "
            "le PDF peut s'afficher ou se télécharger automatiquement."
        )
    else:
        st.info("Choisissez une commune pour afficher le lien correspondant.")

    st.markdown("---")
    st.link_button(
        "Consulter toutes les informations officielles sur l'incendie",
        PORTAIL_INCENDIE_GIRONDE_URL,
        use_container_width=True,
    )


# ============================================================
# CARTE INTERACTIVE DES ÉVACUATIONS
# ============================================================

def render_carte_incendie() -> None:
    """Affiche une carte opérationnelle dans l'interface collaborateurs."""
    evacuees = [
        item for item in COMMUNES_INCENDIE if item["statut"] == "evacuee"
    ]
    reintegrees = [
        item for item in COMMUNES_INCENDIE if item["statut"] == "reintegree"
    ]
    reintegrees_partielles = [
        item
        for item in COMMUNES_INCENDIE
        if item["statut"] == "reintegree_partielle"
    ]

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Situation cartographique</div>
            <p class="section-help">
                Visualisation d'aide aux appels. Toujours vérifier la dernière
                consigne officielle avant tout déplacement.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns([1, 1, 1.15, 2])
    col1.metric("Encore évacuées", len(evacuees))
    col2.metric("Réintégrées", len(reintegrees))
    col3.metric("Retours partiels", len(reintegrees_partielles))
    col4.info(
        "Carte d'aide aux appels. Avant tout déplacement, vérifier la dernière "
        "consigne de la Préfecture ou de la commune."
    )

    carte = folium.Map(
        location=[44.80, -0.90],
        zoom_start=9,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    Fullscreen(
        position="topright",
        title="Afficher en plein écran",
        title_cancel="Quitter le plein écran",
        force_separate_button=True,
    ).add_to(carte)

    for item in COMMUNES_INCENDIE:
        statut = item["statut"]

        if statut == "evacuee":
            couleur = "#d71920"
            statut_label = "Évacuation maintenue"
            conseil = (
                "Ne pas encourager de déplacement. Vérifier les consignes officielles."
            )
        elif statut == "reintegree_partielle":
            couleur = "#e69f00"
            statut_label = "Réintégration partielle"
            conseil = item.get(
                "precision",
                "Le retour est autorisé uniquement dans certains secteurs.",
            )
        else:
            couleur = "#238636"
            statut_label = "Réintégration autorisée"
            conseil = item.get(
                "precision",
                "Vérifier que l'accès aux locaux et la reprise sont réellement possibles.",
            )

        popup_html = f"""
        <div style="font-family:Arial,sans-serif;min-width:230px">
            <div style="font-size:16px;font-weight:700;color:#173b65">
                {html.escape(item["commune"])}
            </div>
            <div style="margin-top:6px;font-weight:700;color:{couleur}">
                {statut_label}
            </div>
            <div style="margin-top:7px;font-size:12px;line-height:1.35">
                {html.escape(conseil)}
            </div>
            <div style="margin-top:7px;font-size:11px;color:#64748b">
                Situation consolidée : {html.escape(CARTE_SITUATION_DATE)}
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=9,
            color="#ffffff",
            weight=2,
            fill=True,
            fill_color=couleur,
            fill_opacity=0.92,
            tooltip=f'{item["commune"]} — {statut_label}',
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(carte)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 25px;
        left: 25px;
        z-index: 9999;
        background: white;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 10px 12px;
        box-shadow: 0 3px 12px rgba(0,0,0,.15);
        font-family: Arial, sans-serif;
        font-size: 12px;
    ">
        <div style="font-weight:700;margin-bottom:7px;color:#173b65">
            Situation des communes
        </div>
        <div style="margin-bottom:5px">
            <span style="display:inline-block;width:11px;height:11px;
            border-radius:50%;background:#d71920;margin-right:6px"></span>
            Évacuation maintenue
        </div>
        <div style="margin-bottom:5px">
            <span style="display:inline-block;width:11px;height:11px;
            border-radius:50%;background:#238636;margin-right:6px"></span>
            Réintégration autorisée
        </div>
        <div>
            <span style="display:inline-block;width:11px;height:11px;
            border-radius:50%;background:#e69f00;margin-right:6px"></span>
            Réintégration partielle / secteurs exclus
        </div>
    </div>
    """
    carte.get_root().html.add_child(folium.Element(legend_html))

    st_folium(
        carte,
        width=None,
        height=500,
        returned_objects=[],
        use_container_width=True,
        key="carte_incendie_gironde",
    )

    st.caption(
        f"Dernière situation intégrée : {CARTE_SITUATION_DATE}. "
        "Les points correspondent aux centres-bourgs et non aux limites administratives."
    )

    source_col1, source_col2 = st.columns(2)
    with source_col1:
        st.link_button(
            "Communiqué officiel de réintégration",
            CARTE_SOURCE_URL,
            use_container_width=True,
        )
    with source_col2:
        faq_url = (
            PREFECTURE_FAQ_ENTREPRISES_URL
            if "PREFECTURE_FAQ_ENTREPRISES_URL" in globals()
            else CARTE_FAQ_URL
        )
        st.link_button(
            "FAQ incendie de la Préfecture",
            faq_url,
            use_container_width=True,
        )


# ============================================================
# PERSONNALISATION SELON LA SITUATION
# ============================================================

def get_recommended_organismes(situation: dict[str, Any]) -> set[str]:
    """Détermine les fiches à présélectionner à partir du mini-diagnostic."""
    recommended: set[str] = {
        "Assurance",
        "Assurances complémentaires",
    }

    salaries = bool(situation.get("salaries"))
    direct = situation.get("sinistre_direct") == "Oui"
    access = situation.get("acces_locaux", "Accessible")
    activity = situation.get("niveau_activite", "Activité normale")
    reasons = set(situation.get("causes_arret", []))

    activity_reduced = activity != "Activité normale"
    activity_strongly_impacted = activity in {
        "Activité fortement réduite",
        "Activité totalement arrêtée",
    }
    access_restricted = access in {
        "Partiellement accessible",
        "Accès interdit",
        "Zone évacuée",
    }

    economic_reasons = {
        "Coupure d'électricité / réseau",
        "Rupture d'approvisionnement",
        "Baisse ou absence de clientèle",
    }
    work_prevention_reasons = {
        "Locaux ou outil de production endommagés",
        "Fumées / qualité de l'air",
        "Accès interdit ou évacuation",
        "Coupure d'électricité / réseau",
        "Rupture d'approvisionnement",
        "Baisse ou absence de clientèle",
        "Autre conséquence directe",
    }

    # Cotisations et aide sociale : utile dès qu'il existe un impact réel
    # sur l'activité ou un sinistre direct.
    if activity_reduced or direct or access_restricted:
        recommended.add("URSSAF / CPSTI")

    # Fiscalité / CCSF : à privilégier lorsque la baisse d'activité ou les
    # tensions de trésorerie sont importantes.
    if activity_strongly_impacted or bool(reasons & economic_reasons):
        recommended.add("DGFIP / SIE / CDED / CCSF")

    # Protection des salariés : fiche utile en présence de salariés lorsque
    # les fumées ou les conditions d'accès peuvent affecter leur sécurité.
    if salaries and (
        "Fumées / qualité de l'air" in reasons
        or access_restricted
    ):
        recommended.add("Protection des salariés / fumées")

    # Activité partielle : seulement en présence de salariés et lorsqu'une
    # impossibilité ou une forte réduction du travail est objectivée.
    if salaries and (
        activity_strongly_impacted
        or access in {"Accès interdit", "Zone évacuée"}
        or (direct and activity_reduced)
        or bool(reasons & work_prevention_reasons)
    ):
        recommended.add("Activité partielle / DREETS")

    return recommended


def diagnostic_signature(situation: dict[str, Any]) -> str:
    """Empreinte stable utilisée pour actualiser les cases uniquement si le diagnostic change."""
    reasons = "|".join(sorted(situation.get("causes_arret", [])))
    raw = "||".join(
        [
            str(bool(situation.get("salaries"))),
            str(situation.get("sinistre_direct", "")),
            str(situation.get("acces_locaux", "")),
            str(situation.get("niveau_activite", "")),
            reasons,
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def build_activity_recommendations(situation: dict[str, Any]) -> list[str]:
    """Construit les recommandations prioritaires selon les réponses du conseiller."""
    recommendations: list[str] = []

    if not situation.get("salaries", False):
        return [
            "L'entreprise n'a pas déclaré de salarié : l'activité partielle n'est pas à mobiliser.",
            "Concentrer l'accompagnement sur l'assurance, la trésorerie, l'URSSAF / CPSTI et la reprise.",
        ]

    direct = situation.get("sinistre_direct") == "Oui"
    access = situation.get("acces_locaux", "")
    reasons = set(situation.get("causes_arret", []))
    activity = situation.get("niveau_activite", "")

    if direct:
        recommendations.append(
            "Dommages directs : documenter précisément le sinistre et vérifier le motif "
            "« Sinistre ou intempéries de caractère exceptionnel »."
        )

    if access in {"Accès interdit", "Zone évacuée"}:
        recommendations.extend([
            "Accès administratif impossible : joindre l'arrêté préfectoral ou municipal et "
            "utiliser le motif « Toute autre circonstance de caractère exceptionnel ».",
            "Conserver une copie d'écran de la liste officielle des communes concernées par "
            "les mesures d'évacuation publiée par la Préfecture de la Gironde. La Préfecture "
            "indique que cette copie d'écran, faisant apparaître le nom de la commune, peut "
            "servir de justificatif.",
            "Conserver également les SMS, courriels, notifications d'évacuation et tout document "
            "attestant de l'impossibilité d'accéder aux locaux.",
        ])
    elif access == "Partiellement accessible":
        recommendations.append(
            "Accès partiel : expliquer les zones, postes ou horaires réellement inutilisables."
        )

    if "Fumées / qualité de l'air" in reasons:
        recommendations.extend([
            "Fumées : tracer l'évaluation des risques et les relevés de qualité de l'air.",
            "Démontrer l'étude du télétravail, de la délocalisation, des horaires adaptés, "
            "des rotations et de la réduction des activités physiques extérieures.",
            "Privilégier les protections collectives ; prévoir des FFP2 adaptés lorsque "
            "l'exposition extérieure prolongée ne peut être évitée.",
        ])

    if "Rupture d'approvisionnement" in reasons:
        recommendations.append(
            "Rupture d'approvisionnement : conserver les messages fournisseurs, délais, "
            "commandes bloquées et preuves de l'impossibilité de substituer l'approvisionnement."
        )

    if "Baisse ou absence de clientèle" in reasons:
        recommendations.append(
            "Baisse de clientèle : réunir comparatifs de chiffre d'affaires, annulations, "
            "réservations perdues et tout élément démontrant le lien direct avec les incendies."
        )

    if "Coupure d'électricité / réseau" in reasons:
        recommendations.append(
            "Coupure de réseau : conserver les avis du gestionnaire, dates et durées d'interruption."
        )

    if activity == "Activité totalement arrêtée":
        recommendations.append(
            "Arrêt total : préciser les dates, salariés concernés et heures chômées ; déposer "
            "la demande dans les 30 jours suivant le placement en activité partielle."
        )
    elif activity == "Activité fortement réduite":
        recommendations.append(
            "Réduction forte : quantifier la baisse, identifier les salariés et les heures réellement chômées."
        )

    recommendations.extend([
        "L'activité partielle ne couvre pas une fermeture volontaire sans impossibilité objectivée.",
        "Tous les salariés de droit privé peuvent être concernés, y compris les apprentis.",
        "Chaque demande est examinée au cas par cas par l'administration.",
    ])
    return recommendations


def build_personalized_activity_fiche(
    base_fiche: dict[str, Any],
    situation: dict[str, Any],
) -> dict[str, Any]:
    fiche = dict(base_fiche)
    fiche["todo"] = build_activity_recommendations(situation) + [
        "Déposer la demande sur activitepartielle.emploi.gouv.fr.",
        "Informer les salariés et conserver les échanges avec l'administration.",
    ]
    return fiche


# ============================================================
# OUTILS
# ============================================================

def find_logo() -> Path | None:
    for path in LOGO_CANDIDATES:
        if path.exists() and path.is_file():
            return path
    return None


def image_to_data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def safe_filename(value: str) -> str:
    clean = "".join(c if c.isalnum() or c in "-_" else "_" for c in value.strip())
    return clean.strip("_") or "entreprise"


def wrap_canvas_text(
    pdf: canvas.Canvas,
    text: str,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines or [""]


def draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica",
    font_size: float = 9,
    leading: float = 12,
    color: str = CMA_TEXT,
    max_lines: int | None = None,
) -> float:
    lines = wrap_canvas_text(pdf, text, font_name, font_size, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]

    pdf.setFillColor(HexColor(color))
    pdf.setFont(font_name, font_size)
    for line in lines:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def pdf_field_name(prefix: str, index: int) -> str:
    """Crée un nom de champ PDF stable, unique et sans caractères spéciaux."""
    normalized = "".join(
        char.lower() if char.isalnum() else "_" for char in prefix
    )
    normalized = "_".join(part for part in normalized.split("_") if part)
    return f"{normalized}_{index}"


def draw_checkbox_list(
    pdf: canvas.Canvas,
    items: list[str],
    x: float,
    y: float,
    width: float,
    field_prefix: str,
    font_size: float = 8.6,
    leading: float = 10.8,
    gap: float = 5.0,
    checkbox_size: float = 10,
    max_lines: int | None = None,
) -> float:
    """Dessine une liste lisible avec de vraies cases PDF cliquables.

    Le premier texte commence volontairement plus bas que le bandeau de section
    afin d'éviter tout chevauchement visuel. Chaque ligne utilise une hauteur
    calculée à partir de son nombre réel de retours à la ligne.
    """
    for index, item in enumerate(items):
        text_width = width - checkbox_size - 10
        lines = wrap_canvas_text(pdf, item, "Helvetica", font_size, text_width)
        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            last = lines[-1].rstrip(" .")
            while stringWidth(last + "...", "Helvetica", font_size) > text_width and last:
                last = last[:-1]
            lines[-1] = last.rstrip() + "..."

        # Le champ est aligné sur la première ligne de texte.
        field_y = y - checkbox_size + 2
        pdf.acroForm.checkbox(
            name=pdf_field_name(field_prefix, index),
            tooltip=item,
            x=x,
            y=field_y,
            size=checkbox_size,
            checked=False,
            buttonStyle="check",
            shape="square",
            borderWidth=1,
            borderColor=HexColor(CMA_BLUE),
            fillColor=white,
            textColor=HexColor(CMA_BLUE),
            forceBorder=True,
            annotationFlags="print",
            fieldFlags="",
        )

        text_x = x + checkbox_size + 8
        pdf.setFillColor(HexColor(CMA_TEXT))
        pdf.setFont("Helvetica", font_size)

        line_y = y
        for line in lines:
            pdf.drawString(text_x, line_y, line)
            line_y -= leading

        # La séparation est placée sous la dernière ligne, jamais dessus.
        separator_y = line_y + 2
        pdf.setStrokeColor(HexColor("#E7EBF0"))
        pdf.setLineWidth(0.35)
        pdf.line(text_x, separator_y, x + width, separator_y)

        y = line_y - gap

    return y

def draw_section_title(
    pdf: canvas.Canvas,
    title: str,
    x: float,
    y: float,
    width: float,
    accent: str,
) -> float:
    bar_height = 25
    pdf.setFillColor(HexColor(accent))
    pdf.roundRect(x, y - bar_height, width, bar_height, 6, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x + 11, y - 17, title)

    # Espace réel sous le bandeau : le premier item ne touche plus le titre.
    return y - bar_height - 18

def draw_logo_or_fallback(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    """Affiche le logo CMA dans un cartouche blanc, uniquement dans le PDF.

    Le logo officiel rouge reste ainsi parfaitement lisible sur les bandeaux bleus,
    sans modifier l'apparence de l'application Streamlit.
    """
    padding_x = 10
    padding_y = 7
    card_x = x - padding_x
    card_y = y - padding_y
    card_w = width + (padding_x * 2)
    card_h = height + (padding_y * 2)

    # Ombre légère
    pdf.setFillColor(HexColor("#102946"))
    pdf.roundRect(
        card_x + 2,
        card_y - 2,
        card_w,
        card_h,
        8,
        stroke=0,
        fill=1,
    )

    # Cartouche blanc
    pdf.setFillColor(white)
    pdf.setStrokeColor(HexColor("#E5EAF0"))
    pdf.setLineWidth(0.6)
    pdf.roundRect(
        card_x,
        card_y,
        card_w,
        card_h,
        8,
        stroke=1,
        fill=1,
    )

    logo = find_logo()
    if logo:
        try:
            pdf.drawImage(
                str(logo),
                x,
                y,
                width=width,
                height=height,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
            return
        except Exception:
            pass

    # Secours si aucun fichier logo n'est disponible
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(x + width / 2, y + height / 2 + 5, "CMA")
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(
        x + width / 2,
        y + height / 2 - 8,
        "NOUVELLE-AQUITAINE · GIRONDE",
    )


def draw_footer(
    pdf: canvas.Canvas,
    page_number: int,
    page_size: tuple[float, float] = A4,
) -> None:
    page_w, _ = page_size
    pdf.setStrokeColor(HexColor(CMA_BORDER))
    pdf.line(34, 28, page_w - 34, 28)
    pdf.setFillColor(HexColor(CMA_MUTED))
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(34, 16, "CMA Réflexe Incendie · Document d'accompagnement")
    pdf.drawRightString(page_w - 34, 16, f"Page {page_number}")


def draw_cover(
    pdf: canvas.Canvas,
    organisation_names: list[str],
    entreprise: str,
    conseiller: str,
    date_edition: str,
) -> None:
    page_w, page_h = A4

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.rect(0, 0, page_w, page_h, stroke=0, fill=1)

    pdf.setFillColor(HexColor(CMA_RED))
    pdf.rect(0, page_h - 18, page_w, 18, stroke=0, fill=1)

    draw_logo_or_fallback(pdf, page_w - 210, page_h - 125, 165, 65)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(44, page_h - 88, "CMA NOUVELLE-AQUITAINE · GIRONDE")

    pdf.setFont("Helvetica-Bold", 31)
    pdf.drawString(44, page_h - 185, "CMA Réflexe")
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.drawString(44, page_h - 225, "Incendie")

    pdf.setFillColor(white)
    pdf.setFont("Helvetica", 14)
    pdf.drawString(44, page_h - 263, "Dossier pratique des démarches après un incendie")

    pdf.setFillColor(HexColor("#24466F"))
    pdf.roundRect(44, page_h - 480, page_w - 88, 160, 12, stroke=0, fill=1)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(62, page_h - 350, "ORGANISMES SÉLECTIONNÉS")

    y = page_h - 375
    pdf.setFont("Helvetica", 10)
    for name in organisation_names:
        pdf.setFillColor(HexColor(CMA_RED))
        pdf.circle(66, y + 3, 2.3, stroke=0, fill=1)
        pdf.setFillColor(white)
        pdf.drawString(76, y, name)
        y -= 22

    # Encadré humain : soutien médico-psychologique
    support_x = 44
    support_y = 205
    support_w = page_w - 88
    support_h = 102

    pdf.setFillColor(HexColor("#F7F9FC"))
    pdf.roundRect(
        support_x,
        support_y,
        support_w,
        support_h,
        10,
        stroke=0,
        fill=1,
    )

    # Accent CMA discret sur la gauche
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.roundRect(
        support_x,
        support_y,
        7,
        support_h,
        3,
        stroke=0,
        fill=1,
    )

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(
        support_x + 20,
        support_y + support_h - 24,
        "BESOIN D'UN SOUTIEN PSYCHOLOGIQUE ?",
    )

    support_text = (
        "Un incendie peut avoir des conséquences importantes sur le plan humain. "
        "La Cellule d'Urgence Médico-Psychologique (CUMP), mise en place par "
        "l'Agence Régionale de Santé, peut être contactée par toute personne "
        "ressentant le besoin d'un accompagnement."
    )
    draw_wrapped(
        pdf,
        support_text,
        support_x + 20,
        support_y + support_h - 42,
        support_w - 170,
        font_name="Helvetica",
        font_size=8.2,
        leading=10.5,
        color=CMA_TEXT,
    )

    # Numéro très visible à droite
    phone_box_w = 126
    phone_box_h = 42
    phone_box_x = support_x + support_w - phone_box_w - 16
    phone_box_y = support_y + 20

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.roundRect(
        phone_box_x,
        phone_box_y,
        phone_box_w,
        phone_box_h,
        7,
        stroke=0,
        fill=1,
    )
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawCentredString(
        phone_box_x + phone_box_w / 2,
        phone_box_y + 27,
        "CELLULE CUMP",
    )
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(
        phone_box_x + phone_box_w / 2,
        phone_box_y + 10,
        CUMP_PHONE_DISPLAY,
    )
    pdf.linkURL(
        CUMP_PHONE_LINK,
        (
            phone_box_x,
            phone_box_y,
            phone_box_x + phone_box_w,
            phone_box_y + phone_box_h,
        ),
        relative=0,
        thickness=0,
    )

    info_y = 135
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(44, info_y + 42, "Entreprise")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(120, info_y + 42, entreprise or "Non renseignée")

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(44, info_y + 22, "Conseiller")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(120, info_y + 22, conseiller or "Non renseigné")

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(44, info_y + 2, "Date d'édition")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(120, info_y + 2, date_edition)

    pdf.setFillColor(HexColor("#D7E1ED"))
    pdf.setFont("Helvetica-Oblique", 8)
    disclaimer = (
        "Ce document constitue une aide pratique. Les conditions d'accès, montants, "
        "délais et justificatifs doivent être confirmés auprès de chaque organisme."
    )
    draw_wrapped(
        pdf,
        disclaimer,
        44,
        72,
        page_w - 88,
        font_name="Helvetica-Oblique",
        font_size=8,
        leading=11,
        color="#D7E1ED",
    )


def draw_situation_page(
    pdf: canvas.Canvas,
    situation: dict[str, Any],
    page_number: int,
) -> None:
    page_w, page_h = A4
    margin = 34
    content_w = page_w - 2 * margin

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.rect(0, page_h - 88, page_w, 88, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.rect(0, page_h - 7, page_w, 7, stroke=0, fill=1)
    draw_logo_or_fallback(pdf, page_w - 170, page_h - 75, 132, 42)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(margin, page_h - 40, "Situation de l'entreprise")
    pdf.setFillColor(HexColor("#D7E1ED"))
    pdf.setFont("Helvetica", 9.5)
    pdf.drawString(margin, page_h - 60, "Qualification rapide réalisée pendant l'appel")

    # Résumé des réponses
    y = page_h - 112
    rows = [
        ("Salariés", "Oui" if situation.get("salaries") else "Non"),
        ("Sinistre direct", situation.get("sinistre_direct", "Non renseigné")),
        ("Accès aux locaux", situation.get("acces_locaux", "Non renseigné")),
        ("Niveau d'activité", situation.get("niveau_activite", "Non renseigné")),
    ]
    reasons = ", ".join(situation.get("causes_arret", [])) or "Aucune cause précisée"
    rows.append(("Causes principales", reasons))

    pdf.setFillColor(HexColor("#EEF3F8"))
    pdf.roundRect(margin, y - 130, content_w, 130, 9, stroke=0, fill=1)
    ry = y - 22
    for label, value in rows:
        pdf.setFillColor(HexColor(CMA_BLUE))
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawString(margin + 14, ry, label)
        draw_wrapped(
            pdf, str(value), margin + 125, ry, content_w - 145,
            font_size=8.5, leading=10, max_lines=2
        )
        ry -= 23

    # Recommandations ciblées
    top = y - 155
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.roundRect(margin, top - 26, content_w, 26, 6, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin + 12, top - 18, "RECOMMANDATIONS PRIORITAIRES")

    recs = build_activity_recommendations(situation)
    current_y = top - 46
    for rec in recs[:11]:
        pdf.setFillColor(HexColor(CMA_RED))
        pdf.circle(margin + 4, current_y + 3, 2, stroke=0, fill=1)
        current_y = draw_wrapped(
            pdf, rec, margin + 14, current_y, content_w - 18,
            font_size=8.6, leading=10.7, max_lines=3
        ) - 7

    # Rappels officiels
    evacuation_case = situation.get("acces_locaux") in {"Accès interdit", "Zone évacuée"}
    box_y = 54
    box_h = 94 if evacuation_case else 124
    pdf.setFillColor(HexColor("#FFF7E8"))
    pdf.setStrokeColor(HexColor("#F0D7A5"))
    pdf.roundRect(margin, box_y, content_w, box_h, 8, stroke=1, fill=1)
    pdf.setFillColor(HexColor(CMA_AMBER))
    pdf.setFont("Helvetica-Bold", 9.5)
    pdf.drawString(margin + 12, box_y + box_h - 20, "REPÈRES DU DISPOSITIF D'ACTIVITÉ PARTIELLE")
    reminders = [
        "Demande en ligne sur le portail officiel ; dépôt rétroactif possible dans les 30 jours.",
        "Dispositif possible pour les salariés de droit privé à temps plein ou partiel et les apprentis.",
        "Lien direct obligatoire entre l'incendie, l'arrêté ou la situation exceptionnelle et la baisse d'activité.",
        "Fermeture volontaire : absence de prise en charge au titre de l'activité partielle.",
        "Taux publiés le 24/07/2026 : indemnité salarié 60 % du brut (minimum 9,74 €) ; "
        "allocation employeur 36 % du brut (minimum 8,57 €), à revérifier au dépôt.",
    ]
    yy = box_y + box_h - 39
    for item in reminders:
        pdf.setFillColor(HexColor(CMA_AMBER))
        pdf.circle(margin + 15, yy + 2, 1.5, stroke=0, fill=1)
        yy = draw_wrapped(
            pdf, item, margin + 23, yy, content_w - 35,
            font_size=7.4 if evacuation_case else 7.7,
            leading=8.8 if evacuation_case else 9.1,
            max_lines=2
        ) - 3

    if evacuation_case:
        evac_y = box_y + box_h + 8
        evac_h = 87
        pdf.setFillColor(HexColor("#EAF2FA"))
        pdf.setStrokeColor(HexColor("#B8CCE1"))
        pdf.roundRect(margin, evac_y, content_w, evac_h, 8, stroke=1, fill=1)

        pdf.setFillColor(HexColor(CMA_BLUE))
        pdf.setFont("Helvetica-Bold", 9.1)
        pdf.drawString(
            margin + 12,
            evac_y + evac_h - 18,
            "JUSTIFICATIF D'ÉVACUATION À CONSERVER",
        )

        evac_text = (
            "La Préfecture de la Gironde indique qu'une copie d'écran de la liste officielle "
            "des communes concernées par les mesures d'évacuation peut servir de justificatif, "
            "à condition que le nom de la commune apparaisse clairement."
        )
        draw_wrapped(
            pdf,
            evac_text,
            margin + 12,
            evac_y + evac_h - 35,
            content_w - 24,
            font_size=7.4,
            leading=8.8,
            max_lines=4,
        )

        pdf.setFillColor(HexColor(CMA_RED))
        pdf.setFont("Helvetica-Bold", 7.4)
        pdf.drawString(margin + 12, evac_y + 16, "À conserver également :")
        draw_wrapped(
            pdf,
            "arrêté préfectoral ou municipal, SMS, courriels, notifications d'évacuation "
            "et tout document prouvant l'impossibilité d'accéder aux locaux.",
            margin + 92,
            evac_y + 16,
            content_w - 104,
            font_size=7.1,
            leading=8.2,
            max_lines=2,
        )

        pdf.linkURL(
            PREFECTURE_EVACUATION_URL,
            (margin, evac_y, margin + content_w, evac_y + evac_h),
            relative=0,
            thickness=0,
        )

    draw_footer(pdf, page_number, A4)


def draw_cpsti_submission_box(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    """Encadré opérationnel avec deux parcours de dépôt clairement séparés."""
    pdf.setFillColor(HexColor("#EEF3F8"))
    pdf.setStrokeColor(HexColor("#C9D6E4"))
    pdf.roundRect(x, y, width, height, 8, stroke=1, fill=1)

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 9.0)
    pdf.drawString(
        x + 12,
        y + height - 17,
        "COMMENT TRANSMETTRE LA DEMANDE D'ACTION SOCIALE ?",
    )

    gap = 12
    col_w = (width - 28 - gap) / 2
    left_x = x + 12
    right_x = left_x + col_w + gap
    banner_y = y + height - 46
    banner_h = 25

    for bx, title in [
        (left_x, "Artisan, commerçant ou profession libérale"),
        (right_x, "Micro-entrepreneur"),
    ]:
        pdf.setFillColor(HexColor(CMA_BLUE))
        pdf.roundRect(bx, banner_y, col_w, banner_h, 5, stroke=0, fill=1)
        pdf.setFillColor(white)
        pdf.setFont("Helvetica-Bold", 7.2)
        lines = wrap_canvas_text(pdf, title, "Helvetica-Bold", 7.2, col_w - 12)
        ty = banner_y + 15
        for line in lines[:2]:
            pdf.drawCentredString(bx + col_w / 2, ty, line)
            ty -= 8

    left_steps = [
        "1. Se connecter à l'espace personnel sur urssaf.fr.",
        "2. Ouvrir Messagerie.",
        "3. Nouveau message > Un autre sujet.",
        "4. Solliciter l'action sociale du CPSTI.",
    ]
    right_steps = [
        "1. Se connecter sur autoentrepreneur.urssaf.fr.",
        "2. Ouvrir Ma messagerie.",
        "3. Nouvelle demande.",
        "4. Une demande d'action sociale.",
    ]

    steps_top = banner_y - 15
    for bx, steps in [(left_x, left_steps), (right_x, right_steps)]:
        sy = steps_top
        for step in steps:
            sy = draw_wrapped(
                pdf,
                step,
                bx + 2,
                sy,
                col_w - 4,
                font_size=6.9,
                leading=8.1,
                max_lines=2,
            ) - 2

    join_y = y + 15
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.setFont("Helvetica-Bold", 7.3)
    pdf.drawString(x + 12, join_y, "À joindre :")
    draw_wrapped(
        pdf,
        "explication de la situation, justificatif du sinistre, pertes ou dépenses urgentes, "
        "éléments financiers récents et RIB.",
        x + 59,
        join_y,
        width - 71,
        font_size=6.9,
        leading=8.0,
        max_lines=2,
    )


def draw_activity_guide_page(
    pdf: canvas.Canvas,
    situation: dict[str, Any],
    page_number: int,
) -> None:
    """Page complémentaire sans cases, consacrée aux recommandations du guide de l'État."""
    page_w, page_h = A4
    margin = 30
    content_w = page_w - 2 * margin

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.rect(0, page_h - 84, page_w, 84, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.rect(0, page_h - 7, page_w, 7, stroke=0, fill=1)
    draw_logo_or_fallback(pdf, page_w - 168, page_h - 72, 132, 42)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 15.5)
    draw_wrapped(
        pdf,
        "Activité partielle : recommandations détaillées",
        margin,
        page_h - 35,
        page_w - margin - 205,
        font_name="Helvetica-Bold",
        font_size=15.5,
        leading=17,
        max_lines=2,
        color="#FFFFFF",
    )
    pdf.setFont("Helvetica", 8.8)
    pdf.setFillColor(HexColor("#D7E1ED"))
    pdf.drawString(
        margin,
        page_h - 56,
        "Synthèse opérationnelle du guide de l'État - incendies exceptionnels",
    )

    sections = [
        (
            "1. AVANT LE RECOURS À L'ACTIVITÉ PARTIELLE",
            [
                "Étudier et tracer les solutions de poursuite d'activité : télétravail, "
                "délocalisation temporaire, adaptation des horaires et rotation des équipes.",
                "Réduire les déplacements et les activités physiques extérieures lorsque la qualité de l'air est dégradée.",
                "Privilégier les mesures collectives ; utiliser des FFP2 adaptés lorsque l'exposition extérieure prolongée ne peut être évitée.",
                "Associer le service de prévention et de santé au travail pour les salariés vulnérables.",
                "Conserver les consignes internes, relevés de qualité de l'air et preuves des mesures testées.",
            ],
        ),
        (
            "2. CHOISIR LE MOTIF ET JUSTIFIER LA SITUATION",
            [
                "Entreprise directement sinistrée : documenter les dommages et vérifier le motif "
                "« Sinistre ou intempéries de caractère exceptionnel ».",
                "Zone évacuée ou interdite d'accès sans dommage direct : joindre l'arrêté et vérifier le motif "
                "« Toute autre circonstance de caractère exceptionnel ».",
                "Fumées : démontrer que le travail reste impossible malgré les mesures de prévention et d'organisation.",
                "Impact économique indirect : prouver la baisse significative d'activité et son lien direct avec les incendies.",
                "Une fermeture volontaire ou de simple convenance ne permet pas la prise en charge.",
            ],
        ),
        (
            "3. PIÈCES À CONSERVER",
            [
                "Déclaration de sinistre, photos, rapports des secours et arrêtés d'évacuation ou d'interdiction.",
                "En Gironde, conserver une copie d'écran de la liste préfectorale des communes évacuées "
                "faisant apparaître le nom de la commune : la Préfecture indique qu'elle peut servir de justificatif.",
                "Conserver aussi les SMS, courriels et notifications reçus au moment de l'évacuation.",
                "Liste des salariés concernés, période demandée et nombre prévisionnel d'heures chômées.",
                "Comparatifs de chiffre d'affaires, annulations, commandes perdues et messages de clients ou fournisseurs.",
                "Avis de coupure, preuves de rupture d'approvisionnement et impossibilité de solution alternative.",
                "Évaluation des risques, consignes aux salariés et échanges avec la médecine du travail.",
                "Avis du CSE lorsque l'entreprise est concernée, ainsi que les échanges avec l'administration.",
            ],
        ),
        (
            "4. DÉPÔT ET SUIVI",
            [
                "Déposer la demande sur le portail officiel ; un dépôt rétroactif est possible dans les 30 jours.",
                "Tous les salariés de droit privé peuvent être concernés, y compris les apprentis, selon leur situation.",
                "Informer les salariés de la mesure et conserver les décisions, accusés de réception et demandes de pièces.",
                "Les taux, minima et durées d'autorisation doivent être revérifiés sur le portail au moment du dépôt.",
                "Chaque dossier est examiné au regard du motif invoqué et des justificatifs produits.",
            ],
        ),
    ]

    y = page_h - 108
    for title, items in sections:
        pdf.setFillColor(HexColor(CMA_BLUE))
        pdf.roundRect(margin, y - 22, content_w, 22, 5, stroke=0, fill=1)
        pdf.setFillColor(white)
        pdf.setFont("Helvetica-Bold", 9.2)
        pdf.drawString(margin + 10, y - 15, title)
        y -= 35

        for item in items:
            pdf.setFillColor(HexColor(CMA_RED))
            pdf.circle(margin + 5, y + 2, 1.7, stroke=0, fill=1)
            y = draw_wrapped(
                pdf,
                item,
                margin + 14,
                y,
                content_w - 20,
                font_size=7.7,
                leading=9.2,
                max_lines=3,
            ) - 5
        y -= 5

    button_w = 250
    button_h = 23
    button_x = page_w - margin - button_w
    button_y = 42
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.roundRect(button_x, button_y, button_w, button_h, 6, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 8.3)
    pdf.drawCentredString(
        button_x + button_w / 2,
        button_y + 7.5,
        "ACCÉDER AU PORTAIL DE L'ACTIVITÉ PARTIELLE",
    )
    pdf.linkURL(
        ACTIVITE_PARTIELLE_URL,
        (button_x, button_y, button_x + button_w, button_y + button_h),
        relative=0,
        thickness=0,
    )

    pdf.setFillColor(HexColor(CMA_MUTED))
    pdf.setFont("Helvetica-Oblique", 6.4)
    pdf.drawString(
        margin,
        47,
        "Source : ministère du Travail et DREETS - documents diffusés en juillet 2026.",
    )
    draw_footer(pdf, page_number, A4)


def draw_organisme_page(
    pdf: canvas.Canvas,
    nom: str,
    fiche: dict[str, Any],
    page_number: int,
) -> None:
    """Fiche organisme en A4 portrait, avec espaces réservés et sans chevauchement."""
    pdf.setPageSize(A4)
    page_w, page_h = A4
    margin = 28
    content_w = page_w - 2 * margin

    header_h = 84
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.rect(0, page_h - header_h, page_w, header_h, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.rect(0, page_h - 7, page_w, 7, stroke=0, fill=1)
    draw_logo_or_fallback(pdf, page_w - 168, page_h - 72, 132, 42)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawString(margin, page_h - 39, nom)
    pdf.setFont("Helvetica", 9.2)
    pdf.setFillColor(HexColor("#D7E1ED"))
    pdf.drawString(margin, page_h - 58, fiche["sous_titre"])

    objective_top = page_h - 102
    objective_h = 50
    pdf.setFillColor(HexColor("#EEF3F8"))
    pdf.roundRect(margin, objective_top - objective_h, content_w, objective_h, 8, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 9.4)
    pdf.drawString(margin + 12, objective_top - 17, "OBJECTIF")
    draw_wrapped(
        pdf,
        fiche["objectif"],
        margin + 78,
        objective_top - 17,
        content_w - 92,
        font_size=8.6,
        leading=10.2,
        max_lines=3,
    )

    # Réservation explicite du bas de page.
    if nom == "URSSAF / CPSTI":
        bottom_h = 220
    elif nom == "Activité partielle / DREETS":
        bottom_h = 142
    else:
        bottom_h = 118

    bottom_y = 43
    safe_top = bottom_y + bottom_h + 10

    col_gap = 18
    col_w = (content_w - col_gap) / 2
    left_x = margin
    right_x = margin + col_w + col_gap
    section_y = objective_top - objective_h - 22

    # Réduction automatique des cases pour les pages denses.
    dense = max(len(fiche["todo"]), len(fiche["documents"])) >= 9
    cpsti = nom == "URSSAF / CPSTI"
    activity = nom == "Activité partielle / DREETS"

    font_size = 7.5 if dense else 8.1
    leading = 8.9 if dense else 9.8
    gap = 3.0 if dense else 4.0
    checkbox_size = 8.2 if dense else 9.0
    max_lines = 2 if dense else 3

    todo_items = list(fiche["todo"])
    doc_items = list(fiche["documents"])

    # La page complémentaire conserve les recommandations détaillées.
    if activity:
        todo_items = todo_items[:7]
        doc_items = doc_items[:7]
        font_size = 7.6
        leading = 9.0
        gap = 3.2
        checkbox_size = 8.3
        max_lines = 2

    left_y = draw_section_title(pdf, "TO-DO LIST", left_x, section_y, col_w, CMA_RED)
    left_y = draw_checkbox_list(
        pdf,
        todo_items,
        left_x + 9,
        left_y,
        col_w - 18,
        field_prefix=f"p{page_number}_{nom}_todo",
        font_size=font_size,
        leading=leading,
        gap=gap,
        checkbox_size=checkbox_size,
        max_lines=max_lines,
    )

    right_y = draw_section_title(pdf, "DOCUMENTS À PRÉPARER", right_x, section_y, col_w, CMA_BLUE)
    right_y = draw_checkbox_list(
        pdf,
        doc_items,
        right_x + 9,
        right_y,
        col_w - 18,
        field_prefix=f"p{page_number}_{nom}_documents",
        font_size=font_size,
        leading=leading,
        gap=gap,
        checkbox_size=checkbox_size,
        max_lines=max_lines,
    )

    # Masque blanc de sécurité : empêche tout élément de liste de pénétrer dans le bloc inférieur.
    pdf.setFillColor(white)
    pdf.rect(0, 0, page_w, safe_top - 2, stroke=0, fill=1)

    pdf.setFillColor(HexColor("#FFF7E8"))
    pdf.setStrokeColor(HexColor("#F0D7A5"))
    pdf.roundRect(margin, bottom_y, content_w, bottom_h, 8, stroke=1, fill=1)

    if cpsti:
        draw_cpsti_submission_box(
            pdf,
            margin + 8,
            bottom_y + 90,
            content_w - 16,
            120,
        )

        pdf.setFillColor(HexColor(CMA_AMBER))
        pdf.setFont("Helvetica-Bold", 8.7)
        pdf.drawString(margin + 12, bottom_y + 75, "POINTS DE VIGILANCE")

        vigilance_w = (content_w - 42) / 2
        for index, point in enumerate(fiche["vigilance"][:4]):
            column = index % 2
            row = index // 2
            vx = margin + 14 + column * (vigilance_w + 14)
            vy = bottom_y + 58 - row * 20
            pdf.setFillColor(HexColor(CMA_AMBER))
            pdf.circle(vx + 2, vy + 2, 1.5, stroke=0, fill=1)
            draw_wrapped(
                pdf,
                point,
                vx + 9,
                vy,
                vigilance_w - 12,
                font_size=6.5,
                leading=7.6,
                max_lines=2,
            )

        form_url = fiche.get("form_url")
        if form_url:
            button_w = 210
            button_h = 20
            button_x = page_w - margin - button_w
            button_y = bottom_y + 7
            pdf.setFillColor(HexColor(CMA_RED))
            pdf.roundRect(button_x, button_y, button_w, button_h, 5, stroke=0, fill=1)
            pdf.setFillColor(white)
            pdf.setFont("Helvetica-Bold", 7.6)
            pdf.drawCentredString(
                button_x + button_w / 2,
                button_y + 6.5,
                "TÉLÉCHARGER LE FORMULAIRE D'AIDE CPSTI",
            )
            pdf.linkURL(
                form_url,
                (button_x, button_y, button_x + button_w, button_y + button_h),
                relative=0,
                thickness=0,
            )

    else:
        pdf.setFillColor(HexColor(CMA_AMBER))
        pdf.setFont("Helvetica-Bold", 8.8)
        pdf.drawString(margin + 12, bottom_y + bottom_h - 17, "POINTS DE VIGILANCE")

        vigilance_items = fiche["vigilance"][:6] if activity else fiche["vigilance"][:4]
        vigilance_gap = 14
        vigilance_w = (content_w - 28 - vigilance_gap) / 2
        row_step = 24 if activity else 27

        for index, point in enumerate(vigilance_items):
            column = index % 2
            row = index // 2
            vx = margin + 14 + column * (vigilance_w + vigilance_gap)
            vy = bottom_y + bottom_h - 35 - row * row_step
            pdf.setFillColor(HexColor(CMA_AMBER))
            pdf.circle(vx + 2, vy + 2, 1.5, stroke=0, fill=1)
            draw_wrapped(
                pdf,
                point,
                vx + 9,
                vy,
                vigilance_w - 10,
                font_size=6.8 if activity else 7.0,
                leading=8.0 if activity else 8.3,
                max_lines=2,
            )

        action_url = fiche.get("action_url")
        button_w = 222 if action_url else 0
        button_h = 22
        button_y = bottom_y + 7

        # Contact limité à la zone située à gauche du bouton.
        contact_x = margin + 12
        contact_label_w = 72
        contact_max_x = (
            page_w - margin - button_w - 18
            if action_url
            else page_w - margin
        )
        contact_text_w = max(90, contact_max_x - (contact_x + contact_label_w))

        pdf.setFillColor(HexColor(CMA_BLUE))
        pdf.setFont("Helvetica-Bold", 6.8)
        pdf.drawString(contact_x, bottom_y + 14, "Contact / démarche :")
        draw_wrapped(
            pdf,
            fiche["contact"],
            contact_x + contact_label_w,
            bottom_y + 14,
            contact_text_w,
            font_size=6.6,
            leading=7.6,
            max_lines=2,
        )

        if action_url:
            button_x = page_w - margin - button_w
            pdf.setFillColor(HexColor(CMA_BLUE))
            pdf.roundRect(button_x, button_y, button_w, button_h, 6, stroke=0, fill=1)
            pdf.setFillColor(white)
            pdf.setFont("Helvetica-Bold", 8.0)
            pdf.drawCentredString(
                button_x + button_w / 2,
                button_y + 7.0,
                fiche.get("action_label", "ACCÉDER AU SITE OFFICIEL").upper(),
            )
            pdf.linkURL(
                action_url,
                (button_x, button_y, button_x + button_w, button_y + button_h),
                relative=0,
                thickness=0,
            )

    # Source positionnée au-dessus du pied de page, sans croiser le contenu.
    pdf.setFillColor(HexColor(CMA_MUTED))
    pdf.setFont("Helvetica-Oblique", 6.1)
    source_text = fiche["source"]
    draw_wrapped(
        pdf,
        source_text,
        margin,
        35,
        content_w,
        font_name="Helvetica-Oblique",
        font_size=6.1,
        leading=7.0,
        max_lines=1,
        color=CMA_MUTED,
    )

    draw_footer(pdf, page_number, A4)

def generate_pdf(
    selected: list[str],
    entreprise: str,
    conseiller: str,
    situation: dict[str, Any],
) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("CMA Réflexe Incendie - PDF interactif")
    pdf.setAuthor("CMA Nouvelle-Aquitaine - Gironde")
    pdf.setSubject("Démarches après incendie avec cases à cocher interactives")

    date_edition = datetime.now().strftime("%d/%m/%Y")

    # Couverture en portrait
    pdf.setPageSize(A4)
    draw_cover(pdf, selected, entreprise, conseiller, date_edition)
    pdf.showPage()

    # Page de qualification et recommandations personnalisées.
    page_number = 2
    draw_situation_page(pdf, situation, page_number)
    pdf.showPage()
    page_number += 1

    # Toutes les pages restent en A4 portrait.
    for nom in selected:
        pdf.setPageSize(A4)
        fiche = ORGANISMES[nom]
        if nom == "Activité partielle / DREETS":
            fiche = build_personalized_activity_fiche(fiche, situation)
        draw_organisme_page(pdf, nom, fiche, page_number)
        pdf.showPage()
        page_number += 1

        if nom == "Activité partielle / DREETS":
            draw_activity_guide_page(pdf, situation, page_number)
            pdf.showPage()
            page_number += 1

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# STYLE STREAMLIT
# ============================================================

st.markdown(
    f"""
    <style>
        :root {{
            --cma-blue: {CMA_BLUE};
            --cma-red: {CMA_RED};
            --cma-light: {CMA_LIGHT};
            --cma-text: {CMA_TEXT};
            --cma-muted: {CMA_MUTED};
            --cma-border: {CMA_BORDER};
        }}

        .stApp {{
            background: #F6F8FB;
        }}

        .block-container {{
            max-width: 1220px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
        }}

        .cma-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 32px;
            min-height: 190px;
            padding: 28px 34px;
            margin-bottom: 24px;
            color: white;
            border-radius: 18px;
            background:
                linear-gradient(118deg, {CMA_BLUE} 0%, {CMA_BLUE} 78%, {CMA_RED} 78%, {CMA_RED} 100%);
            box-shadow: 0 10px 30px rgba(23, 54, 93, .16);
        }}

        .cma-header h1 {{
            margin: 4px 0 8px;
            color: white;
            font-size: 2.35rem;
            line-height: 1.05;
        }}

        .cma-header p {{
            max-width: 680px;
            margin: 0;
            color: #EAF0F7;
            font-size: .97rem;
            line-height: 1.5;
        }}

        .cma-eyebrow {{
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
            color: #D7E2EF;
        }}

        .cma-logo {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 245px;
            min-width: 245px;
            min-height: 108px;
            padding: 12px;
            border-radius: 14px;
            background: white;
            color: {CMA_BLUE};
            font-weight: 900;
            text-align: center;
        }}

        .cma-logo img {{
            max-width: 215px;
            max-height: 85px;
            object-fit: contain;
        }}

        .section-card {{
            padding: 20px 22px;
            margin: 0 0 18px;
            border: 1px solid var(--cma-border);
            border-radius: 15px;
            background: white;
            box-shadow: 0 4px 14px rgba(16, 40, 70, .05);
        }}

        .section-title {{
            margin: 0 0 5px;
            color: var(--cma-blue);
            font-size: 1.25rem;
            font-weight: 850;
        }}

        .module-nav-intro {{
            margin: .75rem 0 .55rem;
        }}

        .briefing-banner {{
            margin: .55rem 0 .8rem;
            padding: .9rem 1rem;
            border-radius: 16px;
            background:
                linear-gradient(135deg, rgba(23, 59, 101, .98), rgba(43, 104, 159, .94));
            color: white;
            box-shadow: 0 10px 26px rgba(23, 59, 101, .18);
        }}

        .briefing-banner-kicker {{
            font-size: .7rem;
            font-weight: 900;
            letter-spacing: .11em;
            text-transform: uppercase;
            opacity: .8;
        }}

        .briefing-banner-title {{
            margin-top: .2rem;
            font-size: 1.08rem;
            font-weight: 900;
        }}

        .briefing-banner-subtitle {{
            margin-top: .25rem;
            font-size: .82rem;
            line-height: 1.4;
            opacity: .84;
        }}

        .news-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 52px;
            height: 52px;
            border-radius: 16px;
            font-size: 1.6rem;
            box-shadow: 0 6px 15px rgba(18, 52, 86, .11);
        }}

        .news-icon-blue {{
            background: #E8F1FB;
            border: 1px solid #C9DBEE;
        }}

        .news-icon-red {{
            background: #FDECEE;
            border: 1px solid #F5C7CC;
        }}

        .news-icon-green {{
            background: #EAF6EF;
            border: 1px solid #CBE6D5;
        }}

        .news-icon-amber {{
            background: #FFF4DA;
            border: 1px solid #F1D99A;
        }}

        .news-icon-violet {{
            background: #F2ECFA;
            border: 1px solid #D9C8EE;
        }}

        .news-pill {{
            display: inline-block;
            padding: .2rem .52rem;
            border-radius: 999px;
            color: white;
            font-size: .68rem;
            font-weight: 900;
            letter-spacing: .03em;
            text-transform: uppercase;
            margin-right: .35rem;
        }}

        .news-pill-blue {{ background: #255D92; }}
        .news-pill-red {{ background: #D9303E; }}
        .news-pill-green {{ background: #2E7D56; }}
        .news-pill-amber {{ background: #C88600; }}
        .news-pill-violet {{ background: #6C4AA0; }}

        .news-meta-line {{
            color: #68798D;
            font-size: .75rem;
            margin-bottom: .15rem;
        }}

        .news-title-line {{
            color: var(--cma-blue);
            font-size: 1rem;
            line-height: 1.3;
            font-weight: 850;
            margin-bottom: .25rem;
        }}

        .news-summary-line {{
            color: #45586D;
            font-size: .84rem;
            line-height: 1.45;
        }}

        .module-nav-kicker {{
            color: var(--cma-red);
            font-size: .76rem;
            font-weight: 900;
            letter-spacing: .09em;
            text-transform: uppercase;
        }}

        .module-nav-title {{
            margin: .15rem 0 0;
            color: var(--cma-blue);
            font-size: 1.2rem;
            font-weight: 900;
        }}

        .module-nav-subtitle {{
            margin: .15rem 0 .7rem;
            color: var(--cma-muted);
            font-size: .91rem;
        }}

        /* Navigation en vraies cartes-boutons Streamlit. */
        div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton > button {{
            min-height: 132px;
            width: 100%;
            padding: 20px 18px;
            border: 1px solid #D7E1EC;
            border-radius: 18px;
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFD 100%);
            color: var(--cma-blue);
            box-shadow: 0 8px 22px rgba(18, 52, 86, .08);
            white-space: pre-line;
            text-align: left;
            justify-content: flex-start;
            align-items: flex-start;
            font-size: 1rem;
            font-weight: 850;
            line-height: 1.42;
            transition:
                transform .18s ease,
                box-shadow .18s ease,
                border-color .18s ease,
                background .18s ease;
        }}

        div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton > button:hover {{
            transform: translateY(-4px) scale(1.012);
            border-color: #9DB4CB;
            color: var(--cma-blue);
            box-shadow: 0 14px 30px rgba(18, 52, 86, .16);
        }}

        /* La carte active est forcée en bleu CMA, indépendamment du thème Streamlit. */
        div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton > button[kind="primary"],
        div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton > button[data-testid="stBaseButton-primary"] {{
            border-color: #173B65 !important;
            background: linear-gradient(135deg, #173B65 0%, #285F96 100%) !important;
            color: white !important;
            box-shadow: 0 16px 34px rgba(23, 59, 101, .24) !important;
            transform: translateY(-2px);
        }}

        div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton > button[kind="primary"]:hover,
        div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton > button[data-testid="stBaseButton-primary"]:hover {{
            color: white !important;
            border-color: #173B65 !important;
            background: linear-gradient(135deg, #173B65 0%, #285F96 100%) !important;
        }}

        @media (max-width: 760px) {{
            div[data-testid="stHorizontalBlock"] {{
                flex-direction: column;
            }}

            div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton > button {{
                min-height: 118px;
            }}
        }}
        .briefing-shell {{
            margin: 1rem 0 1.35rem;
            padding: 1.05rem;
            border: 1px solid #D9E4EE;
            border-radius: 20px;
            background:
                radial-gradient(circle at top right, rgba(229, 37, 42, .09), transparent 28%),
                linear-gradient(180deg, #F9FBFD 0%, #EEF4F9 100%);
            box-shadow: 0 14px 34px rgba(17, 52, 86, .10);
        }}

        .briefing-head {{
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 1rem;
            margin-bottom: .85rem;
        }}

        .briefing-kicker {{
            color: var(--cma-red);
            font-size: .72rem;
            font-weight: 900;
            letter-spacing: .1em;
            text-transform: uppercase;
        }}

        .briefing-title {{
            color: var(--cma-blue);
            font-size: 1.2rem;
            font-weight: 900;
            margin-top: .15rem;
        }}

        .briefing-count {{
            color: #607084;
            background: white;
            border: 1px solid #D6E1EC;
            border-radius: 999px;
            padding: .25rem .65rem;
            font-size: .76rem;
            white-space: nowrap;
        }}

        .featured-news {{
            position: relative;
            overflow: hidden;
            min-height: 190px;
            padding: 1.3rem 1.4rem;
            border-radius: 17px;
            color: white;
            background: linear-gradient(135deg, #173B65 0%, #28639C 100%);
            box-shadow: 0 14px 30px rgba(23, 59, 101, .22);
        }}

        .featured-news::after {{
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            right: -70px;
            top: -85px;
            border-radius: 50%;
            background: rgba(255, 255, 255, .07);
        }}

        .featured-meta {{
            display: flex;
            align-items: center;
            gap: .5rem;
            margin-bottom: .8rem;
            font-size: .78rem;
            opacity: .92;
        }}

        .featured-badge {{
            padding: .28rem .65rem;
            border-radius: 999px;
            background: var(--cma-red);
            font-size: .68rem;
            font-weight: 900;
            letter-spacing: .04em;
            text-transform: uppercase;
        }}

        .featured-title {{
            position: relative;
            z-index: 2;
            max-width: 85%;
            font-size: 1.35rem;
            line-height: 1.25;
            font-weight: 900;
            margin-bottom: .7rem;
        }}

        .featured-summary {{
            position: relative;
            z-index: 2;
            max-width: 92%;
            color: rgba(255, 255, 255, .89);
            font-size: .9rem;
            line-height: 1.5;
        }}

        .news-strip {{
            display: flex;
            gap: .8rem;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            scrollbar-width: thin;
            padding: .85rem .1rem .45rem;
        }}

        .compact-news-card {{
            flex: 0 0 315px;
            scroll-snap-align: start;
            min-height: 180px;
            padding: .95rem;
            border: 1px solid #DCE5EE;
            border-radius: 15px;
            background: white;
            box-shadow: 0 7px 20px rgba(18, 52, 86, .07);
        }}

        .compact-news-title {{
            color: var(--cma-blue);
            font-size: .93rem;
            line-height: 1.32;
            font-weight: 850;
            margin: .5rem 0 .4rem;
        }}

        .compact-news-summary {{
            color: #485A6E;
            font-size: .8rem;
            line-height: 1.43;
        }}

        .compact-news-source {{
            margin-top: .6rem;
            color: #697A8D;
            font-size: .71rem;
            font-weight: 700;
        }}

        @media (max-width: 760px) {{
            .briefing-head {{
                align-items: flex-start;
                flex-direction: column;
            }}

            .featured-title,
            .featured-summary {{
                max-width: 100%;
            }}

            .compact-news-card {{
                flex-basis: 88%;
            }}
        }}

        .news-shell {{
            margin: 0.85rem 0 1.35rem 0;
            padding: 1rem 1rem 0.8rem 1rem;
            border-radius: 18px;
            background: linear-gradient(180deg, #f6f9fc 0%, #eef4f9 100%);
            border: 1px solid #dbe5ee;
            box-shadow: 0 10px 28px rgba(18, 52, 86, 0.08);
        }}

        .news-heading-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.7rem;
        }}

        .news-heading {{
            color: #173b65;
            font-size: 1.08rem;
            font-weight: 800;
            letter-spacing: -0.01em;
        }}

        .news-count {{
            color: #607084;
            background: #ffffff;
            border: 1px solid #d5e0ea;
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-size: 0.76rem;
            white-space: nowrap;
        }}

        .news-carousel {{
            display: flex;
            gap: 1rem;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            padding: 0.15rem 0.1rem 0.55rem 0.1rem;
            scrollbar-width: none;
        }}

        .news-carousel::-webkit-scrollbar {{
            display: none;
        }}

        .news-card {{
            flex: 0 0 min(420px, 88vw);
            scroll-snap-align: start;
            background: #ffffff;
            border: 1px solid #d9e3ec;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 7px 20px rgba(16, 48, 80, 0.09);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }}

        .news-card:hover {{
            transform: translateY(-4px) scale(1.01);
            box-shadow: 0 14px 28px rgba(16, 48, 80, 0.14);
        }}
        .news-body {{
            padding: 1.05rem 1rem 1rem 1rem;
        }}
            padding: 0.95rem 1rem 1rem 1rem;
        }}

        .news-meta {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.4rem;
            color: #6a798a;
            font-size: 0.76rem;
            margin-bottom: 0.5rem;
        }}

        .news-badge {{
            display: inline-block;
            background: #173b65;
            color: white;
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-size: 0.68rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}

        .news-badge.alert {{
            background: #e5252a;
        }}

        .news-badge.evolution {{
            background: #2f6d4f;
        }}

        .news-title {{
            color: #173b65;
            font-size: 1.02rem;
            line-height: 1.35;
            font-weight: 800;
            margin: 0 0 0.5rem 0;
        }}

        .news-summary {{
            color: #3f5062;
            font-size: 0.88rem;
            line-height: 1.47;
            margin: 0;
            min-height: 5.2rem;
        }}

        .news-source {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            margin-top: 0.75rem;
            color: #173b65;
            font-size: 0.79rem;
            font-weight: 700;
        }}

        .news-hint {{
            color: #738194;
            font-size: 0.76rem;
            margin-top: 0.45rem;
        }}

        @media (max-width: 700px) {{
            .news-shell {{
                padding: 0.8rem 0.75rem 0.7rem 0.75rem;
            }}

            .news-card {{
                flex-basis: 92%;
            }}

            .news-summary {{
                min-height: auto;
            }}
        }}

        .section-help {{
            margin: 0;
            color: var(--cma-muted);
            line-height: 1.5;
        }}

        .organism-heading {{
            display: flex;
            align-items: center;
            gap: 9px;
            margin-bottom: 5px;
            color: var(--cma-blue);
            font-size: 1.2rem;
            font-weight: 850;
        }}

        .organism-objective {{
            padding: 12px 14px;
            margin: 8px 0 14px;
            border-left: 4px solid var(--cma-red);
            border-radius: 0 9px 9px 0;
            background: #F7F9FC;
            color: var(--cma-text);
            line-height: 1.5;
        }}

        .mini-title {{
            margin: 4px 0 8px;
            color: var(--cma-blue);
            font-size: .93rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: .03em;
        }}

        .contact-box {{
            padding: 11px 13px;
            margin-top: 10px;
            border-radius: 9px;
            background: #EEF3F8;
            color: var(--cma-blue);
            font-size: .88rem;
            font-weight: 650;
        }}

        div[data-testid="stExpander"] {{
            overflow: hidden;
            margin-bottom: 14px;
            border: 1px solid var(--cma-border);
            border-radius: 14px;
            background: white;
            box-shadow: 0 3px 12px rgba(23, 54, 93, .04);
        }}

        div[data-testid="stExpander"] summary {{
            font-weight: 800;
            color: var(--cma-blue);
        }}

        .stDownloadButton > button {{
            min-height: 50px;
            width: 100%;
            border: 0;
            border-radius: 12px;
            background: var(--cma-red);
            color: white;
            font-weight: 850;
            box-shadow: 0 6px 16px rgba(216, 35, 42, .18);
        }}

        .stDownloadButton > button:hover {{
            background: #B91F25;
            color: white;
            transform: translateY(-1px);
        }}

        .stButton > button {{
            border-radius: 10px;
            font-weight: 750;
        }}

        @media (max-width: 850px) {{
            .cma-header {{
                flex-direction: column;
                align-items: stretch;
                background:
                    linear-gradient(165deg, {CMA_BLUE} 0%, {CMA_BLUE} 74%, {CMA_RED} 74%, {CMA_RED} 100%);
            }}

            .cma-logo {{
                width: 100%;
                min-width: 0;
                max-width: 360px;
                align-self: center;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INTERFACE
# ============================================================

logo_path = find_logo()
if logo_path:
    logo_html = (
        f'<div class="cma-logo"><img src="{image_to_data_uri(logo_path)}" '
        'alt="Logo CMA Nouvelle-Aquitaine Gironde"></div>'
    )
else:
    logo_html = (
        '<div class="cma-logo">CMA<br>'
        '<span style="font-size:.72rem;">NOUVELLE-AQUITAINE · GIRONDE</span></div>'
    )

st.markdown(
    f"""
    <div class="cma-header">
        <div>
            <div class="cma-eyebrow">CMA Nouvelle-Aquitaine · Gironde</div>
            <h1>CMA Réflexe Incendie</h1>
            <p>
                Qualifiez la situation en quelques secondes, sélectionnez les fiches utiles
                et transmettez à l'artisan un guide personnalisé. Les recommandations
                relatives aux fumées et à l'activité partielle reprennent largement les
                documents officiels diffusés en Nouvelle-Aquitaine en juillet 2026.
            </p>
        </div>
        {logo_html}
    </div>
    """,
    unsafe_allow_html=True,
)

# Les actualités restent visibles en haut de l'application, avant les outils.
render_actualites()

st.markdown(
    """
    <div class="module-nav-intro">
        <div class="module-nav-kicker">Accès rapide</div>
        <div class="module-nav-title">Choisissez votre espace de travail</div>
        <div class="module-nav-subtitle">
            Accédez directement au module dont vous avez besoin.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "navigation_principale" not in st.session_state:
    st.session_state.navigation_principale = "Accompagnement"

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    if st.button(
        "🤝  ACCOMPAGNEMENT\nQualifier la situation et préparer le guide entreprise",
        key="nav_accompagnement",
        type=(
            "primary"
            if st.session_state.navigation_principale == "Accompagnement"
            else "secondary"
        ),
        use_container_width=True,
    ):
        st.session_state.navigation_principale = "Accompagnement"
        st.rerun()

with nav_col2:
    if st.button(
        "🗺️  CARTOGRAPHIE\nVisualiser les communes et les zones concernées",
        key="nav_cartographie",
        type=(
            "primary"
            if st.session_state.navigation_principale == "Cartographie"
            else "secondary"
        ),
        use_container_width=True,
    ):
        st.session_state.navigation_principale = "Cartographie"
        st.rerun()

with nav_col3:
    if st.button(
        "📄  ATTESTATIONS\nOuvrir les attestations officielles par commune",
        key="nav_attestations",
        type=(
            "primary"
            if st.session_state.navigation_principale == "Attestations d'évacuation"
            else "secondary"
        ),
        use_container_width=True,
    ):
        st.session_state.navigation_principale = "Attestations d'évacuation"
        st.rerun()

navigation = st.session_state.navigation_principale

if navigation == "Cartographie":
    render_carte_incendie()
    st.stop()

if navigation == "Attestations d'évacuation":
    render_attestations_evacuation()
    st.stop()

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">1. Préparer le dossier</div>
        <p class="section-help">
            Les informations saisies servent uniquement à personnaliser le PDF.
            Elles ne sont ni enregistrées ni transmises par l'application.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    entreprise = st.text_input(
        "Nom de l'entreprise (facultatif)",
        placeholder="Ex. Boulangerie Martin",
    )
with col2:
    conseiller = st.text_input(
        "Nom du conseiller (facultatif)",
        placeholder="Ex. Romain D.",
    )

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">2. Qualifier rapidement la situation</div>
        <p class="section-help">
            Quelques réponses suffisent pour personnaliser les recommandations,
            notamment lorsque l'entreprise emploie des salariés.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

q1, q2 = st.columns(2)
with q1:
    salaries = st.toggle("L'entreprise emploie au moins un salarié", value=False)
    sinistre_direct = st.radio(
        "L'entreprise est-elle directement sinistrée ?",
        ["Oui", "Non"],
        horizontal=True,
    )
with q2:
    acces_locaux = st.selectbox(
        "Accès aux locaux",
        ["Accessible", "Partiellement accessible", "Accès interdit", "Zone évacuée"],
    )
    niveau_activite = st.selectbox(
        "Niveau actuel d'activité",
        [
            "Activité normale",
            "Activité légèrement réduite",
            "Activité fortement réduite",
            "Activité totalement arrêtée",
        ],
    )

causes_arret: list[str] = []
if salaries and niveau_activite != "Activité normale":
    causes_arret = st.multiselect(
        "Pourquoi les salariés ne peuvent-ils pas travailler normalement ?",
        [
            "Locaux ou outil de production endommagés",
            "Fumées / qualité de l'air",
            "Accès interdit ou évacuation",
            "Coupure d'électricité / réseau",
            "Rupture d'approvisionnement",
            "Baisse ou absence de clientèle",
            "Autre conséquence directe",
        ],
        placeholder="Sélectionnez une ou plusieurs causes",
    )

situation = {
    "salaries": salaries,
    "sinistre_direct": sinistre_direct,
    "acces_locaux": acces_locaux,
    "niveau_activite": niveau_activite,
    "causes_arret": causes_arret,
}

if acces_locaux in {"Accès interdit", "Zone évacuée"}:
    st.info(
        "Justificatif utile : la Préfecture de la Gironde indique qu'une copie d'écran "
        "de la liste officielle des communes évacuées, faisant apparaître le nom de la "
        "commune, peut servir de justificatif. Pensez à la conserver."
    )
    st.link_button(
        "Consulter la liste officielle des communes concernées",
        PREFECTURE_EVACUATION_URL,
        use_container_width=True,
    )

if salaries and niveau_activite in {
    "Activité fortement réduite",
    "Activité totalement arrêtée",
}:
    st.info(
        "La fiche Activité partielle est recommandée. Le PDF précisera le motif "
        "et les justificatifs selon la situation décrite."
    )

recommended_organismes = get_recommended_organismes(situation)
current_diagnostic_signature = diagnostic_signature(situation)
previous_diagnostic_signature = st.session_state.get("_diagnostic_signature")

# Les cases sont recalculées uniquement lorsque le mini-diagnostic change.
# Le conseiller peut ensuite modifier librement la sélection sans que ses
# choix soient écrasés à chaque interaction dans l'application.
if previous_diagnostic_signature != current_diagnostic_signature:
    for organisme_name in ORGANISMES:
        st.session_state[f"select_{organisme_name}"] = (
            organisme_name in recommended_organismes
        )
    st.session_state["_diagnostic_signature"] = current_diagnostic_signature

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">3. Sélectionner les fiches utiles</div>
        <p class="section-help">
            Les fiches ont été présélectionnées à partir du mini-diagnostic.
            Le conseiller reste libre de modifier cette sélection.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if recommended_organismes:
    recommended_labels = " · ".join(
        name for name in ORGANISMES if name in recommended_organismes
    )
    st.caption(f"Fiches recommandées : {recommended_labels}")

selection_cols = st.columns(2)
selected: list[str] = []

for idx, (nom, fiche) in enumerate(ORGANISMES.items()):
    with selection_cols[idx % 2]:
        if st.checkbox(
            f"{fiche['icone']} {nom}",
            key=f"select_{nom}",
        ):
            selected.append(nom)

if not selected:
    st.info("Sélectionnez au moins un organisme pour afficher les démarches.")
    st.stop()

total_actions = sum(len(ORGANISMES[n]["todo"]) for n in selected)
total_documents = sum(len(ORGANISMES[n]["documents"]) for n in selected)

m1, m2, m3 = st.columns(3)
m1.metric("Organismes", len(selected))
m2.metric("Démarches", total_actions)
m3.metric("Documents à prévoir", total_documents)

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">4. Consulter la feuille de route</div>
        <p class="section-help">
            Ouvrez uniquement la fiche dont vous avez besoin, puis naviguez entre
            les actions, les documents et les points de vigilance.
            Leur état n'est pas conservé après fermeture ou rechargement de la page.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

for nom in selected:
    fiche = ORGANISMES[nom]

    todo_count = len(fiche["todo"])
    docs_count = len(fiche["documents"])
    vigilance_count = len(fiche["vigilance"])

    completed_todo = sum(
        bool(st.session_state.get(f"todo_{nom}_{i}", False))
        for i in range(todo_count)
    )
    completed_docs = sum(
        bool(st.session_state.get(f"doc_{nom}_{i}", False))
        for i in range(docs_count)
    )
    completed_total = completed_todo + completed_docs
    trackable_total = todo_count + docs_count
    progress_value = (
        completed_total / trackable_total if trackable_total else 0.0
    )

    expander_label = (
        f"{fiche['icone']} {nom}  ·  "
        f"{completed_total}/{trackable_total} éléments traités"
    )

    with st.expander(expander_label, expanded=False):
        st.markdown(
            f"""
            <div class="organism-heading">{fiche['icone']} {html.escape(nom)}</div>
            <div class="organism-objective">
                <strong>Objectif :</strong> {html.escape(fiche['objectif'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        s1, s2, s3 = st.columns(3)
        s1.metric("Actions", todo_count)
        s2.metric("Documents", docs_count)
        s3.metric("Vigilances", vigilance_count)

        st.progress(
            progress_value,
            text=f"Progression : {completed_total} sur {trackable_total}",
        )

        todo_tab, docs_tab, vigilance_tab = st.tabs(
            [
                f"📋 Actions ({todo_count})",
                f"📄 Documents ({docs_count})",
                f"⚠️ Vigilance ({vigilance_count})",
            ]
        )

        with todo_tab:
            if fiche["todo"]:
                for i, action in enumerate(fiche["todo"]):
                    st.checkbox(
                        action,
                        key=f"todo_{nom}_{i}",
                    )
            else:
                st.caption("Aucune action particulière à afficher.")

        with docs_tab:
            if fiche["documents"]:
                for i, document in enumerate(fiche["documents"]):
                    st.checkbox(
                        document,
                        key=f"doc_{nom}_{i}",
                    )
            else:
                st.caption("Aucun document particulier à préparer.")

        with vigilance_tab:
            if fiche["vigilance"]:
                with st.expander(
                    f"Afficher les {vigilance_count} points de vigilance",
                    expanded=False,
                ):
                    for point in fiche["vigilance"]:
                        st.warning(point, icon="⚠️")
            else:
                st.caption("Aucun point de vigilance particulier.")

        if fiche.get("action_url"):
            st.link_button(
                f"🌐 {fiche.get('action_label', 'Accéder au site officiel')}",
                fiche["action_url"],
                use_container_width=True,
            )
            if fiche.get("action_caption"):
                st.caption(fiche["action_caption"])

        if fiche.get("secondary_url"):
            st.link_button(
                f"↗️ {fiche.get('secondary_label', 'Consulter la ressource complémentaire')}",
                fiche["secondary_url"],
                use_container_width=True,
            )

        st.markdown(
            f"""
            <div class="contact-box">
                Contact / démarche : {html.escape(fiche['contact'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if fiche.get("form_url"):
            st.link_button(
                "📄 Télécharger le formulaire de demande d’aide CPSTI",
                fiche["form_url"],
                use_container_width=True,
            )
            st.caption(
                "Le formulaire s’ouvre depuis le site de la Sécurité sociale des indépendants."
            )

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">5. Générer le dossier PDF</div>
        <p class="section-help">
            Le document contient une couverture puis une page en portrait par organisme.
            Les cases sont interactives : elles peuvent être cochées et enregistrées sans impression.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

pdf_bytes = generate_pdf(selected, entreprise, conseiller, situation)
filename = f"CMA_Reflexe_Incendie_{safe_filename(entreprise)}_{datetime.now():%Y%m%d}.pdf"

st.download_button(
    "📄 Télécharger le PDF interactif",
    data=pdf_bytes,
    file_name=filename,
    mime="application/pdf",
    use_container_width=True,
)

if not logo_path:
    st.caption(
        "Logo non trouvé : ajoutez le fichier officiel sous le nom "
        "`logo_cma_na_gironde.png` à la racine du dépôt ou dans le dossier `assets/`."
    )

st.caption(
    "CMA Réflexe Incendie · Outil d'aide à l'accompagnement. "
    "Les procédures et conditions doivent être confirmées auprès des organismes compétents."
)

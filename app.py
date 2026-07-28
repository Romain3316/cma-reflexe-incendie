from __future__ import annotations

import base64
import html
import io
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
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
    "URSSAF / CPSTI": {
        "icone": "🤝",
        "sous_titre": "Cotisations sociales et aide d'urgence aux indépendants",
        "objectif": (
            "Signaler les difficultés liées à l'incendie et solliciter, selon la situation, "
            "un délai de paiement, une modulation des cotisations ou une aide d'urgence."
        ),
        "todo": [
            "Se connecter à la messagerie sécurisée de l'espace URSSAF.",
            "Choisir « Une formalité déclarative » puis « Déclarer une situation exceptionnelle ».",
            "Expliquer précisément l'impact de l'incendie sur l'activité et la trésorerie.",
            "Demander un délai de paiement ou un report des échéances de cotisations.",
            "Pour un indépendant, demander si nécessaire une baisse des cotisations provisionnelles.",
            "Vérifier l'éligibilité à l'aide d'urgence du CPSTI.",
            "Déposer rapidement le formulaire CPSTI avec les justificatifs demandés.",
            "Conserver les accusés de réception et les réponses de l'URSSAF.",
        ],
        "documents": [
            "SIRET et coordonnées de l'entreprise.",
            "Courrier ou message décrivant l'incendie et ses conséquences.",
            "Justificatif du sinistre : attestation, photos ou document des secours.",
            "État des échéances sociales concernées.",
            "Éléments récents de trésorerie et de chiffre d'affaires.",
            "RIB de l'entreprise.",
            "Formulaire de demande d'aide CPSTI, le cas échéant.",
            "Pièces complémentaires demandées par l'URSSAF ou le CPSTI.",
        ],
        "vigilance": [
            "Les démarches et offres de service de l'URSSAF sont gratuites.",
            "Les mesures sont examinées selon la situation de chaque entreprise.",
            "L'aide CPSTI peut atteindre 2 000 € sous conditions pour les indépendants concernés.",
        ],
        "contact": (
            "Employeurs : 3957 - Travailleurs indépendants : 3698 - "
            "Messagerie sécurisée de l'espace en ligne."
        ),
        "source": "Communiqué URSSAF Aquitaine / CPSTI du 24 juillet 2026.",
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
    "Activité partielle / DREETS": {
        "icone": "👥",
        "sous_titre": "Réduction ou suspension temporaire de l'activité des salariés",
        "objectif": (
            "Demander l'activité partielle lorsque l'activité est directement affectée "
            "par une mesure administrative liée aux incendies."
        ),
        "todo": [
            "Identifier l'arrêté préfectoral ou municipal affectant directement l'activité.",
            "Vérifier qu'il existe un lien direct entre la mesure administrative et la baisse d'activité.",
            "Ne pas présenter une fermeture volontaire comme motif de recours.",
            "Réunir les éléments démontrant la réduction ou la suspension temporaire d'activité.",
            "Déposer la demande sur le portail de l'activité partielle.",
            "Utiliser le motif « Toute autre circonstance de caractère exceptionnel ».",
            "Déposer la demande au plus tard dans les 30 jours suivant le placement des salariés.",
            "Conserver les justificatifs et répondre aux éventuelles demandes de l'administration.",
        ],
        "documents": [
            "SIRET et coordonnées de l'établissement concerné.",
            "Arrêté préfectoral ou municipal applicable.",
            "Note expliquant le lien direct avec la baisse d'activité.",
            "Liste des salariés concernés, y compris apprentis le cas échéant.",
            "Période et nombre prévisionnel d'heures chômées.",
            "Éléments de paie nécessaires à la demande.",
            "Justificatifs de baisse ou d'impossibilité temporaire d'activité.",
            "Décisions et échanges avec l'administration.",
        ],
        "vigilance": [
            "La fermeture volontaire n'ouvre pas droit au dispositif.",
            "Chaque demande est examinée au cas par cas.",
            "Le dispositif concerne les salariés de droit privé à temps plein ou partiel et les apprentis.",
            "Les taux et montants doivent être vérifiés au moment du dépôt.",
        ],
        "contact": (
            "Portail : activitepartielle.emploi.gouv.fr - "
            "Gironde : ddets-activite-partielle@gironde.gouv.fr."
        ),
        "source": "Fiche DREETS Nouvelle-Aquitaine du 24 juillet 2026.",
    },
}


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
) -> float:
    """Dessine une liste lisible avec de vraies cases PDF cliquables.

    Le premier texte commence volontairement plus bas que le bandeau de section
    afin d'éviter tout chevauchement visuel. Chaque ligne utilise une hauteur
    calculée à partir de son nombre réel de retours à la ligne.
    """
    for index, item in enumerate(items):
        text_width = width - checkbox_size - 10
        lines = wrap_canvas_text(pdf, item, "Helvetica", font_size, text_width)

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


def draw_organisme_page(
    pdf: canvas.Canvas,
    nom: str,
    fiche: dict[str, Any],
    page_number: int,
) -> None:
    """Fiche organisme en A4 portrait, avec deux colonnes équilibrées."""
    pdf.setPageSize(A4)
    page_w, page_h = A4
    margin = 28
    content_w = page_w - 2 * margin

    # En-tête compact pour préserver la place utile.
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

    # Objectif
    objective_top = page_h - 102
    objective_h = 50
    pdf.setFillColor(HexColor("#EEF3F8"))
    pdf.roundRect(
        margin,
        objective_top - objective_h,
        content_w,
        objective_h,
        8,
        stroke=0,
        fill=1,
    )
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 9.4)
    pdf.drawString(margin + 12, objective_top - 17, "OBJECTIF")
    draw_wrapped(
        pdf,
        fiche["objectif"],
        margin + 78,
        objective_top - 17,
        content_w - 92,
        font_size=8.8,
        leading=10.5,
        max_lines=3,
    )

    # Deux colonnes en portrait. Les retours à la ligne sont calculés et espacés.
    col_gap = 18
    col_w = (content_w - col_gap) / 2
    left_x = margin
    right_x = margin + col_w + col_gap
    section_y = objective_top - objective_h - 22

    left_y = draw_section_title(pdf, "TO-DO LIST", left_x, section_y, col_w, CMA_RED)
    left_y = draw_checkbox_list(
        pdf,
        fiche["todo"],
        left_x + 9,
        left_y,
        col_w - 18,
        field_prefix=f"p{page_number}_{nom}_todo",
        font_size=8.4,
        leading=10.4,
        gap=4.7,
        checkbox_size=9.5,
    )

    right_y = draw_section_title(
        pdf, "DOCUMENTS À PRÉPARER", right_x, section_y, col_w, CMA_BLUE
    )
    right_y = draw_checkbox_list(
        pdf,
        fiche["documents"],
        right_x + 9,
        right_y,
        col_w - 18,
        field_prefix=f"p{page_number}_{nom}_documents",
        font_size=8.4,
        leading=10.4,
        gap=4.7,
        checkbox_size=9.5,
    )

    # Bloc inférieur fixe, suffisamment séparé des listes.
    bottom_y = 43
    bottom_h = 112
    pdf.setFillColor(HexColor("#FFF7E8"))
    pdf.setStrokeColor(HexColor("#F0D7A5"))
    pdf.roundRect(margin, bottom_y, content_w, bottom_h, 8, stroke=1, fill=1)

    pdf.setFillColor(HexColor(CMA_AMBER))
    pdf.setFont("Helvetica-Bold", 9.2)
    pdf.drawString(margin + 12, bottom_y + bottom_h - 18, "POINTS DE VIGILANCE")

    vigilance_gap = 16
    vigilance_w = (content_w - 26 - vigilance_gap) / 2
    for index, point in enumerate(fiche["vigilance"]):
        column = index % 2
        row = index // 2
        vx = margin + 14 + column * (vigilance_w + vigilance_gap)
        vy = bottom_y + bottom_h - 38 - row * 31
        pdf.setFillColor(HexColor(CMA_AMBER))
        pdf.circle(vx + 2, vy + 2, 1.6, stroke=0, fill=1)
        draw_wrapped(
            pdf,
            point,
            vx + 9,
            vy,
            vigilance_w - 10,
            font_size=7.5,
            leading=8.8,
            max_lines=3,
        )

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawString(margin + 12, bottom_y + 12, "Contact / démarche :")
    draw_wrapped(
        pdf,
        fiche["contact"],
        margin + 90,
        bottom_y + 12,
        content_w - 102,
        font_size=7.5,
        leading=8.5,
        max_lines=2,
    )

    # Bouton cliquable vers un formulaire officiel, lorsqu'il existe.
    form_url = fiche.get("form_url")
    if form_url:
        button_w = 210
        button_h = 18
        button_x = page_w - margin - button_w
        button_y = bottom_y + 7

        # Masque propre derrière le bouton dans le bloc inférieur.
        pdf.setFillColor(HexColor("#FFF7E8"))
        pdf.rect(
            button_x - 4,
            button_y - 3,
            button_w + 8,
            button_h + 6,
            stroke=0,
            fill=1,
        )

        pdf.setFillColor(HexColor(CMA_RED))
        pdf.roundRect(
            button_x,
            button_y,
            button_w,
            button_h,
            5,
            stroke=0,
            fill=1,
        )
        pdf.setFillColor(white)
        pdf.setFont("Helvetica-Bold", 7.8)
        pdf.drawCentredString(
            button_x + button_w / 2,
            button_y + 5.6,
            "TÉLÉCHARGER LE FORMULAIRE D'AIDE CPSTI",
        )

        # Zone cliquable du formulaire PDF.
        pdf.linkURL(
            form_url,
            (
                button_x,
                button_y,
                button_x + button_w,
                button_y + button_h,
            ),
            relative=0,
            thickness=0,
        )

    # Alerte discrète uniquement si un contenu exceptionnellement long descend trop bas.
    safe_limit = bottom_y + bottom_h + 8
    if min(left_y, right_y) < safe_limit:
        pdf.setFillColor(HexColor(CMA_RED))
        pdf.setFont("Helvetica-Bold", 6.5)
        pdf.drawRightString(
            page_w - margin,
            safe_limit - 2,
            "Contenu dense : certains éléments gagneraient à être raccourcis.",
        )

    pdf.setFillColor(HexColor(CMA_MUTED))
    pdf.setFont("Helvetica-Oblique", 6.6)
    pdf.drawRightString(page_w - margin, 34, fiche["source"])
    draw_footer(pdf, page_number, A4)

def generate_pdf(
    selected: list[str],
    entreprise: str,
    conseiller: str,
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

    # Toutes les pages restent en A4 portrait.
    page_number = 2
    for nom in selected:
        pdf.setPageSize(A4)
        draw_organisme_page(pdf, nom, ORGANISMES[nom], page_number)
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
            font-size: 1rem;
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
                Sélectionnez les organismes concernés, consultez les démarches
                avec le chef d'entreprise, puis générez un dossier PDF prêt à transmettre.
            </p>
        </div>
        {logo_html}
    </div>
    """,
    unsafe_allow_html=True,
)

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
        <div class="section-title">2. Sélectionner les organismes</div>
        <p class="section-help">
            Cochez uniquement les interlocuteurs utiles à la situation de l'entreprise.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

selection_cols = st.columns(2)
selected: list[str] = []

for idx, (nom, fiche) in enumerate(ORGANISMES.items()):
    with selection_cols[idx % 2]:
        if st.checkbox(
            f"{fiche['icone']} {nom}",
            value=(nom == "Assurance"),
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
        <div class="section-title">3. Consulter la feuille de route</div>
        <p class="section-help">
            Les cases peuvent être cochées pendant l'échange. Leur état n'est pas conservé
            après fermeture ou rechargement de la page.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

for nom in selected:
    fiche = ORGANISMES[nom]
    with st.expander(f"{fiche['icone']} {nom}", expanded=True):
        st.markdown(
            f"""
            <div class="organism-heading">{fiche['icone']} {html.escape(nom)}</div>
            <div class="organism-objective">
                <strong>Objectif :</strong> {html.escape(fiche['objectif'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        todo_col, docs_col = st.columns(2)

        with todo_col:
            st.markdown(
                '<div class="mini-title">To-do list</div>',
                unsafe_allow_html=True,
            )
            for i, action in enumerate(fiche["todo"]):
                st.checkbox(
                    action,
                    key=f"todo_{nom}_{i}",
                )

        with docs_col:
            st.markdown(
                '<div class="mini-title">Documents à préparer</div>',
                unsafe_allow_html=True,
            )
            for i, document in enumerate(fiche["documents"]):
                st.checkbox(
                    document,
                    key=f"doc_{nom}_{i}",
                )

        st.markdown(
            '<div class="mini-title">Points de vigilance</div>',
            unsafe_allow_html=True,
        )
        for point in fiche["vigilance"]:
            st.warning(point, icon="⚠️")

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
        <div class="section-title">4. Générer le dossier PDF</div>
        <p class="section-help">
            Le document contient une couverture en portrait puis une page paysage par organisme.
            Les cases sont interactives : elles peuvent être cochées et enregistrées sans impression.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

pdf_bytes = generate_pdf(selected, entreprise, conseiller)
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

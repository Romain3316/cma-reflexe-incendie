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


def draw_checkbox_list(
    pdf: canvas.Canvas,
    items: list[str],
    x: float,
    y: float,
    width: float,
    font_size: float = 8.3,
    leading: float = 10.2,
    gap: float = 4,
) -> float:
    for item in items:
        pdf.setStrokeColor(HexColor(CMA_BLUE))
        pdf.setLineWidth(0.8)
        pdf.rect(x, y - 7, 7, 7, stroke=1, fill=0)

        text_x = x + 12
        lines = wrap_canvas_text(
            pdf,
            item,
            "Helvetica",
            font_size,
            width - 12,
        )
        pdf.setFillColor(HexColor(CMA_TEXT))
        pdf.setFont("Helvetica", font_size)
        line_y = y
        for line in lines:
            pdf.drawString(text_x, line_y, line)
            line_y -= leading
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
    pdf.setFillColor(HexColor(accent))
    pdf.roundRect(x, y - 20, width, 24, 6, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x + 10, y - 12, title)
    return y - 30


def draw_logo_or_fallback(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
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

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(x + width / 2, y + height / 2 + 5, "CMA")
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(
        x + width / 2,
        y + height / 2 - 8,
        "NOUVELLE-AQUITAINE · GIRONDE",
    )


def draw_footer(pdf: canvas.Canvas, page_number: int) -> None:
    page_w, _ = A4
    pdf.setStrokeColor(HexColor(CMA_BORDER))
    pdf.line(34, 28, page_w - 34, 28)
    pdf.setFillColor(HexColor(CMA_MUTED))
    pdf.setFont("Helvetica", 7)
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
    page_w, page_h = A4
    margin = 34
    content_w = page_w - 2 * margin

    # En-tête
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.rect(0, page_h - 110, page_w, 110, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.rect(0, page_h - 8, page_w, 8, stroke=0, fill=1)

    draw_logo_or_fallback(pdf, page_w - 178, page_h - 92, 138, 48)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 21)
    pdf.drawString(margin, page_h - 48, nom)

    pdf.setFont("Helvetica", 9.5)
    pdf.setFillColor(HexColor("#D7E1ED"))
    pdf.drawString(margin, page_h - 69, fiche["sous_titre"])

    # Objectif
    y = page_h - 135
    pdf.setFillColor(HexColor("#EEF3F8"))
    pdf.roundRect(margin, y - 48, content_w, 52, 8, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(margin + 12, y - 14, "OBJECTIF")
    draw_wrapped(
        pdf,
        fiche["objectif"],
        margin + 12,
        y - 30,
        content_w - 24,
        font_size=8.5,
        leading=10.5,
    )

    # Colonnes principales
    col_gap = 16
    col_w = (content_w - col_gap) / 2
    left_x = margin
    right_x = margin + col_w + col_gap
    section_y = y - 75

    left_y = draw_section_title(
        pdf, "TO-DO LIST", left_x, section_y, col_w, CMA_RED
    )
    left_y = draw_checkbox_list(
        pdf,
        fiche["todo"],
        left_x + 8,
        left_y - 2,
        col_w - 16,
        font_size=7.7,
        leading=9.2,
        gap=2.7,
    )

    right_y = draw_section_title(
        pdf, "DOCUMENTS À PRÉPARER", right_x, section_y, col_w, CMA_BLUE
    )
    right_y = draw_checkbox_list(
        pdf,
        fiche["documents"],
        right_x + 8,
        right_y - 2,
        col_w - 16,
        font_size=7.7,
        leading=9.2,
        gap=2.7,
    )

    # Zone basse
    bottom_top = min(left_y, right_y) - 4
    bottom_height = 112
    bottom_y = max(42, bottom_top - bottom_height)

    pdf.setFillColor(HexColor("#FFF7E8"))
    pdf.setStrokeColor(HexColor("#F0D7A5"))
    pdf.roundRect(
        margin,
        bottom_y,
        content_w,
        bottom_height,
        8,
        stroke=1,
        fill=1,
    )

    pdf.setFillColor(HexColor(CMA_AMBER))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(margin + 12, bottom_y + bottom_height - 18, "POINTS DE VIGILANCE")

    vy = bottom_y + bottom_height - 34
    pdf.setFillColor(HexColor(CMA_TEXT))
    pdf.setFont("Helvetica", 7.4)
    for point in fiche["vigilance"]:
        pdf.setFillColor(HexColor(CMA_AMBER))
        pdf.circle(margin + 16, vy + 2, 1.6, stroke=0, fill=1)
        vy = draw_wrapped(
            pdf,
            point,
            margin + 23,
            vy,
            content_w - 35,
            font_size=7.4,
            leading=8.8,
            max_lines=2,
        ) - 2

    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 7.8)
    pdf.drawString(margin + 12, bottom_y + 14, "Contact / démarche :")
    pdf.setFont("Helvetica", 7.8)
    draw_wrapped(
        pdf,
        fiche["contact"],
        margin + 90,
        bottom_y + 14,
        content_w - 102,
        font_size=7.8,
        leading=9,
        max_lines=2,
    )

    pdf.setFillColor(HexColor(CMA_MUTED))
    pdf.setFont("Helvetica-Oblique", 6.8)
    pdf.drawRightString(page_w - margin, 34, fiche["source"])

    draw_footer(pdf, page_number)


def generate_pdf(
    selected: list[str],
    entreprise: str,
    conseiller: str,
) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("CMA Réflexe Incendie")
    pdf.setAuthor("CMA Nouvelle-Aquitaine - Gironde")

    date_edition = datetime.now().strftime("%d/%m/%Y")

    draw_cover(pdf, selected, entreprise, conseiller, date_edition)
    pdf.showPage()

    page_number = 2
    for nom in selected:
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

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">4. Générer le dossier PDF</div>
        <p class="section-help">
            Le document contient une page de couverture puis une page par organisme sélectionné,
            avec des cases vierges pour l'entreprise.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

pdf_bytes = generate_pdf(selected, entreprise, conseiller)
filename = f"CMA_Reflexe_Incendie_{safe_filename(entreprise)}_{datetime.now():%Y%m%d}.pdf"

st.download_button(
    "📄 Télécharger le dossier PDF",
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

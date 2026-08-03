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
from reportlab.lib.utils import ImageReader
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

BPCE_INCENDIES_URL = (
    "https://newsroom.groupebpce.fr/actualites/"
    "incendies-en-france-le-groupe-bpce-deploie-un-dispositif-d-urgence-"
    "pour-accompagner-les-clients-sinistres-des-banques-populaires-et-des-"
    "caisses-d-epargne-25d7f-7b707.html"
)
LBP_INCENDIES_URL = (
    "https://www.labanquepostale.com/content/dam/lbp/documents/"
    "communiques-de-presse/2026/cp-lbp-incendies.pdf"
)
LCL_INCENDIES_URL = (
    "https://www.lcl.fr/decouvrir-lcl/presse/"
    "incendies-lcl-se-mobilise-pour-accompagner-ses-clients-sinistres"
)

BANK_LOGOS_B64 = {
    "bpce": (
    "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"
    "2EsGGgFqRJD3ep6WPWdnicD4OZU7xEinvJB6BzHtHFONXQlet2ul1Vq5nbSXSdKM73E3sn7fSqNxxwU3e3MfGW87Yxwpvth3srtj"
    "tTcs9Poy3WzcOcvDDEliVJojSeQf88z7ot9lvmPvnF/Bzjr31O20nepfReEIAk0jQC0POxlNlCbD8QQTTDDBBL+R5PnXjeEwlVGD"
    "1wpSs7Ao7Wlfie71etLcx+aQbr8nrYZ/bpqmkiS7bnv5hGC5bV4/K6URB6qUnnhN6R0hPGm1Ptm4Q8lzt7vVPRDnQdqTetJUvV5H"
    "lFI0Gq1fKxnp9UppNoNf62uMjv+vn2jv6nbRWUylPbXvk6JBlsqkYnoHyfpOn8fdJVsO+rnUG9HkuE4wwQQTTHDvJ89FnkoY3TPI"
    "Qn/Qk8Zulvx6/QVpNu768l5vMCfN+uwd3E636ms3KH49XeCLnR0y1V61T9seLXneke1nw67Etda9hrgUZSph8L97Tab9XLSy1JJf"
    "T2jH8snkIEvFOUejfu91FUj7uSQ7keGin0nYiCcE+f/H6FGK4BtYE3Z/LeyTpeMEE0wwwT2ZPP9foixSCcJEWee77I1O1J7IYV70"
    "JQr/LwbcnowizNW9xAVgRD73pg2+pyMrFiQO7x49pE2tmMSoe+b73Hdf8Xv0+eoNJW7W9vo+Bv2h1Bu1CWn6DSfPCkuDySRqggkm"
    "mJDnCSaYYIIJJphgggkm+I2BnhyCCSaYYIIJJphgggkmmJDnCSaYYIIJJphgggkmmJDnCSaYYIIJJphgggkmmJDnCSaYYIIJJphg"
    "ggkmmJDnCSaYYIIJJphgggkmmJDnCSaYYIIJJphgggkmmJDnCSaYYIIJJphgggkmmGBCnieYYIIJJphgggkmmGBCnieYYIIJJphg"
    "ggkmmGBCnieYYIIJJphgggkmmGBCnieYYIIJJphgggkmmODeg/8PoVagz3aYxbgAAAAASUVORK5CYII="
),
    "credit_agricole": (
    "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"
),
    "cic": (
    "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"
),
    "banque_postale": (
    "iVBORw0KGgoAAAANSUhEUgAAAawAAAEsCAYAAACfeId0AACxa0lEQVR42ux9eXzdVZn+877nfO+SpC1dklIoCIo6topoWVqWJikw"
    "ojOu440CwoijdgQKKjI64+jN1XFFlC7g4DjjjI6Cuc6M4/hzHIUml7UFKi60KiI7LU26J7nb95zz/v743psmaba2SZO05/l8YtXk"
    "Jt/lnPc5z3ve8z6Ah4eHh4fHNAD5RzAFIOLfg4fHlImKJP4heHgMgVRbm/JPwcNjai0gU22iUm2i/GLSKyyP/sqKSE5b/ZN4Q/3i"
    "uSqe9Cs7D49JgoG1tFsXHnh/fffARaWobArOKy9PWMcs0mnhTIbcsu89eyknajOuVFwo5N+Hh8ckIiTBXiF+jph+SaT+D3t3rH/g"
    "/a/q7iOuFrL+MXnCOsbYShgZcufcse0UJvm9StTEbCkPIgL8Gs7DY5KiIQGswFqDVABxFrZcfBaCfy+XCus2XXHKNqSF0QrxassT"
    "1jGD6krtnLYXLg6Cmp/ZQm8ZTDGI+Eng4TG5pCUiEBAE4piDOKtELWy+Z7tY++kHLz3hG9GiM83IZJx/YJ6wjn5Ee1c4v23rPOvw"
    "W5Wsm2sL+0IRKCJi/4A8PKbMXBUBLOuYVokamGLvd3uf3rby1zee0VvNlPiHdOTgg+MkreLSaaH7Wk7ogrh3iQn/qGpmBSqeZBFx"
    "IuLz5B4eU2OuEhFpMSUJe/YYXTPj8pqXHP+T137rqeOQIYd02sdQr7COKaUlZ6/eMFOf8NJ3QeRDHIu/DgBsoUcEcETgKLnu4eEx"
    "BeZsqGfMDkzv3vauGT1vfF3PL002lfIVhJ6wjpkJwKAorbDk9keCxMyT3mwVXc2MCzmWhC10Q6y1RMRRVYaHh8dkk1Ywc25Q2rvz"
    "9o2XLfxrXz3oCeuYU1qpLLj/oF/atrWRhK4hpreqRF3MFnrgTOiJy8NjKkxZwOhknbaFvW9/8N0n/9CTliesY3EaUKoN3P+Q4tK2"
    "F19DwIcAvFsn62bbUgEuLFkiEOALNDw8JmeNKU7FE+TKpadivPu1udTi3iii+tTgRMIHvKm1fpBsC1kQSaqtTaXaRG1oOf43D7Yc"
    "f7UthafbQk+rWPN8UDtLcSzJIs4XaHh4TMZMJWJbLDhdd9xLS272VSCSxtYO32bNK6xjHGnh1GJQNd2wpO2Ps+KouwyED3EQfw3g"
    "CzQ8PCYJlmMJtqX87/epva/dkloceoXlCcsjykEM2OdacvsjQWz2CW8lVteAuImDOGy+GyJiCFB+n8vD44hMTMexJKOUb77/0pM6"
    "/F7WxEL7RzBtchCSBWw/4goB/ADAD87JbmuSor2WWL1FJ+sCW+iBs8YTl4fHRNMV4DiWoLCY/zMAHZ31HX6+eYXlMcRUOaBA49y2"
    "588QUX8NonfpmhnH2WIvXLlsiX2BhofHhMxCgdXJWmUKPfdtuHThBdWzlf7JeMLyGAaptja1KJWSTOU81zl3PHUKceKvmOgqlaw7"
    "0YUl2FLBIjq374nLw2P8GEsoiJEz4Vbu2fcnD7z/Vd2etDxheYwFgwo0lrbtmQOULicxH1KJuldBXKVAgxwR+YomD4/x0FikCM6V"
    "YekVD77nhGd8Y1xPWB4HRVxpbkQT5zLNBgAWtT0Wm4WGdwD2Gtax80kFUQcNJ5YI/iCyh8fhEBaYIE7EutdueM/Jv/FNcT1heRza"
    "XDqwg8adz1/EHFwj4t6qa2aQLXTDWesLNDw8DpmwiAAR5+SMjZed9GtPWBMHv59xVC9HKgeRIZRqEwUR2vDuhXc90DL/7c7IWabQ"
    "+08C6g7qZmvSMYoOIYufaB4eBzfPIAJrxfX4h+EVlsc4ItXWprKbU1JdAZ57x/aXicL7iPCXKlHrCzQ8PA5OYAnpgJwJu+LF8BW5"
    "q07d44suPGF5jDcGd9D47gvz4gFdKcR/pWI1iyDWF2h4eIzKV7A6UaNMsffhDe8+8Zwoonqymij4FfSxigy5bAtZpIUb0+160+Un"
    "7nig5YSvxnoKS2ypcKUpFR/geA3pmpmqspC0Ub7ew8OjP2WRjglAD4NIGtO+n+BEwne68MTlcoCDCDW2dqjcVacWAXwHwHeWtm2/"
    "BCa8lonfpGvqlCn0QKzxFiceHvsJi8WGBGd+CgANi5v8om4C4YOOx+AJeEAHjWV3bj0LSl8Nse/SyRlJW+yFC8uWmHwHDY9jGY50"
    "jCQsvRBTwatyLfN7/P7VxMIHG4/Ba5h+FieikBZ+8N0nPPxgquEqQXi6LfR8CcD2YMZsxUGCRcSK+MpCj2NwaeecqEQNCeRfcy3z"
    "exrT7dqTlScsj0lCtoUsMuSQFk61takNLSc/8UDL8Z+wobzWlvI3OGcf17WzlE7UMiDem8vjGGIrEQ7iFPbu3W1V7FaIUA4dfuE2"
    "0ctp/wg8xoxBlYWnf3tbbU1c3klKfYhVcA6xgi30QKTSQcN7c3kcverKBjPnqHL3nk9svPTEL3lbEU9YHlN3dRkVaFRaPwGgZW3b"
    "3gTQ1QS8kZO1ZPO+QMPjKB3+EKdiSbLl4hNhDc7YtOmEIlohPh048fApQY9DWOaQ5DLNBlLpoAHIgy0L/t+DLcf/GSmc64o93wFR"
    "PpgxW5EOSJzzHTQ8jirGIqUJDh/f9JYT86nFWV9o4RWWx3RCqk3Uos2QTKWDxvl3dL7CKrsSgit1zYx5rlyALZd8Bw2PaZ5cEKtr"
    "Zqqwd+9dGy876eK0CFdtfTw8YXlMM6RFeEt2/z7XOd97cT4H9F6I+4BK1L1MbAhbzDsA4jtoeEw3ugIrx0o7saWzH2hZ+Eu/d+UJ"
    "y+PoYK4BBRqNbY/VlVGfAnA1B7EziRk23y0COF+g4TEt6KpSaBHu2/X1DZeddLUnK09YHkffonSgxUmqTS39iwvexEpdA8IbOJas"
    "eHM5b3HiMaXpinQMYu1uZ2nxxt9/vQtohbcR8YTlcSwQF4ClP9h+Hjl3NUDv0Mm6hO+g4TGl1dWM2cr07P7wg5eetNqrK09YHsfG"
    "1D+g9dPZbVsXMbCSSF2mE7XzbLkA5ws0PKbMWkucStSwLeYf29GZP/OJ614eAr6M3ROWxzGFVFubAlKorlTP/d4zJ4iOvw/A+3Si"
    "9lTnCzQ8pgRhRRYiYbHnTRsvPel/vbryhOVxLOOAAo3tdWXIZQT8NccSrwNQ8ebyBRoeR1xd2aB2lgp79vx4w2UnvdmTlScsD49q"
    "dBiwz5Vqa1PP8/I3k9A1IL5IxRIwvkDD4wiyFVgJmENn7Os2Xrrgd0iDfKGFJywPj2GJCwCW3bl1OSn1IYG8QyfqYrbQA2eNqexx"
    "+X0uj/Efhn1l7Du/uuGyk2/w6soTlofHiOMz1SYDCjSWtr34GiJ8AIL36OSM2a6Uhw1Llgi+stBjPOFIByTGbDelPa9++Mnv70Zr"
    "qy+08ITl4TE6Um1talEqJdU2OOe1vXCydXIVc3AVJ2peIqYMWyr4Ag2P8VNXURn7ygcvPekbXl15wvLwOHgMKtBY0rZrVhzhZQL3"
    "IRVLvgboX6BB7Me4x0GTlYjTiVoOC72/SCw48ZymDriM37eaEvApFI/phQy5bAtZpNPcmG7Xm1rm7H2gZf7XY5t/93prSylbLuY4"
    "iFNQO1MBiDrFi/g0jsfYV/FEIuIgLB/LNZPZstgverzC8vAYn+XwAQUa5965rVmUukaseVtQO1PZQjectYYIDPFj3mPEiGhUzazA"
    "5vdmH3z3whafCvSE5eExIWN5cIHGOd977nTWsQ8BcqmumTHLlQoQcX7YewwDB+IAYsMCDF7zwLsbnkSrL2P3hOXhMYFItbWpbCol"
    "qBRonHPHU6ewrnkvAZeKuDqxlvzZY48DgqHAqtoZKuze9fWNl5/yWa+uPGF5eBw5DO6gkW7XaGrSePpp/2w8hkXuqlOLEPEuwh4e"
    "HpNDXI3pdu0fhMfYIH4h7xWWh8cUCER+zewxalT0ysrDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PD"
    "w8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDYzzgm996HBsQocaODuUfhIfH5KKhq0m8z5iHxzBItYknKg+PqYa0"
    "sFdYHh59EyLN6dZWZIjc0n96bA7Nqv8gnJkDIiPix76Hx5GDAxyIgmA3WffQA+9e0N5HWpnIGdwTlscxi8Z0u85lmg0AnN229Z2K"
    "9Jd0Td1L4awf9h4ek0ldJoRYk5Punr9+8KpTf4d0mpHJjIm0/Mz1OPrSDK0QEMmyf9/6EsTVl1QQf5dYA1suGpAf8h4ekwYBAKFg"
    "xmxlevc9LxQu3ZA6aStaQWNRWt423ONomQnUmO5QuQwZZIBz27Z+CKw/o2LJeWHvXkcEEJEf7x4ekwmK/iPct6scO65+YXlP1ydB"
    "dHWqTTjrFZbHsYBUm6hq1dFZbc+fEaj4TSqWuMgW83Bh2RKzL7rw8JhacBzEyIblJ/fx7kVbWl5dBoQAEq+wPI5SUSWUyoKzLWQb"
    "v/VUolyT+ASx/hvWsWTYs8cSiD1ZeXhMzbkrIgSRujk1M2oBlCGjSyhPWB7TV1UR2Sxgl975/EVlFfuKTta+1vTuhQlLlsgTlYfH"
    "lAVBiBgg2lt4oaun8v+NCk9YHtMLlbMb2Rayy779RAPFZ3wGileSUgj37bJExETkycrDY0oLLBhO1MRsqdixaeWZYf+0vicsj6NH"
    "VVUG9dI7X7gcKvi8StScbHr2iAshPv3n4TGl4UREiOB0si5mevftMWK/BBHKtkLG8gs8YXlMA1ElnAEkS2TP+e5zL1eB/jLHa97m"
    "wjLCnj2GiDT5AiIPj6kmo0QAh6iaQnEQZwriIGblysUnpFx87yPvOeXJ9OPCmTEeHvaT3GMqD3hqbO1QlQPAtPT7Wz9MrNIqXjPL"
    "9O61RCCA2D8oD48pw1CCiKSYlWaOJ0FKwxZ74cLy88TqQRD/b3n3c/+5aeWZe32nC4+jAgNK1bNbzwygblaJ2uW20ANnQl+q7uEx"
    "NUjKVUgKxKw4lgDrOMSGsOXCbgg2iZj1JJTbq4Jfb2mZ39P30YMkK09YHlNSVVVL1U//9i9ra5MnfJIIN7COxUy+xxKBQb5dhYfH"
    "5IkoOICESBQHceIgAQAwvfvKQtgMkXtZ03oEsYcfeFv91oEL0TYFpJBNwYFIDvbP+4nvMSVV1Tl3PvcmpeM3qUTtItOzByJiffWf"
    "h8ekMJQAcAQw6YA5lgCxhi32QKx5Cko/QCIdNgxzGy8/6Q8DPp5Oc2NTKzd0ZSWbSh0SSXnC8phaqNoMZMid+83fnoBZc/+BlLoK"
    "AGypYIig4JsAengcKZIalOZLgnUMzpTgyqWdADaJuLvBtiPcrR7btPLEfP9PN6bbdcPiJjlUFeUJy2OqghrT7dWiCpx7x7b3ilaf"
    "04maE0zvHicCEPmiCg+PiRdRlWo+Is1BHByLQwSw+X1lEfk1QDmnuJ0MPbLxsuO3D86MdG7uoBya3MHuSXnC8pgWSLW1qWxLiwWA"
    "s7/z9CIVT9yk4jVvcmERrlzyRRUeHhNKUOQAESIwqYA5lgQpBZvvhoj8AYoeEOvaOVD3PfCO+X8cnBFpbAI3NcFlEDkjHLEVrn97"
    "Hkd4svQVVSy5/ZEgNnPBDdDBJ1U8UWd691mCMIj9uPTwGN+J5wTkIELESqlYAhQEcGEJUi51CuQRQNrJcsfM4xb85qdvolL/T09k"
    "ms8TlscUVVX7iyrOa3vhfCF9s0rUnW0K+yDW+qIKD49xVVHVaj5ojiXAQRziHEyhu0iCX4ui9UyqPVSJTQ+/Y9bOwXP1SKX5PGF5"
    "TC2k05xa3EqRqvrjrNicmlYSup5icbL5HktEvlTdw+OwCaqS5oMoCuLEsQSIGCa/D0T0WwE9AMHdzsmDGy9d8PSAKSrCHR2Tk+bz"
    "hOUxZdDfqn7ZnS+8jZT+skrUvdz07hERJ0Tsiyo8PA6BooAKSYkQK6WifSgNF5bgwtI2CB4WZztEq3u6ses3kefU/tjfmG5XUyHN"
    "5wnLYwqoqv1W9Wd/5/GFKnncF1gF74GzsOWi8e6/Hh4HDRcJKRLCwDSfze/LC9GviLkd0HfHent+kbvq1D39PzxV03yesDwmc+FX"
    "saqvqKq2rR8kDj6j4on5pnevizzafKm6h8foU6l/mg/90nwEk98nIPodgBwc1odiNzxy6cLnBhJUm+qsr6empiaXIchobr6esDyO"
    "KfQvVT/ne8+dzrH4TTqW/FNb8lb1Hh5jYaiIpsgBqKT5ElGar1yEM+XnReQhCNpVTN9b3NGwZdNKCvt9nBpbO6Zdmu9g4NMyHuMx"
    "z/Zb1afbE+VFr7qRlPoEB/GasHevJcBb1Xt4DA1XObQLAmuOxYmDOIs1MMWeblcqPMqEnIO6ex+pTVve1a95LKI0HwBkN7cKiFwO"
    "MEfzw/IKy+MwVdX+UvVl39u2ggK+SSXqXm/yeyHO+VJ1D4+Bi7v95eaoNI+NJQACTL7HENHvxLkOQO6Won14w3tPfmHwfOvc3EFN"
    "aHKZzNGR5vOE5THxiIoqACK35Lu/mxfo4zKs+GpSGrbQ60vVPTyqDAUIqmk+rRQHUVcJVy7AheGzENkgROsJdP9CPv63A6zij4E0"
    "nycsjwlF/1L1c+54/l1KBV9SybqXmN7dEllg+1J1j2MaUZovmgqKg0TUm8+EsIWevcLqEQLlyNmOnrDrF7++8ozewfPLE5QnLI/D"
    "FlWRVT2I5MzvPvPSWCz5RQ5iKWdDuHLJl6p7HLMiakCaL9bPI6rYXQZoC0Tuddbd5XTw0MMt81/s//GB5ebHXprvYOADjMdYJiQ1"
    "tnaoDFFUqp7ddh2RSqtYck7Yu8cRETxZeRxjDLXfCl4HrGIJRaxgS3nYsPSsLZfuJ1Z3OYcHN1664LcHzKeODtXQFamoLPVLAXp4"
    "heVx6Bhgqti2dYkidTMnahudt6r3OLZIakDz2OjQbgxiyrDFwk5iekSADuuow+59/tebVp55xDyiPGF5eAzoqv5CTWyO/jsiupGD"
    "WMz0dvuiCo9jQET1ax4bxKOuEhDYQm8RwGNw7l5A1iNUDz145YLOwQu9fl0lBIAnKU9YHhOuqu547o0qSHxJxWteY3r3QsSXqnsc"
    "tQQVpfkIzKpqBa8iK3hjngLzA0LqZxLSgxsvbxhkBS/c2NTBDV1d42IF7+EJy2M09LOqP+tbTx2v65L/wCr4KwCwxbwlJvZW9R5H"
    "EUsN9IiKJ0A6FjWPLRd3EPFGAdoNuVxNT+mx3FWnFvt/urFddEMXfJrPE5bHkR4H/a3ql35/61+yUp9T8doTvVW9x1Gmogam+WIJ"
    "iDi4Qm9eIL+Gc/c4cEeg8Mh9LSd0Dc48AEB2M2S6No/1hOUxrTGg/9+/PfUqSia/rOM1f+7CIlxY9qXqHtOcoIawgmeGyXcDzj4B"
    "xfcBar2Fu++hlgVPDc44NDZ1cFNT05T2iPKE5XEsTOb+/f90afGffISIPq3iNd6q3mPajuohPaJ0UGkeG74I4GGIvYtI31Pa3bD5"
    "gOaxHVA+zTd14VfPx6SqEpUlslnALrvj+XPLOrg5SNQuNYVumN59laIKz1Ue00VFReQSeUQlo+axzsGWenpsoedXEOSc1h1Om188"
    "/I6FB1jBA5U03zHQPNYrLI/pg35W9Wd/Z8NMHT/lU2D6COu4MoVeQxDlS9U9pgVBARWPqNh+K/jevRDI74iDewXSEcLet6nlxGcH"
    "TgHhjqaKFTz5rhKesDymJPr3/1t65/NvJh27SSdqX2l69kBEfKm6x9RlqL7msf2t4AO4cgFiwxdE5BEQfiZlc2/8xD/+NtfcbPp9"
    "fEBXCZ/mm97wKcGjXlVFVvU5InP2Nx5fqOcc9zlS+kqIQ9i92xBBebLymGLoZwXPWsUSxEGMxVnYQk+PKfY8SqB2p2LtxSDxy1+9"
    "ffae/h8+1jyixg2pNoXOzaOLmIbFgmzLpLST8grr6F2ZDrCqX9q27a+Y9T+oePJ407vHQQD4UnWPKSKiBqb5+lnB9+5xAG8G030A"
    "r7el8oaHrjjp+YFrMuGOjg7OdYy1eaz0i3uto8TAjDtW4sXBpUcP9uc9YXkMu1DaX6q+9N+ffQ3HEzdxPPkGVyrAhSXf/89jKjCU"
    "ICo5Z1aa+6zgS3k4a58DsME5addC99x/6fG/BfU79+TTfBNCVvOXr26WWPI0siUDkQMXsyQilGC4Yldnx/X/7RWWx+HGgb5S9dNW"
    "/yReP/+MG0mpv+VYssbk91kCfP8/j8kanE4kOstERJpjCbCOQayBLfbuE5FfAribQe1Ixn75wNvquwcuwvql+TKHqHpSKYVs1s5b"
    "vvajHEv+GWwxFJERF2+k1MrOu69+EiJ0dBJjmoFWqW+8dT4x/YGD2jpxZpiGNhJRhlhYV1qyY/2qR5Fq4yOZHvR7WEeNqtpfqn7O"
    "Hc81sQq+opN1S0yhGya/zxdVeEyCiOpL82mOxZmDBEAE07PHSbn0KxuG94JkfTkMH9p0xSnbBo/nzvoOqqb5BrjwHio6FxEAEOH1"
    "Kla7wpXcqFlxK72zAACtrYSjsYFtajEhS05ozQ2s6+pcuacEyEi8YClIBuQkDeCtQPaIXq4nrGm/QEpzurUVGSK7tO3ZOQSdIdLX"
    "kg4Q9uwxBF9U4XHEGGpoj6hiL5wJn7Zh+KA4aRfN9z+UOv63AxRLnxV81Dx2Qj2iCHkJC1Zs2YwSnMGsj2KvqjQjm3ILLrrlZGv1"
    "SrFFB0JslH6hSkzRsYq9ub751nO7stc8gFSbOlIqyxPWNEa1VD2TyWBZdluKSH1JxWtPNb27xZmSELF/vx4TSVL9mseyUvEEsY6x"
    "2BCmmN/t8t2PstLrgWB9OWl+tektJ+YHqygAqO5DHbFqPgGDSCE6h6VGpmF79KbQK+rK2rUfJ52YISZvxsQJIgLSDCm3AvhTLNp8"
    "xJSnD2jTcmG0v1T9nDueOoV17ZdVEEuJDRH27DZEpMnvVXlMiIjqs4LXHEswxxIsIrD57rKEpcesCduttesDpofvaznxgOax/T2i"
    "xiXN53FY6qq+cd1pQnwVTNEBGFsmhqiisuIXz2++bcX2zNXrj5TK8oQ1vQIGNbZ2qFyGDDLAsu9vu4ZYZTienGt69zoieKt6j/Fm"
    "KAHgiMA0OM1nwydsb/FBsWi3AR54pOXExweUOqfT3IgmPiJpPo+DVFdbqntXf6dUTXLM6qrf2AAxnJRbAWlHtvWIqCwf3KbL+KoU"
    "VeQAs/TOp19PquYrOlHTbIs9MD17fKm6x3iR1GCPKGIdY2dKcMXCTmvzDxNzu1Fyz67nux994vpXlPp/epAVvMsdM+eYppO4SjMy"
    "GXf8iq8vcpDLxRTGrq4GqKySY524YF7zP75xR3vmJ0dCZXnCmgaqqr9VfXAc/y0p/TGlY4mwe48lAnuy8jg8EQUXxSBSHFTTfA6m"
    "0FMUU/q1CQs5a+UuKcumh/9ywQHNY/un+aoH1T2mMLZsIQDOuvBTHNTGxBQOUl31U1kQkIStSKd/iszE72V5wpoGqioL2HOzL/wp"
    "KLhJJWpPN717YcKSJfbVfx6HQlD9PKKCGKsgoYgZttADZ8p/sOXSfQ6unZU8+EDq5CcGrs6FG9ERpflaUs7vQ01LdWXnrVj7eoJO"
    "ycHsXQ2tsizrmrPqO+QdXbj+BxOtsjxhTclBFZ0yz7aQPed7f5zPQc0/EAfvB3HU/8+XqnscBEUN9ohSQUJREIMrF2FLhU5xZiOB"
    "O0Dqnr3Y8estl7663P8XNLa3635dJVyuosg8pi/ISppiMSVh3o5yGK1yWngkOAHRp7Hk9v9GdrNPCR5zqqqyal12x9YrSKnPq0Tt"
    "QtOzRwQQX1ThMTYV1S/N1+cRZWGLvb02LP5aSoUc4O7Wzm6679KFuwePwX5pPjeg+7nHdA4uCpkW23Dh2mWAfrOYgsNoC19igrjR"
    "VVZQ+5r6mT3v7kLmO2hMa+QyEzJmfPCbMqJKOENRqe/5dzz/CquCL6t44q0uLEcHgIk0+VZaHsMS1KA0XyyhiBgmvw8uLD7uyoV7"
    "Adzl4rUbNr599tODFX0jOriptcllCL7c/GhF9byURSvpgESMG/mMMAlgPyrAp4nUcRXioqFYC84IhP7+tEtWtz3x011h5efGfU/L"
    "E9bkBxtKZcEZIot0mpctXvlRx/pTKpaYFbn/gryq8jgwTSMifR5RWqlYQvVZwZcKL1pnH4Sgw4rKJX+7ZfPAYgihxvYBVvAuB7hc"
    "xj/Yo11dzV9xazMo+FMxxeHVlYglnVTOFu/pWr/qlvqmtYs4SHzAlXvtkJ8hsNiy5aDuFftK+SuBzD9NlMrygXBSx1C//n/fe+4c"
    "FUt8RcWT59tCD0zPXl+q7tEfkUcUDkzzuVJ+ny0VfiXF3g4SycUS4abc2xfuGTzWgIoVfIZcrtl7RB2L6so518qaEFX4DaeuiCAW"
    "JPgsICRm3VcsFd9DxInoc0OrLHGhiOBv51980/e2/7ynMBEWJJ6wJlFVZVvILlr3WN1xDQ1/D8INrAMddu+2RORL1f0YGWwFz6rP"
    "I2qfc+Xi70wp/wDr+M+0jW2499K5z/X/eFqEO1p9ms8DQGNaI5Mx81bc9kbmYPmY1FVYWN+VW3X3kiVBsOm+VY/XN679NsVrV8oI"
    "Kgu2bDmoPdWG8n7gxtVohEZufBdGnrAmUVUty277c4L6skrWvsr07IExZa+qjmWG2m8Fz6w0q3hCkQrgSgWILb/gSvkHAKxnx/de"
    "9Pvjf5vJDPaI2p/my0T+UT7N50HIwQFpJmcy4AAYcW8pUleK+DMAsKn6f2r1ZRcWriDi5MgqqywE+pvZF93+r7vv+uC+yCBz/FSW"
    "J6wjhX6l6kv/9fcnUs2sz7GO/SVEvFX9sYv9aT5mpYKqFbyBLRb22GLvo+KkA87lwiD85abUy/ZWP3g/vBW8x5jUlUIuY+qbb30H"
    "q/hZYgp2VHVleu/q6rg+F53ZWhki1aY6sy1PNjSt/TeK1X5oZJUVWg5qT9Dl7qsB+kK0lzV+49IT1sSvnCtW9WQA4Ozvb3sfs/qc"
    "StQcb3r3OBHf/+9YElGDrOCjNB+AsHefdaX8FglL90LxerL6wQcuq986cM0TpfmicnOf5vMYo7pqbNeQx9KAk5ELjSN1JaQ+CwDY"
    "sjj64Wj/i8jKTS4s/CWxSkDc0CqLiMSVBKw+POPCtd/ovvvaXQAY49SiywfKCURkVU82l4FZduezrwbHv6wSyTe6UhFh925LzMr3"
    "VD/qGWqAFbyKJxUpDVvshTjzrC32bhDIz4yS+x5pWfj7waq8sQnc0JWVbCrVl+bzz9XjYNRVA9VfSkHN6ZVDwsOrqyCpXJj/+Y6O"
    "6+6J1FWlY0Um45BKqe3Z655qaF77r6Rrrx5WZQEMZw3r2oZE2HN9N+jT0XXAE9YUjlP7iyraHosdJ7M/Jqz/TsWTtaZ3nyWIL6o4"
    "el++q3Q4x0CPKANbzO+xhd6HRWwHiHPx+Sf8KtdMPQMXOQM8olwu4wnK49AyO8i1utMuWR3fW8TfkzMyypkrEmcgDgPVVRWLFkUq"
    "y5mbXFj8S2KdhNhh9rJEiS0ISF1b37jutq7cNdvHS2V5whp3VbW/qGJp29ZGgvqKqqk70+T3ITpXRcqf/z3aRFQlzUfQHFSt4AHT"
    "uze0pcJjrhzmiKXDsNr4cMv8Fwer8M7N9UeHR1R1oVYpnfeDYzIDUZaRzdg9hbVXqFjNn0jYO6q6knL+/3bcc929A9RVFX0q6yNP"
    "NzSt/RYHtdcOey4LRBBnWNfMtuXujwH0MaTaGFmvsKYO+lnVv/a/njquNqzJgGgV6YDCHt//7+giqKirBIa0gjdPOtuzAcBdwu7e"
    "DS1DNI/tl+ab3h5RQkiD+prhVhZqfpBMgfeSbZX5F99U60L6O7jyyOqKKuqKhlFXVWQjlRXq2E2BKb4XzLVRcetwKqvkWOkPLrjo"
    "ljXbsqnnqrYmnrAmGf2t6s+9c+tfiNFfUsnal5mePeJMyXmr+uk9+/s3jyVWSsUSinUAMSFsubjT5LsfAXC3aHWPSR7/m01voZGs"
    "4Kd3mi+d5tTiVurc3EEVI1GpNsNtXPdYXalhzvlibXHjpSd1QIRAJH4ITY66suG6v1KxmlNH2G+qqKsaZcP8T3d0XHf/kOpqv8xy"
    "SLWp3dmWZ+c1rfmWjtWtGlllGUu6doYN7ScAuhpb2tgrrMldbTMQWdUv+/cnX0KJGV9gHVwq1iDs3hUVVYB9/m9aqig4EAkBmoME"
    "cRBnAAjz+0q22PtrUSonQEehp/uhX/7VK0aygndHQ5qvs76Dck1NFkQui0zf95Z9/8XFwnQeOXthyGoZAwutwpkAgNaJ6SfnMbq6"
    "mn3R7bPIlP9GbElAI8grijpUEPHI6qpPZUUVg1a7r7ApvBfMdVHF4FB/g1R0SDl4b33juq92ZVv+eLgqyxPWIQ6KVBu4ms45t237"
    "h4TpMyqenBf27HZEBF9UMd0Iiir7UFKxgk9GHlH5bjhrHndh+KBA1rPo+x+4dP4fB6oO4camDm5qanIZQKZ7mi8toP1dMsj1T/Mt"
    "bdtxIqR4HjlaQW3bzhPgVUFyhnImhErWIdy1/fMbL1u4qb/rgMeRV1c6XPMhFa870Y1BXbmw9yddHdc9MLK6OlBl1Tev+RcV1F0f"
    "/Y0hPbUIcJZ0TRJh9ycBXIUtiw9LZXnCOtjxUClVz7bALv3O06/nZM2XOZa80JXyfaXq/ilN/ajcv3kssVK62jw2LMOVC1220P2I"
    "iG0XlVyf6O3ZnLvq1OJgFQUMTPPlpuvTqHRrB4BchkyGIKh0yVjStmuWcr2vZ9bNDDSKlM9QiRkziRVcWIKUSzC9e0IOEgj3dr2Y"
    "L4U3IS2cTfnqxslRV3AnXLh2bujoI86UBAQeUV3ZspDoirraMrZsUHazAELG3HwzofC+kVUWlJiCA+vLZzev+8rubMuWw1FZnrAO"
    "MjWSbSG7tO3ZJCH+CTD9DQfxhOndawneqn7qqyg4gKJqvr7msQ4mv69ky4VHYUrtZKhDzah9+L4/P25Ej6ijIs23uYNymSaLzH5T"
    "xiW3PxLEZ5+02MGdT9b9KVzhbI7VzOcgAbEhXLkIk++20XMUBohEwBTElSvm07+66tQ9lUpZT1iToq5abGjWXKfidQ2u3DO6uirn"
    "/19XbtUGpFIK2ewYx3TGIbVY7c5+7Ln6pjX/rIK6D4+ossQ50jWBLvd8CsC7D0dlecIak6rq11W97YWLCforuqauYlVftr76b6oS"
    "VMUjCqIoiFM/jygRE/7OhKX7xUm7cXbDI5cufHLQ57mxmhab7mk+EUojSvPl0OQwKM13zh3bTiFy5wFYAeJzBe4VQXIGi3NwYRGu"
    "XHC2VHSIdtJ5/3gniMDqZJ0Ke/c+dHKw4duXRL5uPhV45GUyI5ty9Y3rjifGKmcKo6srFzom+mwlygEHU3deUVlW1txMYeF9YDUj"
    "OpdFQ3W/UGKKjlTwznkXfPX1O7Itjx4cQXrCGnOqJN0KZIjssm8/0SCJ2s+y0h8kVt6qfgqG5YEeUVE1H6nICt6FxRdtGD4sSq2H"
    "1veUdzz7m00rzwz7/4LGdLtuWNx0dHhEVdJ8DYubJEtkM1HxgwOApW3PzhHElihgBUSWi3OvUzUzkkQMF5bgykWEPXtsRElgEDH1"
    "BT8aHPcg1ojAfizb0mJTbW1+PkzKqnoxIUuOaM0NHNTNHuPe1Y87O67bGJFHy0GSR6SydmWvf76+ec03lar7qAuHVVmAOCFdo8ia"
    "NIC3Vg4ie4U1XohK1clkMsCy7IuXAvhSkJhxkunZLc5b1U8hFTWcFXxPrysXfwkpthvBeru3+ItNK/c3j60q5wFW8JlpbAVfSfMB"
    "UYPl/mm+034i8dm9O16jXHgBibtYHJ+lY7F5HMQhthyl+Xr32agqMkrzjWUhJs5ZPWO2Mj2773jo0pfc6wstJlddzb7g1pNAWOlM"
    "cRR1xSQuBIl8DkgznjyBgUMgkM7NhFRK2c7E18gUPgBWdSOrrIIjHf/zhuVrl3VmVj2IVNtBE6UPuoMXKm1tKtvyLpvLNJtz73jm"
    "ZaITN6lY4u2RVf1ub1U/6QRVTfOhL80HItjCPmfD0m9duXivkLQrqtlwf8ucZweKjqPII2qUNN/StmdPg+jzyMkKdL+4jAgvVzUz"
    "Ic7BlQtw5byzpbyraKQBab6xXgDrgGyhp8eF9pMQoWyrL2GfTHWl9JqPk66bISZvgGEW1Pt7Bma7ctdvAABsOsQCmUp/wF3IPl/f"
    "uGaNitV9cmSVJUKslDBaAbyhairpCesQA0Bja4fKtjQbALQs27lKCK0qlpxtevd6q/pJeimVYe4ADLSCL+XhwvILNiw9JEqtV0rd"
    "e7/NPYZ39V+xRZ3yq2m+ae8RNUKa7/y2rfUWdDYRN4vIBbDmDFU7I0YEuHIJLiwh7Nlrog5SI6f5xvRmnDhdN0OVu3fd/NCVpzyV"
    "SojKZry6mhx11eLqm1e/jEi/T2xBAKgR1ZUtWxL+3pzG1QstnGYXO+T3JlqYlBE2/D/OFK4bsWKwby8r9qdzV9zavDNzTfvBqiwf"
    "gLG/qCIHmDPv3HpWoIObdTx5QWRVv8eXqh9Z9LOCZ8WxeJTmswa21LvPhcVHpVzIWevuSir9aK5l/oDmsX37UJtbIyv4DI7KNN+S"
    "H0lNItx+uivbJiF3kXV4nYon5pAO4EwIJwLTu3dQmg96fJID4lQ8yaZn99MqmbjZl7FPtrqCE6FPsk4kI3U1UlwXhjMihO8qKKWg"
    "AHUYwlgAGA1HcCQuFhEVjZglASkoW8wAaK8cRPYK62ACQtWqfmbDvE8yq4+yDmLeqv6IvYMBHlEc6988ttvasPhbWy7mRNx6qktu"
    "fPDN814YuNiImsdW03xV37HpOx6z3FlfT7mOjiGq+Z56laLYeQ6ygorblgqpU3XdLIiz0T5UsddFViYgokNJ841Z9wrrGNtC/pMP"
    "vq2+25exT666On7F6kUO+nIxBTeiutqvdIiIa8a3CUm1qYmM9reV2KIjnbxg3vLb3rjjnqv/92BU1jFLWANK1e987k2s41/WidrF"
    "pmcPTFjyqmpiGWq/R5TWrIKkIq3hSnnYsPSsC8sbhNV6At2/oWXB5gH96AZZwVfLzadnmq/SPLapgxu6Dmwee1bb9uO1k6WkqMk5"
    "uxzOna5qZyklEpWbD0rzEREDh57mG+Pbszo5Q4WFffduuPykO9KX+zL2yVZX1tGnOIjHxBTMmGN6ZMA4niNj7INORAACsckg1faz"
    "g1FZxx5h9bOqv+A7Ty8IE4nPKRVcBcBb1U9cYHb7m8cO9IgypfxulPO/kKJ0KKj2sIYe3fSWE/c3j333oDTfdLeCrzSPrY5BZCDV"
    "Zrjn/rBrBpXda60NVxCwAs6eoRI1s0hpkImq+cLevQYiRAQCiMcvzTdGhlUMZ0MrTm4EkWxpE/bje1JW3ArZFjtv+W2vI6aUmOLY"
    "1NVASTQ5iPayLAc1Z9V3bX9bFzL/MVaVdQwR1kCr+mV3brvKMH1OJ+oWWG9VPwEiqtJVAlJN8zEAmEJ36IqFLY7y9xLj56GOPbzp"
    "Lxq2DZyLAz2ipn+5eSXNN7h5bFp42aueW+SYLyCnVkjZng3mk4Pk7P1dJQo9rqpGiUAE0pgkm2pxzgW1s1XYvftfN1520kZfxj6J"
    "WJSq7POaNKlaVXETnl6Lh0jlfRpLbv8Rspt9SrB/AKxa1Z/1vWcWax37iorXXuLCIkzPnqhU3ReqHy5DVSvW9ntEKQVbzMOWS884"
    "a+4FqfaQgvsfubT+94ODepTmOzo8otIC6ugANzXhgOaxZ//HjoUKdqk4aYbZuhzCi2PJ40hE4MpFSFiSMCxbRLvX/dJ8kz5AHQcx"
    "svnufS6e/JQvY59kdZUhO3v52mWsgrdIWHCYblkhIiWmZDmoOb2hrvddncj8+1hU1tFNWP2KKpbc/kgQm33iDUTq7zme2G9V772q"
    "Dn151GcFr6I0XxBjF5bhwlKXK+V/IeLaycg9eat+/etLF/T2//SgrhIyvdN8wqnF6Evz9TWPBdD4X7uPK5riGWTMhcSqGaZ8ukrU"
    "zoiax5bhyoV+aT4iEDFNwXkpzomuq1Phvl1ffOhdC55PtR0bZezCwki1KWzbzUi1TfyqYdFmGbUxbOX8klKShtIEF7rpeTSUCM4I"
    "iP4el/wki+zGEBjZkuaoDdYDiiq++8L5KhbcrBK1Z3ur+sMRUVUreFIcJJiDOAQCW+gpulJhsyv23iuk1lOAjQ/8xYLOwe/jaOsq"
    "MdAjKkLUPPb4xXDqAjBWhGHxLK2CE7luBsSaSvPYfQ5gV20eS8CkpfnGdLsQpxI1bLr3PBHW8epjqow9lJ7Kqt9OkcCmkGmxc5ff"
    "2qxYv0HC4mjqSiCQyQt1QhhucBNYbNlSUPvKeeWnr9iBzDdHU1lHH2FVNrUjVfXHWbG5dWkSup50wN6q/mAJqmIFT9U0XzKygi90"
    "w5nSk2LD+x34Lq34vvveefyTg1XHUWMFX+0q0QHOdWDI5rGsaRmcWyFOLhDhV+raGRBxUR/DclFsuVRJ8wkT8VRJ842ZsUhpduQ+"
    "sektJ+WPpTJ2Ij6v4cK185woTdZNXAqUKoehpERd2L0BuYwZUV2xbQXFAZRlxHFERMQBTZaPpogFxGL4aySCKws593fzL77pju3Z"
    "zYWRVNZRRVhVq/osMlh254tvI6W+rBI1L/dW9WNP/PSl+ZRSOkgoCmKR71FY7nSF7ofFSTvY3SOMxx5sObEw+PkPaB47ra3g+6X5"
    "BnWVOOvfnp9LMVqiIBeCeTlETlexmpqqR9TAar7Bab7ppepFxOqaGcr07F2/8fKT/6O6H3yszAjWsW8BgCIC9ASuc8WCgjrYovk+"
    "mvAAGoboZl5RV/OWr3kj6eTyyM13uMW3CEhDxOwFSu+DlW5hxUROJn7MOCJiEesUEa+Bip0GGw7d35DAYkOrYrWnmrK8H7hxNRrT"
    "ejjCPjoCeFoYrZFV/Xn/9seTXU3dFziIXQZrK6XqpKOY4TF0mq/iERUkmGNxiBPYfE/B2t7foJTPORW0l+Ae+eW7T+w6JtJ8zc0G"
    "mf1pvtN+8ni8YU/da4TRSKyaIPYsChLzORaHVMrNTb67f1cJnuppvjE/FCayYdlAqRsrb/0YW8KFlQBPMpHzEKzhyt27OFa8DpmM"
    "QzrNQ6qrdJopR619pDS8crGs4tqE4de72q/7r8l6fvWN6z7LrL8ttjz8PhsROVsWBm6cc8nqb+366XXdQCsN9cynOWH1K1XPAEu/"
    "v/WvRQUZFU822J49DuRL1YdL8xFEkY6Tilc9orrhTPlxZ80DAvycLO5/8D0Lnxm4LhDuq347Cjyi9neVGKp57PbTAJxLzjbLPrkA"
    "gXqZTtRWmscW+zWPBUfDbGK6Skyy3nbBzONUuG/XNzdcdvIvjs0y9r5VB03gnzCsYtqY3k9u//mNnVUlNZS6alix9u2kk2eLKdgR"
    "9q4ciJUz+V3MbjVSbQqd9YSGriObF+ysp66uju/XN8z7G9bxxWJKw10zw4aWY7UnqlLP1QB9MVJZBxZiTdtgXp08uQzMuf/+1BkS"
    "q7lJJWoucqU8jLeq74s5leZdDlL1iEoqUgFcWISEpe0237PRObmbOLxvH7/ksS0tVB68IDigeew0jTxIC/VvHtufoM5v21pvjT3b"
    "MV/IwAUQ92qVrE0QcdVPa4TmsUfn4oZjcTL57l1Wx9MQoUW+jH0inrOlIKFN2Hvfjo6d/1wpOnAHjN1FmwWNaQ2HNHjUtJ5jndA2"
    "7FnXtf7D25FqU8hNQvYj1aaQy5SlYc0/AHznKLOTnSkJwB+ZceHaf+q++9pdABgYWDGpp+EL7itVb/zWU4lyTeITwvxxFUskTM9e"
    "S3SMW9VX03xEQhhkBV/o7pVCzy9BnGPmDkdm04Z3nbxr5DQfjqY0n+y3gn+hJjFLne5Ymghosk7O5GTdXB3EKuXmB3hEHemuEpM9"
    "jJxO1Kry3h2fe/jyl7zYmG7Xmemc8p2qC0piEmdCKLkuCs4phcEFB41phUzGzG1adykFyddWDgmPoK6UcmF+h3bxtYAQspO0l5xt"
    "sUCad8jO/6g39Cjr+BnDq6zICZR1TUPC5K/rBqXRmFZVC5NpSVj9S9WX3fH8hWWtv6ITdWeY/D6YfLclPgar/wY1j6Ugtt8Kvnev"
    "OFP+rTPmfoK724g88MilC58bNs13FHhEDSo3l/4qatkPuv4EYs4VYy8C5DzRfLKO1/Q1j7WlXmeLvVGaj47ONN9YyUolatn07Nky"
    "e/bJt6bTwplWWGSOqrucCg/acaxG2VL313bkrn90mJJuQg4Ol6yOq6J8EmIkOgkx/MsjHWcxPWu25VbuQGr2IbgJj2fQXkzIthha"
    "vvazAP/nKD+txBYFwKr6xnVf78pds32wypoehNXPqv6sf3t+blCjP0OkroZS6OuqfsyUqosIKs1jRfp5RGm4UhHWlLe6/L6HIXSX"
    "iLvH7N322wFW8BXfr6MjzVdpHosOblh8YPPYJd95ekEsCM4B5EJhdT6cWaQTdTHEETWPLZckDEM7oHns0ZzmGyOISIiZIfLxn76J"
    "SjPaROFoKmNn6YHAjVy0MOF86UgFbMP80y6szSCdZmRSBz7jxrRCLmMaCmuvoFjNq0ZTV8SaXZjfXiomb51UdTVIZXU27/jv+nvm"
    "bWSdPEdsIQQoGDIxKM6wrp1tw+4bALoRqTZGdhoprP5W9ee2bXsXWH1RxWtOMT17RELIMZL+izyiiISItQrifVbwptDd6/Ldv6BA"
    "r7cWObu3MIIVfGRZMa27SlRV1OYOqhTb9KX5Gtu21xmYM5yoZoE0krNnqkTtLNJBxcSwiLDPI6qyD4VjJ803xuWQ1bUzlenZ878b"
    "Ljv5x0dVGXvD4spZJ/pfAa6vFFRM1lxwIBUjCj+684H3d+PENlWxhhmkrjL2tEtWx/cW8TdwJqw4F8gwL89Cx+OQ3tX7NnxgF1Kz"
    "Jldd9QWgLYRM1lLjbR8WMvcRxwNxZQcMRaYiYvMhk3r/3HPXfm1ntmUrkO5TWVP4eL0wAAGRnPndZ14aiye/yEE85UwZrlwyR3X1"
    "36DmsRTEiWMJEFHFlI83g3A/ObnbhHbjQ1ec9PxAgurfPBYyoSW5R5KgWqM0X9/32kQtU7teJbZ0HqxcRETLWAcncrwG4gxcqQBn"
    "ra0efo6c5XzXyJEeNoiFlDZi7JIH373gMYjwUaWu0mlGJuMaGtd+CSr4GKnYkVfU4kBBDWxhx4+6Oq5767DdHSrnkRqa1n5a1dRn"
    "XLkHGLa/rYA4gCvv21Fy4cv35j5cWbROkbnf99y/9jZRyZuZ6KVgPTQFiQUHM2AKXXd0dVx7OVJZrj4fmooBqrG1Q1XO9NDSH2y/"
    "hkEZFUvOCXv3uCh9S3y0BYr9HlFRaz6OJUBKV4Ju+Jw49xARr2dFufvl+N+h/6p3UJpvQFCfhmm+dBrUgQ6OTBkHBsulbTtOJFc8"
    "F1AriOh8gfyJrqnTIuhrHisg26+azxPUmOOos8HMOarcvWvtxktPuu7oLWMXAkgaVtxyukiwhMTNhLgjN06IBToG43p+sGv9DVuB"
    "NA2uhutTWIA0NK+9DCpWTyYUETtk7CMiJyqprJR/uXP9Ne3Ve5xiq4VIKS29OTkvkTib2Z4Eq+oEVhNED3g+zICzxZO64/+yadPK"
    "sP8DmTLoP0HO/d7WMxGor3CittEVeuBMeLSVqjsB+jyiOJYA6xjEGthi7z4Q/YKI77KgXKHoHv31lQObx6baRAFAZAWfmd4r4HSa"
    "G9EUlZsPCpBL2nbNirvS6x2jmYFGZ+3rdc2Muv1dJUoQcdXVlyeowxiPpAM4E+7UTIvvSy3YgdZWmvZja7TgeXRixAaykxvkh+jg"
    "cZA3NmXSPlWr+lkNc/+WWN/AOhY3+W5LdBQEooFpPs2xODhIAABMvrtMzI85yL3OuvZ4LHjo3gM8ovqXmx9Fab5Mk+1/L4vaJHYc"
    "Ohc5mPPh5CICn8NB7HiOJfs8opw1NurOETWPhd+EGh91NWO2Mt17rn3wsoW3VtucHdU3nU4zOiaxyCbXasc0j1NtCp2bxzbGG7bI"
    "4RDCEVO4qSyPek8Ni2VwqnTSJ3p/VXXOd597EwfxL+ua2sWmZy9EnJ2+1X+DreAD5lgCxAq22Atx5mlxtIFZ1oPkngdaFj4+YFXU"
    "l+brkmwqNb3TfNXmsa0d3IQml8kMTPOdc8e2UwjuXCJaAabzIfIKXTOTqs1jJSyLADbqbC5eRY3/SLU6UatMsefR+PELz27qgMtk"
    "Rtjc9/CYJExe4UI/q/ol33l6QRBPfF7p4L3AdLaqH8IKPoixMyFsoXePOPsIQHdZoRyz/dWGS08eqXnstPeI6t9Voto8Ngdgaduz"
    "c5jiZwroQnL2fHHudap2RnJ/V4nS/uaxlTTfdG0eOx0GLSktzhlnQrp2QzOZhrY2BRwj9iEe0wqTMfupMd1eLarAuW3b3iugz+tk"
    "3QKz36p+ehRVDPCIguYgAY4lICKwhZ4SgM0ibr2A2uF408bLjt8+WF326yoxvVe0lTRfdREygIi/9VSiWFu3mMLSCmKsANESjiXr"
    "OYj1S/PZ/l0lfJrvyA1hE8yYo8N9O7644bKT//aYSAV6eMIaC6IzHVFO8pw7nnqVUjVf5njyzyuHOKd+UYVUD+3CEYFJVdN8OvKI"
    "cvaPDHlAgHbi+AMPtAxlBd+hGrqOojRfRwfnOqI2Tv2/vbTt2dMg+jwCrQCwjAgvV8kZleaxBYgNnQicT/NNZj7AWV07S9n8vg3l"
    "fS8uf+nsJS7bEu2z+qfjcewSVv9S9VSbOjfV+FEh+pSKJ2ZUreoxZe0/9qf5WClFQQJc8YhypeIOYt4oIvdCZP1e3vWrLS2vLg9Q"
    "F+3tuqHraCg3H9Q8dpCKOr9ta73hYCk7u1ycaRLB6UHdrBgE0bMKSxCB8eXmU2W94RzHEgwnnVIyZz/4nhOeQVp48MLDw+OYIqz+"
    "RRXL7th+LgL6io7XLjOFfRBjp17/v8EeUbEEOIhDxMEWe3oB3gxnc4C9u2zVpk2Xn7hj8P32bx47zaPa8Gm+tu11BSevJrGNTHQh"
    "iF6v4sm5pDScidJ84mxUbk6go+/s3LSWVkIqEChtbL7who1XnNRxbFqHeEw3TFzRRTrNqcWLK1b1j8yKzznpU2D+MCut+qzqpwJZ"
    "9feIIjAFMVZBQhFXPKLKxcdtWLqfmddb0P0PtRz/1MD7FG5s6uCmpqajpHls1SOqY5BHlNCy7259pQR8HhwuDCHLtKJTVGJWX/NY"
    "U+iptFshIpJjqL/j9GIrKA0KYmx6u6/ceMVLOhrT7TrbQn7fyuPYVFgDDgDf8eJboenLKln3CtOzR0ScEDFP9qTtn+bjWAKkYxVj"
    "vtKLYH6YCO0Qag/qGx7LNQ+czEdPmq/SPLapgxu6uqS6v1jFud/rOkFi9mxx0kTWNgtocVA7UwGoVvNVys3h03zTYj0ijpSCChJs"
    "8t0f2HD5yd/0RRYexy5hpYWBViCTcUv+7Y8nx2rqPs86djmchS0VJrOoYn/zWPRL8zkLW+jtEchvALnHCa2POfPwfZe/ZPdgAgaA"
    "7GbItE/zpdOcWtxKwIFpviVtf5ylkXgNW2oGywoIvU4lamaR0pFHVFiEuEpXiYicfJpv+pCVZRUoUgqmmH/fxstP/pYnK49jlLCq"
    "VvXR4F/WtvWDRPqzKlHTYHr2RAH+SJaqD0jzEVP10C4xTH4fIPI4SO4BqbsZ7oH7W058djDxNjbt94ia/l0lstxZn6JcEwY2jxWh"
    "Zd9/brFjfQETN8PJMlZ6IceTEGvhygU4axxADiS+eez0JSuj4kktIj1hKX/lw5ed/F+erDyOScLqX6p+9reffK2KJ7+iknUXuVIe"
    "LiwfKVUVWcELOcAxV8vNdQBXKkBM+LwQHhbr1jty99q927cc4BHVAdXQhaOjeaxE5ebRvtpARbjs37e+BEl1loRmBQQXEGGxrp1F"
    "IhKVm/d1lfBpvqOBqQSwQd0sbUvFp8qFwrseueLkhxvbRQ9Oc3t4HN2E1a//3yWrH4/vXTDzRhA+qWLJhMl32yMQ7IZN85lCTzeJ"
    "/EpIcgB1hFzz8KaWOQM8ohrT7RoA+vXm28994/dojwzxpYVTizFMmm/XLG17X0fEK4ipGQ5nqGRtpXlsOSIpkdHTfDLGW/H8NkW4"
    "yjkiZl13HEy+53/z+T0f+NV7X/nCYSorAtKE1BYCUhixF1zVeyq7WYBW8We7PCaNsPoXVZx957ZmrfgrKlH3epPfC3ET1P9vCCt4"
    "jiUjj6iePSLAb5lVBxSvN4XyAR5Rjel23YV6Xrx4sT3CKoqQTlNfk82GxYJFmwWZzKF3tuizggflmjGggWZjul2Hi1/+aoFuJEiT"
    "iJzNOnYCx5MQE/ZL87Eba/NYYgIphWh9MKI7N8RMkSJJOYhHO5kkO94LgYqq0ola7WxoxZrMg+864bODsyFjVet9TUqHaER6sMof"
    "ja0q+j2bZZI6pUdzcSzIHHGSPYhrO4TYkU5Pr/3mYZ7/wc3Uyko+20L2/O8+M9vG4p8h4mtJBbDFXkOAGj9VNah5rNLM8SSIVZTm"
    "c+ELAr5fnFuvFN13ghz/u+xgj6iODtXQ1TRaqXm0alxygjqtvsi9XQll6kK2Scu24IZ8yTPijm2pbojvdSNvQ6vKNfb4nl3FLVsy"
    "5VEHUQcYObgRJ/CAcvMDz3ed3bbtVAV1Dmz5QgFdwMyvVDUz0Nc81oRORA6pqwQxwRRKMHt7AaYRpwkpRmzOzKmxElMMYq64oA91"
    "u1L5FsGFJrqvI81bRGCtRrjGg1sIiHOWdKB0zQzYYu9D5bD8kUcuXfgARAitoDEWDBFSbdHYPoCghOaeu24Bxd0CUNBA1swnollC"
    "lCRAO4FjoASSbhHsBORFca4z6E2+sG3TyvyQBDba2PfwOBTCamxv17nmalHF9neS4i+pWPKlpnePiMh4lapHaT4AAz2iLGyxd4/A"
    "/RKCdqWC9UUEvxmc5jvQIyoyMVvQ+JV5lhPrIJgNcjEBJQmIiyBOhECkzy6dATAEDBKOeq/K0M+NiIf8npAlghORMogKgOyF0HaA"
    "tgvkaSL6HRGeiOWLf3h+ww2FAeS1ZTH1BYkR0nxL256dI0YtYZKLwNwI8KtVIlm73yOqOD5dJURAQYCtP74XPY8/B44HkYvXMCNJ"
    "rMOJb2tE7SkL4Mrh5CgXEZBW2PXIb1HcthOk1TCLUYJYh2BmLeadd3p0rc4dmWsWAWmN4vad2PXwFpBSwy+YHUAxhfoLXgcVCyAH"
    "KjIREUdEStfMhC3n90Loy6Vdz960aeWZ4dhTgFUCyfT97IIl6Rozs+EMCM4npjMh9jUQLACrWcRBP3FOgwyYJCJhsXA2LBGhS4An"
    "IPIohB4wQfDQ7rtWPttv4qpK1mFiiKvidju3cc2faB18Qax1MkzsI4IjFdcShus6c1ffdbj+TWO9tvrGdeezin9MpGREhk7LE0SI"
    "A+VsobUr95FfVj874jsFyYwL185NWFoD4hqIm9KpWSI41kntwsK3Ojuu/e/Bz1+PYXIxAMkRmbPbnj5VqdovKBW8S2yIsGePISJN"
    "hx4QB3hEURBnHUtAAJjefcaVio9JWL7fWrcewvdvvOyEQc1j29R+1THUod1WAiBSTtQiSe+iIAk40ze9qDL5qTrJDiet1C9wU9Ta"
    "ofI/uNLqgaO/IA5ii1JKxJ+rb7p1E7H6Gcj9rDNz9ZOVERwZy2XIZSu/8pLVj8d3nlD3Gi3cSECTc/ZsnUg2cCwOqZSbm3x3/+ax"
    "TAR9WJJBBBwL0PvMi+j94wvgRCx6HsN10GKCGItdm36HmpOPn/RRX3yhC/t+/2xEssO+R4IYAxcazL/4bEh45OYyMcH0FtH9u2dA"
    "gR72GsUJVCKGeee+NiKI6s9FG7iWCFrXzlSuVHC22PNdVww/s+HKk5/YnwIclawiRZUlixwMGtO6nhtWgPBOI3IxMZ/CHIdAAGcg"
    "YgFxIqYUsVIltS6DMgKV90DEFCdSCytfTSLuI4EtddevuG0jQP8dFnr+Z0+25ZkBaavxJq4ti6myCG4gXfM2cAgabm6IBQW1oPKO"
    "nwG4C52LJnYFU7k2AKdSrOatMIJhd1REQDoOKRW/AeCX/T47DKL4p4u2lmL6MgqSgFhM6b7SleePMP8wgP8e/Pz1yGkocJbIAqCl"
    "d2y7llm3ciwx1/TsdRQFZn0IDCUAOYIw6YBVLKGqHlFw9hlT7N4gVn5ODvc/ePkJvxu8GmlsauJq89jKtY0K1uScc3slLNQBTiLh"
    "sZ9Thl+dHM62BEllFgsgkOqemQiBSLHSJ4ODkwG83ZlCvr75tp+Ttbd23rPq58SEs7/57MupRi0jsSv2EJ8fQL1MJWshzgHlIlw5"
    "72wp7yKqAO3fN6RxC/oigt2bfhftXY2ujcGxAIVnX0Tvky+g7uUL4UrhpO0PUaDB8dgohAVQIoY9v/oDVCKG+sbXwRXLR+yaiQkc"
    "j41KWBwP+s8gB8Cx0lon67Qt9jhbLPxA4G7e0LLgoWqmIdsCN2rXlVSbQrbFIttiZ51/2+x4zP6liL6KWZ1OrCGuDHGhOGdtREJE"
    "oOq/oGHHWv/nJyIiRiChCJFAhMBqBnPsIhBdFEskP9/QdNt/QfD1zszVG/pdl8M4Fy0RyEiYtyLGQYY9Q2gBVmCUjuR4ZXJlCfNW"
    "bMkCGK4GwEEsMyE8qPvW5CCyW8L8zCj+TWXGIiOU1wAKQ31XDz2ORWWJbBawZ37n2bNiifhNKlHTaIu9MN17DrJUXZxUQnefR5Su"
    "eESV8rsl37NJ4NpZBe0B6De5lhN6hkzzRYUSLneoqy+CApFC9LpoLB84/PkxxO+KJrOIMwIbLemJuIZ0/K3C4VvnX3zb3Qvf3lyn"
    "59a8lqATxKrSVaKIsGdPfyt4Jpqgg7si4HgMPX98HvlntoFjwUGoTcLuX/wOtaeeMPnFDP2/hl9CQSXj2PXQFqiaBOaevQgmXzpy"
    "vZhHu8bK98SJhQirRA2zjrEp9Owxpd6sCd03Hr7shEf6FNXmzWNpD1ZRVS0Wjd9KNHDvh0D4MKvak8WFEFd24soOAFd6QOr975IO"
    "fh5EKfT941+siClE85jVDNLxK2FLVzRc+I//IcZ8rivb8sv+6bJxXL0TWClIJeUx3PMmUtF2wJEcr0R90mo4iSXRVoS4Q7k26hf/"
    "pnQpr0TPf+j3cyBhpWW/VX39nL+D0jewjsXC7r2WCDwqWQ1uHhvEOfKIAmzv3tCVS78SE95nxN0VY3rovpYTugYTVH+PqKO0IefA"
    "SQwRCfMu2heLX7jt/23EvAteg7pXLLSuNxRiVNN8R6ZTCBHE2khdHUyIEgHFNPLPd6LnD89hxqtOgSuVp36pu0QqpuueR6GTccx6"
    "9ctgC0WAp05hVTDjOEVsYYrFX7AqZRnue/e/s3LgXYTTADJjyjhUUs7ZFlvftPYNoMJNpGteA1eCM3kT7d9W9nIncoBVx7LYytiH"
    "IhV/J5S8pWHFratpRz6zPXNjb58K9PAYTFgiQkTkln7v2UsoiN+sE3WLTH4PTFgevqv64OaxOmAVSypihi30wBnzpA333Q/QXeLk"
    "wY2XLvjDYIJsRAc3tTa5DCBjTfMddQRWWVWJK9mwu4CtP76Xj3/DUjVr8UthS+UjF/Mr6qr7988g/3znQaqraqqLsevR36P2ZSdO"
    "n3NZBHCgsf2uh8HJGOpethC2UB5BaQ16KKM9IiLZ/0MS5YmjtDOPcl0iQqbcvW9NfFbdDzZeesLG6l9LtYlalIJkiFxmLPeYSilk"
    "MxaL0rH6+fVfIA4+SkQQkzeAKID0kU8W7ScvCfMWRDEOam908+hP51+w5oPbsy0PoTGt+xeDeHjCQjotHJHVcx/WtbO+JqaMsGdI"
    "q/qoq0S1eSwrpWIJRTryiLLl/A7Jh4+A+W4hugcU/mbDuwZawR+Q5gNcLjNlnomM8+Hhgw0BirQCOULn3Q8jdlwdEgvqIeER2g8i"
    "ggtD7P7F7w8tcyACCjSK23ag+/FnMes1L4MtlCQqIpWxBfcDAnzlv1X3Bof7JX37hABE1EE9e6koSwhe/N8NOPHtjUieUB9du6L9"
    "eX/ql9vqlyaLGo8dkPrtq6SjQXs+KpEAx2pGfZjEiqRczj/yvlM+AUSVn43pDp1rbbIHtbirKJV5F/zDAg7mfI91ssmVe120pUyH"
    "WKAj0m+vtt+QFzqksR/FGXFhjyWVeK3EuKO+cd3Krty13/FKy2M/YYlQhsg1/tfu40qF3lYXFsWFZdtXVFFN81W7SgQJ4liCRRxM"
    "vrsoYfGXKJfuIWfvhnKPPNhy8q4R0nxuSqf5iAiHnXmTfotwJ5DKQeX96ZbR44BiuFKIHff9Ggvf0VRZlsuYgvvA9f8wAb5/cI+C"
    "FsQ56GSc921+igtbu8Dx2KFVSiI6B7X70d9jxstPBilFUWzjQbGeBgb3oQL84MA/BBlUYyNVqugoCED6EK5dBKQYLjTY+uP7sfAd"
    "jS4xv4HFOoK4qKTcOYi4yr6ScwAcAc4RORJxAjgiiv4VcSCEEDKOxABkAFhYF4LcnnDf3loQnzGWQfnSt397zpJLEzuzLa2Sy2QM"
    "DmaBVyWr87/yCg7qfkQqeKULe8xBE5XAgeCqhUMgRdFpEOpXwSjRcxIHiIt6V0Y/z2MkMAJIiylaMCc5iH+7vnHN8V3Zlpu80ppu"
    "C/ZD/vtCwzR2GJASzO/rVToGBXGOIhlliCTyiIolFBHD5rvhwvD3Epbvd5D1xqoHH3n38U8eHWk+gjgpAbYHJAqH+OYoIiYFIE4c"
    "BOBAARSVBbuSQEhGJS4nUPEAhRc60fvMi6h7xcnkSmEUlPtvgFciOBENt7JHdcusb9HbP8D3LYsjQnGlPHZt+i3GcKxu+O2tisoq"
    "de7B3i1P2tmvfyXbQgkgioJ5pdINJE4EjkBOCI4EDiQGQsZBDAgGQgYQE6kLGKr8C8CAKYTARK2lOASJgXOWA10Ou7ubKQgWVg4u"
    "HYTSEpBWYvNFbP3RA70L3nDWqtj8uc+ZUok4HpS0c0ZCsRTnUMrOitJGnDVijXGBNkljjMRjBmFoyq7WJuPW9SSMC4pOdmwrulmJ"
    "l7tNW7OETEt57tk3N+sZdevFhW601GBx316bbbnSRurlINgqnWZkWuy85be8nHX8Z8TqJVEKcKwVvlJdcClSAYMDBgRiioDYbufs"
    "HgA9BCoLRANUA5LjCDSDdEKDFCAW4sqAiBnzoo1IwYkTKQnH6r5c33QLdXV8+MuetKbDgv1w6MoFxBoCq4cnLCKJzmws3Lnsjhf+"
    "KZhZ/xFb6lVEHKX5SoVOZ8KHwOpuaHVPuKP+N5tW0oDSysZ0u25Y3OcRNdXSfGOBYZ3QzhS+aUu9f1viREIhOKSJkUSoy7FYjGw4"
    "g2AaxJZOYlJnAbSCVfw1ECGxZTdqB/tK8rX7iWdN3WkLS2KNgMlByAFwQuIIsBAYBzEEDqUS8AGYKPhXgzyFIDECGCEyLNGKX0QM"
    "gUKxzqqaeGHHht+cVd6dP4u0dpUzeCPmO4cnXCcci9HODY/tqj2x4Z0yM9atrTIgFSKwxtnASBAYsdbEYS3C0LhCjamNGdedCF28"
    "10pXba+rr1/smjrgMhk6qHY09Y2r/5PjdQulnHc42FZhIkRKOdNbmvH09352+c4HP/qn4zvU0gwI8Yxb4xM7pNOMTKssaDxhnlXu"
    "f4j1S8QWx0pWAhEHVop1QjlbhDjzmHNhjp3bYMX9nkk/Fy+V9j4f3xcil7FIpfi07vN15x5Tq7U+PrDllzlFZwKyHJBzWNckIQZi"
    "Sq6ycBpt/46jXvMFw7ruS/VNt2zv6vjwv/n04AQu2EUKgO2ZvCuAcdZqgLpHVFjZlpSDCC3M4sYXdm99iuI1y2zY+ySA9fFi+Ivc"
    "VafuGSnNd3RYFRBAkt/5wMe7AXQf6m/ZO/B/Vs+SfRepNtWwY8efAfgi6cSrxBRHJC0RcSqe5O4ntj47e1/hT5XikrXG1nEQWhjr"
    "CjWm1FC2dTvL7oV9ocxK7HMvnb3EHY5v19xlNz+qa2dATHkkSpLK8QAeaakGOAtJ1D/xz//9yt0P/80/HerzzA1BKACA1lYCWpFu"
    "BbZko6vdvDmr6ptS7refvTV2qOnMyh9hIHTBrLkXN6y49aczF5/61lmvbnB1W7ulqbXJAUCmdfBnWoHWVhltiKGxg5EjA7tWJm4x"
    "K4RUlrCoFSY393us6l4ppndsZCXiQMwU1CgxxZ3WlL7LRN/d3r79kRHbKGWz9glkLYASgF0AtgD4HwBouPC2l1qTfysTX0k6eQbE"
    "QmzZjr6YIIIIiy074vg35jau3bwz2/LIhHegOPZgSCe1K+f/RcUKHy+L1TFSkxTTZ6KrOx61tRukpvWARBYBFUv0tZWvflk+4Y7W"
    "SppvulvBjzhXRQFCWPINjU0fPIwX1kpIIzrJXu1qnW2xncCPZp1/270xCn/OOr5ETNkNH/glypI5W7/p+q/uxN7Ve0b7q5uGUQzV"
    "AJ9GK9AvwHdu7qCnAf3e1qby1y+8bRUHdWe40r7hA4mIoyDJzhSuh9ClrONLxZZkmJQWQSyCGbWfOfnPvvuDc/7ysn3ZbBZYlJIx"
    "BXga8v+Qfo2LBcggkxmQAhM0t7iG5nXjkIgndqV9hoO6N+x77Mnbn1j7pvci1aZyNILay4whrdDQNvGbBKksI9tiGxrX/D3FZ1ws"
    "Yc9YycqSjitxpiy2sNo4s2ZX7vrn+6VSot/RBFdpUDp0aiDdSn1jP9dqO++mJwF8DY3ptQ2u/l1g+hQHNa90Ji8Dc9nDKC2xllQ8"
    "xmK/vWDJ7WduW7S1WG095LlmPDOCUt7+8xt7gUHdtqYI9FBBsjHdoRoWN0lnfQdVreArvkrTLc13KK8sqnyqSx9ut2YZcqthUVts"
    "730tuxsaV18r4PtGPsRc2cgmJOYufeX8nUvT+7BlMaEt5UYP8LT/OvoF+Awyg7ZAhADYdY/+c50Sd4OYwkgHCx2pGDlTeLqrfdXa"
    "hua1O0G8LFqRD/kRFlu2HNQeX8jv+utsC30BjWk9IJ2TmeoDirQLe0MKav+yoWlNV2e25capv4+Sjshq+drXQOlPSViwwBjSoiKW"
    "glolpviQQ3j1jvbrN1XSKarPYaB63zlg+L00QmTZ0/eSo2tqBCOXMZ3Ad+ee+6UfSQwZVvGPiBjA2ZEPtBIpsSXDQd2rwrreTyOT"
    "+QRSixWy8CprnClrfBbs4xGHhwgoQ/1gLtNssi1kc83Rv9Pb0HCKYUtLGUhzZ8OCh+HKfyQOGJFtykjUxxKGCpmMw6LNEQEN9YX+"
    "Xxjbnk9jqwJIuLv416RrTxI7QgGAiIA1icPnAKDT1f2nC/ObScWHvwciihQYfWTGhWvnItdqD6ft1URo6jE8p0DCXkNB7cfqm9fc"
    "iFzGYMntwdTlq2pSU24mFcQgdki9ekBKKKhVYnu/k3TbG3e0X78pUlMSNWSOOk4cRhzIuArZERrTeucDH+/u6rjmo9YW3w1wAaxp"
    "DI1ZlYQFy0pdP7f5tldG7ZummW3GdFm0120dFE+O9NfQ8C97UtAqyLZYId4FivaVRxRZRKGEuhsjLWoPLVgTcq325PNvm02gj4ot"
    "jbTKtaRiLGH+D7Wo+3ek2hRyVxWJ8HmwohHugUWsZV1bn7DuwwAJUtkpM+6IdKWEcrRYKUps0bBKfrm+8WvvxaaVIRrb9ZQbWqk2"
    "hUzGNTSuuYh14mIJC6MXnYhY0jVaTP62zvWrrnwmlylF7zdjJiDlVlFpQmhs1zs6rvu+Dct/LkCeOBi5j1a0Lyqs4gkl9u8ACFKL"
    "vWPoMQRPWJMmd1MKIjP6TqwOM7crZym7dnNNVx/ZjRcq6qqo7SrSyeMh1mIkx2HW5Ii++EzuqiI66wlIc+e+WNaFhd+QijNkuPSM"
    "KLEFIdLXzrvgqwuQTU2BlbEIiOHEPgWBA9QoCoII4pTY0JFK/vO85be8Cblm07enM1WwaLMAgGO6oXLuTUZPA9YoZ/I/7Gy/9hqk"
    "UgpI08RX4ZEg12yw5PZg573XrXe2eLkQEcCjKTnlTEGEODX/gjWnRtfpVZYnLI8JWgGnFNJpnn1B0wkgPlVcGLmrDD2pLVgLQL9G"
    "7qpiZL8wTiteidTV/ItvawDR9SMUTvSpKxf2Pl7rur4XKbNmi0YwNq0MidwXwCO5OxJBnCWdPI44uCFSWZO9MibLOgmIfFdAqzio"
    "YWC0/RCiKL3miIPk9+c0rl6KXGYKkVbULHbO+asXEfFFYooy4tEJgYMKWEzx2VKh9FcACNlFR9YNeNPKEEtuD3bmPvJDZ0tfIp1U"
    "0cnsEXMOloNkUpRcES28fBzzhOUx3it6QmNao3MRIZNxgTKrWCdq4JwdVmGJEMBETn4IAOgYx/fVkmWARMrmo6Rr54xFXUH4C8/k"
    "MsVKSk+Qy1ggzSfti//AhYVfkx5JZSFSWYpXLrjolpORTbnJtu0WEQjLrK6Oa26z5X3/SEGtrhxSHomzGM4KQeqUjv1wbvPXXolc"
    "xiDVpiZ9iFUCt9b8TqWSukLANOKqhTQJuY/t23DDLjSm1aS4/276oEGqTR2XQKsLe39PKjbavi7BGQDqHUCao3HoMZ6rOfRs2+/O"
    "eeS+RoX27+aAVSdXVswajenD+EVNADqAhi2CbNZFKRAYAGhYcetfA3xD5RyWGnn127stDGJZADRuEzOdZmRSbk7j6oVg/SGxBak0"
    "Px3qOiypOIsp/K4rae+INuH7zngJGqE25VaG85rWfB7Ed47QAIPgnKWgts6G9hMAXY0tbZO/YHIMIM1dHdd9qL5p7RwVq2txo5WA"
    "E7HY0LKOzyfEf1zfuO6CrmzLi32d0CcLuVYLZEiAN0ZGi0LDZ5vFkk4oZwoPdXVc+wOkdzAyk1X5SILOND2Ry5Qamtd+Bqy+i+hg"
    "PYZf/JQFzIuPXzHnT15cjy3RuTlyPoCNw7sABH++wGLTtChrP7YXFiDJoyNTbf9zGBhYHTH3orUnsFHLiPB+Yn2J2FCiNnTDZQNh"
    "ieOBM+End7ev3Duup/u3LCaAHNOavyGdmDlyqx4BWJFY+SJ+en0JqQUDS4krKmux7PyP34b0K9Lx08WULYayQiFiMUUnpN9b37ju"
    "q13Z1B/H3fPoYN84iQAZ19iY1i8k3JV7y/l5rGtWjNq+iEiJKVoKak6DKf9oztmrL9r10PXdk0da0ZmkOY2rFwL0mijVPEonFWKA"
    "8I8ACTrSCqNVq04o2WYsIBSb99X/Ku3A06Rip8CNWLHqSMe1M+Y8AFvQ2MrIwRPWYa/XRaMxrfFAXRyXrD5yC5hndwm2ZMqesMYO"
    "FhcCoHPnN9+6SiC60gLpYJfsSoAAQB0RzYGgHiQvhaWXkQ6Oi2zZi5XDwjRM/g2Gg5mBKe/51x25678VnepvGVd1Nf/iNac6o/5K"
    "TEEwXPOwqroK87/tSrg7K+d73AE/1QiVy2VMfeNtnyPithFVlljHQU3ShvlPAnQVtqSmRFo61wXGlutLs87/wjvjAa0nlTxDTN6C"
    "RvB/I1YSFgwFtWfpWtfW2Jj+81wTHDKTcOgylWVkYRXwatax2lEOpAtYKTH5bqLET6IHMOnBXpDKquezNxQamtb8D6lg1Yg9FomE"
    "QHDAmQD+yYevwxcvYgtgyJUNPO+NYkghnPgxTICAFUvD3Odq6tNveCaXKWKEQ8uesAYQVgnMQTM4aKbDeAUE9HUOj5yPLMSZiKj2"
    "l/4NIWVgAdYc1Aa21PPdHdj1gXFXIBV15cI1f8dBsiZSEhhZXTn6QqSu2hSyQwS2XMYAae7C9v+aF877pdLx146mspj1ZfOb131l"
    "e/baLVOiN1w9HFIptTf7t7tnX/CVt2jCvawSLxFbGrnnI5EW02soqHvDlrJ8C5lVV0yUxfuIqHRTIVavItYQKo+gTuBIxZTYwi86"
    "139geyV1OFXUCYHoLji7apSUJkVpT3p5NAZb7Tif+TgG5ZUArGYRqVl0cNath7VOIQ7gXBi3pZmj/kFPWIMFgDMOzrjDfw37J1bk"
    "p9FnsTBkegPEzDqhnS0XbLk705Vb9aWoGo8wboEvUmpubuOaPwEHV4yqrnSMXZjf0lU///vV7gnD/+7FhGyLocZ1nwM4O7LKco50"
    "IubKvZ8G8C4gOzVefzZrkWpTu7MtzzUsX/tm0dQBDubAhaM0KiYtYY/hWN176pvWdnVlWz6KxnaN3JHvrymCk8dkJkkMB3oMANDU"
    "qnDYKfDxeP6bBYBYmN8rWwzBHAzbbZ+IIA4ELIzSsOQwRdsJTS/SciKjH+Aez5Dr4MAAFcakKvwbGvKZ6HH7IlKV9B8NH+4SDFDJ"
    "mfKdMOacro4KWWEcyarfkGSmv2cVj0OcG34ZJQBpItDnkW0pj1qGXjkP04WuH4opPEo6riBihwmYSkzRkQr+Yt6Kta+vEsXUIK0W"
    "i8a07rxn1W+cK78DQCk6GD1ayoy0hL2Gg9qP1Deu+UR0RusIHixuWByNE5J6qVgKjRornDw9taZedMZQ4rxNBLuiNcJww19IxAGE"
    "GXPPrakdtEz0OKwsHfiIfUn0r4yRizxhTar+BgRUFlu+VZXVKzrbP3Rp5z2rfnPaJavjGO8ZmGpTyGZdw4pbTyfS7xJTGLFCsXLu"
    "anNnd9DW155n1L+xmJDLGCH+h1GHljghFVPkpFKKmZ06r6ZytmpHx/U5kfJlIEUVk8zRWwfZguEg+YV5zavfd2QPFmercbxmrMNG"
    "GPumXqwEdhV25QEUK9XOMsosigWcSPh4cuyoCY/JmZwVG0XRArzJxMyaeStue/+sxq8d98RPry9FE3U8zyllK1Tk0qRieuS+bSJg"
    "RUT0eWxaGY65lVJVZc2r/29nC5tIJ0ZRWQVHHHtzffOt504pldVHWu26q/26/xRXvJp0XAFsRyGtajcMy5z4p7nL177liB8sprFv"
    "PIibovO/54SD2Dwh6VEJL608YXkcqXfArE5lnXirUvF/iqnkpvoLb706ejcZNy5BPFJXds6Kr59NHLxttPNfpOLswsJjnfti2TGr"
    "q/4qK9tiyeJzlRXyCK5aIsSaILYVQF9boalDWpFC6mq//usSFtKkkxqg0bthwBGJJdb6jvrzv3rekSGtVFVhFca6Wc7A7CmWdQAA"
    "zAx6ZoCoJtq+Gj61SUQgkrA2tq/gw4gnrGMUIhCx4/eFyA5+hDyNuFAkzFsJ85YJL2WVvLVhxW131zevfhmyLeOgPKJ0kXKmFUrz"
    "qOqKmETU5w5KXQ1SWZ3z7/mRM/lHou4XI6gsW3Ss4hfPbV6zAplxIujxVVrRnlbHqs+I6b0t6oYxaoECi7PCRDUUS/zw+OVfe9WE"
    "d8OoVAkK3E4CYUwOC4yXTalnnW4lAEgm4wsINCdqgzXcFitJ5JBLu7b//GP5qrz0mGrxb5QvRP9Wep55wjr4lIoiCpKKdFJRcBhf"
    "OqlIJxTpGBNrjqqa4KJgNzitRBQVZ5ASZ5yEvYZUvAmI3T93+S1nIdtiD7mNUUVdzWtet5xV7BIJR1FXOs7OFH69A9t/MGpl4Igq"
    "K2sJ/A/7VcfwKgvEYKFWQGjKqSxAkGu1SLWpzvZV14gpZDmoGVMLJ7GhI9bzrIr/eM7Sm0+M3qNM6Jwj8HMjPe7KHRHEAILTMZ4d"
    "VA4XUesxgrhX9yvaGbauHaxAkGf6pc/Hb+wQHZmFU99CQ/RUGOrEwfjEvzHHyURAQVIJaNZYrtCXtQ9QFopEXBfCwqNCUIfVaFbA"
    "RBKDoFaABhDNYR1LEml2tgQ4M5yrLwPEYvKGVXw+KP7/5i2/5bwdmQ//4ZC6KESlwiCRVpAioOyGX4mKgDQLFb+IDjikoLEoffDl"
    "zlsANLbrzu7Hf9JQV9hEQXKJmOLQ90ukxJQc68QF85pvfeOOTOYnU+Jc1sCLFGTFAWmeGQuv2FuSetY1TWPohsFiSpZ18qWUxI/m"
    "XLK6eVeG9lW8tMb3/ipVggT5vTgTtRij4VlNbAgiPr3hwq+e2nn3R5+c9LZS++9BLPgNGgwZSSUSCYEhQFSa34hRO12Q1haummak"
    "YX9v5RnVHNlcFydHXWhQZYqKshMT/zQ5a54lZ7cIXHCE3JyFyTCAbYkdetTx5wlrgLqIKQkL93d2rHr7eP7q+RffVFvOB3OVMq9W"
    "KrgYoBYKak6IvIqGU7mkxZYM62S9E/MdLLn9AmzaenADtRL465vWvoF1vHnUvSudUC7s3bCj47o7KpnE8mHffNO6j0PkZyOna6RC"
    "qq4Vqbb/q5LsFJPegnSanshcX5p1/m3viKGYY5V8jZiCHXE1TqTEFgzp2terkvwAS27/s8gcb5xRfWaKf+NsqURE8cpzpaFDnxjS"
    "NXFn5C8A3DSWgD/BE5CQhZvV+LXjiOTPnC1h2P6W0ZBhEQsLur8/YQ+JquWKs2UWHlnxI9obs3Dzj/B6uYGIRiZpCEEcRExpAsa3"
    "JRXXcPm2zvZrbpyMEdDVPxp5whrzyNGV9Bsjc7gTuFUAku0/v7EXQC+AZwH85PjzV3/eQT5NKnZt1H5GhictUzCs685pmNH9vk5k"
    "bj8oe/bs5kqqRFr7lmfDE4dU/vP/5i1f/TonFLDWh7WSE2fJEe9hW/ojqdjLh221U+nLx0HNWfVd29/Whcx/TD2VBSCTcUgL783Q"
    "7uOXrXuzS5TvIRU/edRuGIi6Yaig7uL6Gfl/7erIXA6kGULjuOmScQCoc868Zxq6On9HOnitmLIMWzUoYLgQJLISS29eh6Z9JeQm"
    "8eBtY6tCLmMCWvuXStc2uLB3hIWACFizmMLumJQjwsqmhp+r1QYYxnYLU4mY4sMeSEYlSw06ZVQiHEdlLOCXjHJoQqLOl9aRqhxH"
    "mID0uYgLkE4zstDYcoQOk6er7yjjFdYhraQzGYd0GoefIslUV7MAWgmpxYTOzfRi7vouAKvqG9eWOJa8IdpXGq6NDjFcKAK6Hktu"
    "/xfkVhqM5UR/JeA3NK17K+n4UjGlUZQAlNgiiPD3xCrN4xG7uOISQWSiPo0j7ZkSQZwI8Gksuf1HyG6empYRGXJItakXsy3PNJx/"
    "y5tdjHLMwXHizAhqOSItF/YaFau9bF7zmt072q+7VtQaGtdCgca0QrbFoGndz4n0a0dsz0RgsWVLQe3L6kWu7cpkbsKSDwbY9I3w"
    "yD/UNCMHN/NPb57DIX8icr4e8VlaUjElzty1LfexHVEHl5GqN1sFyKDGFXYUVF03oOJR3QwNQ+QWELw6aos2wYumKtGSOx0jdtgX"
    "gBQgNu9CF4mRTHRf4xv+OIp/jWl3xFLEB3ELvujiSCQbQZEpXrbFIpcxSAsjneYa1P29C4vPktLD+/9Q1OOQWL9q/qzS6wAIUmNo"
    "GJvdLFEptWutEM8YIiNhf7NXGaevKFiP4U+zmJJTQc3p9XXFdwMZN+XcfPuebaUbxn0f/rUz5XdI1A0DYzhYrF3Ya3Qw85r5zWtX"
    "CakdGE+RVd3Hsi7rbKliGTNi7ovFFh2p4NNzln/tVdj0jXASqjQp8vHKuHg5tpp04nhxxo1cqAOGWALo9srqbPRxDeDZ+/52D4S2"
    "EalKleGQP0riygDRK+Z2zH0FAJo437bIkHXOiq+fCMGrow77w24RSOW6t+/I1+7of1/HEjxhTdYqfctieiZ3VRGQu6ACYERrB7Kk"
    "4nCWzwYAdC6iUdUVMm6emvdOCmrOiNTVWN+1jCdbVb7GqtSI4IwQ8SdPu2R1vLKnMjVnZeVg8c57rm8XG15BxBzZu49GWqJcmHcC"
    "Ws3WfUxsyQI0PvOwcqRg+707HxFnNpJKYARDzSjiOQtiVadU7PuzL/rirPE5RnEQZLXkdo1cxsxrWns9B8n3SJgfORMgYknH2dni"
    "xs6OrvYxnhOUyj0JQX4HVlEPu+HZzXBQEzDzmwHIuBqnDlDE0e9lF17CQU0tnB3JzFXAGgAex6aVYYVEj7kD056wJgud9VWXzRci"
    "Lhl97AnklLEFrs2yKNUWI4dPQazg4JfxR9xJtF+aylFQ88p9JfxlRWWpKfsOqweLc6uyzhavJZ2odMMYhZQj10hiFWsBoMY17lTU"
    "ihB9DcQ06u/uq2SMv0bbGT+cvaRCWhOubtOMVBtj08pwXtOav1IqdsuYFlZRiyyQ8Cejg/VjPCdYKR8H08ZRh6SAYUOQ4P1ItcXQ"
    "BDfSAebDU8RCBFo54pmzvvsmCOFhAJgwEvWE5TE0OiIKAgcHwSOj90yrqKuuHdsv56Bm0ci+SFMRRHChiKhPzL/4ptpIZcnUzX1U"
    "Wzh1XH+rM4XPRN0wxrRZLZUilPG+HgsR2uG6/tOZ/KYRmxDvf+RKwoJlnWjSM2f9vL7x5tOi1HWax19tCUVkGKXI5zXd9ndKJb4Z"
    "pQEdj7y4EkNBjXZh4fudHdfefVA+cZV0qRPuEFtyI6ZL+/b3kq+Y17ntamQyDku+Mb4E3tiukW2x8xrXvpuD5FmVeapGJFEXgq3t"
    "6H8/nrA8jmRwFoY7IzrwPboSIcJoG+KE7GZZuPTmpAg+CWcORV1N8iMBiw0dBzWn2jDx/khltaopfc25Zhu1cLo27cKef4y6YYgZ"
    "9U4nZv4JWloYuYxx1t3Yb/tSRietvGWlzwInN9Q333olMpV9VwhFxHWoC4fK51Nt0dnGXMbMu3DtK+qbb/uRCuKfi4jb0SgHzB2p"
    "hBZTfF4lsSpKBS4ae9CO/Mloh9v+K3Hmd8RxwkhpeAKLLTlWsc8cd/4tp2PTyrByfm4cyCqtkWs2s8/74snE+muICnZGgiOl2dny"
    "s9yb2Njvfo45+CrBI440YxE0cpnyvObVS0BBs5iijGpnDoBFOkeZCAq5jCklVr9PBbUvkxFLg6e6yioLg26cfdEX/3X3XR/fB7TS"
    "ETrIeGgkkctYpNpUV7blQw1N6xooVvcOCXvMmApOxhuVRsI7sy3t9U1r/pFjM/56TNdSOV5ArOYSx/+tYcXXLyXjvrz9HmpHtroX"
    "lubq3gsatsh+0mit/ktIIzIK7dxMaFgsyJKtfn7uuWtP4LhayYIPQ8dm7t+zGuWcHmuIs13izLtf/On1XUjvOlhjU6keCaGm1d8H"
    "6wzcCFWUIIJzQiqYEQSxH9Y3r764q33lH9GY1miCOzRT1cqzy2XM/GU3NUis5oekgvmV85EjzX8HjjGc+a9tm1bmD+poy8GP5KjI"
    "ZAt44opNxoBMqww13z1hDbUarJ7DSqcP/uNbttCAqqVq7rxhsUSr1YzDFpRnN97yaqbgTiKKi8PIaTuJDgw65t+PeN052Lnn1swA"
    "+ONw5dHVlYgdU8+5iVP3I5Rch5ZitSfqEj4E0BejSToFTAZHmurZzQIIJeVfL8+X8//HQc3yUbthTBhppRxSKcV7Sh9zoTqPVaJy"
    "yJlHqxxUECtiCkI6eQl0eEl9823tgHzHqfj/7bzr/VuHPmCc2f8cBpUp1zeuqyMy5wjFWkB4B6vEPLFFICyMbUElJKQUO1t+pqvj"
    "uvuRalPIpNxBl3Q3wSEHaKu/Zbh4I8C1iFpf0AipQcc6fqo46qhvXPeBrty1P0WuH/k0LK6899ZBZxwHHmXpI7kc3PymdecIq28R"
    "61cN2wFmwC8iFlsMbai+0f8+Jmap6MIKGZcndzplvMIa4yszlRd2GJJ7eG+n+c3rFlvB5cy0ikjVRWdOmEde87BytlDUKvZIlIIa"
    "4toqBy85WLuSY7UnSXk0dSVCQY0impxFlNgSorNZw7bIocp5nI8saPzKN7flbtiJagf7KYuMA8DP5DLFGWetfUeyrthBKvHqMRHF"
    "+I9jwaK0bM/c2Du3+bYUWXM/qfhcseUxkAQRCBRdN5hVohnEzWSK++qb1m4ioYdA+A0BTziyOyyZYqysy4as1joWs3DHiaiFRLII"
    "QmcCOIdU4iXEMYgtIlL+4DGr/+jIg+Wg5syGprXf7sy2XFlZwFgcTMVKpbny1mzLc/XNa/6ZgxnXj6o8o6IURypYCK3+t6Fp3bcd"
    "y+od61f9YuA8zAyR8YX0hYIcMLf5tlcqyNVC9CEiFYyBrABxjoI65co9d+y677otSKUUMhPQ+7GyKAZo/vErvr7IoaQZ8UlYIJaB"
    "WB04zG/feveqnRh05tQTVv8RFlUkz6lvXHeGC0STPXiraCVKO0Hg2MWUpVmOZQ7A8xnySoBeK8BiHdRoZ4sQG7pRyAoALKm4ElO4"
    "b9tdK5+NDjMODtppRq7Vzjp//mxiuQGmNIq6qvQNCwvfJMIzEGGQHBmlJUQgERG+jFXslWLD4Q6JMpw1HNQ2mFCuA+jTSLXxVPJ5"
    "HJa0UinVnV21s6bxa28W0L2k4gvHRhTjfSlRgN6Zbfn9vOVr3s4c+wmpoE5sOLZrqfyMmGIUIFnNZJVoJtbN4ixEDODEaBfPW42Q"
    "iJUF4kQ6yawBpaMqfxdCXChwxgKiDuk5VPbYKFZ3RX3j6ie7cte3orFdI9d8cEG10v2Ftf68C3svJdL1EDtCahDVRsYCIlCQvJJN"
    "8fL65nX3AvIzB9moQv10mFA7d2/dWsAWGCw5Qc3G7ppYXXy2FXUSK5wp4IuJpIlVMulMAeJKbvTnIAIKyJliL2n96ag5dOvEzNPI"
    "OQEgvsJBrgBicJNRNS9KWDSFhv4GwE3VbQ5PWEMOyhKIeDmYH1WHegKIqZLrIkAxFDGIGCIu6qRvQ7j9K8yxyhsSyC1RynEIq/rU"
    "YkKWXFyvXUW69vgR964ElnScxZYf7eq49gOT9bjnLV/zCDT/ZJR2USy2KCC6tr5x3W1d2dT2KdGkddSgGO0hbc+2PD1v+VfewlS7"
    "nlhXumEcYUlbOVe1I9ty7/zlq98iOvEfpOKzxZXGnqqsjiWxIsY6IZKoIwOYwBpMM6lvISyAOIgrO7iyq3RuoMpZM31Yx+qo0hQ6"
    "qE3XN97yTFeu+VsHT1oRiW/PtnTOa1x7Pcdid4gpWGDUcvpIMlX23FjFm0CqiV0Ip8NSYNzOhoZ5BWmAISorSG3SEeYoDpLgGAgO"
    "YkqVuU9jnfuGgkTgyt1/13X3dU8iNW9i1NXgDKRM6laxhTg93EV4whryhVk51LMx+x8zSeUMrvQ1tIw6aNOYV5giIcVqA1fu/Z8d"
    "Hdf9v6FbxaQZ2ZSbf/FtDS6U6xAFeBrx/sAkcP8QlRi3xgEYoOnIPN6exwkv3Uo7sqt+2tC09j7SyfNHSI0wxBrWNbPF5m8A6Mbp"
    "obLQ1w1jR+5jj849/5Z3qnjiJ2Cl4dyRP2ZQuZbtuevb5y1ffSHreBvr2tOcyZtKg9kxsghRX+l130dEolTSgFQYoW/dRocwe2j4"
    "PvPilNiyJZ28veH8W57tzDXffdB9J/vezao75zWtPU/HZlzrwu4QoGAMjyBqaRIVSkSTiSlOpE4YaPcs0QK1qiwj4uaDmfscqwtc"
    "uSe7o+O6NZV7dMd6dPaENdzEOPwGC1SduwPn8pgnb0g6Gbiw+BRx4gNRSXErhlNXNlz7ERXUzo02+Yd5r5G6Us7kH+mqP/6/kW4l"
    "ZDLFysrzyD3dl1bKm93azwDys1HSl0psQSC0csF5t6zdlk09N3RadAqi4jS8M/fhu+c1fe1KVrV3gkIbbfQf4eMGlWvZkbv+0YYV"
    "t5xvjbuddc1bxRYBsSZqVHdIg358+iGKWLCuKLmRjmMQQRyRUCCxeNuc5V87f1e25bcHTVqVqs4dwIfrd3QuVEHd21zYMzbSwqBF"
    "p4iIGOlbD/ZduVRL9fVBEne0UA0L91FQvCoa76kRTWCPFfhzWFNP4DkAhnVtIBL+0bn8mzrXf2B7hVzcUOpqTuPqhUx8tdjiKP3j"
    "Ih8gIvossi120k7LVwwpO+9Z9XNnSu2kE8O7EoMoaseTnGFj6uMAyZBp0SlNWu16R8dHvi+udN3YumFM4LWkUqpz/Ye3d7Vf/TYX"
    "Fq6BYCfrWl0JrOYI54Ok4jorFKtTImaHONNJHNCI10FgccYSqzlKx/5rQePt86ptqQ7qb2dTDtmUm/Xc79/tTCHLQV3kUyYHXXBV"
    "PVPHfcoy8rU72HEazf2gLpCw2F4K975l+89v7K300D7096KMHC1k5wlrqtBUxTKaVMCkk9rZwk9Mb75xZ+5jv6tUBrkh1RVIFHAj"
    "B8mZEDdSLzJLOsEuLGzsXL7jx0inecLOcowFFdIRuMyobWkAJabohNRV9Y3rTkM25Sb1jMhBE0WlhVP7qrUuzP8DBWPuhjEBi4Vs"
    "dBAYQl0d19wWlsuvt6b4jyAqsq7RIEX77csnKMj1OW+DKKhRIE1iClmtYktA/HYR2KgvI0YycFRiS4ZV4pWGwx9gUTqG9MHmMUiA"
    "VnriibWlzvVXt7iw98ukYopUwNHB7yNF3iKAGGIVzX2T/5ek2/6mvff97e7x2LO1loMoTHjC8jhkgoKrBAUDEJFOKAqSSpx9HKbw"
    "V53rr/mzXRtueCHypskeuCJPV/auLlhzKli934UFATBSuxkCACZ8FpmMm3SVUlFZOzquz1lT+j8KkmqE7hAEOMcqkRSyn5x2Kqtf"
    "Sq6rY9WnXLn3n6JuGJN1royiQ5mpNrX7/g8/29V+9YfIls+yJv+PEOykoFaRTihQpG4BmIhkDimAC9B/rENIBcy6RgNcElf6gYg7"
    "r3P91S3b7lr5bFf7NQ+IKf4dBzUKgnDkv0m6UoTROK9h3jcrthgHGZgzldZfae5sv/bjYktvFXGPU1CriXSFvCfI2LJK3KSIgzot"
    "ghddufeqzvXX/NUzuUzxsMmqcow0rmIzAa6DODftOt8cs4QlqK4abd8KUiryv/8XxvolcuBXv+9XCWn/RK1+OYCIVMAU1Kio95wU"
    "nQvvEhe+J1b4wxnb26/9l+oqeNi9mi2RunJK/oZ1MgGRclSKOOBvmcp9lkglILZ4//aOVT+JyG4KmCNu2UJRzo8/AVu2RIEGJDzg"
    "HiqBXUw+JI69a96Fa18RVb+l1AghufIsyAz5+6Iu5gZCR24vLNcadcPo2PHXLuz9IQc1uvLe7DD3XPmSiXlX/doubc99+LGu9ms/"
    "5Ix6jQuL14otd4hIsTpGSccYpKiq1ke+3gHPmIg1U5BUVQXnxGw2tveLIdySzruvTnW1X/MA0mmu9i7suufDX7alnu9zfGYMxDTy"
    "3yNI2FtUQfKKhqY16b4eiAdN4FH1YGf7qh+ZnvJZEhY/DeBFitUq0rHq7zOVazmU/aQoRvTdi/Qjbtpjw8JXXVh4fVfuun+tXD8d"
    "djVsJiMASO3VT4jIU5XUe3lM726Sv2iYbvrHRNGFM8II1CzSyYrS71eC21+VD1gUjiWLNzhLUV29VJqUU3XPtV/TchdCbFgSGz4t"
    "1mwicjlnbfuOez78h/2pvraRDekq1YJzG9eeyTr51wCBgmR8pJQakYKz5c9E6qRtaixUslmLdJq7Mtf+cu7yW65UOnkbB7WzZLhF"
    "tTiooDawxZ2rgfSfAYsx3CFtIZnBukZDRA/p3iFOk64Bwt7aI6pssmkBWkXXtl5uexv+j+PHnS+2hJFM+yTMzxajaeKuCTZqx7OY"
    "dmRbtgG4FcCtDRfe9lJniucTSROEXwvYl4PUDNIxFR3VGGquUGUuAOIsxJacc2YrObPZQXJkg44u6ny4Lx1dJZe+hVmkdrp6YlfM"
    "U71PMdQHKYjPITBkJOd0EXBibmtD09ruzsy1X0NqixoyMzEagafa1K5syz4An51/8W23S1i6HOLeA+bXs05oEQc4A3EmUkg0BvUl"
    "lb0t0iAVKGKG2BKcM1tIzPdZ5N9ebL/2mb65P36mkYJ0mrdlVuYblq9dKc5+j4PaeWONcJMjLJzmoBau1FszTKrlqJZVBJCccOHa"
    "ucbiayCeDUggkBiBYtG/CERIAVAEUSAoAanoMC0JAE2CoWwaWAZEQgGBjEAcEUoiVABJnkB7BLKDQM9bwVMs9hlG7Hfbu17cii2Z"
    "8oBrTWW5Uro6iptwSiGbtQ2Na94DHX8zbKkkw53rEAixCmDN05256/62UsY0tcZrpepv/gU3nepU3RtB9hUkMluG7F7NIHGWjfvY"
    "i/dd31V9x4PfeUPTuhvA6iw4U5YhyshJ4MDxmEj5/3W1X/ud6jM9kve7oPEr8xwnvwCRGkdDdaUnARGzk7wTfKQrd23Pgfc7AXOm"
    "sVUh12oH/536xnXHE+wpBD5FFI4HMF8cHUeEpEC0CJWZpCDAHoCeJ+e2sZLHw2LxuZ0PfLx7wJ+JOlUM52rb191g3gW3L4AyywlY"
    "DHInAEgMTwsKZJ2jUuHG7Q/e2Hnoz6pvLlbHA8298NYz2bmLCFgO0KshWBARtx40WQd2eqKKIBVbdoDrFMEWYnWPWHd3V8+vN/Y5"
    "PKfaVOQ+PBHvNnoOc1bcfCJT/A0QWsAiDEzBQlsixzqpXbHws857Vj04OC167FlWDh1Bor5gXeDTTp5DxT2G7bw6AgDTHbILe4mD"
    "2gEDyYUJcjW2XyDcDc6T07XsZqiYeeKnu8JRJX2qTaFzM40wcY+hVzBNStXHOYhMi3nR1wfzMN9vBzhqmJsdS0qNojN3k5m6PoC4"
    "qsRdp6w92Sh+KZgaGO5EAY4jUEKEYkQoC1Akkb1OsFUYndqpJ8Nk+Oyun16/74AYkN0sEz7/j5L5dewQVn9fn/3NKmXCn2+qkn4b"
    "0AR3swCZcSg1rUyog0l5TIcAWX1Oh3MvlRTX6M/kCASL8Xh/k//uoixDqoUHOF4P9Z76j/VFm2W4ztsHpfjGMiYm7lkR0mlCB/jQ"
    "O7UPuQg4wmer+j3LqY5hFvFeYQ35DGS8fqX4x+vhcRSq43Qr9VmojIZxIW4PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8P"
    "Dw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw+PIwffmumgn40M/pYcXfecpsjJGJWecE0AOgb9WL//7+hoOzPEffdD"
    "tYfdos0S2ZVnBL7t1jgjzUgD0fMd7kcA397IB+VjA9Xmt4s2R4O9b2K0yuH3/huit9j0COT7m3qOR0fuanPNhsUycVYJ44FK09nD"
    "6pTfr4npos1SMcuTg/4dqcXTew6Oy3ueDp3rB8WR0R8MjphdzVjQmJ5G3odNQK7DN789JBL68QkKha30kvpT2JZ2kZ1XR7WmaJ/o"
    "Sjhs+qAZ20Tr36F5CgTyqtVD1USv3z3PvuC2hTElJzjBSWBZQEJzANQBiANEAjEEFASyV5zrYs3PMdwL5R48v+uhQdYJ1Y7pU4W8"
    "qsFmEDGfdsnq+N6COokJc0XcAiGaFVlFICBCCNgeMHeC8aJx5V275p704pDk3pjWU5+spybmrPj6iSRSx85ZEXNAXCLS4piVCdG5"
    "976rd6OfZ5aHV1hH0/0JINTQtO5LxMFC54wGJEEksYp3TSCCeOXfAJG1KROIQCAIWAAGJLKtJhAAC4GjyH69AJJ9AtpHDjscyTZA"
    "toH1HzTCZ8Ji7XM7H3h/9zCB88jaCxzgvZPm+sb604V4OZMsE7gzCHQiWM8gUgAx9vtCyoAhE7kCO0AcxJYEQltB8pQIHibme1yo"
    "N+64d+W24f/2ESaqfiQy5+zVM3UdnyMOF4B4KYDTIHICKx0HqX4u0dVbj+5VXAg4txdEnSJ4AiJbhOkhAf9qZ/v2Pwy4t5HeccWb"
    "qKHxlvdA160gWzBDmUxO6YklcBQktbjCt7ffvarjkPyW0mlGplWOa7715AD0CEFmicANGZcIjkgHIuEjXW7H+RVlfIRSs5ECrG9c"
    "VwfCZwk0E+Rk6OciIjrBYoq/7+q47suTqx6jvz333G/OUPHi+wWIY1g77ykjFIRULEZS/tn29dc9NHhcaRwTaCWh+vdyUFPPrtwX"
    "f6ky1vf/Wx3+MgSrD20FXg1uRASAoYkgEgVyZ5xTseK2+uZbtwB4GOLuKYvZuDfbsmdgMJ1g4qoG7CxZAGhYcevpItQC4M0EOV3p"
    "BAQCcgYiFnChiIQORMOM7so+nggBRCBiUupEkD6RWZ0vzn6EdWl3/Ypb74XID8oh/3hvtmX3UOQxwVKSgVap3ve85nXLCbgSwBuI"
    "goUcBJV3ZSI7dxcKxEiFoSqCUva/aAKD1SwiNYtIvZyY3yji4EwxrG+q/wNo7b1wdJeyNvditqVr0Dver8iqPl2sLlTxuve6MjCc"
    "YfTUjSsOHJsJUyj8GkAHOsA4WAvbLYsJIBeTtR/nWO08V+51RBQMv/Q0jnXtOXONatmJq78XuRYPzhJMHDSChEH4IYrVxSFm6PW+"
    "OCidhDGlRwF8ebLjHgBx1DNbIfiqCmoBsVNbp4gDx2fC9HQCwEODx9UxQlgACXaLKcwWVxbI4NUs0SHpTxmwBEdfgO8L5GBifSKR"
    "OpFYXyw2/Lu4w4v1Tbe2i3Lf22F2/BTZFtN/1T3uK6x+jqnzmm79Mya6FsBFSie0OANxZbiw1+4Pyn3XrkYV5vsfm4izAjEiUZBn"
    "sJrNKvYWCN4Sp9LzDStu+07I5X/cnW15dsggPiEk3WKBDOY13vbnrHAjES8njkFsGeJCJy50EKmuNqr3TQNe/OChIVZEnEDK1Xsl"
    "Ig5I6UXgYBHErbRc3FG/4tafi8N3d0jn//W94wPHT48L80Zs0UzDuWhcqDRAhUNOS2da3Lzlt7xcmK9yYd5FYw/Dr5FEBC4UFvup"
    "0y5Z/R+Rq/eRSw2SLgtZ7BKTr48WNkPEDYF1EAVgz5SJfZocRHY5k58JsTJsvJsi4wqh0iDJD/XNabasOyyoKCiQAg3+Ag/5hVG+"
    "+n628nuioKP7ficg4owTU7Qu7DXiyo5YH89B4lJF8f9p4OMfqm++9UoAEVmNeUN3jAEbJMi22LnLb21uaL61Xengx6Rjl0CcdiZv"
    "xJZdJSjvfw6HNpgjeVl9BkQMsSJhwYopWCJeSCrxt4ENfj2/+dbPzTr/C7ORbbGV+x3/yVMhqznLv/aqhuav/0gFwf8QB8vFheLC"
    "XisSSuUd6so189ivgwbfqwJExIZOTN5E96vmKZW4VOngxw18/EPzmte9b8GS22uiFE2/v0OVa5jGXyKHGEMilSkg/iSrZALipF8u"
    "dugvIiW27Dio+ZM9Bb4CyDg0po+og670xZHhvqT636eas+9RMa6OJcKalMXNgOAGsDgjEuatmJIjVq9jnfi3hhW33TPngjVn9wvi"
    "h4fGtMb/b+/Lw+Qqq7x/57zvvdVVnYUk3R0iIAjoQNARjQsKpLoD+DCKG1I9ODp+6oxEIQkIjIgC1aXIhyJL0gkY3NfRrlHH5VNG"
    "IEkBAoMwMmriBiprku5OQkh313Lf9z3fH/dWL0nX0kmnOwl1nueSPHSn6t73vu8553eW38l22lmn3Di3teO2tdpT60j57WJKToK8"
    "jTxSjf2aNyEqG0JxRsQMGRDNJh3/RJN/2MOtHWvOjRCWhKG7SVrvdJqR7bStyVXv1zr+IGn/rWIKTkzBDt/T5HuYNGx8iBTEiAuG"
    "rNiiIS/2Kha5ReKF5kadwCh0le1085O3vJyV924xeRedkXq2FcEZIcKVC85ZmwhzWdIoHnuBSMNgTb0NKytyFltyEgxZYu9U7fn3"
    "tCZXfmSfkUcU15+XvLm9KRF/SOnYBeICEVOww2hwyoPYRAA0xIozgwZEx7Lyv9/aseYLRyfTTUDGIb3PRouQ6mFkMq6lffV17Dd/"
    "FXCzJBiyIOK6FeJkvmMwYI2A8N4t913ch1QPN6oHAWzaFOVW+GpSvh+iq/p1Voiymo81u0r/EqKsLtXQKw2D1ZD9j78YREpMwUJs"
    "jP2Zt7a1d38S2U67V6GOVI9CLmPa2lctVTp+J5E6zplBM6JA9yUSsse1l4aLtFjjxBSt8hJL82r+XXOTK4/c55BoqqeMrG7UfvOV"
    "YgoGYqXO53ZhtQlMxSv8ef3FMeIs6bi2Nv/13vXLf7zfc3YHi6RSCtmsbem4dRGx9y4xBTfhvUlEsCUhpo/NPXvlrAbKahisF7iI"
    "1H/tqxJHmEOCE7F5Q17ztW2LV16AXMZMSIFHCrElueoq0s1fgLMqzFHRRJP5bjclLZHBi4oTojyDjP49TKzKMcz9KRcMBKRip2rt"
    "r29ZfMtL9zokmkqp0FitXM7+zEtdMGgAqRX6K98/iDWTjivScU06Mf7lxRWxDnNdI8atUpGMI+WzM0NPBsa7NAyBbRxnfUgmttdq"
    "7sMJOCCT9r0Tk4ULJXxykyblqwmiqxGU5QJHOnGkKtCHgYxDKtvQZS8A0Y0l2FObgpgmdvbLIAQOIgKKwj4yXLxRH/oQYTEFC+13"
    "zz/rlvu3Zjt/V1f1YJizMq0d3Veybv50GAYTnkCttAsv0cQegz0Oo4YOYkuAOCMOFiRCgALII+0zSIefLwZig+gvE3pmT8yQIdV0"
    "PGncseDMWzo2ZzufDHNadVZMhutjW5Z0v5rIu0lM3tY0ViKWlKegfBZTgLPBkyDzJxI8K4SnAAyISB4ggWAWEY4G4RiIvJSIjyIv"
    "HhpVF0Ccid75qIIVIgewhrNLd963bAcW9ChgT3QlcIpIEUAe9qmsnQCZgM8wof1dEUF6COtN6r/xVI9CptPO6VjzRmJ1zoRyV+M4"
    "PWKLAuLLZr3pi196PpvacVAxZjSkVkSnYbDqOvgQA+cGK5e6j1R6iYS5GSJhgD1izWCN4RSRC8JmUxEbGY9aioIh1pJO+C4wNwM4"
    "q05kZVqTq97POnGd2LwBSZ2FBSIQOFKeIvZZbBFizeNig0dAeBRW/giltlhLO7yYLZBhZ1hiEJkBWzqcqXSUOFkEolcD+HvWcQ9i"
    "IabkImBWhzIjLbZgWMWPtdb9qDW5+vS+9r4hZOpUPhkAECLpvolYa5G8jcrUKz40eQkltvg4TOGbbORnNMvfuPmnS4dqfdWCRWsT"
    "trl0HDD0GgecAcFprGNHgzTEFgFnLCCOvJmeLe26rT938R1lZ6LCRw7B2echMBCn92HbOhHEiShWl9ESOwCB3cfiEwNntTAX6kdX"
    "IcrUIl1EmqJev1qOFFd08Jyx7De3xYqDKwDqCs8CGmHXfXbYgWnr1RKnQodq/I3RMFijvW7dpKwt3B0Y9e6mODwuqd28/F1wXoJt"
    "QSniQKxSSlM+Zo32PbgZguIsa0ptIDqWIScI4TVE6kTSMSWmAIi4muiDSInJW1L+mS0dNy/uz3z0nor5j7CXxc5Ldr+GlF4rpmgB"
    "V5+xErHEnoL2lNji38QWs2D5wSzf/vqxOy4uTnT55iVXnYDS0DnE/I+k/deEwKto6yuVJx2GQ2ecLMXnv4RM5nykTqqtfKJ1aWuf"
    "cwapRDIsLKnosYecjqzYmcJ1dtB8diyVVESfVUna4TZnlg4B+G10fXXBorUJO7t4qog5D8Db2YvPJ7BypaE/SSlxRRiq7LJ7MLqW"
    "36XjNLum/xtFJvfSagTaaC+vTely9hJXheHQccPAw93eInJ2sRD8Pj4zrvfc4xOQUgzNoIF+ADUbeCN01dZ+yxmk/LPqyV0RaxZn"
    "pKL2JLCYooB5eduSW27rzaZ6GyhrX/RfXLkg/z1WcpNz8CgMfU+tuSQltjikpan0F4T7yjYMVjXnQlxx533LduycjM9LpvVcdfir"
    "lS39CxF9kFhrsSVXB/IQYi1s9QcA3FMFDmLBOWsTZiD4OpHyxRVroYsIVZGw16ycLTwlpnBDyZW+uTP30ecAoLesXPYg8R1tKIEx"
    "RL+5jNmWW/EHAH8A8Pm25Jp3iMLH2Uu8XmwBcK6OZyYtwaBhf+Y/tnSs/EV/tvMr9RYqCKkPECkZpiwZ31wJaZ+dyV8RUuZEodR2"
    "uIig2IXJ+wqSi9Z8FFnw5mznEIA7Adx5+Gkrr7KQ80n5HwaCFdvuv2jXcC9cBenLLRsAMDAZW601ufr5er1iT1Ff34OXbX9+Ks9W"
    "dqMAQg7dXYrCFsUK9ysghjjznJjgK6T0ZRVZJSKUpfzmua5gLgPoYw2UtdeWQkIqNjy5dd2Khw7U8GDDYI13CIYZIlI1vM8uGlbg"
    "2E2Jh+znZjvwEICH2hZ3f000vkI6doKYYi0FznABCXDGkafcGH8625nfw3NM9TAynTZoX3WV8mculNKAAdUosBARMBMpn6zJr1WB"
    "uXrLfRf3DSvv8J5dTSORGc94pglJMHIZ25u76D+R6vlJW3/vCiH1GVY6LrZk68hXsNiSI+gbWk5f+/P+bGpL5XyWELJk5591Q7Mz"
    "lIQLqGL4KAx7sjOFjX0bVnxumNcwlzGhIcrUf3hCVnY3/NypHgaAiIqpGwtTa7EpWwJAdRhb2ue+rEW365CEeXXdZ9k68urf4/WE"
    "0Ws8RLkgqH3eW5SOn1YDCVtWTdq6wR/25ZZf3tqx+i3M/t+JDWTc6ASBnckLlLd0bnLlqu3Z1DMTyoE2ZDcVQT5SKYVdh2vMPN1M"
    "/R1kAaQqTgFoGKzxD6FgYVqATqmpwKrru8gjb+feXMcDLafftIS9+D1Q3nFwpkp8HiTOgJiPKiT8EwH8D9JdhExZMYSNly2Lb3kp"
    "sb6kruS1iBArEnDRmcLSvg3Lvz5sqHJdFjnal80pQEaGEUrEj9gL3Dz3tNX3w3PfZd10TA1FFRpqCQx7zXOd25UG6MNhufo4vxmt"
    "h1jvOAKOEGdQJXTkwJrZBg+Ehj+LSVJoo0ayRKNVcpkS6u8Qln3OFcxIR+NrVtdt+YisTGCPTw66SvUo6tuaHhOdHHc9mJ0pFJno"
    "pjBsiuug1TcQVrxWQFnOst88i0v2CoCWV9wzDanH/xBksxbJNOGO6WrDyFZREA3Zv3A2k3HIdRhcsNbrv/fSzc4UVhAx1VBnFFay"
    "xQDgZQAQkUBGHmtEa8N8JaumOMQ5VNV8IsRaBJwXW3xH34blX0dyvQaEwtzDJMf8ywwWyfV6+33L/rtkhpaIM38iHVMh22zVR1di"
    "8o7Ye/9wqft4TBgRgaxz3lHEPkWop3oGX1wcIEFv637IKJNEeZwGncXu6AoZ19rb+07W8deGec0KTouII93ETsx3tq5fthHJtO4b"
    "8L7rTP53pGMctU9gfJRVcEzqg21n3HpsSCadbui2Q1AaL3Wq5PalAdJp7r/no3eIKf6atF/5AIaOoxAY7OiI3aAFI9tp5ydvPoaI"
    "/1FsXsIy7qpevBNiFlv4P325i+/AorUech1mvyencx0GybTeee+//dWZ4jnibB9YU9XnDo21I90UI6UvDFHgOPt0eCqwnQFi1Bib"
    "wLAlAauzDj/tM63IdRgsWuvtNyelIWPR1aK1HshdE/ZcSeV1I2ZnCwUouh4AoQ+MR5YG5Og6kKLKfV9EcFZYNyXEmE8CkIN+MGZD"
    "GgZr2iVESQLCncReGKqqofkEctiY/xkpb4H3XvYSibCJtWrPkSOdUM4WP9+XuySLRWs9PLI0mLJnzmUMkmndf88lf7am9C9h31FN"
    "pc5wRZDI+XPOXDs7RC4y7th6dlSqw0awOCOs/Dbnz/nWnEXXzw7XQCicxNpgSdiv6GpGcD57za8QW3TV0VWcYO23++9e/iekehib"
    "MgHSae4d8P7DBYO/JR3jaD7GeDaLXYjM3zP3zDUnItvpkEo1KJsaBqsh+ywOf613jprsnmfMZUI2CJLz4AxG5jWN/02kfBYz+FhT"
    "IbgGqR4VJuinWHIZg0VrvW33XPwTZ4vfIi+uUL1klsUaRzp+uLbFM0LlV4HJgNxmcaZ2zxcRiyk4Yv9Nevbs+1rO6D5nJIxHIQFv"
    "Mq1DJdswYJMg4aTps1fGQO4qOFM9XxehKxH7WQAU9WwJNoQoS4SuQ/VQOgHiWPsxZczV4dFJNd7CISaNootpEAFpqvvUYxQaCquf"
    "5vc+e6Kw93KxpepceSICViwW1z794GV5HFW9zHq/yjnPWjwiBFrV5UzhXCKOV0VGRA7ERIJzAPxgJARYDjWF1W1F6/3RJ7OdWM+t"
    "OKNojNHKW1b+y4HYT9qWrPklhL9uCD/bvu4jz4wpa0+nuVy+3hh5vxeSTCvkyLQVu/8PeYmXRSTEldCVJT+hbGngW9vuueTP5Z6t"
    "YQctneb+DS//j9bgt1eybnpFlTyYcqFTkmpNrv5cX7bz0QaH48SVU+i0beQpQ6gLewToQj3zABsGa1pwrRxDdRY0E2ikJSwJRg7O"
    "QZ/OOq7EDFUb/OfAnnLB0FN6RiwbloFj+kp9MxmHNLgvk3m8tX3Vj8lrPl9MvvL9S1jaD+I3jJosOyqcSIJ0mndmLtzR2r46R8p/"
    "hxhra+5pIiU2cABAOnYqiE/VpvB8W/vqBwWyDpD7jI79bkdm6U6M4QqMqgDbTpKwp6hRNl112+a67PyzZjQ7gyvhgmqORJi7MoU8"
    "C49GVyM/3wCFXIeRjtWfAfH3qvt3Ykn5WtxQGsA7sTDVcDQm8uJISpGBt1O5XRoI60CUtpMEEIKsXiLOlLkGK6Ejiqqenx377wFh"
    "vL4Oc+dY+2yD4Iebf7p0CKk50+9pbjqJACHBrd+CuPMhwhX1GIFEDETkuFaee3Qf8DiQJiAjYz8PcCKrWOw76y7Qi/p5xBRCAj5W"
    "s0jF3kTEb4IrwrPBM60d3Y+KyP3C6gG28vu+HG1BbjQlxWgD1jkx8t8XCLqSoPtf2Ws+RoLB6pWBfkJJMPDNvtyKx8agq7JEKOuk"
    "DX0/+L2Z9yjppleKKdkKU7GVmLxj9t7Wllx5Sm+GHmygrLqglYItAsA729pXHyOApr0hN564rXICpUjslt7e/kuwqXpbSMNgTZUs"
    "Wush2xnMW7zyrazjrxJTqk7TFJJ7giT4y7CxisJgBDkB4kL4XtlvZXEWzrq7MG3EYLtJFForqu4Hm0xhO7OeK5XDeAQnjnXMs6XC"
    "ywA8jtRJNKZFI9tpkU7ztszyDa3tK/+d/VnvltKuAMT1VQCW815iJeplE0AUsT6C2DuCiN8iNoCw2d7avuZ3RPIgBPcbVg9vX0fP"
    "jDFgw6wZL3TkJYQc7Jwz47Nh6N/ElaQK+4qAFLkgP0Ssx0NXY1BWLpcxrcnVnyHF2Sq9XAQRB62Vc6U0gH9ooKw6sZUYkPKOB3vH"
    "U+X1nWRxYPZhizv7F8Rx+Wag1EBY0yppxqIXKTyyNJi75MYjGP6a2iMVRECaxJm+YFfiD6Fy3ihApyxYtDZhpHQExAIkPP6mEgEz"
    "O1MsGvJ/C0DGH28x5YdCAKFdd9O2eHv3H8D6jTDGVfCUAYIj0sxERwPAHnksACGtErhkvIt8GnoFe80vl2CwfqMVHdaReyCIsw7W"
    "iISs+wziuay8xcRqsTgLbYs72zpW/xpC66Hcnb3P+Q8jtzQIWTPSHBrWF6hHHzZPGx10X0h+4oja6KpJSWngG713r/gLUimFTGb8"
    "dYtQVt+Gvv9sMy2/Jh07uSLKIlISFJxSsbPnJbvbt2VoQwNl1Qd3xAWCKGQ+RV/pQIYJeE55s2qX+zZeUoVlDKei1nlJeKXTjFSP"
    "QqpHjZRLZxweWRq0dqx6pZL4XczqqIo0MyP+pCPlC4AHdzyydGeY/OwSADAzglkAzQn7b6mSkytEGiDZnJjJvZFmPzC8zKjaz4n8"
    "GcQYHsVScSkAYVlQ1QimgZ33XbjDmPybxRYfZX+mBxFbu0m5yrkIlaxGyKAvYgrWBUMmpNXi2aRi7ezHMxB9f9ss85u2jluvb1nS"
    "/WogM0JttS8DKQ9W5yzXZWee0T0PTB8Nx39UQVccoiu2+FyIrhZK1a2wAYxcxgjwGYBrZIFFwAoM6QKACsitIeM6b6Sm7EL4p6C+"
    "MTMNg1XpcPT0lPMSdVwUXplIWWU7bblcuuWM7pe1ddx6PUE9wKzr4REcvXOiBHMKw7yFwAwi8WuGl8OqjudHjc04MA5shJKYqJfq"
    "n24xu+pPMxkHpHnHvZc/VbTFDmcK3yTdpEJ2BLHYZ9bp4YnNGjTWgEGMEOsTWDddwVC/au249RdtS25753DIMjRaL4wy+SQYIGmy"
    "7hLWza1V6cdEHOsmJrFf33rvir8ilao99y2XMUCa+6T/R84M/c/w+x3/lSkJCo69eLI1ufrsfZ5o3ZADQhohwUoIq7OTMe5EWQl5"
    "7ABgA/j4+Fy1HYipvEqIqJlMMs+RORrgVzLoVAheR7qpSWweUeMk1zCVDspjFww+BeEfRSSvDuk0IQNYCTwtmqurwIgJm6RUhlwH"
    "Wlm2EIbq1eMk5Nf+rdBoRazz72tb0v1DwLuavfirRCScVxVOR+Yo87cPRmT3EGLgxAUOgGbVdBYgZ7Utue0+ONvVm+28exh9HNKV"
    "hSG6ajl99gIi7yKx+WpRBAEx26AwWBIvRFfZhfXtzzDcamhJ97UA/6DGLgs/k10XIP+FhV0NlNUwWIcMElaRUlvS1r76D+gD0J4c"
    "5xdXk9zTqsuBo+eLojTggSUGsQlSOqY4ASKGOAuxJYRxfNQ3AZjEkfK1c8G1/RuWDSDZp5GDQSZUsOxpK65WZ2sIr0jK7O0HXg8R"
    "CWL1T8itt8Q248LQbBf1Zpb/EMn0T+Zj/nlO6AIi7mDVpEVMOEUZMBChKGS1jwYMHF1h8QZApJtOA9Fdbck1a+LovfyJXKZQ1/To"
    "g1VSJxGy5Ii7LyPdNCdsuagwPSCqDHTFga/tzK3424TySxG3ZO+8+T9u7dvyMOv4ayqSKhMpMQXLOvH6tiWr39Gbyfywkcs6uKUR"
    "EtzNISNWzaS8l1W+/Jcyey8JL30MsXcUWB8OUnOIKCYuEAnyUb6jYMMPpXonABvSCe1KA+v7W+Z/Gek0jwzGC71DJ3oQgKmpXkUA"
    "omakevxhtX8gSLk0nzCn3qJZAU9gdFMUmk31KOQyZuu6C7/bt/4jS9ja15pg8Hpnir8BANIJTV5CEevyJGgTGTGLvS/nLcf/WUzB"
    "ijOOY80X5dXhd7YtuWV+OXR56IGrNCObcnNOveXFpNQFYgoCVCikiQqCxBQGNPMNYQRhgvmlqKiFwNfWsbUJcHAO1yCZ1lEuq8Fk"
    "Uu24QabpahisvXhdTsSGIR6x41xu9GWcOOPgjECslK3ESL6DJpC/EEOqSYspPmlF3odsyo07tmSgtAtCOyOHvmIMLQzty4J5z2xt"
    "Gd6HB4IMJ7/puLA0vzYNkojrnfD3hF40lXNIW3LLH+7fsPzKvg39rwKZV7rSwHIXFHpE7OMAgXRck05o0k0qJFqFGzFgmHifVfju"
    "2QW7Atax0yD+HbNP+/ac0PE4xKifNp1EAIny+OOkmmYCzlbc9wLHOk7Oma9uWb/sibAIZ4Kos4yyWtt+6kz+V6R9VSWXxWKKVnnx"
    "k+dxSycyGYdkupHLqrxvCaSn8FIqJP6pJ+zfCAlW8JKjw0b1/5N9gnWAJR3XYoOnyZXesj13ydNIb98tfBR+x/aHtg+0dLRsZlbz"
    "xdgKnVhEEOeI/RnwSi8D8Gw4rG+6J7EKIUNuwTlrE2awdALEoOqEZBGCWLDIE6PR2YS8xXL4p0y1lMuY3nX4DYDfAFh95Ck3xovx"
    "xMucGVhEUK8H6JUkciIpbxaUxxABXIBo3lYURgTXh5gBgDwXDAbszTjZlx1fA+jtYWjwEGk0TqcZmU7Xmlx9PDG/P2rGroqubJAf"
    "NMQ3Ip1mbIr2xQSPKJJgZDsNta/+DMD/Wf19EEGsMHAVzl75fbx+e4BcYwzMeOsqzg0BbtdUoVAiOHGkAGxWsbk130fDYE0r9IYF"
    "WLOX0M4U7i8GA+/dee+//XXcbn9AyvF3dqsfh1YnR2zvlVCyI+Ux29ISABvG7WGaagmNprP50iuZvSMlpOypkpgnFU4gdo+NRWd7"
    "IaHxD3sBRo25D6c543+j6ysA0Lbki/PF5F8hLngVBG8A6NXEdDSpuIY4iCsCIgYjuat6jJZhP/G2tvbV7+nNLPv2KLqpQwBdwQnZ"
    "T7JKxKO+q4qTn9mLK1savP25DcufwPp9+N5o7Xo3LPtRa/uqB1nHT6mcywKLKVn2mk9sKQy8tz+T+XIjl7WHGNJNGsHQ1wM9eKWR"
    "Zq3Jn5L96YIh0sFM+8T9HyiiRjioYbCm2kgJHAgCIs0qrq0tDlkzdNPsJ/9w7WOPdRerHqTI6AjJrwj0rhrfxGIDQORcJNOfQq7L"
    "Apnp9SrD+xdxdB5pH3CmGvefEGtytvSMX7SPh0anSyYwzr7yyuw+5n6UAUO20/au+9BWAFsB3AUA88+6odmUmk5UbnCxgM4G4TTW"
    "iThcCWIDW3Pac/Q+YAMRuE9iYU8Wuc4AB/uwxwhdzelYfRITvydiC+HK6EqxC/I7PVJr5591Q7MrxUkPeHtdhFKKPafiTpui8I0Q"
    "11OD+JjgAiHQJxYsWvvvmxduLKAxbHNPhEWU33HXx3ceqHfYMFj7FUFJWKZOJGEoiRVpX4EUxBZ2WVf6rjWFm7ff89Hf94UagKt6"
    "feWQmNhfiishHNxYkYuPxQWOvaaTWkrzzuoH/Xx6vUoh5Lrc7OTNhxHonyLesirN0yJgT8iZh55+8LJ8eO9k98t7GmvAwntNZRm9"
    "GwltJ8nWbOcggIej66bWjpXHOTOUAvhD7DUfK2YoyktVi0qBxQaOddOJ8+dtOW0rsO6g9/LD5nqnIVeTinkRIztXDssJRFxTAPoF"
    "BU2KSGBnlvb66xUSIY8PQcSWao2YYbEly17zsWb2wAeRyaxuoKwKjhWEsOh2PfWjiKgREtyLNyY1JuLufg5lt38e5b9YgRRIaRU2"
    "cQucyRfggv8RBD8mQrbv7g+HPIHhwXE1k88Rl2CsaB8pUvAEK+9oqd6cKQCBFF0D4I5pXdaIssejVRezFz/clQbrQSbkxP18NLqc"
    "soMzJt8XlsqHOTC4vvUXPw7g+jlnXn+bsvJxZv1xOFueplvFy4cj1mQ1nQFg3QERpt1bSaUUslnbsqT71QR9npiCq/0+BUQcI1Yv"
    "nlxcgHKOsdZZJbiSQPiKua9b+Y3t2dSuA7FH8QBAWoIZaTkQ16VhsPZ4V4pI+Qq1yB9p5C+E8ly56P2Kg5iCFbgdYt2fIfK/IHoA"
    "sL/sXbfs8ZFD36OQ3Sj1e3kkSPWop7Od+Zbk6p+C/YuqsgmU+1C8xCmtyVUX9WU7V0/5xOERg2zmLr75RCLv31xQqNFALQJWSkx+"
    "F2LmZwAQhTTrCFHtjz4nkqhIIvrsNCMJjkInV7YkV/2Fdex2hM3DVYtIRIQgdCIAoB0u5B88iI+LkzR5vorQVV0ufORkTQ5qj/gp"
    "6yyCYbGBVV7zkWgeWgrQDeHeRANlHSTSMFhj3D8mEdsvtvBoCI0r6i+JBitagPMibsBBdjFoKxFttuQ2K3FPFUWejpgXxpq6ZFoh"
    "B7cv4QiBfE1s4ULUSvqHZb2OlP+5eYtv+e9t9yz9FRZd4OGR26fIaIVhziNPuTFeVP43WOnmKDle5b7JkoppF+R/0v9fl26uLxwY"
    "ViCOVJztT+8w48Jhj2HopD+39Itt7d1nk46fKyZfHTmKA0Faw4+ZlJzcNKCrMJTW2rHmjczqrVHuaiKl4pPUTkPRfyYAVIlIbFEg"
    "uOzIU2788tPZ1I4GymoYrIPQXIkj7Ssp5X/Zl1v2jskNh6XDdc4hDPvtS3VY1IOyLbf84db27rtZx8+soSQJYoVYxZXyfzgv+fkz"
    "t+Uu/8OUIK1yjiCZ1kWOf4d17DVhFRnXUm4stiRWbPdEPO15b7zpNdvup4eH1zyXsdivSfVy6CTNjuh7iujcOp2Ng7sPKKrWJHFp"
    "cIxgAwc6aKKbLGINe4n5JWA5QJkGymoYrIM4xgEeGRGRqhK66CKkEZb17p6LaDtJsHCjhB40yaSXL0dzoQR8LcSeWVNZELHYkiMV"
    "O0Ihcdf89tXv2rph6X8PFxdMeuI5Gm6Y7TSzkzcf5rP/Tdaxc8QMGRDrGo6DJS+hXDD0k+25ix+MKtFsdaNIdv7ilR3wm3/R2rHm"
    "e065j227a/mzIz/fjyPu204SYCOUk6H6hkcSANoRgs8uOuj6saKWi/kdq5aA/TdJUJgoujowjJYtiBCtaFtyyxd6s6neQ5/rsWGw"
    "DmHJOCxMM9BZfdxBzWjOfgr3ZDstUinVn70o15Zc+X32Z7zL1UIuRCy26Eh5R4jQ+tb2NZf3baBbQ89ytIGmvaclKpeH58ggB9O2"
    "uPsNpPRaKP8VYvKVueVGrykxxJZKLOoTdRnGhV0y742fnSmsvkhiNavYe8gFZ7Qtue16f97Q7VGf1cioj8meDrxxowIyJYdVpzBq"
    "jEshEiIWAYV5zA2oQLB8AEtEo+SEupgVYEtyEDIdMcQZ1om51rhLAboCqR4eMxx0UiTNQJaA9BQ5JV2TVCghhIHbaXoZWagxcfiQ"
    "kuxCAYSY11zmbPEMsDcLztaYYkws1jgQxdlrWtO65LZ3CuRT/esuvHf4sKZ6VLmcO1ROXWWFJGOMU5m1flT/Urk8fM7pa47SGpeC"
    "eBmIdZSQr2OviSWvWbvCwHW99yz/XYUG6hFJdilkMoaTK29gL3GcM4MmLETTh0P5t5S2uY+0tN96qzbBv2/JdvaNQQnDyjcje2HA"
    "CKkexl92MB5ZWmrtWHkcSC+FLUjVVgMREnEEkfsPyj0XhXhbOla/mVXs9NroSqLm+OkJldTQb0psQRj8kbnJld3bs6lnJhdlkZt6"
    "xDYZDrKERu8RGGBpo0qwIZOIAlMnqS3ZZU+0JVctJ7/5myL5MvtCtXPMgBMJhhzrpjMh5sy2Jbf+TBy+UpLi3Tuznc9VOATRwDwq"
    "zwDDmMq5VI9q27r1dVD0HgDvJh2fK2YorAirq7HWWfIS2gUDD/b19187UupfVXmalsW3vJm9+FJXNooEiBhBYBwp/++Up1dawida"
    "O279IQNZL59/YBh1DTvCEW3TcIgPI6wamzYRkBopqy8b5zCMatsWd78BpL5BpFvElVxl5o6ocdbkdxTg3wWgvsrHAw1dpdNMOdcV"
    "jYKrgq4EIEWs49OjY0TgzFD1k+CsJa95Jge7rgBo+eShLAGAxPzTV71ERBOR2e+K33GgSKldvesu2bov9y1C/oJFaxNDM4Z8H960"
    "MLG4YJC2FQ8rjJdjbxisgxplhQUNvbkV32rt6H6t8maucMGuAKAa4+HDeU5htR6YVPzNxPLmmJVn2jrWPCBw9wjofzXwRGnQ7tj+"
    "0PaB0FsMldPRyXTTEFoPI2XaAP57OH6d9Pd2QKuXk2qC2AKGKXrqGakiYknFlLNBLzvzbmzKlJBKV2H3TTMWbpTZp906h5T7AsTt"
    "1oMQPZ8LHGxJiPV8UrEPw5U+XIo3PTZ/yZr1VmQ9wT7U17LgbxGKq+INj9ViR55yYzwf819PTO8H8XuIlK5j1pklFdcwu74zkFva"
    "vx8bofcrumrNdb+Ldfy11Qt9REAa4swOGwx8laTMxD0FlXhMBCciRLMJ+BCq9sURiyk4Iv3BttNuvbk3m/rrPqOskE4MRPJa0fwn"
    "wFUtOJ4c4wzLeqYvpvQfADr3sr1DiymASd5nZpbe4sPj6SEBIaMTLX6bHvp0L3D77hRmDYN1sEsuY5HqUX3Zzotb2ruP1P6Mc10w"
    "UIfRQplRHGLyIbs26yNI+ecR6Dy4EqwLCrqZ+1vbW58n6i4BsALy8yIJIpkH8Q4jFQMUg1wAcQHCOUii6k7EiziwViIyCBecuzX3"
    "0b/VDAWmNhEyWRtLdt9CuvkoCQYq5e84HA1mRIy1gChi/3iwd7wS9yFnC6XW/t6/oH31n4jwexH3JIl61rFsB3iQnLNMiAkwA+wW"
    "iNBREJxcAi1SSh9H7EFMHuJcLWPlQJrFDD0fKPe5cu7tINpl4QiQRWs9oHQN4KrnrQSOdEw5F9zYv37FddN1060d3Uewjr9FTMFU"
    "0HUEsY695oRzuz4B0L9OHsoiqiNnO1kWi0GaBME+fp8ArGYy8cxp22niwNqHMUNzGiHBQ1MkLJYQ6u/tenfrfO5R3oy3u2DQRPkU"
    "quNshcperJNgSMLCAVFE3ESkjiSU+zKjFmmRaGyUQ+RpSzTJl8M9Ve9EFWdJxZSIDEpQPLfv3ot/iWRaI9tpann6Lcnu86H9f66r"
    "8jC8eV2eDgwXOIgQEfvE+gSwOoFIvU1EADFQ4kKSEMUQUGiLSIFZQcQBzkBcSSTkQlRV84ZldKVjnhQHL9ux/pInkXqRQiZzMKEr"
    "RrbTzpux6p/Ya/77KCepKhpnpVnM4JZA7K1YtNZD/llCa/vU5XPiv1GYucDwti2fEmv+IQzTyvhMAEQsJu+g/PfOS676/LZs5x/L"
    "LB6TEpecGnfCARJyX+27wRAJIxbTJUac0QQyDYN1yAoJkGZsygR9m1LvaluS/CJ5iQ9IMBRalvrLjnnEvhEgIiJGRkUGJLJaGGYX"
    "KH/2xOqJBBBLOqHFBZvFFjv77r3kvjoYzIc9faLSpewlyBV2MjDBZxx+ThGxgcCWRMrVfQIGjeYFFIiQQKLfGZ5STFz7/IgAMOzN"
    "9Fzx+TW9uRVfOgj568I1T6abmOgqOFMDXYkQx9jZ4OaduY8+h2Ra45FMMMW5OoNUj9q6bsVDre2rfsRe8zvDKtVKKMs51vEYbHA1"
    "gPcAKWCSYNbUuKxCk/hdhOkt+2QALBXm5DUGOB4yknGhPelxveuWfdCVBq4AKUc6pgCYvfT2KFTuw1cZTUxgHtQeh8sCIPZmaHGl"
    "+0H50/pyl9xXnhBc29B1CR551jqNd9jiri+AFciLqxHYN6HAezjbqjxwE9CjZl1FF0VrMGYoZz15OQewkDfDk9KuL/bmViwLJ/N2"
    "Hlxl7KkeBjKuhef9s/ISfye25EAV5l0JHJTHEgw9Y3RsbUR4PE3GOVuOln1KbMlEDoZUAOAsJu9IeZ2tydUnI9vpkEo1hjwegNIw"
    "WIcc0iIgnea+DSs+J7bYLs79mnVCR1N0zZSFKcYzVAJHOq5AqmRLQ5/utVuTvXdf+peJoQ4SIOO23bX82b71F34ExpwmpvQTsEfk"
    "JVQ0ENJMiMB4kh80nB4dY7AiG+y6euuG5RcAaY7K/g+i3FU4vn7+Wd9oJvCVzgVSdeAmRIh9Arkbd9y1dCeSXWraKI+y2TC3m1v2"
    "qNjS90k3cehEVHBcxAkpXwu5ayq9IzHFg3lS9CFBPdUwWIeeSDQGXPflLrlvlr/xDc4WPgnBttBwaQqNh9gp2MSubCRJxxVpn0WC"
    "n1trTu3bcNE1IaJK7yXThhBSPar3nuUP9K6/8G1O3GJnit8ToSHWCU3KK+ctysZr/z6riIOIJfaIdbN2zv6WXOnM/vUrrkU6zXvZ"
    "7zXN6CocXy/Bzn9VOvES2KDKZIBwYKgLBp+yxfyXphddjUFZxKw+LbZkwCwVHTYiJSbvmP23z19y2+vKBm/MZvbb8gQyBHIHBfdg"
    "OvxDMc0D0cywmpYOZqP7gjJYkZKOlPXuV/nngkODniWXMUil1GN3dBd71114neeCk50pfBYim8lLKNJN5YIMEz3/JCj14bCcgcAR"
    "a6YI3YkLfuGC0j/03v2RN2/LLX84Uga09yXEFPZDpdMMpLl/3YX39q2/8HwHvNqaoU85V/o92CPSCU3aZ0RTk0YMmEzeswIg3cTk"
    "NStx7ilrCh/rc1tet3X9inDmVVhivH8VHFHkHNRxsa7jXoSQ7XTzz/pGs4Auda5kQHDjnp3wXBmwRxDcsO3+K3ZNK7oai7J46/pl"
    "G50rfYG9mXp4DcZ9DgTESsSWrgEwasI1CdLCW+983yAgj5LXxBAEda/3fr8o+pPHOgiZsBJVu9IzgDwfFtJKUPEdHhBXqIeJ5IXN"
    "dCHAbPYSCq44PhOBOEVeArCFGYfMQ4eVToRUDz+T7XwawMdfdEb3DSYonQd2/wTIG0gnPEAAF4QzhcIiDSlHeEZrxJGQ1/D/GrWp"
    "RIWjWTxFpCDOwEnwNzL5/wfrvt17z/IHhhVhuouqlq1PRMr9JpE3vC3b+UcAaVyw9tqWP5k3ksu/FSJnEfBy8hLlasjoWa0Ao3qh"
    "hp+3zAI+zrOGRRcKpImUp0AMMXk4GzwABN806vnvDE9sncoCC0GCvYQWF+jq1dQCJ0O1z32ySyEHY4OdV+n4vBdLaQDQ8Yq2m1RM"
    "2dLOp9kvfAVI8wHTFJ1NOaTT7D3SdIUZfP5o1s1vJexeRzQsCgJw02FvaUl2n9OfWf7TkXfYBUAooDUf84LCQvKbjyFxkAOBlkqc"
    "Zi8Bawqz9nDqUim1OXt5f2ty1dWk493EvndAA/2yHg4Gm8aP3R7aEo3AFmprX/NlYj5CnK3EBuGIPd/Z4Jd9ueVdkWI6hEYO7El0"
    "Oy+56gQmtYRIlgjwKgKOIRVjYh2WdSO6ZHQ0q6zTecSOCQBbhDizU4g2kdB9QrgLTu7vyy0bqPT9+ykOEvEido4ZwDj3tFUnep46"
    "RYRPA8krAfdSkJ5JygcRYbi3Vdw4zzqq/kIEYosQcb2A/BaguwR8Z//6Cx8ZCaUNs3RMwf4JG13nJledqXXi7WLzAaRKTxhBIEOf"
    "7ct9bEuVsRoEQI4/e2Xs+QLfDtZt1eeuwRL7TbDmi1s3XPS9A7ASksrvYt6SNW9VUIvFBS8GJEG7W3ciS+z5Ykv39W5Y/qmxjcTh"
    "es187XXz4jPmnAvY4wWITXtMhsSRbtLOFh/tX7/sK3u+15E9orR/HtngqAM2ukZkif0mZ4u39W1Y/v3dWwwOdYPVkIqGayzR7ZGn"
    "9MTzsR1HMxcXEvFLnJNjGPQiAQ4DIQGBTyQkgCGgCKFdjtBLQk+C8FcAf+QCPbb1gQt7x3xdqkeFzPVTzoQd8v0BGE95tpx+0wJS"
    "8WMh9qVgOkZEXsyQ+SDMAqgJECVCARGVIG4XSHpF1JMg+TOT+mOhJH/eed+FO/Z41v3JDH9QOYmH6n0drKzuh8bMrxeOwUqnGZtO"
    "qv28ISGqe8GsyWjy2sk6GMkuFX7mAaO8R5jkJ/VZw8nDaIebBoM8PrKsK0w2EfQ3gc+dHsdk4k5Mmdy56hpV27vRHgdQ83OmUmqt"
    "/25FJAe0VFj/BsJqyMghTHfR8Hyv0SSwe5RjRygN2I0U9mBCF9EzjL7/cQ/KOM/aDjc866whDWlIQxrSQOSNZ21IQxrSkIY0pCEN"
    "achBJ/8fET/gH0U/5A8AAAAASUVORK5CYII="
),
    "lcl": (
    "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"
    "2b1rG4ePPMU111zD3/rb/5SpiYSarrG+2mXfQ/t5//s/jBa1UEGKgqxvsG4wdlaiE0UtNdzx1tt5y1teS7MVY4VhebXLpz55D1+/"
    "Zx8njh1karrFWucQMzMpV2yZ4x++9d3ccOMNzG2aZXaTot2GkydPUU/qHH7mOF/6wr28748/RKebgUhRqkG73WN2fp7V5dOkKfzI"
    "j7yN17/m5QhbMDnR4r57H+Sv/uqv2PfwV/n7v/izvO6Nr2B2rsVkq8lEM8VbeOqpJT75mS/yhS/fw4MPPMDs7BVMtBbJsh5RVPKz"
    "f+/d3HbbbjwdksgzO69wOJzNmZiKede77+Ilt7wcJ5polfD1r93Ppz/zFbqdPsJYojgkkkO3P68r7ko08ni4PJHzIg3cLhkzIZAh"
    "Qg+NJDzejzlBOoF3Cu80+EAdj5QKQ91WU+YlkWzgjaXdK+h1C6z1ZHlGEqWgYGKqhcTRaDY5efIkAoP0PX78nW/hH/2TdzM7D70u"
    "NBrh45UFXHvdHEUBL3npPLfffg1/8Lsf433v+zBl3mZluUvhBFGzAYmgND1mprfwhjfuZWE2ENePndzEV791H3nRw/kE7yFNmggP"
    "vayLlII0lWzbOs1b3nI1M7PQL+GxJxybN81w8NBx+j1LUXZZ2DzNW99yI1vmq/69XeDzX/xTfvzdv8y7f+LusKkq0DGcOLmDVjPm"
    "qCmQyuFxYB1SSLxzCBRpLaFer1NkBluEfvP66jKNuuSVr7qRf/wrP8OuPWEjbncs9XpgfBsTE8Vw5TVXcfddV/GJV7+K33nPH/HA"
    "vv3UGpuIGw1OLa+T1mK8U8OA7AfmUMLh/ZkX/5hNYVXdZVmB1ppur00/z0nTkmMnTqOVZ34+4Zd/+Vd59R23smtXSlFAlkGSwMwk"
    "2EXFdddu5pW3v4Uffsdb+NVf/decPNrm+JEDLM7tYr3bIVISYwxa5Nz+suu4622LKAkHn57h+IkH+PEffz0/+uPv5Mpr5hjwpbSE"
    "LZunyPod6o2ZSjtfjuwth5HLIqUMELrMiaOcVjPh5IkV/v1v/K/c+caXsrAJlIbV9QDHL6awc+c011//em67dS//+T/9f6mlDld2"
    "0MQIQHuo6RTvJDqpk2eWWAbXtKLM2bV7K3fe+TJ+5mffSlSDielh5xdhYEYIdu9c4OrrF7j51lv4wz/+IB/58CdZb59mYfPOYPWi"
    "dWhDhKsQITay3v1AW30seA8g9PE4b6xltb1Ov5+xZct26s2wfpaW4Btf30c9naTVaFGPNEunj5JGjl/65Z/kp37qbiZmYHJmhNAY"
    "B7YAvSniyt1X8trXX8ntd9zMH/6Pv+QrX3qUXq9LFCtajSbXXXMlO3dKagnEGnbs2MZvvue3mJ3bQb3eDL0WYYhUjURFGFOj7LXR"
    "ac6tt+zizW/Zw8ws9Ao4eQJ++z1/RC3R6FpMp3MaQc5b3/xGfubvvptduxOEgJU1SGswNQnbts0jgD179vCqV+7h1Xe8hF/65X/J"
    "RGs71kmaaZ315VWatTpa9blqzzbe+cM7wYWj2u8e49Ofzvk3/+7XuOvtb2HrDjGQ86csIZLQnJzl6pf8EC+5cRvv/e2Sxx4+gZNT"
    "KA3t3hKvfMVLedMPXEGaUhECHZ6CSElkU3LVNdu5+iXbyU0gGZ46dRL5hRLns4CKy4jReOe4CczAXteCN5eD94u34q5mfcadgaoR"
    "IiUrolJ1H3TNA8zqBGjpUV5iC4MkYmpymqy/jHCCVmOStFYD6TAeut2cY8eOkec5otfDlD2u2Fbjf/vX/4pXv3YHpQkbf60e5mU7"
    "XWg2QhUUxSHobJ6HX/u1t3LjDVfwH/79b3HkcMHczBZWsy7rq2vUa5LSrtPp9Ym31cCEi1nJDCUNSTJJ1vfY0pFlGV54ZNUrLkwb"
    "Lwhwv4YkcZRFF2cyaq1ZTLmGKbvoGFQULt5Tx0/ysluv5Ed/+E20GiHgWQG9PiRSEVXwtAipM6pyRAumEILlpaUAk9ug3NXrt7n6"
    "qm380A/9GO98163MzkAvCyN305OKLINuzxJHCgOULpyyd7x9N9dc+f/kP/7H9/Cpz34DJxvU0njMrVOMPCQcVTBXw1MvzijlAtFN"
    "hyoLmJ2d5uTSCRpNTff0Gjt37eSf/9rP84bX70BW+V6ShJ+ygF4vJC/Gh/GXxS3w27/zv/BHv/fX/MZvvIflZUdjcgZnocwMea9N"
    "pEzQBgCmZzw3vHQb85u2c/0Nc4iqd2uqTc6UfbCV2p+Ih73E4az0gNdrDJYMQY9GQ1CWp/jN9/w6r7xjB2kaSJdKhzWHqBj1CmZn"
    "4VV3bEXLv8+ppaepJYJ6HGFxWCPQSlCWnlhL8rxLKQokPa7YvZmf+Zm/xVvv2kOUhO8vgHbfhrEyD85ZkjRhehpuf8Uku3b/T8xM"
    "pvzFX3ycLFtGqQbGGmLdGF6Kg+DtxUA8RgyD9pl9r+H/EY56vY6xKUrHdLo5n/jEAQQF7dU2T+w/yuL8NtrdPv3VFV5yww7e/rbX"
    "cfc7XsWWLdDpQ79H+B4mBKw0rkAbC1MT8M4ffQlXX7WH333vh/nEJ78CSB64/34+9rGP8Iu/9HaSWki0br4t4tWvvY19Dx3DlhlF"
    "ryStN6Bqp8RK47xg796tvPZ1L2V2foQqPP3UIR564H6mZ3bQrKXMTCf8s3/+/+KNb9pLswHtXlh3U1PQ6QX+Rr0W1mEjhXaZ8ba7"
    "r+OLt3yAX/0n/5b77z9ErTZJJFOKfI3WTES/c4r1VZiaBmdg+/Yav/arP8vtr3o5zcmAIOkoIBVKeJQSTDbDmrz7rltp1lL+23/9"
    "Mx55cDVov7sS6wryIoxVSkFIIqv2hpRB+KdXhmvYA6UvcS4EYilAKofxVRHl1VgQHxKULjskv3h73HKM3yCfHZKTIKVDaY+Owman"
    "CMzIWq2GVQJTlhS9ddrt0+zYMcvVV+8ljjVxBMZCp5dx/PhxlBIsnTrF5oU6//Jf/Bw33LA5EG0UJBpOnCg5dGiJleU2eZ6zeWGW"
    "3bsXaNSDl3QjhTvvvJZ68vP8vZ/73zh1wpJMTjM13SIvVsmzLkqVSFnDAqWxZHmbXr9N6lt4F+N9IGYJ5bDOkGU98BlRHAKNA/B9"
    "IuVRQhArDS68jhnAlxJmp6e5+213MzedcPxYsPFrdx1SSZZOrJP1HUrGOAdSeKQi9C1l6MHOTM9RliVSuso0xPCy26/nHT90K9Mz"
    "0M3CsV86bdh/4AAHDxymlxkW5rayuG0rV187hVLhRO3ZDW9/+50cOXGShx47ha5N46wEXw6htZEPQoWcsJHV7MTGtdHt9EjjhMNH"
    "DtKaanB66RBal/yTX/k57njVDqiIi+1Vw9HjKxw7dJpTSyskScTmhTn2XLmd+VSjYpidhJ/+uTdy7NQJPvmxz7OydpiJ6S2YMiLW"
    "nkYtIY4CAUs2NNdcvYvNC1dQlnDy9Cq9Xkak69SSCbRIqNeblX20Qwzhfl95UIfXqdVqrCwvMz2jWF46yP/yr36FN9y5g5WVUAlG"
    "GlZXHM8cPs6Bp58m6xcsLGxhz66rWNwEr3nNlRw5PE+tFlWvXmKtQnqIlKIoCpJI0O8v85Lrd/CTP3kXr3/THuI0JJ46gkcfOcGB"
    "g0+TZT3qacTM9CRbFxfYsXUe52B+Hn7xF38cpQR//McfotfrU6vNIIQPUKmsSHicQ1lLBOtVWU0dyDPEZNbbq8RJAjLmG/c+yH3f"
    "ugdnMhq1JmurGdaWzM5OY5M2L7v9et717lcxPQ1r656JScHaKnzpC4+xstqhLA1xJLnlpuvZvbtOux1y/d27a7zhztt4+OFHOXhw"
    "GVOUHNj/FEuncqYnE7IiHOs73/hKvvSl/5vm5AJJGlWjipLClOAdpuyxbeseNi00KcoCoSRlofnwhz/G7MxmWs0WyyvH+Hu/8A94"
    "2117MRbyPFyvR46UPHngEEun26ysrDDRirn++l1cvXczjbrGe8vsrOLv//xP8tP/878g79WoN2eC37ormJyoMTMThGmsL9i5c4G9"
    "e/ciCAjgyRMZhw4/RRQ7FjfPMT05RbMVE8XBhOkVr7ieJx47wdOPf5Ret8PkxCSHnjnKk09MInQfaS233rIb7zWlNfhScOL0CodO"
    "5Eg9iZQxnXafNGmQaYF3EmtthSRVKlcbWpnucp/7xR243YiqyjkGcyvo3HsFMgd64EucK3FYrM8RwlSKXCW9fkmz4bnt5Teze8/W"
    "UI0RBD8eemg//V4RnKfqih/5wTfz6lddy8RE+Jv1Vdh/YIU/ed9H+PBHvsCJEyvEcUyzGfOOt7+On3j329izaw4tPUlsufmWnfzD"
    "f/h3+e+//Re08zb1tEG/10HKlFarQbcLrQZI5anVEtI0JYoiBJKyzIN2c2GJE0kUK+qNmLLIyYuISEsEJf1eh6zfpywK4iii1ajT"
    "aAhUBEXmiHTE5rkFntpvuPe+h/nyV+7jqYNHmJmd5/TSKu01i1YNTCEhkkgtMS7DyzBGVBhDP8uAPvWa5bqXbudNb3sF84uhaq3V"
    "YN9DXX7vvX/Mhz78KbrrOZ6YNGqyuG2WX/vnP8073n4tumISv+y23Xzqc/N86d77WZxoUHoQqkDIcgj1+aFuSxoyeeFGwz0b5rQE"
    "k60pDpSrTE5N4m2GlAW/9Mt/lze/ZWeoUIEjJ3t87lP38Gd/9nG+8dV9rK71mZmdYnHLDK953S28/YffzO0v34UR4GL4Oz/3I3zr"
    "kfsoDq2z3m6jhEYrRVlYelX1pKOU7Tuu4NRJz/0PPMp93/wWjzz2GMtL60xPbmPpuEeqBkgRLCuFr2w23WikRgR4sl6vc+z4E/zC"
    "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"
),
}

BANK_LOGO_CACHE: dict[str, ImageReader] = {}

# Données Crédit Agricole et CIC communiquées en interne à la CMA.
# Elles doivent être confirmées par le conseiller bancaire professionnel
# avant toute décision ou contractualisation.
BANQUES_INCENDIES = [
    {
        "nom": "Crédit Agricole",
        "logo_key": "credit_agricole",
        "couleur": "#007A5E",
        "accent": "#00A0AF",
        "fond": "#EDF8F5",
        "bordure": "#9ED6C8",
        "mesures": [
            "Pause des crédits professionnels jusqu'à 12 mois.",
            "Prêt de trésorerie jusqu'à 50 000 € à taux préférentiel.",
            "Étude personnalisée selon la situation de l'entreprise.",
        ],
        "source": "Information interne CMA - à confirmer auprès du conseiller bancaire.",
        "url": "",
    },
    {
        "nom": "CIC",
        "logo_key": "cic",
        "couleur": "#1C2D8C",
        "accent": "#FF4A22",
        "fond": "#EEF1FB",
        "bordure": "#AEB9E8",
        "mesures": [
            "Report des loyers de crédit-bail jusqu'à 6 mois.",
            "Suspension ou report des échéances de crédit jusqu'à 6 mois.",
            "Prêt jusqu'à 50 000 € sur 60 mois à taux 0 %.",
        ],
        "source": "Information interne CMA - à confirmer auprès du conseiller bancaire.",
        "url": "",
    },
    {
        "nom": "Banque Populaire / Caisse d'Épargne",
        "logo_key": "bpce",
        "couleur": "#23365F",
        "accent": "#D71920",
        "fond": "#F0F3F8",
        "bordure": "#B9C3D3",
        "mesures": [
            "Prêt professionnel « urgence reprise » jusqu'à 15 000 € à 0 %.",
            "Durée de 3 à 5 ans, selon acceptation du dossier.",
            "Crédit-bail « urgence reprise » jusqu'à 15 000 € à conditions privilégiées.",
        ],
        "source": "Groupe BPCE - dispositif disponible dans certaines caisses régionales.",
        "url": BPCE_INCENDIES_URL,
    },
    {
        "nom": "La Banque Postale",
        "logo_key": "banque_postale",
        "couleur": "#204A9D",
        "accent": "#39A7E0",
        "fond": "#EDF5FC",
        "bordure": "#A8CEEA",
        "mesures": [
            "Report gratuit des échéances des professionnels jusqu'à 12 mois.",
            "Moratoire entreprises jusqu'à 6 mois lorsque cela est possible.",
            "Financements d'urgence et de reconstruction à conditions préférentielles.",
        ],
        "source": "Communiqué officiel La Banque Postale du 30 juillet 2026.",
        "url": LBP_INCENDIES_URL,
    },
    {
        "nom": "LCL",
        "logo_key": "lcl",
        "couleur": "#2E3182",
        "accent": "#FFD500",
        "fond": "#F1F1FA",
        "bordure": "#B9BBDF",
        "mesures": [
            "Report jusqu'à 12 mois des crédits professionnels et du crédit-bail.",
            "Crédit « Coup de Pouce » jusqu'à 10 000 €, ou 20 000 € si assuré dommages.",
            "Gestes tarifaires possibles, notamment sur les frais de compte et d'encaissement.",
        ],
        "source": "Communiqué officiel LCL du 27 juillet 2026.",
        "url": LCL_INCENDIES_URL,
    },
]

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
    "Banques / Trésorerie": {
        "icone": "🏦",
        "sous_titre": "Reports d'échéances et financements de reprise",
        "objectif": (
            "Préserver la trésorerie de l'entreprise en sollicitant rapidement "
            "les mesures exceptionnelles proposées par son établissement bancaire."
        ),
        "todo": [
            "Contacter sans délai le conseiller bancaire professionnel.",
            "Présenter l'impact de l'incendie sur l'activité et la trésorerie.",
            "Demander un report ou une suspension temporaire des échéances de crédit.",
            "Vérifier les possibilités de report des loyers de crédit-bail.",
            "Étudier un prêt de trésorerie ou un financement d'urgence.",
            "Demander si une facilité de caisse ou un découvert exceptionnel est possible.",
            "Obtenir une confirmation écrite des conditions proposées.",
        ],
        "documents": [
            "Dernier bilan ou dernière situation comptable disponible.",
            "Prévisionnel ou plan de trésorerie des prochaines semaines.",
            "Tableau des crédits professionnels et échéances à venir.",
            "Contrats de crédit-bail ou de location financière.",
            "Justificatif d'évacuation, déclaration de sinistre ou photos des dommages.",
            "Estimation des pertes d'activité et des dépenses urgentes.",
            "RIB et coordonnées de l'expert-comptable.",
        ],
        "vigilance": [
            "Les mesures varient selon les établissements, les caisses régionales et la situation du client.",
            "Les reports et financements restent soumis à l'étude et à l'acceptation du dossier.",
            "Un report peut modifier la durée ou le coût total du financement : demander un écrit détaillé.",
            "La liste présentée dans le PDF est non exhaustive et doit être confirmée avec le conseiller bancaire.",
        ],
        "contact": (
            "Conseiller bancaire professionnel ou directeur d'agence de l'entreprise."
        ),
        "source": (
            "Informations internes CMA et communiqués officiels des établissements bancaires, "
            "à confirmer lors de la demande."
        ),
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
    treasury_risk = bool(situation.get("tresorerie_fragile"))

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

    # Banque / trésorerie : présélection explicite si le dirigeant anticipe
    # une insuffisance de trésorerie dans les prochaines semaines.
    if treasury_risk:
        recommended.add("Banques / Trésorerie")

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
            str(bool(situation.get("tresorerie_fragile"))),
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
    pdf.setFillColor(HexColor("#EEF3F8"))
    pdf.setStrokeColor(HexColor("#C7D5E4"))
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


def get_bank_logo_reader(logo_key: str) -> ImageReader | None:
    """Décode et met en cache un logo bancaire intégré dans app.py."""
    if logo_key in BANK_LOGO_CACHE:
        return BANK_LOGO_CACHE[logo_key]

    encoded = BANK_LOGOS_B64.get(logo_key)
    if not encoded:
        return None

    reader = ImageReader(io.BytesIO(base64.b64decode(encoded)))
    BANK_LOGO_CACHE[logo_key] = reader
    return reader


def draw_image_contain(
    pdf: canvas.Canvas,
    image: ImageReader,
    x: float,
    y: float,
    width: float,
    height: float,
    padding: float = 4,
) -> None:
    """Dessine une image sans déformation, centrée dans son cadre."""
    img_w, img_h = image.getSize()
    available_w = max(1, width - 2 * padding)
    available_h = max(1, height - 2 * padding)
    scale = min(available_w / img_w, available_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale
    draw_x = x + (width - draw_w) / 2
    draw_y = y + (height - draw_h) / 2
    pdf.drawImage(
        image,
        draw_x,
        draw_y,
        width=draw_w,
        height=draw_h,
        preserveAspectRatio=True,
        mask="auto",
    )


def draw_bank_logo_header(
    pdf: canvas.Canvas,
    bank: dict[str, Any],
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    """En-tête de carte avec le véritable logo et les couleurs de la banque."""
    main = HexColor(bank["couleur"])
    accent = HexColor(bank["accent"])

    pdf.setFillColor(white)
    pdf.roundRect(x, y, width, height, 7, stroke=0, fill=1)

    # Liseré de marque.
    pdf.setFillColor(main)
    pdf.roundRect(x, y, 6, height, 3, stroke=0, fill=1)
    pdf.setFillColor(accent)
    pdf.rect(x + 6, y + height - 4, width - 6, 4, stroke=0, fill=1)

    logo = get_bank_logo_reader(bank["logo_key"])
    if logo is not None:
        draw_image_contain(pdf, logo, x + 10, y + 5, width - 18, height - 10, padding=2)
    else:
        pdf.setFillColor(main)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(x + width / 2, y + height / 2 - 3, bank["nom"])


def draw_bank_card(
    pdf: canvas.Canvas,
    bank: dict[str, Any],
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    """Carte bancaire harmonisée avec la charte du logo."""
    main = HexColor(bank["couleur"])
    background = HexColor(bank["fond"])
    border = HexColor(bank["bordure"])

    pdf.setFillColor(background)
    pdf.setStrokeColor(border)
    pdf.roundRect(x, y, width, height, 9, stroke=1, fill=1)

    # Accent latéral.
    pdf.setFillColor(main)
    pdf.roundRect(x, y, 5, height, 3, stroke=0, fill=1)

    header_h = 43
    draw_bank_logo_header(
        pdf,
        bank,
        x + 9,
        y + height - header_h - 8,
        width - 18,
        header_h,
    )

    current_y = y + height - header_h - 22
    for measure in bank["mesures"]:
        pdf.setFillColor(main)
        pdf.circle(x + 17, current_y + 2, 1.9, stroke=0, fill=1)
        current_y = draw_wrapped(
            pdf,
            measure,
            x + 25,
            current_y,
            width - 38,
            font_size=7.15,
            leading=8.35,
            max_lines=3,
            color="#263445",
        ) - 4.5

    # Source sur bandeau clair en pied de carte.
    pdf.setFillColor(white)
    pdf.roundRect(x + 8, y + 7, width - 16, 20, 5, stroke=0, fill=1)
    draw_wrapped(
        pdf,
        bank["source"],
        x + 13,
        y + 20,
        width - 26,
        font_name="Helvetica-Oblique",
        font_size=5.55,
        leading=6.3,
        max_lines=2,
        color="#657486",
    )

    if bank.get("url"):
        pdf.linkURL(
            bank["url"],
            (x, y, x + width, y + height),
            relative=0,
            thickness=0,
        )


def draw_bank_page(
    pdf: canvas.Canvas,
    page_number: int,
) -> None:
    """Plaquette bancaire dédiée en A4 portrait."""
    page_w, page_h = A4
    margin = 28
    content_w = page_w - 2 * margin

    # En-tête CMA.
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.rect(0, page_h - 86, page_w, 86, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.rect(0, page_h - 7, page_w, 7, stroke=0, fill=1)
    draw_logo_or_fallback(pdf, page_w - 168, page_h - 73, 132, 42)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawString(margin, page_h - 38, "Banques & trésorerie")
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(HexColor("#D7E1ED"))
    pdf.drawString(
        margin,
        page_h - 57,
        "Solutions à étudier rapidement avec votre conseiller bancaire professionnel",
    )

    # Intro.
    intro_top = page_h - 103
    pdf.setFillColor(HexColor("#EEF3F8"))
    pdf.roundRect(margin, intro_top - 50, content_w, 50, 8, stroke=0, fill=1)
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(margin + 12, intro_top - 18, "RÉFLEXE PRIORITAIRE")
    draw_wrapped(
        pdf,
        (
            "Contactez rapidement votre conseiller bancaire professionnel pour étudier "
            "un report d'échéances, une suspension de crédit-bail, un financement "
            "d'urgence ou une facilité de caisse."
        ),
        margin + 115,
        intro_top - 18,
        content_w - 130,
        font_size=8.2,
        leading=9.6,
        max_lines=3,
    )

    # Cartes banques : 2 colonnes.
    gap = 12
    card_w = (content_w - gap) / 2
    card_h = 145
    start_y = intro_top - 70

    positions = [
        (margin, start_y - card_h),
        (margin + card_w + gap, start_y - card_h),
        (margin, start_y - card_h * 2 - gap),
        (margin + card_w + gap, start_y - card_h * 2 - gap),
        (margin, start_y - card_h * 3 - gap * 2),
    ]

    for bank, (x, y) in zip(BANQUES_INCENDIES, positions):
        draw_bank_card(pdf, bank, x, y, card_w, card_h)

    # Carte finale : points à demander.
    x = margin + card_w + gap
    y = start_y - card_h * 3 - gap * 2
    pdf.setFillColor(HexColor("#FFF7E8"))
    pdf.setStrokeColor(HexColor("#F0D7A5"))
    pdf.roundRect(x, y, card_w, card_h, 9, stroke=1, fill=1)
    pdf.setFillColor(HexColor(CMA_BLUE))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(x + 12, y + card_h - 22, "À DEMANDER AU CONSEILLER")
    requests = [
        "Report ou suspension des échéances",
        "Crédit-bail : report des loyers",
        "Prêt de trésorerie d'urgence",
        "Facilité de caisse ou découvert temporaire",
        "Écrit précisant durée, coût et conditions",
    ]
    yy = y + card_h - 42
    for item in requests:
        pdf.acroForm.checkbox(
            name=f"bank_request_{page_number}_{yy:.0f}",
            x=x + 12,
            y=yy - 2,
            size=8,
            borderWidth=1,
            borderColor=HexColor(CMA_BLUE),
            fillColor=white,
            textColor=HexColor(CMA_BLUE),
            checked=False,
            buttonStyle="check",
            forceBorder=True,
        )
        draw_wrapped(
            pdf,
            item,
            x + 25,
            yy + 3,
            card_w - 37,
            font_size=7.2,
            leading=8.2,
            max_lines=2,
        )
        yy -= 18

    # Avertissement.
    warning_y = 42
    pdf.setFillColor(HexColor("#FDECEE"))
    pdf.setStrokeColor(HexColor("#F4C1C6"))
    pdf.roundRect(margin, warning_y, content_w, 47, 7, stroke=1, fill=1)
    pdf.setFillColor(HexColor(CMA_RED))
    pdf.setFont("Helvetica-Bold", 8.4)
    pdf.drawString(margin + 12, warning_y + 31, "IMPORTANT - LISTE NON EXHAUSTIVE")
    draw_wrapped(
        pdf,
        (
            "Les offres peuvent varier selon les établissements, les caisses régionales "
            "et la situation de l'entreprise. Elles restent soumises à l'étude et à "
            "l'acceptation du dossier. Rapprochez-vous impérativement de votre conseiller "
            "bancaire professionnel pour confirmer les mesures applicables."
        ),
        margin + 12,
        warning_y + 18,
        content_w - 24,
        font_size=6.8,
        leading=7.8,
        max_lines=3,
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
        if nom == "Banques / Trésorerie":
            draw_bank_page(pdf, page_number)
            pdf.showPage()
            page_number += 1
            continue

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

tresorerie_fragile = st.toggle(
    "La trésorerie risque-t-elle d'être insuffisante dans les prochaines semaines ?",
    value=False,
    help=(
        "Cette réponse présélectionne la fiche Banques / Trésorerie. "
        "Le conseiller reste libre de la retirer."
    ),
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
    "tresorerie_fragile": tresorerie_fragile,
    "causes_arret": causes_arret,
}

if tresorerie_fragile:
    st.info(
        "La fiche Banques / Trésorerie a été recommandée. Le PDF présentera "
        "les principales mesures annoncées et les documents à préparer."
    )

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

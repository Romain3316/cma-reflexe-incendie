# PASS CMA Liberté — Simulateur conseiller V1

Application indépendante. Aucun changement de l'application incendies.

## Démarrer

Python 3.11 recommandé.

```bash
pip install -r pass-cma/requirements.txt
streamlit run pass-cma/app.py
```

## Streamlit Community Cloud

Créer une nouvelle app depuis le dépôt `Romain3316/cma-reflexe-incendie`, branche `codex/pass-cma-simulateur-v1`, fichier principal `pass-cma/app.py`. Le requirements.txt du dossier contient les dépendances. Configurer l'accès privé pour l'équipe depuis l'hébergement : l'application n'intègre pas d'authentification.

## Calcul

- Comparaison sur 12 mois, HT ou TTC (TVA 20 % sur conseil, formalités et abonnement). La récupération partielle n'est pas gérée.
- Conseil 79 € HT/h ; seules les heures nécessaires sont valorisées, maximum 2 h couvertes.
- Formalités tarifées selon EI/micro ou société ; maximum 2 affectées explicitement au PASS. Les suivantes restent payantes. Frais légaux exclus des deux colonnes.
- Formation : reste à charge et réduction journalière saisis dans la base choisie. Aucune conversion implicite du plafond de 70 €. Réduction limitée au reste à charge, sous validation du service formation. Pour des journées avec des restes à charge différents, réaliser des simulations distinctes (V1 homogène par simulation).
- Deux mois offerts uniquement sur confirmation d'éligibilité à la souscription avec assistance CMA à l'immatriculation. Pas de cumul parrainage dans cette V1.
- Grille publique relevée le 06/11/2026 dans tariffs.json, à valider en interne. Sources visibles dans l'application. Conseil confirmé par Romain : 79 € HT/h.
- Le PDF est débloqué après validation conseiller. Les droits restants ne gonflent pas les économies.
- Aucune donnée client enregistrée sur disque ou dans GitHub par l'app, PDF généré en mémoire. Pas d'envoi email automatique.

## Contrôles

```bash
cd pass-cma
python -m unittest -v
```

Le module de calcul utilise Decimal. Tests du cas micro (-8,56 €), plafonds, gratuité et PDF. Test interactif local effectué avec Streamlit AppTest. Grille et présentation à valider avant diffusion commerciale. Le nom CMA est utilisé en texte ; aucun logo reconstitué.

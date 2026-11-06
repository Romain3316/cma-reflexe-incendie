from decimal import Decimal, ROUND_HALF_UP

def money(value):
    value = Decimal(str(value))
    if not value.is_finite() or value < 0:
        raise ValueError('Montant invalide')
    return value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

def calculate(formalities, hours=0, days=0, rac=0, eligible=False, cap=70, basis='TTC', free=False):
    if basis not in ('HT', 'TTC') or not 0 <= hours <= 20 or not 0 <= days <= 100:
        raise ValueError('Paramètres invalides')
    if sum(bool(f['covered']) for f in formalities) > 2:
        raise ValueError('Deux formalités maximum peuvent être affectées au PASS.')
    factor = Decimal('1.2') if basis == 'TTC' else Decimal(1)
    rows=[]
    for f in formalities:
        price=money(money(f['ht'])*factor)
        rows.append((f['label'],price,Decimal(0) if f['covered'] else price))
    advice=money(Decimal(str(hours))*79*factor)
    advice_after=money(Decimal(str(max(0,hours-2)))*79*factor)
    rows.append((f'Conseil personnalisé : {hours:g} h',advice,advice_after))
    training=money(Decimal(str(days))*money(rac))
    saving=money(Decimal(str(days))*min(money(rac),money(cap))) if eligible else Decimal(0)
    rows.append((f'Formation : {days:g} jours',training,training-saving))
    sub=money(Decimal('24.90')*factor*(10 if free else 12))
    rows.append(('Abonnement PASS - 12 mois',Decimal(0),sub))
    before=sum(r[1] for r in rows); after=sum(r[2] for r in rows)
    return dict(rows=rows,before=before,after=after,gain=before-after,subscription=sub,remaining_formalities=2-sum(bool(f['covered']) for f in formalities),remaining_hours=max(0,2-hours))

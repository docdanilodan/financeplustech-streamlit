def to_float(value):
    try:
        return float(str(value).replace('EUR', '').replace('€', '').replace('.', '').replace(',', '.').strip())
    except Exception:
        return 0.0


def calcola_score_da_indicatori(ricavi, mol, utile, cash_flow, indice_indebitamento):
    score = 50
    if to_float(ricavi) >= 1_000_000:
        score += 10
    if to_float(mol) > 0:
        score += 10
    if to_float(utile) > 0:
        score += 10
    if to_float(cash_flow) > 0:
        score += 10
    indeb = to_float(indice_indebitamento)
    if 0 < indeb <= 3:
        score += 10
    elif indeb > 5:
        score -= 10
    score = max(0, min(100, score))
    if score >= 80:
        return score, 'A - Buono', 'Verde', round(score * 2500, 2)
    if score >= 60:
        return score, 'B - Medio', 'Giallo', round(score * 2500, 2)
    return score, 'C - Critico', 'Rosso', round(score * 2500, 2)


def valutazione_base(score, rating, rischio, fido):
    return f'Score FinancePlusTech: {score}/100. Rating: {rating}. Semaforo: {rischio}. Fido stimato: EUR {fido:,.2f}. Suggerimenti: rafforzare patrimonio netto, migliorare liquidita e ridurre passivita a breve.'

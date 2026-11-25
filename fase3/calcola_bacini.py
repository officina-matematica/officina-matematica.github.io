"""Fase 3 interattiva: punteggio di difficolta', livelli e bacini di esercizi.

Legge soltanto: esercizi/*_contenuti.json, esercizi/*_fase3.json,
schede_fase3/<codice>_fase3.json (solo per le attivita' da scheda),
tassonomia.yaml e la copia del foglio Argomenti. Scrive solo in fase3/:
    bacini_proposta.csv    gli esercizi proposti, livello per livello
    punteggi_tutti.csv     tutti gli esercizi col loro punteggio e livello
    RIEPILOGO.md           numeri per attivita', casi dubbi, codici che non tornano
    anteprima_bacini.html  le consegne disegnate, tre colonne per attivita'

Uso (dalla cartella principale):  python fase3/calcola_bacini.py

PUNTEGGIO. Ogni ingrediente diventa la posizione in classifica dentro
l'attivita' (0 = il valore piu' basso, 1 = il piu' alto, pari merito = stessa
posizione). Il punteggio, su 100, e':
    50% passaggi  +  25% regole diverse  +  15% parentesi annidate  +  10% lunghezza
LIVELLI: la classifica dell'attivita' tagliata in tre parti uguali, salvo le
attivita' in FASCE, dove il tipo di esercizio decide a quali livelli puo' stare.
BACINO: livello 3 senza esercizi-maratona (oltre il 90° percentile dei
passaggi E oltre 12 passaggi), passaggi che crescono da un livello all'altro,
nessun doppione fra attivita' (la consegna resta nell'attivita' che viene
prima, salvo le eccezioni in TIENE_DOPPIONE).
SCHEDE DI FASE 3: le attivita' le cui guide hanno origine "scheda fase 3"
non passano da punteggio e filtri. Il bacino e' la scheda intera, ogni
esercizio col livello scritto in schede_fase3/<codice>_fase3.json.

Prova a secco di una scheda (non scrive niente, non servono le guide):
    python fase3/calcola_bacini.py --prova schede_fase3/<codice>_fase3.json
"""

import csv
import html
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
ESERCIZI = RADICE / "esercizi"
USCITA = RADICE / "fase3"
FOGLIO_ARGOMENTI = RADICE.parent / "OM_DASHBOARD" / "test" / "dati" / "argomenti.csv"

PESI = {"passaggi": 0.50, "regole": 0.25, "annidamento": 0.15, "lunghezza": 0.10}
ESCLUSE = {"gon"}          # eserciziario aperto: cresce a ogni invio
SCARTA_FILE = ("prima_del_riordino", "riserva")
PERCENTILE_MARATONA = 0.90
# un esercizio e' una maratona solo se supera il 90° percentile della sua
# attivita' E anche questo numero di passaggi (decisione di Simone, 22/11/2026)
PASSAGGI_MARATONA = 12
# doppioni fra attivita': di norma la consegna resta nell'attivita' che viene
# prima; qui l'attivita' indicata la tiene comunque (Simone, 22/11/2026: le 11
# espressioni di P4 restano a P4 e si tolgono da P3)
TIENE_DOPPIONE = {frozenset({"p3", "p4"}): "p4"}
# livello 1 scritto apposta per la fase 3 (Simone, 22/11/2026): queste guide
# sono il livello 1; il livello 1 di prima diventa il 2; il 2 e il 3 di prima
# si fondono nel 3
L1_SCRITTO = {
    "neg5": ["neg5_34", "neg5_35", "neg5_36"],
    "odx1": ["odx1_8", "odx1_9", "odx1_10"],
    "odx2": ["odx2_7", "odx2_8", "odx2_9"],
    "of4": ["of4_52", "of4_53", "of4_54"],
    "p4": ["p4_12", "p4_13", "p4_14"],
    "log7": ["log7_7", "log7_8", "log7_9"],
    "log8": ["log8_6", "log8_7", "log8_8"],
}
PARTE_L1_SCRITTO = "Fase 3 · livello 1 scritto apposta"

# schede di fase 3 (dal progetto Claude): il livello lo decide la scheda
SCHEDE = RADICE / "schede_fase3"
ORIGINE_SCHEDA = "scheda fase 3"
PARTE_SCHEDA = "Scheda fase 3 · livello {}"
CAMPI_SCHEDA = ("n_scheda", "livello", "consegna_label", "consegna_tex", "consegna_sympy",
                "risultato_tex", "risultato_sympy")


def leggi_scheda(file):
    """(codice in minuscolo, esercizi, problemi) di un file <codice>_fase3.json."""
    dati = json.loads(Path(file).read_text(encoding="utf-8"))
    cod = str(dati.get("codice", "")).lower()
    esercizi = dati.get("esercizi") or []
    problemi = []
    if Path(file).name != f"{cod}_fase3.json":
        problemi.append(f"il codice {dati.get('codice')!r} non corrisponde al nome del file")
    numeri = []
    for i, e in enumerate(esercizi, start=1):
        manca = [k for k in CAMPI_SCHEDA if k not in e]
        if manca:
            problemi.append(f"esercizio {i}: mancano {', '.join(manca)}")
        if not isinstance(e.get("n_scheda"), int) or not 1 <= e["n_scheda"] <= 21:
            problemi.append(f"esercizio {i}: n_scheda deve essere un numero da 1 a 21")
        if e.get("livello") not in (1, 2, 3):
            problemi.append(f"esercizio {i}: livello deve essere 1, 2 o 3")
        numeri.append(e.get("n_scheda"))
    doppi = sorted({n for n in numeri if numeri.count(n) > 1 and n is not None})
    if doppi:
        problemi.append(f"n_scheda ripetuti: {doppi}")
    per_livello = Counter(e.get("livello") for e in esercizi)
    if len(esercizi) != 21 or any(per_livello[L] != 7 for L in (1, 2, 3)):
        problemi.append(f"{len(esercizi)} esercizi, per livello "
                        f"{per_livello[1]} / {per_livello[2]} / {per_livello[3]}: "
                        "una scheda completa ne ha 21, sette per livello")
    return cod, esercizi, problemi


def livelli_scheda(cod):
    """{id guida: livello} dalla scheda dell'attivita', o None se manca."""
    f = SCHEDE / f"{cod}_fase3.json"
    if not f.exists():
        return None
    _, esercizi, _ = leggi_scheda(f)
    return {f"{cod}_{e['n_scheda']}": e["livello"] for e in esercizi}


def punti(p):
    """Il punteggio come lo scrive il CSV: vuoto per gli esercizi di una scheda."""
    return "" if p is None else str(p).replace(".", ",")


# ------------------------------------------------- progressione per tipo
# Dove il punteggio non basta (guide che citano molte regole per conti
# semplici, esercizi dello stesso tipo a pari punteggio), e' il tipo di
# esercizio a dire a quali livelli puo' stare. Il primo criterio che vale
# decide. Dentro un gruppo con piu' livelli, il gruppo si divide in parti
# uguali secondo il punteggio (o secondo la "chiave" indicata).

def _parte(*prefissi):
    return lambda e: e["parte"].startswith(prefissi)


def _ids(*ii):
    return lambda e: e["id"] in ii


def _tutti(e):
    return True


def _numeri(e):
    m = re.search(r"numeri\s+([\d,\s]+)", e["tex"])
    return [int(x) for x in re.findall(r"\d+", m.group(1))] if m else []


FASCE = {
    # PR4: riconoscere il tipo -> 1; una proporzione semplice, diretta o
    # inversa -> 1 o 2; dividere in due parti, il rettangolo con due domande -> 2;
    # problemi composti (operai e giorni insieme), divisione in tre parti o con
    # un passo in piu', percentuale all'indietro -> 3
    "pr4": [(lambda e: e["label"].startswith("Stabilisci"), (1,)),
            (_ids("pr4_34", "pr4_39", "pr4_27", "pr4_30", "pr4_31", "pr4_40", "pr4_38"), (3,)),
            (_ids("pr4_24", "pr4_25", "pr4_26", "pr4_28", "pr4_29", "pr4_32"), (2,)),
            (_tutti, (1, 2))],
    # MP6: somma per differenza -> 1; quadrato -> 1 o 2; cubo -> 2; espressioni -> 3
    "mp6": [(_parte("Parte 2"), (1,)), (_parte("Parte 1"), (1, 2)),
            (_parte("Parte 3"), (2,)), (_parte("Parte 4"), (3,))],
    # P3: le semplificazioni brevi scritte per la fase 3 -> 1; le espressioni -> 2 o 3
    "p3": [(_parte("Fase 3"), (1,)), (_tutti, (2, 3))],
    # LOG1: quando il risultato e' una radice (log_x 64 = 5) non e' livello 1
    "log1": [(lambda e: r"\sqrt" in e["ris"], (2, 3)), (_tutti, (1, 2, 3))],
    # NEG6: potenze, proprieta', scrivere in notazione scientifica e tornare
    # indietro -> 1 o 2; calcolare in notazione e trovare l'errore -> 2;
    # espressioni e problemi di realta' -> 3
    "neg6": [(_parte("Parte 1", "Parte 2", "Parte 4", "Parte 5"), (1, 2)),
             (_parte("Parte 6", "Parte 7"), (2,)),
             (_parte("Parte 3", "Parte 8"), (3,))],
    # MCD e mcm: due numeri piccoli -> 1, due numeri piu' grandi -> 2, tre numeri -> 3
    "fmdc2": [(lambda e: len(_numeri(e)) >= 3, (3,)),
              (_tutti, (1, 2), lambda e: max(_numeri(e)))],
    "fmdc3": [(lambda e: len(_numeri(e)) >= 3, (3,)),
              (_tutti, (1, 2), lambda e: max(_numeri(e)))],
    # OF2: i prodotti che si semplificano subito -> 1; completare l'uguaglianza
    # (si ragiona all'indietro, ma la guida e' breve) -> 2; i prodotti con un
    # intero da trasformare o quattro fattori da semplificare in croce -> 3.
    # (Tre fattori -> 1, quattro -> 2, completa -> 3 metteva al livello 1
    # guide piu' lunghe di quelle del livello 2.)
    "of2": [(_parte("Parte 2"), (2,)), (_ids("of2_3", "of2_4"), (1,)), (_tutti, (3,))],
}


# ------------------------------------------------ livello 1 da scrivere apposta
# Proposte per le attivita' in cui anche il livello 1 e' lungo: consegna piu'
# corta, una sola parentesi. NON sono guide: le decide Simone. Risultati
# controllati con SymPy (vedi controlla_proposte in fondo).
# Le proposte del 22/11 (NEG5, ODX1, ODX2, OF4, P4, LOG7, LOG8) sono diventate
# guide vere: stanno in L1_SCRITTO. Qui restano solo eventuali proposte nuove.
PROPOSTE_L1 = {}


# ---------------------------------------------------------------- ingredienti

def nomi_regole(g):
    nomi = []
    for r in g["righe"]:
        t = r.get("tendina") or {}
        teoria = t.get("teoria") or []
        # una tendina puo' richiamare piu' regole insieme: allora e' una lista
        for te in (teoria if isinstance(teoria, list) else [teoria]):
            nome = (te or {}).get("nome")
            if nome:
                nomi.append(re.sub(r"\s+", " ", nome.strip()))
    # distinte, ignorando maiuscole: «Potenza di potenza» = «potenza di potenza»
    viste, uniche = set(), []
    for n in nomi:
        if n.lower() not in viste:
            viste.add(n.lower())
            uniche.append(n)
    return uniche


def passaggi(g):
    # la prima riga riscrive la consegna: i passaggi sono le righe dopo
    return max(1, len(g["righe"]) - 1)


def parti_matematiche(tex):
    """Il LaTeX su cui contare parentesi e lunghezza. Nelle consegne in prosa
    contano solo le formule tra $...$; il disegno SVG non conta."""
    tex = re.sub(r"<svg.*?</svg>", " ", tex, flags=re.S)
    tex = re.sub(r"<[^>]+>", " ", tex)
    if "$" in tex:
        formule = re.findall(r"\$([^$]*)\$", tex)
        testo = re.sub(r"\$[^$]*\$", " ", tex)
        return " ".join(formule), testo
    return tex, ""


def annidamento(tex):
    mat, _ = parti_matematiche(tex)
    mat = re.sub(r"\\(left|right|big|Big|bigg|Bigg)\b", "", mat)
    mat = mat.replace(r"\lbrace", r"\{").replace(r"\rbrace", r"\}")
    prof = massimo = 0
    for m in re.finditer(r"\\\{|\\\}|[(\[]|[)\]]", mat):
        s = m.group(0)
        if s in ("(", "[", r"\{"):
            prof += 1
            massimo = max(massimo, prof)
        else:
            prof = max(0, prof - 1)
    return massimo


FORMATO = {r"\left", r"\right", r"\displaystyle", r"\,", r"\;", r"\!", r"\quad",
           r"\qquad", r"\text", r"\mathrm", r"\big", r"\Big"}


def lunghezza(tex):
    """Simboli visibili: numeri, lettere, operatori, comandi come \\frac.
    Nella prosa ogni parola vale un simbolo."""
    mat, testo = parti_matematiche(tex)
    simboli = [t for t in re.findall(r"\\[a-zA-Z]+|\\.|[0-9]+(?:[.,{][0-9]+)?|[a-zA-Z]|[^\s{}]", mat)
               if t not in FORMATO]
    return len(simboli) + len(re.findall(r"[A-Za-zÀ-ÿ0-9]+", testo))


def posizioni(valori):
    """Posizione in classifica da 0 a 1, i pari merito con la media."""
    n = len(valori)
    if n == 1:
        return [0.5]
    ordine = sorted(range(n), key=lambda i: valori[i])
    rango = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and valori[ordine[j + 1]] == valori[ordine[i]]:
            j += 1
        medio = (i + j) / 2
        for k in range(i, j + 1):
            rango[ordine[k]] = medio
        i = j + 1
    if len(set(valori)) == 1:
        return [0.5] * n
    return [r / (n - 1) for r in rango]


# ---------------------------------------------------------------------- parti

def parte_da_etichetta(label):
    label = re.sub(r"\s+(per|di)\s+\$.*$", "", label).strip()
    return label.rstrip(":").strip()


def assegna_parti(guide, extra):
    """La sezione del foglio (scritta sulla prima guida della sezione e valida
    fino alla successiva); senza sezioni, l'etichetta della consegna."""
    ha_sezioni = any(g.get("sezione") for g in guide)
    # gli esercizi dei file *_fase3.json stanno in coda, dopo l'ultima sezione,
    # ma non ne fanno parte: hanno una parte loro (per MP2 quella del foglio)
    nome_parte_f3 = {}
    for g in guide:
        p = extra.get(g["id"], {}).get("parte")
        if p is not None:
            nome_parte_f3.setdefault(p, parte_da_etichetta(g["consegna_label"]))
    corrente = None
    for g in guide:
        if g.get("sezione"):
            corrente = g["sezione"].strip()
        if g["id"] in extra:
            p = extra[g["id"]].get("parte")
            g["_parte"] = (f"Fase 3, parte {p} · {nome_parte_f3[p]}" if p is not None
                           else f'Fase 3 · {parte_da_etichetta(g["consegna_label"])}')
        elif ha_sezioni and corrente:
            g["_parte"] = corrente
        else:
            g["_parte"] = parte_da_etichetta(g["consegna_label"])


# ------------------------------------------------------------------ selezione

def scegli(candidati, k, parti_gia_usate):
    """Scelta golosa: a ogni giro prende l'esercizio che porta una parte nuova,
    poi regole nuove, poi un tipo di consegna nuovo; a parita', quello piu'
    vicino al centro del livello. Cosi' il bacino e' vario e non pesca solo
    dagli estremi."""
    if not candidati:
        return []
    punti = sorted(c["punteggio"] for c in candidati)
    centro = punti[len(punti) // 2]
    scelti, parti, regole, etichette = [], Counter(), set(), set()
    resto = list(candidati)
    while resto and len(scelti) < k:
        def merito(c):
            nuova_parte = parti[c["parte"]] == 0
            mai_usata = c["parte"] not in parti_gia_usate
            regole_nuove = len({r.lower() for r in c["nomi"]} - regole)
            etichetta_nuova = parte_da_etichetta(c["label"]) not in etichette
            return (-parti[c["parte"]], nuova_parte and mai_usata, regole_nuove,
                    etichetta_nuova, -abs(c["punteggio"] - centro), -c["ordine"])
        migliore = max(resto, key=merito)
        resto.remove(migliore)
        scelti.append(migliore)
        parti[migliore["parte"]] += 1
        regole |= {r.lower() for r in migliore["nomi"]}
        etichette.add(parte_da_etichetta(migliore["label"]))
    return sorted(scelti, key=lambda c: c["ordine"])


# ------------------------------------------------------------------- lettura

def carica():
    base = yaml.safe_load((RADICE / "tassonomia.yaml").read_text(encoding="utf-8"))
    titoli = {a["codice"].lower(): a["titolo"]
              for arg in base["argomenti"] for a in arg["attivita"]}
    # l'ordine delle attivita' nel percorso: decide chi tiene un doppione
    ordine = {a["codice"].lower(): i for i, a in
              enumerate(a for arg in base["argomenti"] for a in arg["attivita"])}
    sito = base["sito"]["github_pages"].rstrip("/")

    attivita = {}
    for f in sorted(ESERCIZI.glob("*_contenuti.json")):
        if any(s in f.name for s in SCARTA_FILE):
            continue
        cod = f.name.replace("_contenuti.json", "")
        attivita[cod] = json.loads(f.read_text(encoding="utf-8"))["guide"]

    fase3 = {}
    for f in sorted(ESERCIZI.glob("*_fase3.json")):
        cod = f.name.replace("_fase3.json", "")
        for e in json.loads(f.read_text(encoding="utf-8"))["esercizi"]:
            fase3[e["id"]] = dict(e, _attivita=cod)
    return attivita, fase3, titoli, ordine, sito


def firma(label, tex):
    """La consegna ridotta all'osso, per riconoscere i doppioni: stessa
    etichetta e stessa formula, a meno di spazi e \\left/\\right."""
    t = re.sub(r"\\(left|right|displaystyle|,|;|!)", "", tex).replace(r"\dfrac", r"\frac")
    return (label.strip().lower(), re.sub(r"\s+", "", t))


def mediana(v):
    v = sorted(v)
    if not v:
        return 0
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def percentile(v, q):
    """Percentile «al rango più vicino»: il valore sotto cui sta la quota q."""
    v = sorted(v)
    return v[max(0, math.ceil(q * len(v)) - 1)] if v else 0


def assegna_livelli(ex, cod):
    """Senza FASCE: la classifica in tre parti uguali. Con FASCE: ogni gruppo
    di esercizi va nei livelli che il suo tipo ammette, diviso in parti uguali."""
    regole = FASCE.get(cod, [(_tutti, (1, 2, 3))])
    gruppi = defaultdict(list)
    for e in ex:
        for r in regole:
            if r[0](e):
                e["ammessi"] = r[1]
                chiave = r[2] if len(r) > 2 else None
                gruppi[(r[1], id(r))].append((e, chiave))
                break
        else:
            e["ammessi"] = (1, 2, 3)
            gruppi[((1, 2, 3), 0)].append((e, None))
    for (livelli, _), membri in gruppi.items():
        def chiave(m):
            e, k = m
            base = (e["punteggio"], e["passaggi"], e["regole"], e["lunghezza"], -e["ordine"])
            return ((k(e),) + base) if k else base
        membri.sort(key=chiave)
        n = len(membri)
        for i, (e, _) in enumerate(membri):
            e["livello"] = livelli[(len(livelli) * i) // n]


def sistema_coerenza(scelta, cand, cod, dubbi):
    """Mediana dei passaggi crescente da 1 a 3, e nessun esercizio di livello 1
    oltre la mediana del livello 2. Si scambia solo con esercizi dello stesso
    livello, cosi' la progressione per tipo resta com'e'."""
    scambi = []

    def p(L):
        return [e["passaggi"] for e in scelta[L]]

    def sostituisci(L, vecchio, filtro, preferisci):
        liberi = [c for c in cand[L] if c not in scelta[L] and filtro(c)]
        if not liberi:
            return False
        nuovo = max(liberi, key=lambda c: (c["parte"] == vecchio["parte"],
                                           c["parte"] not in {x["parte"] for x in scelta[L]},
                                           preferisci(c), -c["ordine"]))
        scelta[L][scelta[L].index(vecchio)] = nuovo
        scambi.append(f"liv. {L}: {vecchio['id']} ({vecchio['passaggi']} pass.) → "
                      f"{nuovo['id']} ({nuovo['passaggi']} pass.)")
        return True

    # si ripete finche' non cambia piu' niente: uno scambio fra i livelli 2 e 3
    # puo' abbassare la mediana del livello 2 e rimettere in gioco il livello 1
    avvisi = {}
    for _giro in range(6):
        prima = len(scambi)
        avvisi = {}
        # 1. livello 1: niente oltre la mediana del livello 2
        if scelta[1] and scelta[2]:
            tetto = mediana(p(2))
            for e in sorted(scelta[1], key=lambda e: -e["passaggi"]):
                if e["passaggi"] > tetto and not sostituisci(
                        1, e, lambda c: c["passaggi"] <= tetto, lambda c: -c["passaggi"]):
                    avvisi[e["id"]] = (
                        f"{e['id']} (liv. 1) ha {e['passaggi']} passaggi, più della mediana "
                        f"del livello 2 ({tetto:g}), e al livello 1 non c'è un esercizio più "
                        "corto con cui scambiarlo")

        # 2. mediane crescenti: prima si accorcia il livello basso, poi si allunga l'alto
        for basso, alto in ((1, 2), (2, 3)):
            for _ in range(12):
                if not scelta[basso] or not scelta[alto] or mediana(p(basso)) < mediana(p(alto)):
                    break
                lungo = max(scelta[basso], key=lambda e: e["passaggi"])
                corto = min(scelta[alto], key=lambda e: e["passaggi"])
                if sostituisci(basso, lungo, lambda c: c["passaggi"] < lungo["passaggi"],
                               lambda c: -c["passaggi"]):
                    continue
                if sostituisci(alto, corto, lambda c: c["passaggi"] > corto["passaggi"],
                               lambda c: c["passaggi"]):
                    continue
                break
            if scelta[basso] and scelta[alto] and mediana(p(basso)) >= mediana(p(alto)):
                avvisi[basso] = (
                    f"la mediana dei passaggi non cresce dal livello {basso} "
                    f"({mediana(p(basso)):g}) al livello {alto} ({mediana(p(alto)):g}) "
                    "e con gli esercizi disponibili non si può sistemare"
                    + (": qui conta il tipo di esercizio, non la lunghezza"
                       if cod in FASCE else ""))
        if len(scambi) == prima:
            break
    dubbi.extend(avvisi.values())
    if scambi:
        dubbi.append("scambi per la coerenza fra livelli: " + "; ".join(scambi))
    for L in scelta:
        scelta[L].sort(key=lambda c: c["ordine"])


def main():
    attivita, fase3, titoli, ordine, sito = carica()
    righe_tutte, bacini, note, conteggi = [], {}, {}, {}

    # gli esercizi dei file *_fase3.json che non sono nei contenuti
    for i, e in fase3.items():
        if i not in {g["id"] for g in attivita.get(e["_attivita"], [])}:
            note.setdefault(e["_attivita"], []).append(
                f"{i} sta in {e['_attivita']}_fase3.json ma non ha la guida nei contenuti: escluso")

    # --- 1. ingredienti e punteggio, attivita' per attivita'
    escluse_build, tutti, schede = [], {}, set()
    for cod, guide in attivita.items():
        if cod in ESCLUSE:
            continue
        # solo le guide finite: il file sta nella cartella principale
        pronte = []
        for g in guide:
            if (RADICE / f'{g["id"]}.html').exists():
                pronte.append(g)
            else:
                escluse_build.append(g["id"])
        assegna_parti(pronte, fase3)
        ex = []
        for n, g in enumerate(pronte):
            nomi = nomi_regole(g)
            ex.append({
                "id": g["id"], "cod": cod, "ordine": n, "label": g["consegna_label"],
                "tex": g["consegna_tex"], "ris": g.get("risultato_tex", ""),
                "prosa": bool(g.get("consegna_prosa")) or g.get("tipo") == "problema",
                "tipo": g.get("tipo", ""), "parte": g["_parte"], "nomi": nomi,
                "passaggi": passaggi(g), "regole": len(nomi),
                "annidamento": annidamento(g["consegna_tex"]),
                "lunghezza": lunghezza(g["consegna_tex"]),
                "metodi": sum(1 for r in g["righe"] if r.get("metodo")),
                "figura": "<svg" in g["consegna_tex"],
                "fase3": g["id"] in fase3, "doppione": None,
            })
        if any(g.get("origine") == ORIGINE_SCHEDA for g in pronte):
            # scheda di fase 3: livello dalla scheda, niente punteggio
            livelli = livelli_scheda(cod)
            if livelli is None:
                print(f"  ! {cod.upper()}: guide da scheda di fase 3, ma manca "
                      f"schede_fase3/{cod}_fase3.json: attivita' esclusa")
                continue
            fuori = [e["id"] for e in ex if e["id"] not in livelli]
            if fuori:
                print(f"  ! {cod.upper()}: guide che non sono nella scheda, escluse: "
                      + ", ".join(fuori))
            ex = [e for e in ex if e["id"] in livelli]
            for e in ex:
                e["punteggio"], e["livello"] = None, livelli[e["id"]]
                e["ammessi"], e["parte"] = (e["livello"],), PARTE_SCHEDA.format(e["livello"])
            schede.add(cod)
            tutti[cod] = ex
            continue
        pos = {k: posizioni([e[k] for e in ex]) for k in PESI}
        for i, e in enumerate(ex):
            e["punteggio"] = round(100 * sum(PESI[k] * pos[k][i] for k in PESI), 1)
        assegna_livelli(ex, cod)
        if cod in L1_SCRITTO:
            # i livelli di prima si calcolano sugli esercizi di prima, poi
            # scalano di uno; le guide nuove sono il livello 1
            nuovi = set(L1_SCRITTO[cod])
            vecchi = [e for e in ex if e["id"] not in nuovi]
            assegna_livelli(vecchi, cod)
            for e in vecchi:
                e["livello"] = {1: 2, 2: 3, 3: 3}[e["livello"]]
            for e in ex:
                if e["id"] in nuovi:
                    e["livello"], e["ammessi"], e["parte"] = 1, (1,), PARTE_L1_SCRITTO
        tutti[cod] = ex

    # --- 2. doppioni: la consegna resta nell'attivita' che viene prima nel percorso
    # (le schede di fase 3 ne restano fuori: niente filtri, e non tolgono
    # niente alle altre attivita')
    per_firma = defaultdict(list)
    for cod, ex in tutti.items():
        if cod in schede:
            continue
        for e in ex:
            per_firma[firma(e["label"], e["tex"])].append(e)
    doppioni = []
    for gruppo in per_firma.values():
        if len(gruppo) < 2:
            continue
        gruppo.sort(key=lambda e: (ordine.get(e["cod"], 999), e["ordine"]))
        tiene = gruppo[0]
        chi = TIENE_DOPPIONE.get(frozenset(e["cod"] for e in gruppo))
        if chi:
            tiene = next(e for e in gruppo if e["cod"] == chi)
        gruppo = [tiene] + [e for e in gruppo if e is not tiene]
        for e in gruppo[1:]:
            e["doppione"] = tiene["id"]
            doppioni.append((e, tiene))

    # --- 3. bacini
    for cod, ex in tutti.items():
        dubbi = note.setdefault(cod, [])
        n = len(ex)
        per_livello = {L: [e for e in ex if e["livello"] == L] for L in (1, 2, 3)}
        if cod in schede:
            # il bacino e' la scheda intera, livello per livello
            bacini[cod] = per_livello
            conteggi[cod] = {"n": n, "k": None, "livelli": {L: len(per_livello[L]) for L in (1, 2, 3)},
                             "parti": Counter(e["parte"] for e in ex), "maratona": None,
                             "mediane": {L: mediana([e["passaggi"] for e in per_livello[L]])
                                         for L in (1, 2, 3)},
                             "doppioni": 0,
                             "l1": mediana([e["passaggi"] for e in per_livello[1]])}
            righe_tutte.extend((cod.upper(), e) for e in ex)
            continue
        k = 5 if n >= 15 else 3
        p90 = percentile([e["passaggi"] for e in ex], PERCENTILE_MARATONA)
        maratona = max(p90, PASSAGGI_MARATONA)

        cand = {}
        for L in (1, 2, 3):
            c = [e for e in per_livello[L] if not e["doppione"]]
            if L == 3:
                lunghi = [e for e in c if e["passaggi"] > maratona]
                if lunghi:
                    dubbi.append(f"fuori dal livello 3 perché oltre il 90° percentile dei "
                                 f"passaggi ({p90}) e oltre {PASSAGGI_MARATONA} passaggi: "
                                 + ", ".join(f"{e['id']} ({e['passaggi']})" for e in lunghi))
                c = [e for e in c if e["passaggi"] <= maratona]
                buoni = [e for e in c if e["regole"] >= 2]
                if len(buoni) < min(k, len(c)):
                    dubbi.append(
                        f"livello 3: solo {len(buoni)} esercizi su {len(c)} usano almeno due "
                        "regole diverse"
                        + ("" if buoni else ": il livello 3 resta vuoto, va deciso a mano"))
                c = buoni
            cand[L] = c

        usate, scelta = set(), {}
        for L in (3, 1, 2):          # il 3 per primo: e' quello col vincolo
            scelta[L] = scegli(cand[L], min(k, len(cand[L])), usate)
            usate |= {e["parte"] for e in scelta[L]}
        sistema_coerenza(scelta, cand, cod, dubbi)

        bacini[cod] = scelta
        conteggi[cod] = {"n": n, "k": k, "livelli": {L: len(per_livello[L]) for L in (1, 2, 3)},
                         "parti": Counter(e["parte"] for e in ex), "maratona": maratona,
                         "mediane": {L: mediana([e["passaggi"] for e in scelta[L]])
                                     for L in (1, 2, 3)},
                         "doppioni": sum(1 for e in ex if e["doppione"]),
                         "l1": mediana([e["passaggi"] for e in (scelta[1] or per_livello[1])])}

        # casi dubbi
        if conteggi[cod]["doppioni"] == n:
            dubbi.insert(0, f"**tutte le {n} consegne sono doppioni** di un'attività che viene "
                            "prima: il bacino resta vuoto finché non si decide (vedi «Doppioni»)")
        tutte_parti = set(conteggi[cod]["parti"])
        coperte = {e["parte"] for L in scelta for e in scelta[L]}
        if len(tutte_parti) > 1 and tutte_parti - coperte:
            dubbi.append("parti senza nessun esercizio nel bacino: "
                         + "; ".join(sorted(tutte_parti - coperte)))
        if max(e["regole"] for e in ex) <= 1:
            dubbi.append("nessun esercizio usa piu' di una regola: la difficolta' la fanno "
                         "solo i passaggi e la lunghezza")
        corti = [L for L in (1, 2, 3) if 0 < len(scelta[L]) < 3]
        if corti:
            dubbi.append("attività piccola: " + ", ".join(
                f"il livello {L} ha {len(scelta[L])} "
                + ("esercizio" if len(scelta[L]) == 1 else "esercizi") for L in corti)
                + ". Chi resta su quel livello rivede presto lo stesso esercizio: "
                "servono esercizi nuovi o un bacino unico per più livelli")
        nel_bacino = [(L, e) for L in (1, 2, 3) for e in scelta[L]]
        metodi = [f"{e['id']} (liv. {L})" for L, e in nel_bacino if e["metodi"] >= 2]
        figure = [f"{e['id']} (liv. {L})" for L, e in nel_bacino if e["figura"]]
        aperti = [f"{e['id']} (liv. {L})" for L, e in nel_bacino if e["tipo"] == "aperto"]
        if metodi:
            dubbi.append("guide con due metodi uno dopo l'altro, quindi passaggi contati due "
                         "volte e punteggio un po' gonfiato: " + ", ".join(metodi))
        if figure:
            dubbi.append("consegna con un disegno, che la fase 3 deve mostrare insieme al "
                         "testo: " + ", ".join(figure))
        if aperti:
            dubbi.append("risposta da spiegare a parole o da scrivere liberamente, "
                         "l'autovalutazione è meno netta: " + ", ".join(aperti))
        if cod not in FASCE:
            classifica = sorted(ex, key=lambda e: (e["punteggio"], e["passaggi"], e["regole"],
                                                   e["lunghezza"], -e["ordine"]))
            spezzati = [f"{a['id']}/{b['id']} ({a['livello']}|{b['livello']})"
                        for a, b in zip(classifica, classifica[1:])
                        if a["livello"] != b["livello"] and a["punteggio"] == b["punteggio"]]
            if spezzati:
                dubbi.append("stesso punteggio ma livelli diversi (il taglio li separa per "
                             "passaggi e lunghezza; si possono scambiare): " + ", ".join(spezzati))

        for e in ex:
            righe_tutte.append((cod.upper(), e))

    scrivi_csv(bacini)
    scrivi_tutti(righe_tutte)
    scrivi_riepilogo(attivita, bacini, conteggi, note, titoli, escluse_build, fase3, doppioni,
                     schede)
    scrivi_anteprima(bacini, conteggi, titoli, sito)
    print(f"Attivita' con bacino: {len(bacini)}")
    for cod in bacini:
        m = conteggi[cod]["mediane"]
        print(f"  {cod.upper():6} {conteggi[cod]['n']:4} esercizi  ->  "
              + "  ".join(f"L{L}:{len(bacini[cod][L])}" for L in (1, 2, 3))
              + f"   mediane passaggi {m[1]} / {m[2]} / {m[3]}")


# ------------------------------------------------------------------ scrittura

COLONNE = ["codice attività", "livello", "id esercizio", "punteggio", "passaggi",
           "regole", "parte", "consegna in LaTeX"]


def scrivi_csv(bacini):
    with open(USCITA / "bacini_proposta.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(COLONNE)
        for cod, scelta in bacini.items():
            for L in (1, 2, 3):
                for e in scelta[L]:
                    w.writerow([cod.upper(), L, e["id"], punti(e["punteggio"]),
                                e["passaggi"], e["regole"], e["parte"], e["tex"]])


def scrivi_tutti(righe):
    with open(USCITA / "punteggi_tutti.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codice attività", "id esercizio", "livello", "punteggio", "passaggi",
                    "regole", "annidamento", "lunghezza", "parte", "nomi delle regole",
                    "consegna in LaTeX"])
        for cod, e in sorted(righe, key=lambda r: (r[0], r[1]["ordine"])):
            w.writerow([cod, e["id"], e["livello"], punti(e["punteggio"]),
                        e["passaggi"], e["regole"], e["annidamento"], e["lunghezza"],
                        e["parte"], " | ".join(e["nomi"]), e["tex"]])


def foglio_argomenti():
    if not FOGLIO_ARGOMENTI.exists():
        return None
    with open(FOGLIO_ARGOMENTI, encoding="utf-8") as f:
        r = list(csv.reader(f))
    return {row[1].strip(): (row[0].strip(), row[2].strip()) for row in r[1:] if len(row) > 2}


def scrivi_riepilogo(attivita, bacini, conteggi, note, titoli, escluse_build, fase3, doppioni,
                     schede=()):
    out = ["# Fase 3 — proposta dei bacini", "",
           "Proposta da controllare: nessuna guida, nessun file di contenuto, nessun prompt "
           "è stato modificato. I file sono in `fase3/`:", "",
           "- `bacini_proposta.csv` — gli esercizi proposti, per attività e livello "
           "(separatore `;`, si apre con Excel)",
           "- `punteggi_tutti.csv` — tutti gli esercizi con punteggio e livello, per "
           "sostituire a mano un esercizio del bacino",
           "- `anteprima_bacini.html` — le consegne disegnate, tre colonne per attività",
           "- `calcola_bacini.py` — lo script che rifà tutto: `python fase3/calcola_bacini.py`",
           "", "## Come è calcolato il punteggio", "",
           "Per ogni esercizio si contano quattro cose: i **passaggi** (le righe della guida "
           "dopo la consegna), le **regole diverse** (i nomi distinti nelle tendine «Regola»), "
           "la **profondità delle parentesi** della consegna e la sua **lunghezza** (simboli "
           "della formula, parole nei problemi).",
           "Dentro ogni attività ciascuna quantità diventa una posizione in classifica da 0 a 1; "
           "il punteggio (su 100) è **50% passaggi + 25% regole + 15% parentesi + 10% lunghezza**. "
           "Le regole pesano meno di prima (erano al 35%) perché alcune guide citano molte regole "
           "anche per conti semplici.",
           "", "**Livelli**: la classifica dell'attività divisa in tre parti con lo stesso numero "
           "di esercizi (1 = il terzo più facile, 3 = il più complesso).",
           "", "**Progressione per tipo** — in alcune attività il punteggio non basta, e decide "
           "il tipo di esercizio (dentro un tipo che può stare su due livelli, si divide a metà "
           "secondo il punteggio):", "",
           "- **PR4**: riconoscere se la proporzionalità è diretta o inversa → 1; un problema "
           "con una sola proporzione, diretta o inversa → 1 o 2; dividere in due parti secondo "
           "un rapporto, e il rettangolo con due domande → 2; problemi composti (operai *e* "
           "giorni), divisioni in tre parti o con un passo in più, percentuale all'indietro → 3.",
           "- **MP6**: somma per differenza → 1; quadrato di binomio → 1 o 2; cubo → 2; "
           "espressioni → 3.",
           "- **P3**: le semplificazioni brevi scritte per la fase 3 → 1; le espressioni → 2 o 3.",
           "- **LOG1**: gli esercizi che hanno una radice come risultato (come log1_93, "
           "$\\log_x 64=5$) non stanno al livello 1.",
           "- **NEG6**: potenze con esponente negativo, proprietà, scrivere in notazione "
           "scientifica e tornare al numero → 1 o 2; calcolare in notazione scientifica e "
           "trovare l'errore → 2; espressioni e problemi di realtà → 3.",
           "- **FMDC2, FMDC3**: due numeri piccoli → 1; due numeri più grandi → 2; tre numeri → 3.",
           "- **NEG5, ODX1, ODX2, OF4, P4, LOG7, LOG8**: il livello 1 sono le tre guide "
           "scritte per la fase 3; il livello 1 di prima è il 2; il 2 e il 3 di prima sono il 3.",
           "- **OF2**: i prodotti che si semplificano subito (of2_3, of2_4) → 1; completare "
           "l'uguaglianza → 2; i prodotti con un intero da trasformare o con quattro fattori "
           "(of2_1, of2_2, of2_5) → 3 (confermato da Simone il 22/11).",
           ] + ([
           "- **" + ", ".join(c.upper() for c in sorted(schede)) + "**: schede di fase 3. "
           "Il bacino è la scheda intera, ogni esercizio con il livello della scheda "
           "(`schede_fase3/<codice>_fase3.json`): niente punteggio, niente filtri, niente "
           "controllo dei doppioni."] if schede else []) + [
           "", "**Bacino**: 5 esercizi per livello (3 se l'attività ha meno di 15 esercizi). "
           "Lo script sceglie prima esercizi di parti diverse dell'attività, poi esercizi che "
           "portano regole nuove, poi tipi di consegna diversi; a parità, quelli vicini al centro "
           "del livello. Poi tre filtri:", "",
           "- **livello 3 senza maratone**: fuori gli esercizi che superano *sia* il 90° "
           "percentile dei passaggi della loro attività *sia* i 12 passaggi (restano nei "
           "punteggi, non nel bacino), e dentro solo esercizi con almeno due regole diverse;",
           "- **coerenza fra livelli**: la mediana dei passaggi deve crescere dal livello 1 al 3, "
           "e nessun esercizio del livello 1 può avere più passaggi della mediana del livello 2. "
           "Dove non succede, lo script scambia con un altro esercizio *dello stesso livello* "
           "(così la progressione per tipo resta) e lo scrive nei casi dubbi;",
           "- **doppioni**: una consegna presente in due attività resta solo in quella che "
           "viene prima nel percorso, tranne P3/P4: lì resta a P4.",
           "", "## Cosa è stato escluso", "",
           "- **GON — Eserciziario**: escluso perché è aperto (si allunga a ogni invio di "
           "esercizi). Ha 9 guide: un bacino andrebbe fatto quando l'eserciziario sarà fermo.",
           "- `of2/of3/of4_prima_del_riordino.json` e `of4_riserva_contenuti.json` "
           "(le 33 espressioni di riserva di OF4, of4_19 … of4_51).",
           ]
    if escluse_build:
        out.append("- Guide senza file nella cartella principale: " + ", ".join(escluse_build))
    else:
        out.append("- Guide rimaste in `build/`: nessuna da escludere. In `build/` c'è "
                   "`mp6_17.html`, ma la guida mp6_17 è anche nella cartella principale "
                   "(rifatta nell'ultimo commit): è quella che conta.")
    n_f3 = Counter(e["_attivita"] for e in fase3.values())
    scelti_f3 = Counter(e["id"].rsplit("_", 1)[0] for s in bacini.values()
                        for L in s for e in s[L] if e["fase3"])
    out += ["", "**Esercizi dei file `*_fase3.json`**: sono già dentro i contenuti delle "
            "rispettive attività (stessi id, guide pubblicate), quindi concorrono come gli "
            "altri. " + "; ".join(f"{c.upper()}: {n_f3[c]} esercizi, {scelti_f3.get(c, 0)} "
                                   f"entrati nel bacino" for c in sorted(n_f3)) + ".",
            "", "## Attività per attività", "",
            "Passaggi: la mediana dei passaggi degli esercizi del bacino, livello per livello. "
            "Soglia: oltre questo numero di passaggi un esercizio non entra nel livello 3 (il "
            "più grande fra il 90° percentile dell'attività e 12).", "",
            "| Attività | Esercizi | Liv. 1 / 2 / 3 | Bacino 1 / 2 / 3 | Passaggi 1 / 2 / 3 "
            "| Soglia | Parti |",
            "|---|---:|---|---|---|---:|---:|"]
    for cod, s in bacini.items():
        c = conteggi[cod]
        lv, m = c["livelli"], c["mediane"]
        med = " / ".join(f"{m[L]:g}" if s[L] else "—" for L in (1, 2, 3))
        out.append(f"| {cod.upper()} — {titoli.get(cod, '')} | {c['n']} | "
                   f"{lv[1]} / {lv[2]} / {lv[3]} | "
                   f"{len(s[1])} / {len(s[2])} / {len(s[3])} | {med} | "
                   f"{'—' if c['maratona'] is None else c['maratona']} | "
                   f"{len(c['parti'])} |")

    # --- doppioni
    out += ["", "## Doppioni fra attività", "",
            "La stessa consegna (stessa etichetta, stessa formula) sta in due attività. "
            "Resta nel bacino solo dell'attività che viene prima nel percorso; nell'altra conta "
            "nei punteggi ma non entra nel bacino. Eccezione decisa da Simone il 22/11: le 11 "
            "espressioni comuni a P3 e P4 restano a P4 e si tolgono da P3, che fa il bacino "
            "con le altre.", ""]
    per_att = defaultdict(list)
    for e, tiene in doppioni:
        per_att[e["cod"]].append((e, tiene))
    for cod in sorted(per_att, key=lambda c: c):
        coppie = sorted(per_att[cod], key=lambda x: x[0]["ordine"])
        out.append(f"- **{cod.upper()}** (tolti dal bacino): " + ", ".join(
            f"{e['id']} = {t['id']}" for e, t in coppie))

    # --- livello 1 scritto per la fase 3
    out += ["", "## Livello 1 scritto per la fase 3", "",
            "In queste sette attività anche il livello 1 superava i 6 passaggi. Il 22/11 Simone "
            "ha approvato tre consegne corte per ciascuna (una sola parentesi), e sono diventate "
            "guide con il procedimento di sempre (prompt, `verifica.py`, validatore "
            "indipendente), con origine «scritto per la fase 3». Nei bacini **le guide nuove "
            "sono il livello 1, il livello 1 di prima è diventato il 2, il 2 e il 3 di prima si "
            "sono fusi nel 3** (scelti con la stessa soglia dei passaggi).", ""]
    for cod in L1_SCRITTO:
        if cod not in bacini:
            continue
        out.append(f"**{cod.upper()} — {titoli.get(cod, '')}**")
        out.append("")
        for e in bacini[cod][1]:
            out.append(f"- {e['id']}: ${e['tex']}$ → ${e['ris']}$ ({e['passaggi']} passaggi)")
        out.append("")
    lunghe = [cod for cod in bacini if conteggi[cod]["l1"] > 6 and cod not in L1_SCRITTO
              and cod not in schede]
    if lunghe:
        out += ["## Livello 1 non basico", "",
                "Attività in cui il livello 1 supera ancora i 6 passaggi: "
                + ", ".join(c.upper() for c in lunghe) + ".", ""]

    out += ["## Casi dubbi", ""]
    for cod in bacini:
        d = note.get(cod) or []
        if d:
            out.append(f"**{cod.upper()}**")
            out += [f"- {x}" for x in d]
            out.append("")
    if not any(note.get(c) for c in bacini):
        out.append("Nessuno.")

    out += ["## Codici delle guide e foglio Argomenti", ""]
    foglio = foglio_argomenti()
    if foglio is None:
        out.append(f"Copia del foglio Argomenti non trovata in `{FOGLIO_ARGOMENTI}`.")
    else:
        out += ["Confronto fatto con la copia del foglio usata dalla dashboard "
                "(`OM_DASHBOARD/test/dati/argomenti.csv`, del 18/11/2026): se nel frattempo "
                "il foglio è cambiato, il confronto va rifatto.", "",
                "| Codice guide | Nel foglio Argomenti | Cosa non torna |", "|---|---|---|"]
        for cod in sorted(attivita):
            C = cod.upper()
            tit = titoli.get(cod, "")
            if C in foglio:
                arg, t_foglio = foglio[C]
                if t_foglio.strip().lower() != tit.strip().lower():
                    out.append(f"| {C} — {tit} | {C} — {t_foglio or '(senza titolo)'} "
                               f"({arg}) | titolo diverso |")
            else:
                simili = [k for k in foglio if re.sub(r"[^A-Z]", "", k) == re.sub(r"[^A-Z]", "", C)]
                out.append(f"| {C} — {tit} | — | codice assente; nel foglio ci sono: "
                           f"{', '.join(simili) or 'nessun codice simile'} |")
        out += ["", "Da guardare con attenzione:", "",
                "- **GON**: le guide usano un solo codice (`gon_1`, `gon_2`, …) per tutto "
                "l'eserciziario; il foglio ha **GON1** e **GON2**, senza titolo. Va deciso a "
                "quale attività appartiene l'eserciziario (o se va diviso).",
                "- **LOG1, LOG2**: il codice c'è, ma nel foglio LOG1 è «Crescita esponenziale» e "
                "LOG2 «La funzione esponenziale», mentre le guide sono *Calcolo logaritmi* e "
                "*Proprietà dei logaritmi*: lo stesso codice indica contenuti diversi.",
                "- **LOG7**: nel foglio è scritto **«LOG7ù»** (refuso, la dashboard lo scarta "
                "come riga anomala). **LOG8** nel foglio non c'è. LOG5 e LOG6 sono nel foglio "
                "senza argomento.",
                "- **SCO1**: il codice c'è, ma nel foglio SCO1 è «Raccoglimento totale e parziale» "
                "(argomento SCO | Scomposizioni), mentre in `tassonomia.yaml` è «Scomposizioni in "
                "fattori» sotto CLE | Calcolo letterale. Le 17 guide mescolano raccoglimento, "
                "prodotti notevoli e trinomio speciale, cioè anche SCO2 e SCO3 del foglio.",
                "- Gli altri sono solo differenze di titolo (P2, P3, F1, OF5, NEG6): stesso "
                "contenuto, parole diverse.", ""]
    (USCITA / "RIEPILOGO.md").write_text("\n".join(out), encoding="utf-8")


def consegna_html(e):
    tex = e["tex"]
    if e["prosa"]:
        corpo = re.sub(r"\$[^$]*\$", lambda m: m.group(0).replace("<", "&lt;"), tex)
        return f'<div class="m prosa">{corpo}</div>'
    return f'<div class="m">$\\displaystyle {html.escape(tex, quote=False)}$</div>'


def scrivi_anteprima(bacini, conteggi, titoli, sito):
    sez = []
    indice = []
    for cod, s in bacini.items():
        C = cod.upper()
        indice.append(f'<a href="#{cod}">{C}</a>')
        colonne = []
        for L, nome in ((1, "Livello 1 · facile"), (2, "Livello 2 · medio"), (3, "Livello 3 · complesso")):
            schede = []
            for e in s[L]:
                url = f"{sito}/{e['id']}.html"
                regole = html.escape(", ".join(e["nomi"])) or "—"
                parte = ("" if e["parte"] == parte_da_etichetta(e["label"])
                         else f'<div class="parte">{html.escape(e["parte"])}</div>')
                schede.append(f"""
      <article class="scheda">
        <header><a href="{url}" target="_blank" rel="noopener">{e['id']}</a>
          <span class="dati" title="punteggio · passaggi · regole">{punti(e['punteggio']) or 'scheda'} · {e['passaggi']} pass. · {e['regole']} reg.</span></header>
        {parte}
        <div class="consegna">
          <div class="t">📌 {e['label']}</div>
          {consegna_html(e)}
        </div>
        <details><summary>Regole</summary><p>{regole}</p></details>
      </article>""")
            if L == 1 and conteggi[cod]["l1"] > 6 and cod not in L1_SCRITTO:
                for tex, ris, perche in PROPOSTE_L1.get(cod, []):
                    schede.append(f"""
      <article class="scheda proposta">
        <header><span class="tag">proposta da scrivere</span>
          <span class="dati">risultato ${ris}$</span></header>
        <div class="consegna">
          <div class="m">$\\displaystyle {html.escape(tex, quote=False)}$</div>
        </div>
        <p class="perche">{perche}</p>
      </article>""")
            vuoto = '<p class="vuoto">Nessun esercizio: da decidere a mano.</p>' if not schede else ""
            colonne.append(f'<div class="col"><h3 class="l{L}">{nome}</h3>{"".join(schede)}{vuoto}</div>')
        c = conteggi[cod]
        avviso = (f'<p class="avviso">Tutte le {c["n"]} consegne sono uguali a esercizi di '
                  "un'attività che viene prima (P3): il bacino è vuoto finché non decidi. "
                  "Le strade sono nel riepilogo, alla voce «Doppioni».</p>"
                  if c["doppioni"] == c["n"] else "")
        sez.append(f"""
  <section id="{cod}">
    <h2>{C} — {html.escape(titoli.get(cod, ''))}</h2>
    {avviso}
    <p class="sotto">{c['n']} esercizi · per livello {c['livelli'][1]} / {c['livelli'][2]} / {c['livelli'][3]} · {len(c['parti'])} {'parte' if len(c['parti']) == 1 else 'parti'}</p>
    <div class="griglia">{''.join(colonne)}</div>
  </section>""")

    pagina = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bacini fase 3</title>
<script>
MathJax = {{
  loader: {{ load: ['[tex]/cancel'] }},
  tex: {{ packages: {{ '[+]': ['cancel'] }}, inlineMath: [['$','$']], displayMath: [['$$','$$']], processEscapes: true }},
  svg: {{ fontCache: 'global', scale: 1.06, exFactor: .5 }},
  options: {{ enableMenu: false }}
}};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-svg.js"></script>
<style>
:root{{
  --ink:#0f172a; --body:#334155; --muted:#475569; --line:#e2e8f0; --paper:#f8fafc;
  --blu:#12519e; --blubg:#e8f1fb; --blubd:#a8c9ea; --card:#ffffff;
  --l1:#15803d; --l2:#b45309; --l3:#9f1239;
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{
    --ink:#e2e8f0; --body:#cbd5e1; --muted:#94a3b8; --line:#334155; --paper:#0f172a;
    --blu:#93c5fd; --blubg:#172554; --blubd:#1e40af; --card:#1e293b;
    --l1:#4ade80; --l2:#fbbf24; --l3:#fb7185;
  }}
}}
:root[data-theme="dark"]{{
  --ink:#e2e8f0; --body:#cbd5e1; --muted:#94a3b8; --line:#334155; --paper:#0f172a;
  --blu:#93c5fd; --blubg:#172554; --blubd:#1e40af; --card:#1e293b;
  --l1:#4ade80; --l2:#fbbf24; --l3:#fb7185;
}}
*{{box-sizing:border-box}}
body{{margin:0;padding:24px 16px 60px;background:var(--paper);color:var(--body);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.45}}
h1{{color:var(--ink);font-size:24px;margin:0 0 6px}}
.intro{{max-width:900px;margin:0 0 14px}}
nav{{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 24px}}
nav a{{font-size:13px;padding:3px 9px;border:1px solid var(--line);border-radius:999px;
  color:var(--blu);text-decoration:none;background:var(--card)}}
section{{margin:0 0 40px;scroll-margin-top:12px}}
h2{{color:var(--ink);font-size:20px;margin:0}}
.sotto{{margin:2px 0 12px;color:var(--muted);font-size:14px}}
.griglia{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}
@media (max-width:900px){{.griglia{{grid-template-columns:1fr}}}}
h3{{font-size:14px;text-transform:uppercase;letter-spacing:.05em;margin:0 0 8px;
  padding-bottom:4px;border-bottom:3px solid currentColor}}
h3.l1{{color:var(--l1)}} h3.l2{{color:var(--l2)}} h3.l3{{color:var(--l3)}}
.scheda{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:0 0 12px}}
.scheda header{{display:flex;justify-content:space-between;gap:8px;align-items:baseline;flex-wrap:wrap}}
.scheda header a{{font-weight:600;color:var(--blu)}}
.dati{{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}}
.parte{{font-size:12px;color:var(--muted);margin:2px 0 8px}}
.consegna{{background:var(--blubg);border:1px solid var(--blubd);border-radius:10px;padding:10px 12px;color:var(--ink)}}
.consegna .t{{font-size:13px;font-weight:600;color:var(--blu);margin:0 0 6px}}
.scheda header + .consegna{{margin-top:8px}}
.consegna .m{{overflow-x:auto;overflow-y:hidden;text-align:center;padding:2px 0}}
.consegna .m.prosa{{text-align:left;font-size:15px}}
details{{margin-top:6px;font-size:12px;color:var(--muted)}}
details p{{margin:4px 0 0}}
.vuoto{{color:var(--l3);font-style:italic}}
.avviso{{margin:6px 0;padding:8px 12px;border-left:4px solid var(--l3);background:var(--card);color:var(--ink);font-size:14px}}
.proposta{{border-style:dashed;border-width:2px;background:transparent}}
.proposta .tag{{font-size:12px;font-weight:600;color:var(--l2);text-transform:uppercase;letter-spacing:.04em}}
.perche{{margin:6px 0 0;font-size:12px;color:var(--muted)}}
</style>
</head>
<body>
<h1>Fase 3 — bacini proposti</h1>
<p class="intro">Per ogni attività, gli esercizi proposti per i tre livelli. Il numero accanto
all'id è il punteggio di difficoltà (su 100, dentro l'attività), poi passaggi e regole diverse.
Il link apre la guida pubblicata. GON è escluso perché l'eserciziario è aperto.</p>
<nav>{''.join(indice)}</nav>
{''.join(sez)}
<script>
// le espressioni lunghe si rimpiccioliscono fino a stare nella colonna (al
// minimo il 55%); oltre, scorrono di lato. Mai a capo, come nel documento.
function adatta(){{
  document.querySelectorAll('.consegna .m:not(.prosa)').forEach(function(m){{
    m.style.fontSize = '';
    var r = m.clientWidth / m.scrollWidth;
    if (r < 1) m.style.fontSize = Math.max(55, Math.floor(r * 100)) + '%';
  }});
}}
window.addEventListener('load', function(){{
  if (window.MathJax && MathJax.startup) MathJax.startup.promise.then(adatta);
}});
var attesa; window.addEventListener('resize', function(){{ clearTimeout(attesa); attesa = setTimeout(adatta, 150); }});
</script>
</body>
</html>
"""
    (USCITA / "anteprima_bacini.html").write_text(pagina, encoding="utf-8")


def prova(file):
    """Prova a secco di una scheda: id, livelli e le righe che finirebbero in
    bacini_proposta.csv. Non scrive niente. Passaggi e regole si contano sulle
    guide, che qui non ci sono ancora: restano vuoti."""
    cod, esercizi, problemi = leggi_scheda(file)
    print(f"Scheda {cod.upper()} ({Path(file).name}): {len(esercizi)} esercizi")
    for p in problemi:
        print(f"  ! {p}")
    print("\nid e livelli:")
    for e in sorted(esercizi, key=lambda e: (e["livello"], e["n_scheda"])):
        print(f"  {cod}_{e['n_scheda']:<4} livello {e['livello']}   {e['risultato_tex']}")
    print("\nrighe per bacini_proposta.csv (passaggi e regole dalle guide, quando ci saranno):")
    print(";".join(COLONNE))
    for e in sorted(esercizi, key=lambda e: (e["livello"], e["n_scheda"])):
        print(";".join([cod.upper(), str(e["livello"]), f"{cod}_{e['n_scheda']}", "", "", "",
                        PARTE_SCHEDA.format(e["livello"]), e["consegna_tex"]]))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--prova":
        prova(sys.argv[2])
    else:
        main()

"""Fase 3 interattiva: punteggio di difficolta', livelli e bacini di esercizi.

Legge soltanto: esercizi/*_contenuti.json, esercizi/*_fase3.json,
tassonomia.yaml e la copia del foglio Argomenti. Scrive solo in fase3/:
    bacini_proposta.csv    gli esercizi proposti, livello per livello
    punteggi_tutti.csv     tutti gli esercizi col loro punteggio e livello
    RIEPILOGO.md           numeri per attivita', casi dubbi, codici che non tornano
    anteprima_bacini.html  le consegne disegnate, tre colonne per attivita'

Uso (dalla cartella principale):  python fase3/calcola_bacini.py

PUNTEGGIO. Ogni ingrediente diventa la posizione in classifica dentro
l'attivita' (0 = il valore piu' basso, 1 = il piu' alto, pari merito = stessa
posizione). Il punteggio, su 100, e':
    40% passaggi  +  35% regole diverse  +  15% parentesi annidate  +  10% lunghezza
LIVELLI: la classifica dell'attivita' tagliata in tre parti uguali.
"""

import csv
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

RADICE = Path(__file__).resolve().parent.parent
ESERCIZI = RADICE / "esercizi"
USCITA = RADICE / "fase3"
FOGLIO_ARGOMENTI = RADICE.parent / "OM_DASHBOARD" / "test" / "dati" / "argomenti.csv"

PESI = {"passaggi": 0.40, "regole": 0.35, "annidamento": 0.15, "lunghezza": 0.10}
ESCLUSE = {"gon"}          # eserciziario aperto: cresce a ogni invio
SCARTA_FILE = ("prima_del_riordino", "riserva")


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
    return attivita, fase3, titoli, sito


def ordina_id(i):
    cod, n = i.rsplit("_", 1)
    return (cod, int(n))


def main():
    attivita, fase3, titoli, sito = carica()
    righe_tutte, bacini, note, conteggi = [], {}, {}, {}

    # gli esercizi dei file *_fase3.json che non sono nei contenuti
    for i, e in fase3.items():
        if i not in {g["id"] for g in attivita.get(e["_attivita"], [])}:
            note.setdefault(e["_attivita"], []).append(
                f"{i} sta in {e['_attivita']}_fase3.json ma non ha la guida nei contenuti: escluso")

    escluse_build = []
    for cod, guide in attivita.items():
        if cod in ESCLUSE:
            continue
        dubbi = note.setdefault(cod, [])
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
                "id": g["id"], "ordine": n, "label": g["consegna_label"],
                "tex": g["consegna_tex"],
                "prosa": bool(g.get("consegna_prosa")) or g.get("tipo") == "problema",
                "tipo": g.get("tipo", ""), "parte": g["_parte"], "nomi": nomi,
                "passaggi": passaggi(g), "regole": len(nomi),
                "annidamento": annidamento(g["consegna_tex"]),
                "lunghezza": lunghezza(g["consegna_tex"]),
                "metodi": sum(1 for r in g["righe"] if r.get("metodo")),
                "figura": "<svg" in g["consegna_tex"],
                "fase3": g["id"] in fase3,
            })
        pos = {k: posizioni([e[k] for e in ex]) for k in PESI}
        for i, e in enumerate(ex):
            e["punteggio"] = round(100 * sum(PESI[k] * pos[k][i] for k in PESI), 1)

        # livelli: la classifica tagliata in tre parti uguali
        classifica = sorted(ex, key=lambda e: (e["punteggio"], e["passaggi"],
                                               e["regole"], e["lunghezza"], -e["ordine"]))
        n = len(classifica)
        for i, e in enumerate(classifica):
            e["livello"] = 1 + (3 * i) // n
        per_livello = {L: [e for e in ex if e["livello"] == L] for L in (1, 2, 3)}

        k = 5 if n >= 15 else 3
        usate, scelta = set(), {}
        for L in (3, 1, 2):          # il 3 per primo: e' quello col vincolo
            cand = per_livello[L]
            if L == 3:
                buoni = [e for e in cand if e["regole"] >= 2]
                if len(buoni) < min(k, len(cand)):
                    dubbi.append(
                        f"livello 3: solo {len(buoni)} esercizi su {len(cand)} usano almeno due "
                        f"regole diverse"
                        + ("" if buoni else ": il livello 3 resta vuoto, va deciso a mano"))
                cand = buoni
            scelta[L] = scegli(cand, min(k, len(cand)), usate)
            usate |= {e["parte"] for e in scelta[L]}
            if len(scelta[L]) < min(k, len(per_livello[L])) and L != 3:
                dubbi.append(f"livello {L}: solo {len(scelta[L])} esercizi scelti")

        bacini[cod] = scelta
        conteggi[cod] = {"n": n, "k": k, "livelli": {L: len(per_livello[L]) for L in (1, 2, 3)},
                         "parti": Counter(e["parte"] for e in ex)}

        # casi dubbi
        tutte_parti = set(conteggi[cod]["parti"])
        coperte = {e["parte"] for L in scelta for e in scelta[L]}
        if len(tutte_parti) > 1 and tutte_parti - coperte:
            dubbi.append("parti senza nessun esercizio nel bacino: "
                         + "; ".join(sorted(tutte_parti - coperte)))
        if max(e["regole"] for e in ex) <= 1:
            dubbi.append("nessun esercizio usa piu' di una regola: la difficolta' la fanno "
                         "solo i passaggi e la lunghezza")
        corti = [L for L in (1, 2, 3) if len(scelta[L]) < 3]
        if corti:
            dubbi.append("attività piccola: " + ", ".join(
                f"il livello {L} ha {len(scelta[L])} esercizi" for L in corti)
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
        # pari merito spezzati dal taglio fra due livelli
        spezzati = [f"{a['id']}/{b['id']} ({a['livello']}|{b['livello']})"
                    for a, b in zip(classifica, classifica[1:])
                    if a["livello"] != b["livello"] and a["punteggio"] == b["punteggio"]]
        if spezzati:
            dubbi.append("stesso punteggio ma livelli diversi (il taglio li separa per passaggi "
                         "e lunghezza; si possono scambiare): " + ", ".join(spezzati))

        for e in ex:
            righe_tutte.append((cod.upper(), e))

    scrivi_csv(bacini)
    scrivi_tutti(righe_tutte)
    scrivi_riepilogo(attivita, bacini, conteggi, note, titoli, escluse_build, fase3)
    scrivi_anteprima(bacini, conteggi, titoli, sito)
    print(f"Attivita' con bacino: {len(bacini)}")
    for cod in bacini:
        print(f"  {cod.upper():6} {conteggi[cod]['n']:4} esercizi  ->  "
              + "  ".join(f"L{L}:{len(bacini[cod][L])}" for L in (1, 2, 3)))


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
                    w.writerow([cod.upper(), L, e["id"], str(e["punteggio"]).replace(".", ","),
                                e["passaggi"], e["regole"], e["parte"], e["tex"]])


def scrivi_tutti(righe):
    with open(USCITA / "punteggi_tutti.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codice attività", "id esercizio", "livello", "punteggio", "passaggi",
                    "regole", "annidamento", "lunghezza", "parte", "nomi delle regole",
                    "consegna in LaTeX"])
        for cod, e in sorted(righe, key=lambda r: (r[0], r[1]["ordine"])):
            w.writerow([cod, e["id"], e["livello"], str(e["punteggio"]).replace(".", ","),
                        e["passaggi"], e["regole"], e["annidamento"], e["lunghezza"],
                        e["parte"], " | ".join(e["nomi"]), e["tex"]])


def foglio_argomenti():
    if not FOGLIO_ARGOMENTI.exists():
        return None
    with open(FOGLIO_ARGOMENTI, encoding="utf-8") as f:
        r = list(csv.reader(f))
    return {row[1].strip(): (row[0].strip(), row[2].strip()) for row in r[1:] if len(row) > 2}


def scrivi_riepilogo(attivita, bacini, conteggi, note, titoli, escluse_build, fase3):
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
           "il punteggio (su 100) è **40% passaggi + 35% regole + 15% parentesi + 10% lunghezza**: "
           "pesano soprattutto quanti passaggi servono e quante regole si mescolano.",
           "", "**Livelli**: la classifica dell'attività divisa in tre parti con lo stesso numero "
           "di esercizi (1 = il terzo più facile, 3 = il più complesso). Dividere invece in tre "
           "fasce uguali di punteggio lascerebbe pochissimi esercizi ai livelli 1 e 3, perché i "
           "punteggi si addensano al centro.",
           "", "**Bacino**: 5 esercizi per livello (3 se l'attività ha meno di 15 esercizi). "
           "Lo script sceglie prima esercizi di parti diverse dell'attività, poi esercizi che "
           "portano regole nuove, poi tipi di consegna diversi; a parità, quelli vicini al centro "
           "del livello. Al livello 3 entrano solo esercizi con almeno due regole diverse.",
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
            "| Attività | Esercizi | Liv. 1 / 2 / 3 | Bacino 1 / 2 / 3 | Parti |",
            "|---|---:|---|---|---:|"]
    for cod, s in bacini.items():
        c = conteggi[cod]
        lv = c["livelli"]
        out.append(f"| {cod.upper()} — {titoli.get(cod, '')} | {c['n']} | "
                   f"{lv[1]} / {lv[2]} / {lv[3]} | "
                   f"{len(s[1])} / {len(s[2])} / {len(s[3])} | {len(c['parti'])} |")
    out += ["", "## Casi dubbi", ""]
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
          <span class="dati" title="punteggio · passaggi · regole">{str(e['punteggio']).replace('.', ',')} · {e['passaggi']} pass. · {e['regole']} reg.</span></header>
        {parte}
        <div class="consegna">
          <div class="t">📌 {e['label']}</div>
          {consegna_html(e)}
        </div>
        <details><summary>Regole</summary><p>{regole}</p></details>
      </article>""")
            vuoto = '<p class="vuoto">Nessun esercizio: da decidere a mano.</p>' if not schede else ""
            colonne.append(f'<div class="col"><h3 class="l{L}">{nome}</h3>{"".join(schede)}{vuoto}</div>')
        c = conteggi[cod]
        sez.append(f"""
  <section id="{cod}">
    <h2>{C} — {html.escape(titoli.get(cod, ''))}</h2>
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


if __name__ == "__main__":
    main()

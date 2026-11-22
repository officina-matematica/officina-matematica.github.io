# Fase 3 — proposta dei bacini

Proposta da controllare: nessuna guida, nessun file di contenuto, nessun prompt è stato modificato. I file sono in `fase3/`:

- `bacini_proposta.csv` — gli esercizi proposti, per attività e livello (separatore `;`, si apre con Excel)
- `punteggi_tutti.csv` — tutti gli esercizi con punteggio e livello, per sostituire a mano un esercizio del bacino
- `anteprima_bacini.html` — le consegne disegnate, tre colonne per attività
- `calcola_bacini.py` — lo script che rifà tutto: `python fase3/calcola_bacini.py`

## Come è calcolato il punteggio

Per ogni esercizio si contano quattro cose: i **passaggi** (le righe della guida dopo la consegna), le **regole diverse** (i nomi distinti nelle tendine «Regola»), la **profondità delle parentesi** della consegna e la sua **lunghezza** (simboli della formula, parole nei problemi).
Dentro ogni attività ciascuna quantità diventa una posizione in classifica da 0 a 1; il punteggio (su 100) è **40% passaggi + 35% regole + 15% parentesi + 10% lunghezza**: pesano soprattutto quanti passaggi servono e quante regole si mescolano.

**Livelli**: la classifica dell'attività divisa in tre parti con lo stesso numero di esercizi (1 = il terzo più facile, 3 = il più complesso). Dividere invece in tre fasce uguali di punteggio lascerebbe pochissimi esercizi ai livelli 1 e 3, perché i punteggi si addensano al centro.

**Bacino**: 5 esercizi per livello (3 se l'attività ha meno di 15 esercizi). Lo script sceglie prima esercizi di parti diverse dell'attività, poi esercizi che portano regole nuove, poi tipi di consegna diversi; a parità, quelli vicini al centro del livello. Al livello 3 entrano solo esercizi con almeno due regole diverse.

## Cosa è stato escluso

- **GON — Eserciziario**: escluso perché è aperto (si allunga a ogni invio di esercizi). Ha 9 guide: un bacino andrebbe fatto quando l'eserciziario sarà fermo.
- `of2/of3/of4_prima_del_riordino.json` e `of4_riserva_contenuti.json` (le 33 espressioni di riserva di OF4, of4_19 … of4_51).
- Guide rimaste in `build/`: nessuna da escludere. In `build/` c'è `mp6_17.html`, ma la guida mp6_17 è anche nella cartella principale (rifatta nell'ultimo commit): è quella che conta.

**Esercizi dei file `*_fase3.json`**: sono già dentro i contenuti delle rispettive attività (stessi id, guide pubblicate), quindi concorrono come gli altri. MP2: 26 esercizi, 6 entrati nel bacino; P2: 15 esercizi, 5 entrati nel bacino; P3: 15 esercizi, 4 entrati nel bacino.

## Attività per attività

| Attività | Esercizi | Liv. 1 / 2 / 3 | Bacino 1 / 2 / 3 | Parti |
|---|---:|---|---|---:|
| DX3 — Numeri decimali e frazioni | 34 | 12 / 11 / 11 | 5 / 5 / 5 | 5 |
| F1 — Introduzione alle frazioni | 8 | 3 / 3 / 2 | 3 / 3 / 2 | 1 |
| F2 — Frazioni e numeri misti | 88 | 30 / 29 / 29 | 5 / 5 / 5 | 8 |
| FMDC1 — Fattorizzazione | 14 | 5 / 5 / 4 | 3 / 3 / 3 | 1 |
| FMDC2 — Massimo Comun Divisore | 17 | 6 / 6 / 5 | 5 / 5 / 5 | 1 |
| FMDC3 — Minimo Comune Multiplo | 17 | 6 / 6 / 5 | 5 / 5 / 5 | 1 |
| FMDC4 — Problemi con MCD e mcm | 14 | 5 / 5 / 4 | 3 / 3 / 3 | 1 |
| LOG1 — Calcolo logaritmi | 113 | 38 / 38 / 37 | 5 / 5 / 5 | 5 |
| LOG2 — Proprietà dei logaritmi | 64 | 22 / 21 / 21 | 5 / 5 / 5 | 6 |
| LOG7 — Equazioni logaritmiche | 6 | 2 / 2 / 2 | 2 / 2 / 2 | 1 |
| LOG8 — Disequazioni logaritmiche | 5 | 2 / 2 / 1 | 2 / 2 / 1 | 1 |
| MP1 — I monomi | 75 | 25 / 25 / 25 | 5 / 5 / 5 | 7 |
| MP2 — Operazioni con i monomi | 77 | 26 / 26 / 25 | 5 / 5 / 5 | 9 |
| MP3 — MCD e mcm con i monomi | 35 | 12 / 12 / 11 | 5 / 5 / 5 | 4 |
| MP4 — Polinomi | 25 | 9 / 8 / 8 | 5 / 5 / 5 | 4 |
| MP5 — Somme algebriche e moltiplicazioni di polinomi | 18 | 6 / 6 / 6 | 5 / 5 / 5 | 3 |
| MP6 — Prodotti notevoli | 39 | 13 / 13 / 13 | 5 / 5 / 5 | 4 |
| NEG4 — Espressioni con i numeri negativi | 30 | 10 / 10 / 10 | 5 / 5 / 5 | 2 |
| NEG5 — Numeri negativi, potenze ed espressioni | 33 | 11 / 11 / 11 | 5 / 5 / 5 | 1 |
| NEG6 — Espressioni con potenze negative e notazione scientifica | 82 | 28 / 27 / 27 | 5 / 5 / 5 | 8 |
| ODX1 — Espressioni con i numeri decimali | 7 | 3 / 2 / 2 | 3 / 2 / 2 | 1 |
| ODX2 — Numeri decimali e potenze | 6 | 2 / 2 / 2 | 2 / 2 / 2 | 1 |
| OF1 — Addizioni e sottrazioni con le frazioni | 11 | 4 / 4 / 3 | 3 / 3 / 3 | 1 |
| OF2 — Moltiplicare le frazioni | 11 | 4 / 4 / 3 | 3 / 3 / 3 | 2 |
| OF3 — Dividere le frazioni | 8 | 3 / 3 / 2 | 3 / 3 / 2 | 2 |
| OF4 — Frazioni, potenze ed espressioni | 18 | 6 / 6 / 6 | 5 / 5 / 5 | 2 |
| OF5 — Problemi con frazioni | 52 | 18 / 17 / 17 | 5 / 5 / 5 | 15 |
| ON2 — Proprietà delle operazioni | 54 | 18 / 18 / 18 | 5 / 5 / 5 | 6 |
| ON3 — Espressioni con i numeri naturali | 10 | 4 / 3 / 3 | 3 / 3 / 3 | 1 |
| P1 — Alla scoperta delle potenze | 74 | 25 / 25 / 24 | 5 / 5 / 5 | 5 |
| P2 — Potenze con la stessa base | 60 | 20 / 20 / 20 | 5 / 5 / 5 | 4 |
| P3 — Potenze con lo stesso esponente | 50 | 17 / 17 / 16 | 5 / 5 / 5 | 2 |
| P4 — Espressioni con le potenze | 11 | 4 / 4 / 3 | 3 / 3 / 3 | 1 |
| PR2 — Calcolo di proporzioni | 33 | 11 / 11 / 11 | 5 / 5 / 5 | 1 |
| PR4 — Problemi con le proporzioni | 40 | 14 / 13 / 13 | 5 / 5 / 5 | 2 |
| PX1 — Alla scoperta delle percentuali | 12 | 4 / 4 / 4 | 3 / 3 / 3 | 2 |
| PX2 — Problemi con le percentuali | 51 | 17 / 17 / 17 | 5 / 5 / 5 | 9 |
| SCO1 — Scomposizioni in fattori | 17 | 6 / 6 / 5 | 5 / 5 / 5 | 1 |

## Casi dubbi

**DX3**
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: dx3_16 (liv. 1), dx3_21 (liv. 1), dx3_23 (liv. 1), dx3_13 (liv. 2), dx3_20 (liv. 2), dx3_22 (liv. 2), dx3_18 (liv. 3), dx3_19 (liv. 3), dx3_29 (liv. 3)
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): dx3_16/dx3_15 (1|2), dx3_20/dx3_19 (2|3)

**F1**
- attività piccola: il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**F2**
- consegna con un disegno, che la fase 3 deve mostrare insieme al testo: f2_1 (liv. 1), f2_5 (liv. 3)
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): f2_25/f2_24 (1|2)

**FMDC1**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): fmdc1_14/fmdc1_2 (2|3)

**FMDC2**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): fmdc2_4/fmdc2_2 (1|2)

**FMDC3**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): fmdc3_3/fmdc3_2 (1|2), fmdc3_14/fmdc3_13 (2|3)

**LOG1**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): log1_82/log1_31 (2|3)

**LOG7**
- attività piccola: il livello 1 ha 2 esercizi, il livello 2 ha 2 esercizi, il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**LOG8**
- attività piccola: il livello 1 ha 2 esercizi, il livello 2 ha 2 esercizi, il livello 3 ha 1 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**MP1**
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: mp1_55 (liv. 2)

**MP2**
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: mp2_67 (liv. 1)

**MP3**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): mp3_20/mp3_5 (1|2), mp3_13/mp3_12 (2|3)

**MP4**
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: mp4_21 (liv. 1), mp4_24 (liv. 1), mp4_20 (liv. 2), mp4_23 (liv. 2), mp4_17 (liv. 3), mp4_19 (liv. 3), mp4_22 (liv. 3)

**MP5**
- guide con due metodi uno dopo l'altro, quindi passaggi contati due volte e punteggio un po' gonfiato: mp5_18 (liv. 3)

**MP6**
- guide con due metodi uno dopo l'altro, quindi passaggi contati due volte e punteggio un po' gonfiato: mp6_29 (liv. 3), mp6_30 (liv. 3)

**NEG6**
- parti senza nessun esercizio nel bacino: Parte 8 · Matematica e realtà
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: neg6_76 (liv. 2)
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): neg6_40/neg6_39 (2|3)

**ODX1**
- attività piccola: il livello 2 ha 2 esercizi, il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**ODX2**
- attività piccola: il livello 1 ha 2 esercizi, il livello 2 ha 2 esercizi, il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**OF1**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): of1_6/of1_4 (1|2)

**OF2**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): of2_8/of2_7 (2|3)

**OF3**
- attività piccola: il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): of3_4/of3_3 (1|2)

**OF5**
- parti senza nessun esercizio nel bacino: Parte 10 · Dalla frazione di una frazione all'intero
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): of5_27/of5_12 (1|2)

**ON2**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): on2_35/on2_25 (2|3)

**P1**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): p1_53/p1_25 (2|3)

**PR4**
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: pr4_5 (liv. 1), pr4_7 (liv. 1)

**PX1**
- guide con due metodi uno dopo l'altro, quindi passaggi contati due volte e punteggio un po' gonfiato: px1_10 (liv. 1), px1_1 (liv. 3), px1_3 (liv. 3)
- consegna con un disegno, che la fase 3 deve mostrare insieme al testo: px1_7 (liv. 1), px1_5 (liv. 2), px1_6 (liv. 2), px1_1 (liv. 3), px1_3 (liv. 3)

**PX2**
- guide con due metodi uno dopo l'altro, quindi passaggi contati due volte e punteggio un po' gonfiato: px2_22 (liv. 1), px2_2 (liv. 2), px2_7 (liv. 2), px2_20 (liv. 2), px2_6 (liv. 3), px2_13 (liv. 3)
- consegna con un disegno, che la fase 3 deve mostrare insieme al testo: px2_31 (liv. 1)

**SCO1**
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): sco1_12/sco1_9 (1|2)

## Codici delle guide e foglio Argomenti

Confronto fatto con la copia del foglio usata dalla dashboard (`OM_DASHBOARD/test/dati/argomenti.csv`, del 18/11/2026): se nel frattempo il foglio è cambiato, il confronto va rifatto.

| Codice guide | Nel foglio Argomenti | Cosa non torna |
|---|---|---|
| F1 — Introduzione alle frazioni | F1 — Introduzione alle frazioni e primi problemai (F | Frazioni) | titolo diverso |
| GON — Eserciziario | — | codice assente; nel foglio ci sono: GON1, GON2 |
| LOG1 — Calcolo logaritmi | LOG1 — Crescita esponenziale (LOG | Logaritmi) | titolo diverso |
| LOG2 — Proprietà dei logaritmi | LOG2 — La funzione esponenziale (LOG | Logaritmi) | titolo diverso |
| LOG7 — Equazioni logaritmiche | — | codice assente; nel foglio ci sono: LOG1, LOG2, LOG3, LOG4, LOG5, LOG6, LOG7ù |
| LOG8 — Disequazioni logaritmiche | — | codice assente; nel foglio ci sono: LOG1, LOG2, LOG3, LOG4, LOG5, LOG6, LOG7ù |
| NEG6 — Espressioni con potenze negative e notazione scientifica | NEG6 — Esp. con potenze negative e notazione scientifica (NEG | Numeri negativi e operazioni) | titolo diverso |
| OF5 — Problemi con frazioni | OF5 — Problemi con le frazioni (OF | Operazioni con le frazioni) | titolo diverso |
| P2 — Potenze con la stessa base | P2 — Proprietà delle potenze con ugual base (P | Potenze e operazioni) | titolo diverso |
| P3 — Potenze con lo stesso esponente | P3 — Proprietà delle potenze con ugual esponente (P | Potenze e operazioni) | titolo diverso |
| SCO1 — Scomposizioni in fattori | SCO1 — Raccoglimento totale e parziale (SCO | Scomposizioni) | titolo diverso |

Da guardare con attenzione:

- **GON**: le guide usano un solo codice (`gon_1`, `gon_2`, …) per tutto l'eserciziario; il foglio ha **GON1** e **GON2**, senza titolo. Va deciso a quale attività appartiene l'eserciziario (o se va diviso).
- **LOG1, LOG2**: il codice c'è, ma nel foglio LOG1 è «Crescita esponenziale» e LOG2 «La funzione esponenziale», mentre le guide sono *Calcolo logaritmi* e *Proprietà dei logaritmi*: lo stesso codice indica contenuti diversi.
- **LOG7**: nel foglio è scritto **«LOG7ù»** (refuso, la dashboard lo scarta come riga anomala). **LOG8** nel foglio non c'è. LOG5 e LOG6 sono nel foglio senza argomento.
- **SCO1**: il codice c'è, ma nel foglio SCO1 è «Raccoglimento totale e parziale» (argomento SCO | Scomposizioni), mentre in `tassonomia.yaml` è «Scomposizioni in fattori» sotto CLE | Calcolo letterale. Le 17 guide mescolano raccoglimento, prodotti notevoli e trinomio speciale, cioè anche SCO2 e SCO3 del foglio.
- Gli altri sono solo differenze di titolo (P2, P3, F1, OF5, NEG6): stesso contenuto, parole diverse.

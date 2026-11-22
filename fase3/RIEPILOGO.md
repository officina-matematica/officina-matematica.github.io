# Fase 3 — proposta dei bacini

Proposta da controllare: nessuna guida, nessun file di contenuto, nessun prompt è stato modificato. I file sono in `fase3/`:

- `bacini_proposta.csv` — gli esercizi proposti, per attività e livello (separatore `;`, si apre con Excel)
- `punteggi_tutti.csv` — tutti gli esercizi con punteggio e livello, per sostituire a mano un esercizio del bacino
- `anteprima_bacini.html` — le consegne disegnate, tre colonne per attività
- `calcola_bacini.py` — lo script che rifà tutto: `python fase3/calcola_bacini.py`

## Come è calcolato il punteggio

Per ogni esercizio si contano quattro cose: i **passaggi** (le righe della guida dopo la consegna), le **regole diverse** (i nomi distinti nelle tendine «Regola»), la **profondità delle parentesi** della consegna e la sua **lunghezza** (simboli della formula, parole nei problemi).
Dentro ogni attività ciascuna quantità diventa una posizione in classifica da 0 a 1; il punteggio (su 100) è **50% passaggi + 25% regole + 15% parentesi + 10% lunghezza**. Le regole pesano meno di prima (erano al 35%) perché alcune guide citano molte regole anche per conti semplici.

**Livelli**: la classifica dell'attività divisa in tre parti con lo stesso numero di esercizi (1 = il terzo più facile, 3 = il più complesso).

**Progressione per tipo** — in alcune attività il punteggio non basta, e decide il tipo di esercizio (dentro un tipo che può stare su due livelli, si divide a metà secondo il punteggio):

- **PR4**: riconoscere se la proporzionalità è diretta o inversa → 1; un problema con una sola proporzione, diretta o inversa → 1 o 2; dividere in due parti secondo un rapporto, e il rettangolo con due domande → 2; problemi composti (operai *e* giorni), divisioni in tre parti o con un passo in più, percentuale all'indietro → 3.
- **MP6**: somma per differenza → 1; quadrato di binomio → 1 o 2; cubo → 2; espressioni → 3.
- **P3**: le semplificazioni brevi scritte per la fase 3 → 1; le espressioni → 2 o 3.
- **LOG1**: gli esercizi che hanno una radice come risultato (come log1_93, $\log_x 64=5$) non stanno al livello 1.
- **NEG6**: potenze con esponente negativo, proprietà, scrivere in notazione scientifica e tornare al numero → 1 o 2; calcolare in notazione scientifica e trovare l'errore → 2; espressioni e problemi di realtà → 3.
- **FMDC2, FMDC3**: due numeri piccoli → 1; due numeri più grandi → 2; tre numeri → 3.
- **OF2**: i prodotti che si semplificano subito (of2_3, of2_4) → 1; completare l'uguaglianza → 2; i prodotti con un intero da trasformare o con quattro fattori (of2_1, of2_2, of2_5) → 3 (confermato da Simone il 22/11).

**Bacino**: 5 esercizi per livello (3 se l'attività ha meno di 15 esercizi). Lo script sceglie prima esercizi di parti diverse dell'attività, poi esercizi che portano regole nuove, poi tipi di consegna diversi; a parità, quelli vicini al centro del livello. Poi tre filtri:

- **livello 3 senza maratone**: fuori gli esercizi che superano *sia* il 90° percentile dei passaggi della loro attività *sia* i 12 passaggi (restano nei punteggi, non nel bacino), e dentro solo esercizi con almeno due regole diverse;
- **coerenza fra livelli**: la mediana dei passaggi deve crescere dal livello 1 al 3, e nessun esercizio del livello 1 può avere più passaggi della mediana del livello 2. Dove non succede, lo script scambia con un altro esercizio *dello stesso livello* (così la progressione per tipo resta) e lo scrive nei casi dubbi;
- **doppioni**: una consegna presente in due attività resta solo in quella che viene prima nel percorso, tranne P3/P4: lì resta a P4.

## Cosa è stato escluso

- **GON — Eserciziario**: escluso perché è aperto (si allunga a ogni invio di esercizi). Ha 9 guide: un bacino andrebbe fatto quando l'eserciziario sarà fermo.
- `of2/of3/of4_prima_del_riordino.json` e `of4_riserva_contenuti.json` (le 33 espressioni di riserva di OF4, of4_19 … of4_51).
- Guide rimaste in `build/`: nessuna da escludere. In `build/` c'è `mp6_17.html`, ma la guida mp6_17 è anche nella cartella principale (rifatta nell'ultimo commit): è quella che conta.

**Esercizi dei file `*_fase3.json`**: sono già dentro i contenuti delle rispettive attività (stessi id, guide pubblicate), quindi concorrono come gli altri. MP2: 26 esercizi, 7 entrati nel bacino; P2: 15 esercizi, 4 entrati nel bacino; P3: 15 esercizi, 5 entrati nel bacino.

## Attività per attività

Passaggi: la mediana dei passaggi degli esercizi del bacino, livello per livello. Soglia: oltre questo numero di passaggi un esercizio non entra nel livello 3 (il più grande fra il 90° percentile dell'attività e 12).

| Attività | Esercizi | Liv. 1 / 2 / 3 | Bacino 1 / 2 / 3 | Passaggi 1 / 2 / 3 | Soglia | Parti |
|---|---:|---|---|---|---:|---:|
| DX3 — Numeri decimali e frazioni | 34 | 12 / 11 / 11 | 5 / 5 / 5 | 3 / 4 / 5 | 12 | 5 |
| F1 — Introduzione alle frazioni | 8 | 3 / 3 / 2 | 3 / 3 / 2 | 3 / 4 / 5 | 12 | 1 |
| F2 — Frazioni e numeri misti | 88 | 30 / 29 / 29 | 5 / 5 / 5 | 2 / 3 / 5 | 12 | 8 |
| FMDC1 — Fattorizzazione | 14 | 5 / 5 / 4 | 3 / 3 / 3 | 3 / 5 / 6 | 12 | 1 |
| FMDC2 — Massimo Comun Divisore | 17 | 4 / 4 / 9 | 4 / 4 / 5 | 3 / 3 / 4 | 12 | 1 |
| FMDC3 — Minimo Comune Multiplo | 17 | 4 / 4 / 9 | 4 / 4 / 5 | 3 / 3 / 4 | 12 | 1 |
| FMDC4 — Problemi con MCD e mcm | 14 | 5 / 5 / 4 | 3 / 3 / 3 | 5 / 6 / 10 | 12 | 1 |
| LOG1 — Calcolo logaritmi | 113 | 35 / 39 / 39 | 5 / 5 / 5 | 2 / 4 / 5 | 12 | 5 |
| LOG2 — Proprietà dei logaritmi | 64 | 22 / 21 / 21 | 5 / 5 / 5 | 3 / 5 / 9 | 12 | 6 |
| LOG7 — Equazioni logaritmiche | 6 | 2 / 2 / 2 | 2 / 2 / 2 | 11.5 / 15 / 17.5 | 20 | 1 |
| LOG8 — Disequazioni logaritmiche | 5 | 2 / 2 / 1 | 2 / 2 / 1 | 8 / 12.5 / 15 | 15 | 1 |
| MP1 — I monomi | 75 | 25 / 25 / 25 | 5 / 5 / 5 | 2 / 3 / 9 | 12 | 7 |
| MP2 — Operazioni con i monomi | 77 | 26 / 26 / 25 | 5 / 5 / 5 | 3 / 4 / 8 | 12 | 9 |
| MP3 — MCD e mcm con i monomi | 35 | 12 / 12 / 11 | 5 / 5 / 5 | 3 / 3 / 4 | 12 | 4 |
| MP4 — Polinomi | 25 | 9 / 8 / 8 | 5 / 5 / 5 | 1 / 4 / 6 | 12 | 4 |
| MP5 — Somme algebriche e moltiplicazioni di polinomi | 18 | 6 / 6 / 6 | 5 / 5 / 5 | 5 / 7 / 9 | 12 | 3 |
| MP6 — Prodotti notevoli | 39 | 13 / 13 / 13 | 5 / 5 / 5 | 2 / 4 / 10 | 12 | 4 |
| NEG4 — Espressioni con i numeri negativi | 30 | 10 / 10 / 10 | 5 / 5 / 5 | 4 / 5 / 13 | 14 | 2 |
| NEG5 — Numeri negativi, potenze ed espressioni | 33 | 11 / 11 / 11 | 5 / 5 / 5 | 9 / 10 / 12 | 16 | 1 |
| NEG6 — Espressioni con potenze negative e notazione scientifica | 82 | 24 / 44 / 14 | 5 / 5 / 5 | 2 / 4 / 9 | 12 | 8 |
| ODX1 — Espressioni con i numeri decimali | 7 | 3 / 2 / 2 | 3 / 2 / 2 | 15 / 17.5 / 23.5 | 29 | 1 |
| ODX2 — Numeri decimali e potenze | 6 | 2 / 2 / 2 | 2 / 2 / 2 | 8 / 11.5 / 20 | 21 | 1 |
| OF1 — Addizioni e sottrazioni con le frazioni | 11 | 4 / 4 / 3 | 3 / 3 / 2 | 5 / 9 / 12 | 13 | 1 |
| OF2 — Moltiplicare le frazioni | 11 | 2 / 6 / 3 | 2 / 3 / 3 | 4.5 / 5 / 6 | 12 | 2 |
| OF3 — Dividere le frazioni | 8 | 3 / 3 / 2 | 3 / 3 / 2 | 4 / 5 / 10.5 | 12 | 2 |
| OF4 — Frazioni, potenze ed espressioni | 18 | 6 / 6 / 6 | 5 / 5 / 5 | 7 / 12 / 20 | 23 | 2 |
| OF5 — Problemi con frazioni | 52 | 18 / 17 / 17 | 5 / 5 / 5 | 4 / 5 / 7 | 12 | 15 |
| ON2 — Proprietà delle operazioni | 54 | 18 / 18 / 18 | 5 / 5 / 5 | 3 / 3 / 4 | 12 | 6 |
| ON3 — Espressioni con i numeri naturali | 10 | 4 / 3 / 3 | 3 / 3 / 3 | 5 / 7 / 9 | 12 | 1 |
| P1 — Alla scoperta delle potenze | 74 | 25 / 25 / 24 | 5 / 5 / 5 | 2 / 2 / 3 | 12 | 5 |
| P2 — Potenze con la stessa base | 60 | 20 / 20 / 20 | 5 / 5 / 5 | 3 / 4 / 5 | 12 | 4 |
| P3 — Potenze con lo stesso esponente | 50 | 15 / 18 / 17 | 5 / 5 / 5 | 4 / 7 / 9 | 13 | 2 |
| P4 — Espressioni con le potenze | 11 | 4 / 4 / 3 | 3 / 3 / 2 | 8 / 13 / 14 | 14 | 1 |
| PR2 — Calcolo di proporzioni | 33 | 11 / 11 / 11 | 5 / 5 / 5 | 5 / 6 / 12 | 18 | 1 |
| PR4 — Problemi con le proporzioni | 40 | 18 / 15 / 7 | 5 / 5 / 5 | 2 / 4 / 5 | 12 | 2 |
| PX1 — Alla scoperta delle percentuali | 12 | 4 / 4 / 4 | 3 / 3 / 3 | 6 / 7 / 8 | 12 | 2 |
| PX2 — Problemi con le percentuali | 51 | 17 / 17 / 17 | 5 / 5 / 5 | 4 / 5 / 7 | 12 | 9 |
| SCO1 — Scomposizioni in fattori | 17 | 6 / 6 / 5 | 5 / 5 / 5 | 2 / 3 / 4 | 12 | 1 |

## Doppioni fra attività

La stessa consegna (stessa etichetta, stessa formula) sta in due attività. Resta nel bacino solo dell'attività che viene prima nel percorso; nell'altra conta nei punteggi ma non entra nel bacino. Eccezione decisa da Simone il 22/11: le 11 espressioni comuni a P3 e P4 restano a P4 e si tolgono da P3, che fa il bacino con le altre.

- **NEG5** (tolti dal bacino): neg5_19 = neg4_29
- **P3** (tolti dal bacino): p3_1 = p4_2, p3_11 = p4_1, p3_18 = p4_11, p3_20 = p4_7, p3_27 = p4_3, p3_28 = p4_6, p3_30 = p4_4, p3_31 = p4_9, p3_32 = p4_8, p3_34 = p4_10, p3_35 = p4_5

## Livello 1 non basico

Attività in cui anche il livello 1 supera i 6 passaggi (mediana dei passaggi del livello 1). Per ognuna, 2-3 esercizi di livello 1 da scrivere apposta: consegna più corta, una sola parentesi. **Sono solo proposte, le guide non sono state scritte.** I risultati sono controllati con SymPy.

**LOG7 — Equazioni logaritmiche** · livello 1 di oggi: mediana 11.5 passaggi

- $\log_{2}\left(x-1\right)=3$ → $x=9$ — un solo logaritmo, si passa all'esponenziale
- $\log_{3}x+\log_{3}2=2$ → $x=\frac{9}{2}$ — la proprietà del prodotto, poi come sopra
- $\ln\left(2x+1\right)=\ln 5$ → $x=2$ — stessa base ai due membri

**LOG8 — Disequazioni logaritmiche** · livello 1 di oggi: mediana 8 passaggi

- $\log_{2}\left(x-1\right)<3$ → $1<x<9$ — base maggiore di 1, con il dominio
- $\log_{\frac{1}{3}}x>2$ → $0<x<\frac{1}{9}$ — base minore di 1: il verso si gira
- $\ln\left(x+2\right)\ge 0$ → $x\ge -1$ — confronto con $\ln 1=0$

**NEG5 — Numeri negativi, potenze ed espressioni** · livello 1 di oggi: mediana 9 passaggi

- $\left(-\frac{2}{3}\right)^{2}-\frac{1}{9}$ → $\frac{1}{3}$ — una potenza di base negativa e una sottrazione
- $\left(-\frac{1}{2}+\frac{3}{4}\right)^{2}\cdot 8$ → $\frac{1}{2}$ — prima la parentesi, poi la potenza
- $-2^{2}+\left(-3\right)^{2}:3$ → $-1$ — la differenza fra $-2^{2}$ e $\left(-3\right)^{2}$

**ODX1 — Espressioni con i numeri decimali** · livello 1 di oggi: mediana 15 passaggi

- $\left(0{,}5+0{,}25\right)\cdot 4$ → $3$ — solo decimali finiti
- $0{,}\overline{3}\cdot 1{,}2-0{,}1$ → $0{,}3$ — un solo periodico da trasformare in frazione
- $\left(1{,}5-0{,}\overline{6}\right):0{,}5$ → $1{,}\overline{6}$ — un periodico dentro una parentesi

**ODX2 — Numeri decimali e potenze** · livello 1 di oggi: mediana 8 passaggi

- $\left(0{,}3\right)^{2}+0{,}91$ → $1$ — una potenza di un decimale
- $\left(0{,}5\right)^{3}\cdot 4$ → $0{,}5$ — cubo di un decimale, poi un prodotto
- $\left(1{,}2\right)^{2}-0{,}44$ → $1$ — quadrato di un decimale maggiore di 1

**OF4 — Frazioni, potenze ed espressioni** · livello 1 di oggi: mediana 7 passaggi

- $\left(\frac{1}{2}+\frac{1}{3}\right)\cdot\frac{6}{5}$ → $1$ — una somma in parentesi, poi un prodotto
- $\left(\frac{2}{3}\right)^{2}\cdot\frac{3}{2}$ → $\frac{2}{3}$ — una potenza di frazione e una semplificazione
- $\frac{3}{4}-\left(\frac{1}{2}\right)^{2}$ → $\frac{1}{2}$ — prima la potenza, poi la sottrazione

**P4 — Espressioni con le potenze** · livello 1 di oggi: mediana 8 passaggi

- $\left(2^{3}+2^{2}\right):3$ → $4$ — potenze da calcolare, poi una divisione
- $5^{2}-\left(3^{2}-2^{3}\right)$ → $24$ — una parentesi con due potenze
- $\left(2^{5}:2^{3}\right)^{2}+1$ → $17$ — quoziente di potenze con la stessa base, poi il quadrato

## Casi dubbi

**DX3**
- scambi per la coerenza fra livelli: liv. 1: dx3_16 (4 pass.) → dx3_2 (3 pass.)
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: dx3_21 (liv. 1), dx3_23 (liv. 1), dx3_13 (liv. 2), dx3_20 (liv. 2), dx3_22 (liv. 2), dx3_18 (liv. 3), dx3_19 (liv. 3), dx3_29 (liv. 3)
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): dx3_16/dx3_15 (1|2), dx3_20/dx3_19 (2|3)

**F1**
- attività piccola: il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**F2**
- scambi per la coerenza fra livelli: liv. 1: f2_25 (3 pass.) → f2_12 (2 pass.)
- consegna con un disegno, che la fase 3 deve mostrare insieme al testo: f2_8 (liv. 1), f2_5 (liv. 3)
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): f2_25/f2_24 (1|2)

**FMDC2**
- la mediana dei passaggi non cresce dal livello 1 (3) al livello 2 (3) e con gli esercizi disponibili non si può sistemare: qui conta il tipo di esercizio, non la lunghezza

**FMDC3**
- la mediana dei passaggi non cresce dal livello 1 (3) al livello 2 (3) e con gli esercizi disponibili non si può sistemare: qui conta il tipo di esercizio, non la lunghezza

**LOG2**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (9) e oltre 12 passaggi: log2_34 (14)

**LOG7**
- attività piccola: il livello 1 ha 2 esercizi, il livello 2 ha 2 esercizi, il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**LOG8**
- attività piccola: il livello 1 ha 2 esercizi, il livello 2 ha 2 esercizi, il livello 3 ha 1 esercizio. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**MP1**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (10) e oltre 12 passaggi: mp1_41 (13), mp1_43 (15), mp1_44 (21), mp1_45 (18)
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: mp1_55 (liv. 2)

**MP2**
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: mp2_68 (liv. 1), mp2_70 (liv. 2)

**MP3**
- la mediana dei passaggi non cresce dal livello 1 (3) al livello 2 (3) e con gli esercizi disponibili non si può sistemare
- scambi per la coerenza fra livelli: liv. 1: mp3_4 (3 pass.) → mp3_1 (1 pass.); liv. 2: mp3_2 (3 pass.) → mp3_25 (4 pass.)
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): mp3_20/mp3_5 (1|2), mp3_28/mp3_14 (2|3)

**MP4**
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: mp4_21 (liv. 1), mp4_23 (liv. 1), mp4_20 (liv. 2), mp4_25 (liv. 2), mp4_19 (liv. 3), mp4_22 (liv. 3)

**MP5**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (12) e oltre 12 passaggi: mp5_16 (13)
- guide con due metodi uno dopo l'altro, quindi passaggi contati due volte e punteggio un po' gonfiato: mp5_18 (liv. 3)

**MP6**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (11) e oltre 12 passaggi: mp6_27 (14), mp6_30 (16)
- guide con due metodi uno dopo l'altro, quindi passaggi contati due volte e punteggio un po' gonfiato: mp6_29 (liv. 3), mp6_31 (liv. 3)

**NEG4**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (14) e oltre 12 passaggi: neg4_24 (15), neg4_29 (16), neg4_30 (17)

**NEG5**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (16) e oltre 12 passaggi: neg5_18 (19), neg5_23 (17), neg5_24 (18)

**NEG6**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (8) e oltre 12 passaggi: neg6_33 (18), neg6_35 (17), neg6_36 (13)

**ODX1**
- attività piccola: il livello 2 ha 2 esercizi, il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**ODX2**
- attività piccola: il livello 1 ha 2 esercizi, il livello 2 ha 2 esercizi, il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**OF1**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (13) e oltre 12 passaggi: of1_8 (16)
- attività piccola: il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): of1_6/of1_4 (1|2)

**OF2**
- attività piccola: il livello 1 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**OF3**
- attività piccola: il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): of3_4/of3_3 (1|2)

**OF4**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (23) e oltre 12 passaggi: of4_17 (24)

**OF5**
- parti senza nessun esercizio nel bacino: Parte 10 · Dalla frazione di una frazione all'intero
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): of5_27/of5_12 (1|2)

**ON2**
- la mediana dei passaggi non cresce dal livello 1 (3) al livello 2 (3) e con gli esercizi disponibili non si può sistemare
- stesso punteggio ma livelli diversi (il taglio li separa per passaggi e lunghezza; si possono scambiare): on2_35/on2_25 (2|3)

**P1**
- la mediana dei passaggi non cresce dal livello 1 (2) al livello 2 (2) e con gli esercizi disponibili non si può sistemare
- scambi per la coerenza fra livelli: liv. 1: p1_14 (2 pass.) → p1_16 (1 pass.); liv. 1: p1_19 (2 pass.) → p1_17 (1 pass.); liv. 2: p1_4 (2 pass.) → p1_55 (3 pass.)
- parti senza nessun esercizio nel bacino: Parte 1 · Scrivere una potenza e calcolarla

**P3**
- scambi per la coerenza fra livelli: liv. 1: p3_49 (8 pass.) → p3_36 (2 pass.)

**P4**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (14) e oltre 12 passaggi: p4_7 (16)
- attività piccola: il livello 3 ha 2 esercizi. Chi resta su quel livello rivede presto lo stesso esercizio: servono esercizi nuovi o un bacino unico per più livelli

**PR2**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (18) e oltre 12 passaggi: pr2_31 (20), pr2_32 (26)

**PR4**
- scambi per la coerenza fra livelli: liv. 2: pr4_9 (6 pass.) → pr4_25 (4 pass.); liv. 2: pr4_15 (6 pass.) → pr4_26 (4 pass.); liv. 2: pr4_22 (6 pass.) → pr4_29 (4 pass.); liv. 2: pr4_23 (6 pass.) → pr4_32 (4 pass.); liv. 3: pr4_38 (3 pass.) → pr4_27 (5 pass.); liv. 1: pr4_12 (6 pass.) → pr4_33 (2 pass.)
- risposta da spiegare a parole o da scrivere liberamente, l'autovalutazione è meno netta: pr4_5 (liv. 1), pr4_7 (liv. 1)

**PX1**
- guide con due metodi uno dopo l'altro, quindi passaggi contati due volte e punteggio un po' gonfiato: px1_10 (liv. 1), px1_1 (liv. 3), px1_2 (liv. 3), px1_3 (liv. 3)
- consegna con un disegno, che la fase 3 deve mostrare insieme al testo: px1_4 (liv. 1), px1_5 (liv. 2), px1_6 (liv. 2), px1_1 (liv. 3), px1_2 (liv. 3), px1_3 (liv. 3)

**PX2**
- fuori dal livello 3 perché oltre il 90° percentile dei passaggi (12) e oltre 12 passaggi: px2_15 (13), px2_28 (15), px2_39 (13), px2_40 (13)
- parti senza nessun esercizio nel bacino: Parte F · Al supermercato
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

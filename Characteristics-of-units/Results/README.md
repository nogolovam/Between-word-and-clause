# Characteristics of units – results tables

Positional results for the PhD thesis *Between word and clause* (written
Czech, SUD annotation). Every table in this folder answers one version of a
single question:

> **Does a property of a syntactic unit depend on where that unit sits in the
> linear order of a larger unit?**

The properties tested are **length**, **degree of embedding**, and the
**variety of grammatical types** (DEPREL and UPOS). The units tested are the
**phrase**, the **subphrase**, the **chunk** and the **word**.

These are the full tables behind **Chapter 3, *Characteristics of units and
their position in the tree***.

---

## 1. Quick orientation

```
Results/
├── Phrase/          ← target unit: the phrase
├── Subphrase/       ← target unit: the subphrase
├── Chunk/           ← target unit: the chunk
│   ├── length/               how long is the unit at position k?
│   ├── embedding/            how deeply embedded is the unit at position k?
│   ├── deprel_entropy_type/  how varied are the DEPRELs at position k?
│   └── upos_entropy_type/    how varied are the UPOSes at position k?
└── Word/            ← target unit: the word
    └── length/               how long in syllables is the word at position k?
```

60 CSV files: 18 for the phrase, 21 for the subphrase, 18 for the chunk, 3 for
the word.

To find a table, answer three questions in this order:

| Question | Answer selects |
|---|---|
| Which unit am I measuring? | the top-level folder (`Phrase`, `Subphrase`, `Chunk`, `Word`) |
| What am I measuring about it? | the metric folder (`length`, `embedding`, `deprel_entropy_type`, `upos_entropy_type`) |
| Inside what larger unit is it positioned? | the file-name suffix (`_sentence`, `_clause`, `_subunit`, `_unit`) |

---

## 2. The units

The hierarchy used throughout is

> sentence — independent clause — clause — **phrase** — **subphrase** — **chunk** — **word** — syllable — phoneme

The independent clause is not analysed in this part of the thesis.

**Phrase.** Defined by a head and everything it governs. The first phrase of a
clause is the predicate together with its leftmost direct dependent and
everything dependent on that; each further dependent of the predicate heads a
phrase of its own. Every phrase therefore corresponds to one primary syntactic
branch of the predicate, with the predicate itself folded into the leftmost
branch.

**Subphrase.** A minimal, non-overlapping dependency chain inside a phrase. It
starts at the phrase root and continues as long as each following word has
exactly one dependent. A word that branches into several dependents starts a new
subphrase — except the subphrase root itself, which is allowed to branch.

**Chunk.** A unit of a subphrase, possibly a single word, meeting four
conditions: (a) all dependents share the same immediate head; (b) the chunk
spans a single level of dependency; (c) its words are linearly contiguous;
(d) no dependent inside the chunk governs anything outside it.

**Position** of a unit is the mean ID (linear index) of all its words, which
keeps discontinuous phrases and subphrases orderable. Ties are broken by the
lowest individual word ID. Words, which have a single ID, are ordered by it
directly.

---

## 3. Naming convention

```
03all_SUD_chunks_words_subunit.csv
│  │        │      │     └── construct: within what the position is measured
│  │        │      └──────── metric: what is measured
│  │        └─────────────── target unit: phrases / subphrases / chunks
│  └──────────────────────── dataset: the whole merged SUD-annotated material
└─────────────────────────── sort key only; orders files within the folder
```

**`Word/length/` inverts the middle field.** There the target unit is always the
word, and the unit named in the file — `01…phrases_syllables.csv`,
`02…subphrases_syllables.csv`, `03…chunks_syllables.csv` — is the *container*
the word sits in. Read `01all_SUD_phrases_syllables.csv` as "words inside
phrases".

### Construct suffixes

| Suffix | The unit inside which position is counted |
|---|---|
| `_sentence`, `_sen` | the sentence |
| `_clause`, `_cl`, `in_cl` | the clause |
| `_subunit`, `_subunits` | the **immediate higher-level unit** — the subphrase for chunks, the phrase for subphrases |
| `_unit` | none: position is counted **inside the target unit itself**, word by word |

`_subunit` and `_unit` are easy to confuse. `_subunit` still measures the target
unit, only inside a smaller construct. `_unit` looks *within* the target unit and
measures its individual words.

### Metric fragments

| Fragment | Meaning |
|---|---|
| `words` | length in words |
| `subunits` | length in immediate constituents (subphrases for phrases, chunks for subphrases) |
| `syllables` | length in syllables (`Word/length/` only) |
| `hdist_mean` | mean hierarchical distance = degree of embedding |
| `merged_normalized_seq` | normalised count of unique DEPREL/UPOS sequences |
| `merged_rel_entropy` | relative (normalised Shannon) entropy of those sequences |

---

## 4. How to read a table

Every file has the same shape. Row = one construct size. Column = one position
in that construct. Rows are **ragged**: a row for constructs of *k* units has
*k* filled position cells, so the header carries as many `Pos` columns as the
longest row needs and shorter rows simply stop early.

From `Chunk/length/01all_SUD_chunks_words_sentence.csv`:

| Weighted Parent Size | Count (N) | Pos 1 | Pos 2 | Pos 3 | Pos 4 | Pos 5 |
|---|---|---|---|---|---|---|
| 5.0 | 13429 | 1.5682 | 1.4006 | 1.3749 | 1.4346 | 1.7974 |

Read as: *there are 13,429 sentences made of exactly 5 chunks; averaged over all
of them, the first chunk is 1.57 words long, the third 1.37, the last 1.80.*
The rise in the final cell is the end-weight effect these tables were built to
test. The raised first cell in phrase- and chunk-level tables is a consequence of
the definition, which attaches the predicate to the leftmost phrase of the
clause.

### The first two columns

| Column | Meaning |
|---|---|
| `Weighted Parent Size` / `Weighted Parent Size (Words)` / `Weighted Avg Units (x)` | size of the construct, i.e. how many target units it contains. The three labels denote the same quantity; entropy files print it to 2 decimals, the others to 4. |
| `Count (N)` | number of constructs of that size in the dataset |
---


## 5. Source

These tables accompany the thesis and are referenced from it as
<https://github.com/nogolovam/Between-word-and-clause/tree/main/Characteristics-of-units>.
Definitions, worked examples and the figures built from these tables are in the
thesis sections *Length/complexity of syntactic units* and *The distribution of
unique grammatical types*.

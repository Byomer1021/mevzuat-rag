<!--
Final rapor taslağı (teslim 17 Aralık). Durum:
- Yazıldı, okunacak: 3 Data, 4 Method, 5 Experimental setup.
- Test koşusundan sonra (6-10 Aralık): Abstract'taki boşluklar, 6 Results, 7 Error analysis, 8 Ablation.
- Ömer Can: 1 Introduction, 2 Related work (araştırma lideri bölümü dahil).
- Kayıtlar: sayıların hepsi docs/olcumler.md ve docs/kararlar.md'de, bölüm numaraları yorumlarda.
-->

# Article or Window? Chunking Turkish University Regulations for Retrieval

Team 15 (RAGTU), CSE 484/654 Natural Language Processing, Gebze Technical University

## Abstract

Question answering over university regulations has to cut documents into chunks before retrieval.
We ask whether cutting Turkish regulations at their numbered articles (MADDE) retrieves the sentence
that answers a student's question more often than fixed-length windows of the same count. We build a
versioned knowledge base of 114 Gebze Technical University sources and two indexes that differ only in
chunk boundaries: 923 article chunks against 922 windows of 721 characters. Each answerable question
among 150 hand-written test questions carries the verbatim sentence that answers it, so both conditions
are scored on the same characters. With BM25 and multilingual-e5-base, windows reach evidence
Recall@5 of 0.274 and 0.429. Article chunks reach [METHOD RESULT], a difference of [Δ] (95% CI [LOW,
HIGH]). Removing the document-title prefix [ABLATION RESULT].

## 1 Introduction

[Ömer Can. Problem, why chunk boundaries matter for regulations, the research question and its "no"
result, contributions C1 to C3.]

## 2 Related work

[Ömer Can. Eight references from the Project Card, each with how we differ. Includes the research lead
section: two recent papers and the ablation.]

## 3 Data

### 3.1 Sources

The knowledge base holds 114 sources downloaded from GTÜ's public web sites in October 2026
(table 1). 109 of them are PDFs: regulations, directives, implementation principles, guides,
curricula and three FAQ documents. The other five are the academic calendar, the catalogue of
student forms and three collections of web pages (FAQ and unit pages, 201 items). Every file is listed
in `data/kaynaklar.csv` with its URL, download date and sha256.

| source type | count |
|---|---|
| directive (yönerge) | 48 |
| curriculum | 21 |
| implementation principles (esaslar) | 17 |
| guide | 14 |
| regulation (yönetmelik) | 4 |
| FAQ (PDF) | 3 |
| other legal text | 2 |
| academic calendar, form catalogue | 2 |
| web collections | 3 |
| **total** | **114** |

*Table 1. Sources in the knowledge base.*

The knowledge base was frozen on 7 November 2026 as version `b3c7d85cce08`, before most test questions
were written. At freezing we checked every source against the live site. 110 of the 111 checkable
sources were current. The only change was in the form catalogue (two unit forms revised and one form
for department-head elections added, none of them for students), so the frozen version was kept. The web collections were not crawled again.

Officially published regulations are free to reproduce under Law 5846, Article 31. For directives
and web pages no licence is stated. The public repository keeps the files as published, each with its
URL and sha256, and we remove any file on request.

### 3.2 Preprocessing

PDF text is read at line level with PyMuPDF. Every PDF in the knowledge base has a text layer, so no
OCR is needed. One downloaded curriculum had none and was left out. The
quality-form header and footer that GTÜ prints on each page (document number, revision, page) is
removed. This drops 4.2% of all characters. A scan for personal data found no traces.

A rule-based parser finds article headings. It recognises eleven heading formats seen in the
documents, such as `MADDE 8-`, `MADDE-7 –`, `Madde 3.`, `MADDE 12a:` and `EK MADDE 1 –`, and it keeps
the article title when there is one. 49 PDFs are article-structured. They hold 914 articles (901 regular,
8 provisional, 5 additional) and 9 introductory chunks. The other 60 PDFs have no articles and are cut
into paragraphs with a target of 395 characters, the median article length. Curriculum tables have no
blank lines, so long blocks are split at line ends. The calendar is cut into rows (150), the form
catalogue into student forms (141) and the web collections into items (1,914 chunks). In total the
knowledge base has 5,537 chunks.

Every chunk keeps its document, page range and character offsets in the cleaned document text. An
automatic check confirms that the chunks of each document cover its cleaned text without loss or
overlap, and that each page range is the narrowest one that contains the chunk. Articles are short
but uneven: median 395 characters, 90th percentile 1,580, maximum 9,289.

### 3.3 Questions

**Schema.** A question has a type (single article, multi-article or unanswerable), a reference answer,
the gold chunk(s) that answer it and, for each gold chunk, the sentence that carries the answer,
copied verbatim (the evidence). A validator rejects a question if an evidence sentence cannot be found
in its gold chunk (whitespace-insensitive) or if the number of gold chunks does not match the type.

**Writing.** Questions were written in the student's voice first (FAQ topics, forms, the calendar) and
looked up in the regulations afterwards (`docs/soru-yazma.md`). The rule exists because questions
written while reading an article reuse its words, which favours BM25 and may favour article chunks.
Team members wrote in a browser page that searches the chunks and checks evidence as it is selected.

**Splits.** Nothing is trained, so there is no training set (table 2). The dev set (51 questions) was
written by one team member in October and used for all development. The test set (150 questions) was
written by three team members between mid-October and 11 November. It was frozen on 11 November
(sha256 `b4bae07e3a80`) before any method run on it. No question appears in both sets.

| | dev | test |
|---|---|---|
| single article | 30 | 111 |
| multi-article | 13 | 20 |
| unanswerable | 8 | 19 |
| **total** | **51** | **150** |
| authors | 1 | 3 |
| compared (primary set) | 37 | 106 |

*Table 2. Question sets. The primary set holds the answerable questions whose gold chunks all lie in
the 49 article-structured PDFs.*

**Review before freezing.** Every incoming test question was checked against its evidence. Some
question topics came from a brainstorming list. 52 reference answers had been copied from that list
and were rewritten by a team member. 49 reference answers contradicted their evidence, added
information the article does not contain or were incomplete, and these were corrected. Ten questions
had their gold chunks, evidence sentence or type fixed. In one case two questions had swapped evidence, and one question marked
unanswerable turned out to be answered in a GTÜ FAQ. Two questions were removed: a duplicate and one
the regulation does not answer clearly.

**Agreement.** To measure label reliability, 40 test questions (20 from each of the two main authors,
stratified by type) are labelled again by the other author, who does not see the original labels. We
report Cohen's κ for answerability and type, and the share of questions where both labellers point to
the same article, the same document and the same evidence sentence. The protocol was fixed before the
second labels were collected (decision K-026). [Results after 30 November.]

**Example (dev).** "Derslere devam zorunluluğu yüzde kaç?" (What attendance rate do I need?) Gold
chunk: undergraduate regulation, Article 23, page 5. Evidence: "Teorik derslerde en az %70, laboratuvar
ve uygulamalı derslerde en az %80 devam zorunluluğu aranır."

## 4 Method

### 4.1 The two conditions

The comparison changes one thing: where chunks begin and end in the 49 article-structured PDFs.

- **Article chunks (method).** One chunk per article, with its heading: 923 chunks.
- **Windows (baseline).** The same 49 documents cut into windows of 721 characters, without overlap,
  each cut moved to the nearest word boundary: 922 chunks.

We chose 721 characters so that the two conditions have the same number of chunks, and therefore the
same mean chunk length. Dividing total characters by the article count gives 694. Word-boundary cuts
shorten windows, so we raised the size until the counts matched. The boundaries really differ: 60.1%
of articles are split across two or more windows, and 61.8% of windows touch more than one article.

Everything else is identical in the two conditions. The other 60 PDFs contribute the same paragraph
chunks, every chunk is indexed with its document title in front, and queries, retrievers and scoring
are the same. The experiment index holds only PDFs: 3,332 chunks with articles, 3,331 with windows.
Web pages, calendar rows and forms are left out of the experiment because they are identical in both
conditions. They cannot change the comparison, but FAQ pages written in the student's own words often
outrank the article that is the actual source.

### 4.2 Retrievers

**BM25.** rank-bm25 0.2.2 (BM25Okapi, k1 = 1.5, b = 0.75) over word tokens with Turkish-aware
lowercasing (I becomes ı, İ becomes i) and no stemming. The Snowball Turkish stemmer makes known errors
on this vocabulary ("devam" becomes "deva"), so stemming is left out.

**Dense.** multilingual-e5-base (revision d1287505) with its `query:` and `passage:` prefixes,
normalised embeddings and cosine similarity. The model reads at most 512 tokens. 43 of the 914 articles
(4.7%) are longer, so 3.0% of the article-condition text is never seen by the model. No window exceeds
the limit (the longest has 287 tokens). This is a known handicap of article chunks with this model.

The indexed text of every chunk is its document title, a line break and the chunk text. The title
separates documents that reuse the same article titles, such as the fifteen departmental internship
rules.

### 4.3 System and demo

The experiment isolates one design choice. The system around it answers questions over the whole
knowledge base, web pages included. It searches article chunks with e5, gives the language model the
five best document chunks and the two best web chunks, and asks it to answer only from these numbered
sources, cite them, and say it does not know when they do not contain the answer. The model is
Qwen3-8B in 4-bit on a free Colab T4. Answers for the demo questions are generated in advance and
matched to the live retrieval by the hash of the prompt. Answer generation is not part of the research
question and is evaluated on the dev set only (appendix [X]).

### 4.4 Compute

All retrieval runs on a laptop CPU (Intel i7-8750H). The GPU of this machine is faulty and is not used.
Encoding both experiment indexes with e5 takes 988 s once and is cached afterwards. BM25 indexes build
in under a second. A full baseline run from a fresh clone, including preprocessing and e5 encoding,
took 928 s. Answer generation for 51 questions takes 9 to 13 minutes on a Colab T4.

## 5 Experimental setup

### 5.1 Metric

The primary metric is evidence Recall@5. A question's evidence counts as found if its characters lie
entirely inside the union of the top 5 chunks that come from the gold document. The test looks at
character offsets, so it means the same in both conditions. An evidence sentence that a window
boundary splits needs both windows in the top 5. The same sentence in another document does not count,
because the system has to cite the right source. For multi-article questions the score is the share of
evidence found. We also report Recall@1, Recall@10 and MRR@10, where a question's rank is the first
rank at which all its evidence is covered. Unanswerable questions have no evidence and are left out of
retrieval metrics.

### 5.2 Question sets

The primary set holds the answerable questions whose gold chunks all lie in the 49 article-structured
PDFs: 106 test questions. These are the questions the chunking can affect. We also report the all-PDF
set (123 test questions), which adds questions answered in the other PDFs.

### 5.3 Statistics and decision rule

For each retriever we compute the mean per-question difference, article minus window, with a 95%
percentile interval from a paired bootstrap over questions (10,000 resamples, seed 0). An exact
McNemar test on hits at Recall@5 serves as a check. The answer to the research question is "no" for a
retriever if the interval contains zero. With 106 questions the interval spans about ±9 points when
20% of questions disagree, so smaller differences will be reported as not distinguishable. This rule
was fixed in the proposal on 21 October, before any test result.

### 5.4 Protocol

The knowledge base was frozen on 7 November and the test set on 11 November. The experiment script
checks the test set against its frozen hash and refuses to run the method on the test set before the
final run. Until then only the baseline ran on test (for the mid-project report). All development,
including the analyses in sections 7 and 8 on dev, used the dev set only. The method runs on the test
set once, together with the ablation.

### 5.5 Ablation and further analyses

**Ablation.** We remove the document-title prefix from both conditions. If article chunks win only
with the title, the gain comes from identifying the document rather than from the boundaries (claim
C3).

**Split analysis.** To separate the metric from retrieval, we also score with a lenient rule: an
evidence sentence counts as found if any chunk that overlaps it is retrieved. The lenient rule is
applied to both conditions.

### 5.6 Reproducibility

The repository is public (github.com/Byomer1021/mevzuat-rag). One command, `uv run python
scripts/tablo.py`, rebuilds the baseline table from a fresh clone, including preprocessing. We checked
this on a fresh clone and got the same table. Versions: Python 3.12.10, torch 2.7.1 (CPU),
sentence-transformers 6.1.0, rank-bm25 0.2.2, multilingual-e5-base revision d1287505. Knowledge base
`b3c7d85cce08`, chunks `2b5af885972a`, test set `b4bae07e3a80`. BM25 and e5 are deterministic on CPU,
and the bootstrap uses seed 0.

## 6 Results

[After the test run, 6-10 December. Table: BM25 and e5, windows and articles, R@1, R@5, R@10, MRR@10
with intervals, differences and McNemar, primary and all-PDF sets.]

## 7 Error analysis

[After the test run. Baseline errors on test are already grouped (BM25 80, e5 63, six categories). Add
the method's errors and the split analysis on test.]

## 8 Ablation

[After the test run. On dev (37 questions), without the title the e5 difference fell from +23.0 to
+9.5 points and its interval included zero.]

## 9 Limitations

[To write. Notes so far: the dev set has one author. One person scored the generated answers.
Agreement is measured on 40 questions. 43 articles exceed e5's input. The generation step tends to answer
unanswerable questions.]

## Appendix

**A. Answer generation (dev).** [Pilot of Qwen3-4B and Qwen3-8B, blind manual scoring of 153 answers.]

**B. Who did what.** [To write.]

**C. AI tools.** [To write.]

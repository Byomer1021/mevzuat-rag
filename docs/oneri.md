# Project proposal: source text

Kaynak metin. `scripts/oneri_docx.py` bunu dersin resmî formuna yazar
(`## <anahtar>` başlıkları formdaki kutular; boş satır paragraf, `**…**`
kalın). Sayılar `results/onisleme.json` ve `results/ilk_bakis.json`'dan,
bilgi tabanı sürümü `b3c7d85cce08`. Köşeli parantezli yerler doldurulmadan
teslim edilmez.

## team

[Team ##]

## members

Ahmet Eren İncir, [student number], CSE 654 (**research lead**)

Ömer Can Atlı, [student number], CSE 484

Veysel Cemaloğlu, [student number], CSE 484

Muhammed Korkmaz, [student number], CSE 484

## type

System

## 1

On at least 150 hand-written student questions about Gebze Technical University's undergraduate regulations (test split), does cutting the regulations at article (MADDE) boundaries retrieve the sentence that answers the question more often than fixed-length chunks of equal count, with the same retriever? Metric: evidence Recall@5, tested separately for BM25 and for a dense retriever (multilingual-e5-base).

**No**, for a retriever, if the 95% paired-bootstrap confidence interval of the Recall@5 difference (article − fixed) contains zero.

## 2

Turkish universities publish their rules as regulations and directives written in numbered articles (MADDE), and students ask about them daily. Anyone building question answering over them must choose how to cut the text: article-aware cutting needs a custom parser (ours handles 11 header formats), fixed windows are free.

**Closest work.** (1) *turkish-legal-retrieval* (GitHub, Aug 2026) compares whole articles, fixed windows and structural cuts on 907 Turkish laws. With a dense retriever, whole articles lost to 400-token windows (570 vs 669 of 5,010 found at R@10, McNemar p < 0.001), partly because 8.1% of articles exceed the 512-token model limit; structural cuts were no better than windows. Its queries are citing passages built from cross-references, not questions. (2) LegalBench-RAG (Pipitone & Alami, 2024) labels the relevant text of each legal query as character spans within documents, independent of any chunking; we label evidence the same way. (3) Element-based chunking beat fixed windows on financial reports (Jimeno Yepes et al., 2024); more in box 7.

**Left open:** whether article boundaries matter for real user questions over short, uniformly structured regulations (median article 395 characters).

## 3

**Knowledge base** (built, versioned, sha256 per file): GTÜ regulations, directives and guides in Turkish, from kalite.gtu.edu.tr and unit pages; 109 PDFs, 49 of them article-structured (914 articles). FAQ and other web pages are in the system but not in this experiment. **Licence:** officially published regulations are free to reproduce and use (Law No. 5846 on Intellectual and Artistic Works, Art. 31); for directives and web pages this is not explicit, so the public repository will hold code, questions and chunk IDs, and a download script instead of the files.

**Questions** (none written yet; no training data): 50 dev by 1 Nov, at least 150 test by 22 Nov, written by hand before any test run. Each has a type (single article, several articles, unanswerable), gold chunk IDs, a reference answer, and an evidence quote copied verbatim from each gold article; a validator rejects quotes not found in that article.

**Example (dev):** "Derslere devam zorunluluğu yüzde kaç?" → gold `lisans-yonetmelik/m23` (p. 5); evidence: "Teorik derslerde en az %70, laboratuvar ve uygulamalı derslerde en az %80 devam zorunluluğu aranır."; answer: 70% for theory, 80% for lab and practice courses.

## 4

Nothing is trained. Two indexes over the same 109 PDFs differ only in how the 49 article-structured documents are cut. **Baseline:** fixed windows of 721 characters, no overlap, cut at a word boundary; the size makes both indexes hold the same number of chunks (922 vs 923), hence the same mean chunk length. **Method:** one chunk per article, with its heading. The other 60 documents are cut into paragraphs identically in both. Every chunk carries its document title in both conditions.

Retrievers: BM25 (rank-bm25, Turkish-aware lowercasing, no stemming) and multilingual-e5-base (planned, not yet run). Compute: one GTX 1080 (8 GB); both BM25 indexes build in under a second. Answer generation with citations is the demo, outside the comparison. **Fair** because only chunk boundaries change: same documents, text, chunk count, title prefix, queries and scoring.

## 5

**Evidence Recall@5** (primary): a question counts as found when its evidence quote lies entirely within the top 5 chunks from the gold document; a quote split across two windows needs both. The criterion does not depend on chunking, so both conditions are scored on the same characters. Also Recall@1, Recall@10 and MRR. **Test set:** test questions whose evidence is in the 49 article-structured documents; all tuning on dev, test run once.

**Noise:** paired bootstrap over questions (10,000 resamples, 95% CI of the difference), exact McNemar as a check. If about 20% of question pairs disagree (an assumption, to be measured on dev), the CI half-width at n = 150 is about 7 points; smaller differences will be reported as not distinguishable.

## 6

In the 49 article-structured documents, fixed windows of equal count **cut 60.1% of the 914 articles** into two or more pieces, and **61.8% of the 922 windows mix text from two or more articles**.

One dev query, BM25: "Derslere devam zorunluluğu yüzde kaç?" With article chunks the gold article ranks **4th**; rank 1 is the English-preparatory attendance rule (85%), a plausible answer for the wrong programme. With fixed windows, the window that contains the whole gold article ranks **10th**.

*Shows:* the two conditions differ in most of the text, not at the margins, and one case where a window dilutes a 298-character article with its neighbours. *Does not show:* any average difference. It is one query, chosen by us, from the dev split; no test question has been run.

## 7

**Ahmet Eren İncir.** [Draft; Ahmet Eren revises and owns this box.] (1) Qu, Tu & Bao (Findings of NAACL 2025) find semantic chunking not worth its cost over fixed-size chunks for document and evidence retrieval. Their alternative to fixed windows is cutting by sentence similarity, not boundaries the document itself declares; ours is the article structure the author wrote. (2) Reuter et al. (arXiv 2510.06999, 2025) show that legal retrievers often return text from the wrong one of many similar documents, and reduce it by prepending a document summary to every chunk. They vary the context added to chunks; we hold it fixed (the document title) and vary only where chunks begin and end.

**Ablation:** drop the title prefix in both conditions. If article chunks win only with it, the gain comes from identifying the document, not from the boundaries.

## 8

**The test set.** Questions written while reading an article reuse its words, which favours BM25 and may favour article chunks. Mitigation: write each question from the student's side first (FAQ topics, forms, the academic calendar), then look up the article; all four of us write, so no single style dominates, and two of us label the same 40 questions independently to report agreement. **Fallback:** if fewer than 150 test questions exist on 22 Nov, run on what exists and report the wider interval; question and metric stay the same. **Second risk:** 57 articles exceed 2,000 characters and may exceed the dense model's 512-token limit (not yet measured); there the article condition loses text the windows keep, as in box 2. We will count the test questions affected and report them separately.

## 9

**Mid-project (5 Nov):** BM25 Recall@1/5/10 and MRR for both conditions on the 50 dev questions, with intervals; dense results if ready. Then: test questions (22 Nov), dense runs (29 Nov), single test run and error analysis (6–10 Dec), report and code (17 Dec).

**Roles:** Ahmet Eren İncir: research lead, related work, experimental design and the ablation in box 7. Ömer Can Atlı: modelling (chunking and retrieval). Veysel Cemaloğlu: data (questions and evidence sentences). Muhammed Korkmaz: evaluation and demo. All four write questions.

**AI tools:** Claude (Anthropic), through Claude Code, wrote and tested code, ran the measurements in boxes 3 and 6, and drafted this text. All numbers come from scripts in the repository; [we checked them].

## 10

Not yet.

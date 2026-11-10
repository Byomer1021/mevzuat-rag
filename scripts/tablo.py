"""Sonuç tablosu, tek komutla: taban sistem (sabit pencere) dondurulmuş test setinde.

    uv run python scripts/tablo.py

BM25 ve e5 için scripts/deney.py --bolum test --kosul sabit çalışır, tablo
results/tablo.md'ye yazılır. Yöntemin (madde) satırları boş kalır: onun test
sonucu en sonda, bir kez alınır (deney.py --son). e5 vektörleri
.cache/gomme/'de yoksa ilk çalıştırma CPU'da ~16 dk sürer.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
OLCULER = ("R@1", "R@5", "R@10", "MRR@10")
SISTEMLER = [("BM25", "bm25"), ("e5 (multilingual-e5-base)", "e5")]


def hucre(a: dict) -> str:
    return f"{a['ortalama']:.3f} [{a['alt']:.3f}, {a['ust']:.3f}]"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ortam = {**os.environ, "CUDA_VISIBLE_DEVICES": ""}  # K-002
    for _, arama in SISTEMLER:
        subprocess.run([sys.executable, str(KOK / "scripts" / "deney.py"), "--bolum", "test",
                        "--kosul", "sabit", "--arama", arama], check=True, env=ortam, cwd=KOK)

    satirlar, ust = [], None
    for ad, arama in SISTEMLER:
        r = json.loads((KOK / "results" / "deney" / f"{arama}-sabit-test.json").read_text(encoding="utf-8"))
        s = r["sonuclar"]["birincil"]
        ust = ust or (r["test_dondurma"], r["bilgi_tabani_surumu"], r["parca_surumu"], s["n"])
        satirlar.append(f"| {ad} + 721-character windows (baseline) | "
                        + " | ".join(hucre(s["aralik"]["sabit"][o]) for o in OLCULER) + " |")
        satirlar.append(f"| {ad} + article chunks (method) | " + " | ".join("—" for _ in OLCULER) + " |")
    dondurma, bt, ps, n = ust
    metin = "\n".join([
        (f"Test set frozen {dondurma['tarih']} ({dondurma['n']} questions, sha256 "
         f"{dondurma['ozet'][:12]}); primary set n = {n}. Knowledge base {bt}, chunks {ps}."),
        "Mean evidence recall, 95% paired-bootstrap interval over questions (10,000 resamples, seed 0).",
        "",
        "| System | " + " | ".join(OLCULER) + " |",
        "|---|" + "---|" * len(OLCULER),
        *satirlar,
        "",
        "Method rows stay empty until the single final test run (scripts/deney.py --son).",
    ])
    (KOK / "results" / "tablo.md").write_text(metin + "\n", encoding="utf-8")
    print("\n" + metin)


if __name__ == "__main__":
    main()

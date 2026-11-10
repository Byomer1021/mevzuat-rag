"""Test setini dondurur: soruların özetini data/testset/dondurma.json'a yazar.

    uv run python scripts/test_dondur.py              # dondur
    uv run python scripts/test_dondur.py --yeniden    # bilerek yeniden dondur (gerekçe kararlar.md'ye)

Dondurmadan sonra test sorusu eklenir ya da değişirse scripts/deney.py test
setinde çalışmaz: sonuçlar dondurulan sete aittir. Dondurmadan önce bütün
test soruları şemaya göre denetlenir.
"""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from mevzuat_rag.testset import bolum_ozeti, dogrula, oku, parcalari_oku

KOK = Path(__file__).resolve().parents[1]
SORULAR = KOK / "data" / "testset" / "sorular.jsonl"
DONDURMA = KOK / "data" / "testset" / "dondurma.json"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--yeniden", action="store_true")
    a = ap.parse_args()
    if DONDURMA.exists() and not a.yeniden:
        sys.exit(f"test seti zaten dondurulmuş: {DONDURMA.read_text(encoding='utf-8')}")

    sorular = oku(SORULAR)
    test = [s for s in sorular if s["bolum"] == "test"]
    if not test:
        sys.exit("test bölümünde soru yok")
    parcalar = {p["id"]: p["metin"]
                for p in parcalari_oku(KOK / "data" / "processed" / "parcalar_madde.jsonl")}
    hatali = [(s["id"], h) for s in test
              if (h := dogrula(s, parcalar, {x["id"] for x in sorular} - {s["id"]}))]
    if hatali:
        sys.exit("denetimden geçmeyen sorular:\n" + "\n".join(f"  {i}: {'; '.join(h)}" for i, h in hatali))

    rapor = json.loads((KOK / "results" / "onisleme.json").read_text(encoding="utf-8"))
    kayit = {
        "tarih": time.strftime("%Y-%m-%d %H:%M"),
        "n": len(test),
        "tur": dict(Counter(s["tur"] for s in test)),
        "yazan": dict(Counter(s["yazan"] for s in test)),
        "ozet": bolum_ozeti(sorular, "test"),
        "bilgi_tabani_surumu": rapor["bilgi_tabani_surumu"],
        "parca_surumu": rapor["parca_surumu"],
    }
    DONDURMA.write_text(json.dumps(kayit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(kayit, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

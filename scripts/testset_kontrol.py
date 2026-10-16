"""Test setini denetler ve dağılımını yazar. Elle düzenlenen dosya için.

    uv run python scripts/testset_kontrol.py [data/testset/sorular.jsonl]
"""

import json
import sys
from pathlib import Path

from mevzuat_rag.testset import dogrula, oku, ozet, parcalari_oku

KOK = Path(__file__).resolve().parents[1]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    yol = Path(sys.argv[1]) if len(sys.argv) > 1 else KOK / "data" / "testset" / "sorular.jsonl"
    parca_idleri = {p["id"] for p in parcalari_oku(KOK / "data" / "processed" / "parcalar_madde.jsonl")}
    sorular = oku(yol)
    hatali, gorulen = 0, set()
    for s in sorular:
        hatalar = dogrula(s, parca_idleri, gorulen)
        gorulen.add(s.get("id"))
        for h in hatalar:
            print(f"{s.get('id', '?')}: {h}")
        hatali += bool(hatalar)
    print(json.dumps(ozet(sorular), ensure_ascii=False, indent=2))
    print(f"{len(sorular)} soru, {hatali} hatalı")
    sys.exit(1 if hatali else 0)


if __name__ == "__main__":
    main()

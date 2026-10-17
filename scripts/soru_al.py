"""Soru defterinden gelen soruları test setine katar.

    uv run python scripts/soru_al.py gelen/veysel.jsonl gelen/ahmet.txt ...
    uv run python scripts/soru_al.py -          # panodan yapıştır, Ctrl+Z Enter

Her satır defterin "Dışa aktar" çıktısındaki bir soru. Aynı satırları tekrar
vermek güvenli: bilinen soru atlanır, düzenlenmiş soru yerinde güncellenir
(eşleme data/testset/defter.json'da). Şemaya uymayan soru alınmaz, nedeni
yazılır.
"""

import json
import sys
from pathlib import Path

from mevzuat_rag.testset import hepsini_yaz, iceri_al, oku, ozet, parcalari_oku

KOK = Path(__file__).resolve().parents[1]
SORULAR = KOK / "data" / "testset" / "sorular.jsonl"
DEFTER = KOK / "data" / "testset" / "defter.json"


def satirlar(kaynak: str) -> list[str]:
    if kaynak == "-":
        return sys.stdin.read().splitlines()
    return Path(kaynak).read_text(encoding="utf-8-sig").splitlines()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gelenler = []
    for kaynak in sys.argv[1:]:
        for n, s in enumerate(satirlar(kaynak), 1):
            if not s.strip():
                continue
            try:
                gelenler.append(json.loads(s))
            except json.JSONDecodeError as e:
                print(f"{kaynak}:{n}: okunamadı ({e.msg}); satır kopyalanırken bölünmüş olabilir")
    parcalar = {p["id"]: p["metin"]
                for p in parcalari_oku(KOK / "data" / "processed" / "parcalar_madde.jsonl")}
    defter = json.loads(DEFTER.read_text(encoding="utf-8")) if DEFTER.exists() else {}
    sorular, defter, rapor = iceri_al(oku(SORULAR), gelenler, parcalar, defter)
    hepsini_yaz(SORULAR, sorular)
    DEFTER.write_text(json.dumps(defter, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\n".join(rapor))
    print(json.dumps(ozet(sorular), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

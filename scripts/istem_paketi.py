"""Colab'a gidecek istem paketi: her soru için arama burada yapılır, istem hazır yazılır.

    uv run python scripts/istem_paketi.py                       # dev, BM25, madde, k=5, bütün bilgi tabanı
    uv run python scripts/istem_paketi.py --arama e5 --k 8
    uv run python scripts/istem_paketi.py --kosul sabit --dizin pdf

Çıktı: results/istem/<ad>.jsonl (satır başına bir soru: kaynak kimlikleri,
künyeler, sohbet mesajları) ve <ad>.ust.json (konfigürasyon, sürümler). Paket
Colab'da notebooks/cevap_uret.ipynb ile cevaplanır; cevaplar
scripts/cevap_ozet.py ile ölçülür. Cevapsız sorular da pakete girer:
"bilmiyorum" demesi gereken yerler onlar.
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

if "--cihaz" not in sys.argv:  # GPU'yu torch yüklenmeden gizle (K-002)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

from mevzuat_rag.arama import E5, BM25Dizin, YogunDizin
from mevzuat_rag.deney import deney_parcalari
from mevzuat_rag.testset import oku, parcalari_oku
from mevzuat_rag.uretim import istem, kunye

KOK = Path(__file__).resolve().parents[1]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arama", choices=("bm25", "e5"), default="bm25")
    ap.add_argument("--kosul", choices=("madde", "sabit"), default="madde")
    ap.add_argument("--dizin", choices=("tum", "pdf"), default="tum",
                    help="tum: sistemin bütün bilgi tabanı; pdf: deneyin dizini")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--bolum", choices=("dev", "test"), default="dev")
    ap.add_argument("--sorular", type=Path, default=KOK / "data" / "testset" / "sorular.jsonl")
    ap.add_argument("--cihaz", default="cpu")
    ap.add_argument("--ad")
    a = ap.parse_args()

    parcalar = parcalari_oku(KOK / "data" / "processed" / f"parcalar_{a.kosul}.jsonl")
    if a.dizin == "pdf":
        parcalar = deney_parcalari(parcalar)
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        adlar = {r["belge_id"]: r["baslik"] for r in csv.DictReader(f)}
    if a.arama == "bm25":
        dizin = BM25Dizin(parcalar, adlar)
    else:
        dizin = YogunDizin(parcalar, adlar, onbellek=KOK / ".cache" / "gomme", cihaz=a.cihaz)
    parca = {p["id"]: p for p in parcalar}

    sorular = [s for s in oku(a.sorular) if s["bolum"] == a.bolum]
    ad = a.ad or f"{a.bolum}-{a.arama}-{a.kosul}-{a.dizin}-k{a.k}"
    klasor = KOK / "results" / "istem"
    klasor.mkdir(parents=True, exist_ok=True)
    with (klasor / f"{ad}.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for s in sorular:
            ids = [x.id for x in dizin.ara(s["soru"], a.k)]
            ps = [parca[i] for i in ids]
            f.write(json.dumps({"id": s["id"], "soru": s["soru"], "kaynaklar": ids,
                                "kunyeler": [kunye(p, adlar) for p in ps],
                                "mesajlar": istem(s["soru"], ps, adlar)}, ensure_ascii=False) + "\n")
    rapor = json.loads((KOK / "results" / "onisleme.json").read_text(encoding="utf-8"))
    ust = {"ad": ad, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "bilgi_tabani_surumu": rapor["bilgi_tabani_surumu"], "parca_surumu": rapor["parca_surumu"],
           "arama": a.arama, "model": E5 if a.arama == "e5" else None, "kosul": a.kosul,
           "dizin": a.dizin, "k": a.k, "bolum": a.bolum, "soru": len(sorular)}
    (klasor / f"{ad}.ust.json").write_text(json.dumps(ust, ensure_ascii=False, indent=1) + "\n",
                                           encoding="utf-8")
    print(f"{len(sorular)} soru -> results/istem/{ad}.jsonl")


if __name__ == "__main__":
    main()

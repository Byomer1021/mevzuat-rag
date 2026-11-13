"""Colab'a gidecek istem paketi: her soru için arama burada yapılır, istem hazır yazılır.

    uv run python scripts/istem_paketi.py                       # dev, BM25, madde, k=5, bütün bilgi tabanı
    uv run python scripts/istem_paketi.py --arama e5 --k 8
    uv run python scripts/istem_paketi.py --kosul sabit --dizin pdf
    uv run python scripts/istem_paketi.py --arama e5 --secim demo   # demonun kaynak seçimi (K-025)

--secim demo, demonun kodunu (src/mevzuat_rag/demo.py) olduğu gibi çağırır:
bütün bilgi tabanı, madde koşulu, önce 3 belge sonra 2 web parçası. Pilot
böylece demoda gösterilecek istemin aynısıyla yapılır.

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
from mevzuat_rag.demo import bilgi_tabani, cevapla, dizin_kur
from mevzuat_rag.deney import deney_parcalari
from mevzuat_rag.testset import oku, parcalari_oku
from mevzuat_rag.uretim import istem, kunye

KOK = Path(__file__).resolve().parents[1]
K_BELGE, K_WEB = 3, 2  # demonun varsayılanı (K-025)


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
    ap.add_argument("--secim", choices=("tek", "demo"), default="tek",
                    help="tek: tek sıralamadan ilk k; demo: demonun seçimi (--kosul, --dizin, --k yok sayılır)")
    a = ap.parse_args()
    if a.secim == "demo":
        return demo_paketi(a)

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
    ust_yaz(klasor, ad, a, len(sorular), kosul=a.kosul, dizin=a.dizin, k=a.k)


def ust_yaz(klasor: Path, ad: str, a, n: int, **konf):
    rapor = json.loads((KOK / "results" / "onisleme.json").read_text(encoding="utf-8"))
    ust = {"ad": ad, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "bilgi_tabani_surumu": rapor["bilgi_tabani_surumu"], "parca_surumu": rapor["parca_surumu"],
           "arama": a.arama, "model": E5 if a.arama == "e5" else None, **konf,
           "bolum": a.bolum, "soru": n}
    (klasor / f"{ad}.ust.json").write_text(json.dumps(ust, ensure_ascii=False, indent=1) + "\n",
                                           encoding="utf-8")
    print(f"{n} soru -> results/istem/{ad}.jsonl")


def demo_paketi(a):
    bt = bilgi_tabani()
    dizin = dizin_kur(a.arama, bt, cihaz=a.cihaz)
    sorular = [s for s in oku(a.sorular) if s["bolum"] == a.bolum]
    ad = a.ad or f"{a.bolum}-{a.arama}-demo"
    klasor = KOK / "results" / "istem"
    klasor.mkdir(parents=True, exist_ok=True)
    with (klasor / f"{ad}.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for s in sorular:
            r = cevapla(s["soru"], dizin, bt, K_BELGE, K_WEB)
            f.write(json.dumps({"id": s["id"], "soru": s["soru"], "kaynaklar": [p["id"] for p in r["kaynaklar"]],
                                "kunyeler": [kunye(p, bt.adlar) for p in r["kaynaklar"]],
                                "mesajlar": r["mesajlar"]}, ensure_ascii=False) + "\n")
    ust_yaz(klasor, ad, a, len(sorular), kosul="madde", dizin="tum", secim="demo",
            k_belge=K_BELGE, k_web=K_WEB)


if __name__ == "__main__":
    main()

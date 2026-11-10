"""Araştırma sorusunun deneyi: madde mi, aynı sayıda sabit parça mı (K-022).

    uv run python scripts/deney.py                         # BM25, dev
    uv run python scripts/deney.py --arama e5               # yoğun arama
    uv run python scripts/deney.py --kok                    # BM25 + kök bulma (K-013)
    uv run python scripts/deney.py --onek-yok               # ablasyon: belge adı öneki yok
    uv run python scripts/deney.py --bolum test --kosul sabit   # taban sistem, test seti
    uv run python scripts/deney.py --bolum test --son           # yöntem de: bir kez, en sonda

Sonuç: results/deney/<ad>.json ve ekranda tablo. Her sonuç bilgi tabanı
sürümünü ve konfigürasyonu taşır. Test seti yalnız dondurulduğu hâliyle
çalışır (scripts/test_dondur.py); yöntemin (madde) test sonucu ancak --son
ile alınır, ara aşamada test setinde yalnız taban sistem (sabit) çalışır.
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

# GPU'yu torch yüklenmeden gizle: geliştirme makinesinin kartı yük altında
# düşüyor (K-002). Başka makinede GPU için: --cihaz cuda.
if "--cihaz" not in sys.argv:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

from mevzuat_rag.arama import E5, BM25Dizin, YogunDizin
from mevzuat_rag.deney import calistir, deney_parcalari, soru_kumeleri
from mevzuat_rag.testset import dondurma_denetle, oku, parcalari_oku

KOK = Path(__file__).resolve().parents[1]
ISLENMIS = KOK / "data" / "processed"
DONDURMA = KOK / "data" / "testset" / "dondurma.json"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arama", choices=("bm25", "e5"), default="bm25")
    ap.add_argument("--kok", action="store_true", help="BM25'te Türkçe kök bulma")
    ap.add_argument("--onek-yok", action="store_true", help="belge adı önekini kaldır")
    ap.add_argument("--bolum", choices=("dev", "test"), default="dev")
    ap.add_argument("--sorular", type=Path, default=KOK / "data" / "testset" / "sorular.jsonl")
    ap.add_argument("--ad", help="sonuç dosyasının adı")
    ap.add_argument("--cihaz", default="cpu", help="yoğun arama cihazı; varsayılan cpu (K-002)")
    ap.add_argument("--kosul", choices=("ikisi", "madde", "sabit"), default="ikisi")
    ap.add_argument("--son", action="store_true", help="yöntemin test sonucu: tek çalıştırma")
    a = ap.parse_args()
    if a.kok and a.arama != "bm25":
        ap.error("--kok yalnız BM25 için")
    dondurma = None
    if a.bolum == "test":
        if a.kosul != "sabit" and not a.son:
            ap.error("yöntemin (madde) test sonucu en sonda, bir kez alınır: ara aşamada "
                     "--kosul sabit, son çalıştırmada --son")
        dondurma = json.loads(DONDURMA.read_text(encoding="utf-8")) if DONDURMA.exists() else None
        if sorun := dondurma_denetle(oku(a.sorular), dondurma):
            ap.error(sorun)

    madde = parcalari_oku(ISLENMIS / "parcalar_madde.jsonl")
    sabit = parcalari_oku(ISLENMIS / "parcalar_sabit.jsonl")
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        adlar = None if a.onek_yok else {r["belge_id"]: r["baslik"] for r in csv.DictReader(f)}
    kumeler = {"madde": deney_parcalari(madde), "sabit": deney_parcalari(sabit)}
    if a.kosul != "ikisi":
        kumeler = {a.kosul: kumeler[a.kosul]}

    t0 = time.perf_counter()
    if a.arama == "bm25":
        dizinler = {ad: BM25Dizin(ps, adlar, kok=a.kok) for ad, ps in kumeler.items()}
    else:
        dizinler = {ad: YogunDizin(ps, adlar, onbellek=KOK / ".cache" / "gomme", cihaz=a.cihaz)
                    for ad, ps in kumeler.items()}
    kurma = time.perf_counter() - t0
    arayicilar = {ad: (lambda s, k, d=d: [x.id for x in d.ara(s, k)]) for ad, d in dizinler.items()}

    sorular = [s for s in oku(a.sorular) if s["bolum"] == a.bolum]
    altkumeler = soru_kumeleri(sorular, madde)
    dayanak = {p["id"]: p for p in madde}
    t0 = time.perf_counter()
    sonuclar = {ad: calistir(ss, kumeler, arayicilar, dayanak) for ad, ss in altkumeler.items()}
    sure = time.perf_counter() - t0

    rapor_on = json.loads((KOK / "results" / "onisleme.json").read_text(encoding="utf-8"))
    ad = a.ad or "-".join(x for x in [a.arama, "kok" if a.kok else "", "onekyok" if a.onek_yok else "",
                                     "" if a.kosul == "ikisi" else a.kosul, a.bolum] if x)
    cikti = {
        "bilgi_tabani_surumu": rapor_on["bilgi_tabani_surumu"],
        "parca_surumu": rapor_on["parca_surumu"],
        "sabit_boyut": rapor_on["sabit_karsilastirma"]["boyut"],
        "konfigurasyon": {"arama": a.arama, "model": E5 if a.arama == "e5" else None,
                          "cihaz": a.cihaz if a.arama == "e5" else None,
                          "kok": a.kok, "belge_adi_oneki": not a.onek_yok, "bolum": a.bolum,
                          "kosul": a.kosul,
                          "sorular": str(a.sorular.relative_to(KOK) if a.sorular.is_relative_to(KOK)
                                         else a.sorular)},
        "test_dondurma": dondurma,
        "zaman": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sure_s": {"dizin": round(kurma, 1), "sorgular": round(sure, 1)},
        "soru_sayisi": {"bolumde": len(sorular), **{k: len(v) for k, v in altkumeler.items()}},
        "sonuclar": sonuclar,
    }
    yol = KOK / "results" / "deney" / f"{ad}.json"
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(cikti, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{ad}: {len(sorular)} soru ({a.bolum}); dizin {kurma:.1f} s, sorgular {sure:.1f} s")
    for kume_adi, s in sonuclar.items():
        print(f"\n[{kume_adi}] n = {s['n']}")
        if not s["n"]:
            continue
        for kosul, m in s["aralik"].items():
            print(f"  {kosul:6} " + "  ".join(f"{k} {v['ortalama']:.3f} [{v['alt']:.3f}, {v['ust']:.3f}]"
                                             for k, v in m.items()))
        for olcu, f in s["fark"].items():
            print(f"  fark {olcu}: {f['fark']:+.3f}  %95 aralık [{f['alt']:+.3f}, {f['ust']:+.3f}]")
        if m := s.get("mcnemar_R@5"):
            print(f"  McNemar R@5: yalnız madde {m['yalniz_a']}, yalnız sabit {m['yalniz_b']}, "
                  f"p = {m['p']:.3f}")
    print(f"\n-> {yol.relative_to(KOK)}")


if __name__ == "__main__":
    main()

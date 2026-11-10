"""Bir deney çıktısındaki hataları kategorilere ayırır (src/mevzuat_rag/hata.py).

    uv run python scripts/hata_analizi.py results/deney/bm25-sabit-test.json
    uv run python scripts/hata_analizi.py results/deney/e5-dev.json --kosul madde

Hata: birincil kümede kanıtı ilk 5 parçada tam kapsanmayan soru. Çıktı
results/hata/<ad>-<koşul>.json (soru başına kategori) ve .md (sayılar ve
kategori başına bir örnek).
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from mevzuat_rag.degerlendirme import Kume, kanitlar
from mevzuat_rag.deney import MADDE_TURLERI, deney_parcalari
from mevzuat_rag.hata import KATEGORILER, kategori
from mevzuat_rag.testset import oku, parcalari_oku

KOK = Path(__file__).resolve().parents[1]
ISLENMIS = KOK / "data" / "processed"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sonuc", type=Path)
    ap.add_argument("--kosul", choices=("madde", "sabit"), default="sabit")
    ap.add_argument("--kume", default="birincil")
    a = ap.parse_args()

    r = json.loads(a.sonuc.read_text(encoding="utf-8"))
    madde = parcalari_oku(ISLENMIS / "parcalar_madde.jsonl")
    kosul_parcalari = madde if a.kosul == "madde" else parcalari_oku(ISLENMIS / "parcalar_sabit.jsonl")
    kume = Kume(deney_parcalari(kosul_parcalari))
    dayanak = {p["id"]: p for p in madde}
    madde_belgeleri = {p["belge_id"] for p in madde if p["tur"] in MADDE_TURLERI}
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        adlar = {s["belge_id"]: s["baslik"] for s in csv.DictReader(f)}
    sorular = {s["id"]: s for s in oku(KOK / r["konfigurasyon"]["sorular"])}

    hatalar = []
    satirlar = r["sonuclar"][a.kume]["sorular"]
    for satir in satirlar:
        sonuc = satir[a.kosul]
        if sonuc["kapsam"]["5"] >= 1:
            continue
        s = sorular[satir["id"]]
        ids = sonuc["getirilen"]
        hatalar.append({
            "id": s["id"], "soru": s["soru"], "dayanak": s["dayanak"],
            "kategori": kategori(ids, kanitlar(s, dayanak), kume, adlar, madde_belgeleri),
            "ilk": ids[0], "ilk_belge": adlar.get(kume.parca[ids[0]]["belge_id"], ""),
            "ilk5": ids[:5], "sira": sonuc["sira"],
        })

    sayim = Counter(h["kategori"] for h in hatalar)
    konf = r["konfigurasyon"]
    baslik = (f"{konf['arama']} · {a.kosul} · {konf['bolum']} · {a.kume}: "
              f"{len(hatalar)} errors of {len(satirlar)} questions")
    md = [f"# {baslik}", "", "| category | count | example | top-1 retrieved |", "|---|---|---|---|"]
    for kat, etiket in KATEGORILER.items():
        ornek = next((h for h in hatalar if h["kategori"] == kat), None)
        md.append(f"| {etiket} | {sayim.get(kat, 0)} | "
                  + (f"{ornek['id']}: {ornek['soru']} (gold {', '.join(ornek['dayanak'])}) | "
                     f"{ornek['ilk']} ({ornek['ilk_belge']})" if ornek else "— | —") + " |")
    klasor = KOK / "results" / "hata"
    klasor.mkdir(parents=True, exist_ok=True)
    ad = f"{a.sonuc.stem}-{a.kosul}"
    (klasor / f"{ad}.json").write_text(json.dumps(
        {"kaynak": str(a.sonuc), "kosul": a.kosul, "kume": a.kume, "n": len(satirlar),
         "sayim": dict(sayim), "hatalar": hatalar}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (klasor / f"{ad}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

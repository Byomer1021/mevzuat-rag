"""Demonun kaynak seçimi: doğru madde dil modeline ne sıklıkla gidiyor? (dev)

    uv run python scripts/demo_arama.py

Yalnız dev seti, yalnız demo. Deneyin düzeni (K-022) ve test seti bu
betikte yok. Ölçü: cevaplı dev sorularında bütün kanıtların modele verilen
kaynakların içinde olması (cevap.py'deki "kanit_getirildi" ile aynı). Her
düzen için ortalama istem uzunluğu da yazılır: kaynak arttıkça istem uzar,
model yavaşlar.

Denenenler: e5, BM25, ikisinin karşılıklı sıra füzyonu (RRF, k = 60), belge
ve web kaynak sayıları. Çıktı: results/demo_arama.json ve .md.
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")  # K-002

from mevzuat_rag.degerlendirme import Kume, bootstrap_araligi, kanitlar  # noqa: E402
from mevzuat_rag.demo import bilgi_tabani, dizin_kur, sec  # noqa: E402
from mevzuat_rag.testset import oku  # noqa: E402
from mevzuat_rag.uretim import istem  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
RRF_K = 60
DUZENLER = [  # (arama, k_belge, k_web)
    ("e5", 3, 2), ("e5", 5, 2), ("e5", 8, 2),
    ("bm25", 3, 2), ("bm25", 5, 2),
    ("rrf", 3, 2), ("rrf", 5, 2), ("rrf", 8, 2),
]


def rrf(*siralamalar: list[str]) -> list[str]:
    puan = {}
    for s in siralamalar:
        for n, i in enumerate(s, 1):
            puan[i] = puan.get(i, 0.0) + 1 / (RRF_K + n)
    return sorted(puan, key=lambda i: -puan[i])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bt = bilgi_tabani()
    kume = Kume(bt.parcalar)
    sorular = [s for s in oku(KOK / "data" / "testset" / "sorular.jsonl")
               if s["bolum"] == "dev" and s["tur"] != "cevapsiz"]
    dizin = {a: dizin_kur(a, bt) for a in ("e5", "bm25")}
    siralama = {}
    for s in sorular:
        tam = {a: [x.id for x in d.ara(s["soru"], len(bt.parcalar))] for a, d in dizin.items()}
        siralama[s["id"]] = {**tam, "rrf": rrf(tam["e5"], tam["bm25"])}

    sonuc = []
    for arama, kb, kw in DUZENLER:
        bulundu, uzunluk = [], []
        for s in sorular:
            ids = sec(siralama[s["id"]][arama], bt.parca, kb, kw)
            ks = kanitlar(s, bt.parca)
            bulundu.append(float(all(kume.kapsar_mi(k, ids) for k in ks)))
            uzunluk.append(sum(len(m["content"]) for m in istem(s["soru"], [bt.parca[i] for i in ids], bt.adlar)))
        a = bootstrap_araligi(bulundu)
        sonuc.append({"arama": arama, "k_belge": kb, "k_web": kw, "bulundu": int(sum(bulundu)), "n": len(sorular),
                      "oran": a["ortalama"], "alt": a["alt"], "ust": a["ust"],
                      "istem_ort": round(sum(uzunluk) / len(uzunluk)), "istem_en_uzun": max(uzunluk),
                      "sorular": {s["id"]: b for s, b in zip(sorular, bulundu, strict=True)}})

    (KOK / "results" / "demo_arama.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1) + "\n",
                                                    encoding="utf-8")
    md = ["# Demo kaynak seçimi (dev, cevaplı sorular)", "",
          "Kanıtın tamamı modele verilen kaynaklarda mı. Aralık 10 000 bootstrap, tohum 0. Yalnız demo, deney değil.",
          "", "| arama | belge + web | kanıt modele gidiyor | istem ort. / en uzun (karakter) |", "|---|---|---|---|"]
    for r in sonuc:
        md.append(f"| {r['arama']} | {r['k_belge']} + {r['k_web']} | {r['bulundu']}/{r['n']} = {r['oran']:.0%} "
                  f"[{r['alt']:.0%}, {r['ust']:.0%}] | {r['istem_ort']} / {r['istem_en_uzun']} |")
    (KOK / "results" / "demo_arama.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

"""Yoğun arama modelinin girdi sınırı: hangi parçalar kırpılıyor?

    uv run python scripts/token_olcum.py [model]

e5 ailesi 512 token alıyor; fazlası modele hiç ulaşmıyor. Parça, aramada
dizine girdiği biçimiyle sayılır ("passage: " + belge adı + metin). İki
koşul için ayrı ayrı: kaç parça sınırı aşıyor, metnin yüzde kaçı sınırın
ötesinde kalıyor. Sonuç: results/token_olcum.json, olcumler §11.
"""

import csv
import json
import statistics
import sys
from pathlib import Path

from mevzuat_rag.arama import E5, gomme_metni
from mevzuat_rag.deney import MADDE_TURLERI, deney_parcalari
from mevzuat_rag.testset import parcalari_oku

KOK = Path(__file__).resolve().parents[1]
SINIR = 512


def main():
    # Paketten sonra: .env'deki HF_HOME (D:) transformers yüklenmeden ayarlanmış olmalı (K-003)
    from transformers import AutoTokenizer

    sys.stdout.reconfigure(encoding="utf-8")
    model = sys.argv[1] if len(sys.argv) > 1 else E5
    tok = AutoTokenizer.from_pretrained(model)
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        adlar = {r["belge_id"]: r["baslik"] for r in csv.DictReader(f)}
    rapor = {"model": model, "sinir": SINIR, "kosullar": {}}
    for kosul in ("madde", "sabit"):
        ps = deney_parcalari(parcalari_oku(KOK / "data" / "processed" / f"parcalar_{kosul}.jsonl"))
        metinler = ["passage: " + gomme_metni(p, adlar) for p in ps]
        kodlar = tok(metinler, add_special_tokens=True, return_offsets_mapping=True)
        uzunluk = [len(x) for x in kodlar["input_ids"]]
        asan = [i for i, n in enumerate(uzunluk) if n > SINIR]
        # sınırın ötesinde kalan karakter: SINIR-1'inci (son özel token öncesi) tokenın bitişinden sonrası
        kayip = sum(len(metinler[i]) - kodlar["offset_mapping"][i][SINIR - 2][1] for i in asan)
        maddeler = [i for i in asan if ps[i]["tur"] in MADDE_TURLERI]
        q = statistics.quantiles(uzunluk, n=20)
        rapor["kosullar"][kosul] = {
            "parca": len(ps),
            "token": {"medyan": int(statistics.median(uzunluk)), "p95": int(q[-1]), "max": max(uzunluk)},
            "sinir_asan": len(asan),
            "sinir_asan_madde": len(maddeler),
            "kirpilan_karakter_orani": round(kayip / sum(len(m) for m in metinler), 4),
            "en_uzun": [ps[i]["id"] for i in sorted(asan, key=lambda i: -uzunluk[i])[:10]],
            "karakter_token_orani": round(sum(len(m) for m in metinler) / sum(uzunluk), 2),
        }
    yol = KOK / "results" / "token_olcum.json"
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rapor, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

"""Colab'dan gelen cevapları ölçer ve elle puanlama tablosu çıkarır.

    uv run python scripts/cevap_ozet.py results/istem/<paket>.jsonl <cevaplar>.jsonl

Cevap dosyası notebooks/cevap_uret.ipynb çıktısı: ilk satır {"_ust": ...}
(model, revizyon, süre), sonra soru başına {"id", "cevap", ...}. Sonuç:
results/cevap/<cevap dosyası adı>.json (özet + satırlar) ve _puanlama.csv;
CSV'nin "dogruluk" sütunu elle doldurulur: dogru / kismen / yanlis.
"""

import csv
import json
import sys
from pathlib import Path

from mevzuat_rag.cevap import olc
from mevzuat_rag.degerlendirme import Kume
from mevzuat_rag.testset import oku, parcalari_oku

KOK = Path(__file__).resolve().parents[1]


def jsonl(yol: Path) -> list[dict]:
    return [json.loads(s) for s in yol.read_text(encoding="utf-8-sig").splitlines() if s.strip()]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    paket_yolu, cevap_yolu = Path(sys.argv[1]), Path(sys.argv[2])
    ust_paket = json.loads(paket_yolu.with_suffix(".ust.json").read_text(encoding="utf-8"))
    satirlar = jsonl(cevap_yolu)
    ust_cevap = satirlar[0].get("_ust", {}) if satirlar else {}
    cevaplar = [s for s in satirlar if "_ust" not in s]

    islenmis = KOK / "data" / "processed"
    madde = parcalari_oku(islenmis / "parcalar_madde.jsonl")
    kume_parcalari = madde if ust_paket["kosul"] == "madde" else parcalari_oku(
        islenmis / "parcalar_sabit.jsonl")
    sorular = oku(KOK / "data" / "testset" / "sorular.jsonl")
    ozet, sonuc = olc(sorular, jsonl(paket_yolu), cevaplar, Kume(kume_parcalari),
                      {p["id"]: p for p in madde})

    klasor = KOK / "results" / "cevap"
    klasor.mkdir(parents=True, exist_ok=True)
    ad = cevap_yolu.stem
    (klasor / f"{ad}.json").write_text(json.dumps(
        {"paket": ust_paket, "uretim": ust_cevap, "ozet": ozet, "sorular": sonuc},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with (klasor / f"{ad}_puanlama.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "tur", "soru", "referans_cevap", "cevap", "bilmiyorum", "dogruluk", "not"])
        for r in sonuc:
            w.writerow([r["id"], r["tur"], r["soru"], r["referans_cevap"], r["cevap"],
                        "evet" if r["bilmiyorum"] else "", "", ""])
    print(json.dumps({"model": ust_cevap.get("model"), **ozet}, ensure_ascii=False, indent=1))
    print(f"-> results/cevap/{ad}.json, {ad}_puanlama.csv")


if __name__ == "__main__":
    main()

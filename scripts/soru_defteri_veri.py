"""Soru defteri sayfasının verisi: bütün parçalar ve belge adları, tek JSON.

    uv run python scripts/soru_defteri_veri.py <cikti>/parcalar.json

Sayfa (app/soru_defteri.html) bu dosyayı yanında `parcalar.json` adıyla
okur. Parça sırası: id, belge_id, tur, baslik, bolum, sayfa_bas, sayfa_son,
metin, web adresi, tarih. Kimlikler bilgi tabanı sürümüne bağlı; sürüm
dosyada ve sayfada yazar.
"""

import csv
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]


def main():
    cikti = Path(sys.argv[1])
    rapor = json.loads((KOK / "results" / "onisleme.json").read_text(encoding="utf-8"))
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        kaynak = {r["belge_id"]: r for r in csv.DictReader(f)}
    with (KOK / "data" / "processed" / "parcalar_madde.jsonl").open(encoding="utf-8") as f:
        parcalar = [json.loads(s) for s in f if s.strip()]
    veri = {
        "surum": f"{rapor['bilgi_tabani_surumu']} / parça {rapor['parca_surumu']}",
        "belgeler": {b: {"ad": r["baslik"], "tur": r["tur"], "url": r["url"]}
                     for b, r in kaynak.items()},
        "parcalar": [[p["id"], p["belge_id"], p["tur"], p["baslik"], p["bolum"], p["sayfa_bas"],
                      p["sayfa_son"], p["metin"], p["url"] if p["tur"] == "web" else "",
                      p.get("tarih", "")] for p in parcalar],
    }
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(json.dumps(veri, ensure_ascii=False, separators=(",", ":")),
                     encoding="utf-8")
    print(f"{len(parcalar)} parça, sürüm {veri['surum']} -> {cikti}")


if __name__ == "__main__":
    main()

"""Model adı gizli, karışık sıralı elle doğruluk puanlaması (K-005 pilotu).

    uv run python scripts/kor_puanlama.py olustur results/cevap/A.json results/cevap/B.json
    uv run python scripts/kor_puanlama.py hesapla

olustur: cevap_ozet.py çıktılarındaki bütün cevapları tek tabloda karıştırır,
model adını çıkarır: results/cevap/kor_puanlama.csv. Hangi satırın hangi
modelden geldiği results/cevap/kor_anahtar.json'da (puanlayan açmasın).
Puanlayan "dogruluk" sütununa dogru / kismen / yanlis yazar. Cevapsız
sorularda doğru cevap "bilmiyorum" demektir.

hesapla: doldurulmuş tabloyu anahtarla birleştirir, model başına sayar:
results/cevap/kor_sonuc.json.
"""

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KLASOR = KOK / "results" / "cevap"
TABLO, ANAHTAR = KLASOR / "kor_puanlama.csv", KLASOR / "kor_anahtar.json"
TOHUM = 0
DEGERLER = ("dogru", "kismen", "yanlis")


def olustur(yollar: list[Path]):
    if TABLO.exists():
        sys.exit(f"{TABLO.relative_to(KOK)} zaten var; puanlama başladıysa ezilmesin. Silip yeniden çalıştır.")
    satirlar = []
    for yol in yollar:
        d = json.loads(yol.read_text(encoding="utf-8"))
        model = d["uretim"].get("model") or yol.stem
        satirlar += [{"model": model, **r} for r in d["sorular"]]
    random.Random(TOHUM).shuffle(satirlar)
    anahtar = {}
    with TABLO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["satir", "id", "tur", "soru", "referans_cevap", "cevap", "dogruluk", "not"])
        for i, r in enumerate(satirlar, 1):
            ref = r["referans_cevap"] or "(cevapsız: doğru cevap 'bilmiyorum')"
            w.writerow([i, r["id"], r["tur"], r["soru"], ref, r["cevap"], "", ""])
            anahtar[str(i)] = {"model": r["model"], "id": r["id"]}
    ANAHTAR.write_text(json.dumps({"tohum": TOHUM, "satirlar": anahtar}, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    print(f"{len(satirlar)} cevap -> {TABLO.relative_to(KOK)} (anahtar ayrı: {ANAHTAR.relative_to(KOK)})")


def hesapla():
    anahtar = json.loads(ANAHTAR.read_text(encoding="utf-8"))["satirlar"]
    with TABLO.open(encoding="utf-8-sig", newline="") as f:
        satirlar = list(csv.DictReader(f))
    sayim, bos, gecersiz = {}, [], []
    for r in satirlar:
        d = r["dogruluk"].strip().lower()
        if not d:
            bos.append(r["satir"])
            continue
        if d not in DEGERLER:
            gecersiz.append((r["satir"], d))
            continue
        model = anahtar[r["satir"]]["model"]
        tur = "cevapsiz" if r["tur"] == "cevapsiz" else "cevapli"
        sayim.setdefault(model, {"cevapli": Counter(), "cevapsiz": Counter()})[tur][d] += 1
    sonuc = {m: {t: dict(c) for t, c in v.items()} for m, v in sayim.items()}
    (KLASOR / "kor_sonuc.json").write_text(json.dumps({"sonuc": sonuc, "bos": bos, "gecersiz": gecersiz},
                                                      ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for m, v in sonuc.items():
        print(m, v)
    if bos or gecersiz:
        print(f"puanlanmamış {len(bos)} satır; geçersiz değer: {gecersiz}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) >= 4 and sys.argv[1] == "olustur":
        olustur([Path(p) for p in sys.argv[2:]])
    elif len(sys.argv) == 2 and sys.argv[1] == "hesapla":
        hesapla()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

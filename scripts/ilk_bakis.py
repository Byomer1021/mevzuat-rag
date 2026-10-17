"""Öneri raporunun "ilk bakış" kutusu: iki parçalama koşulunu yapı olarak
karşılaştırır ve gösterim sorusunun BM25 çıktısını yazar. Soru seti yok;
burada arama başarısı ölçülmüyor.

    uv run python scripts/ilk_bakis.py

Çıktı: results/ilk_bakis.json, olcumler §10.
"""

import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

from mevzuat_rag.arama import BM25Dizin
from mevzuat_rag.testset import parcalari_oku

KOK = Path(__file__).resolve().parents[1]
ISLENMIS = KOK / "data" / "processed"
CIKTI = KOK / "results" / "ilk_bakis.json"
MADDE_TURLERI = ("madde", "gecici", "ek")
# Deneyin dizini yalnız PDF belgeleri (K-022): web, takvim ve form iki koşulda
# aynı, ama aynı bilgiyi veren SSS cevabı yönetmelik maddesinin önüne geçip
# mutlak sayıları bozuyor (bu betiğin ilk çalıştırması).
DENEY_DISI = ("web", "takvim", "form")
# Gösterim sorusu dev bölümünde sayılır; test setine yazılmaz (soru-yazma.md).
GOSTERIM = ("Derslere devam zorunluluğu yüzde kaç?", "lisans-yonetmelik/m23")


def kesisen(aralik: tuple[int, int], parcalar: list[dict]) -> list[dict]:
    a, b = aralik
    return [p for p in parcalar if p["bas"] < b and a < p["son"]]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    madde = [p for p in parcalari_oku(ISLENMIS / "parcalar_madde.jsonl")
             if p["tur"] not in DENEY_DISI]
    sabit = [p for p in parcalari_oku(ISLENMIS / "parcalar_sabit.jsonl")
             if p["tur"] not in DENEY_DISI]
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        adlar = {s["belge_id"]: s["baslik"] for s in csv.DictReader(f)}
    rapor_on = json.loads((KOK / "results" / "onisleme.json").read_text(encoding="utf-8"))

    sabit_belge: dict[str, list[dict]] = {}
    for p in sabit:
        if p["tur"] == "sabit":
            sabit_belge.setdefault(p["belge_id"], []).append(p)
    maddeler = [p for p in madde if p["belge_id"] in sabit_belge and p["tur"] in MADDE_TURLERI]
    madde_belge: dict[str, list[dict]] = {}
    for p in madde:
        if p["belge_id"] in sabit_belge:
            madde_belge.setdefault(p["belge_id"], []).append(p)

    # Bir madde kaç sabit parçaya dağılıyor; bir sabit parça kaç maddeye değiyor
    dagilim = Counter(len(kesisen((p["bas"], p["son"]), sabit_belge[p["belge_id"]]))
                      for p in maddeler)
    sabit_parcalar = [p for ps in sabit_belge.values() for p in ps]
    karisik = sum(len(kesisen((p["bas"], p["son"]), madde_belge[p["belge_id"]])) > 1
                  for p in sabit_parcalar)

    t0 = time.perf_counter()
    dizinler = {"madde": BM25Dizin(madde, adlar), "sabit": BM25Dizin(sabit, adlar)}
    kurma = time.perf_counter() - t0
    soru, hedef = GOSTERIM
    hedef_parca = next(p for p in madde if p["id"] == hedef)
    ornek = {}
    for ad, dizin in dizinler.items():
        kume = {p["id"]: p for p in (madde if ad == "madde" else sabit)}
        dizin.ara(soru, k=1)  # ilk çağrı ısınma
        t0 = time.perf_counter()
        sonuc = dizin.ara(soru, k=len(kume))
        sure = time.perf_counter() - t0
        ornek[ad] = {"sure_ms": round(sure * 1000, 1), "ilk3": [
            {"id": s.id, "skor": round(s.skor, 2),
             "metin": kume[s.id]["metin"][:160].replace("\n", " ")} for s in sonuc[:3]],
            "dayanagi_kesen_parcalarin_sirasi": {
                s.id: s.sira for s in sonuc
                if s.id in {p["id"] for p in kesisen((hedef_parca["bas"], hedef_parca["son"]),
                                                     [x for x in kume.values()
                                                      if x["belge_id"] == hedef_parca["belge_id"]
                                                      and x["bas"] >= 0])}}}
    hedef_sabit = kesisen((hedef_parca["bas"], hedef_parca["son"]),
                          sabit_belge[hedef_parca["belge_id"]])

    rapor = {
        "bilgi_tabani_surumu": rapor_on["bilgi_tabani_surumu"],
        "karsilastirma": rapor_on["sabit_karsilastirma"],
        "madde_sayisi": len(maddeler),
        "madde_kac_sabit_parcaya_dagiliyor": dict(sorted(dagilim.items())),
        "madde_bolunen_oran": round(1 - dagilim[1] / len(maddeler), 3),
        "sabit_parca_sayisi": len(sabit_parcalar),
        "birden_cok_maddeye_degen_sabit_parca": karisik,
        "birden_cok_maddeye_degen_oran": round(karisik / len(sabit_parcalar), 3),
        "dizin_parca": {"madde": len(madde), "sabit": len(sabit)},
        "dizin_kurma_s": round(kurma, 1),
        "gosterim": {"soru": soru, "dayanak": hedef,
                     "dayanak_uzunluk": len(hedef_parca["metin"]),
                     "dayanagi_kesen_sabit_parcalar": [p["id"] for p in hedef_sabit],
                     **ornek},
    }
    CIKTI.parent.mkdir(exist_ok=True)
    CIKTI.write_text(json.dumps(rapor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rapor, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

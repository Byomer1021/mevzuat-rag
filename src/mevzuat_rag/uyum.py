"""Etiket uyumu (K-026): test setinden 40 soruyu soruyu yazmamış biri yeniden etiketler.

Karşılaştırılan iki şey: test setindeki etiket (altın) ve ikinci kişinin
etiketi. Ölçülenler cevaplanabilirlik ve soru türü için Cohen's κ, cevaplı
sorularda madde, belge ve kanıt cümlesi örtüşmesi. Referans cevap serbest
metin olduğu için ölçülmez.
"""

from __future__ import annotations

import random
from collections import Counter

import numpy as np

from mevzuat_rag.testset import alinti_kalibi

KANIT_ESIK = 0.5  # iki kanıt alıntısı, kısa olanın en az yarısı örtüşürse aynı cümle sayılır


def cohen_kappa(a: list, b: list) -> float | None:
    """İki etiketçinin aynı öğelere verdiği kategoriler. Beklenen uyum 1 ise (tek
    kategori) κ tanımsızdır, None döner."""
    if len(a) != len(b) or not a:
        raise ValueError("a ve b aynı uzunlukta ve boş olmamalı")
    n = len(a)
    gozlenen = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    beklenen = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n**2
    if beklenen == 1:
        return None
    return (gozlenen - beklenen) / (1 - beklenen)


def kappa_araligi(a: list, b: list, n: int = 10_000, tohum: int = 0, guven: float = 0.95) -> dict:
    """κ ve öğeler yeniden örneklenerek yüzdelik güven aralığı. κ'nın tanımsız
    olduğu örneklemler atlanır, sayısı raporlanır."""
    k = cohen_kappa(a, b)
    rng = np.random.default_rng(tohum)
    degerler, atlanan = [], 0
    for idx in rng.integers(0, len(a), size=(n, len(a))):
        d = cohen_kappa([a[i] for i in idx], [b[i] for i in idx])
        if d is None:
            atlanan += 1
        else:
            degerler.append(d)
    alt, ust = (np.quantile(degerler, [(1 - guven) / 2, 1 - (1 - guven) / 2]) if degerler
                else (np.nan, np.nan))
    return {"kappa": k, "alt": float(alt), "ust": float(ust), "n": len(a), "atlanan": atlanan,
            "ham_uyum": sum(x == y for x, y in zip(a, b, strict=True)) / len(a)}


def oran_araligi(a: list[bool], n: int = 10_000, tohum: int = 0, guven: float = 0.95) -> dict:
    """Bir evet/hayır oranı ve bootstrap aralığı. Boş listede oran tanımsız."""
    if not a:
        return {"oran": None, "alt": None, "ust": None, "n": 0}
    x = np.asarray(a, float)
    rng = np.random.default_rng(tohum)
    ort = x[rng.integers(0, len(x), size=(n, len(x)))].mean(axis=1)
    alt, ust = np.quantile(ort, [(1 - guven) / 2, 1 - (1 - guven) / 2])
    return {"oran": float(x.mean()), "alt": float(alt), "ust": float(ust), "n": len(x)}


def aralik(metin: str, alinti: str) -> tuple[int, int] | None:
    """Alıntının parça metnindeki karakter aralığı (boşluklar esnek), yoksa None."""
    m = alinti_kalibi(alinti).search(metin)
    return (m.start(), m.end()) if m else None


def ortusme(a: tuple[int, int], b: tuple[int, int]) -> float:
    """İki aralığın kesişiminin kısa olana oranı."""
    kesisim = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    kisa = min(a[1] - a[0], b[1] - b[0])
    return kesisim / kisa if kisa > 0 else 0.0


def belge(parca_id: str) -> str:
    return parca_id.split("/")[0]


def karsilastir(altin: dict, ikinci: dict, parcalar: dict[str, str]) -> dict:
    """Bir sorunun iki etiketini karşılaştırır. parcalar: kimlik → metin."""
    a_cevapli, b_cevapli = altin["tur"] != "cevapsiz", ikinci["tur"] != "cevapsiz"
    sonuc = {"id": altin["id"], "tur_altin": altin["tur"], "tur_ikinci": ikinci["tur"],
             "cevapli_altin": a_cevapli, "cevapli_ikinci": b_cevapli,
             "dayanak_altin": altin["dayanak"], "dayanak_ikinci": ikinci["dayanak"]}
    if not (a_cevapli and b_cevapli):
        return sonuc
    da, db = set(altin["dayanak"]), set(ikinci["dayanak"])
    ortak = sorted(da & db)
    kanit_a = dict(zip(altin["dayanak"], altin["kanit"], strict=True))
    kanit_b = dict(zip(ikinci["dayanak"], ikinci["kanit"], strict=True))
    kanit_ortusme = {}
    for d in ortak:
        ra, rb = aralik(parcalar[d], kanit_a[d]), aralik(parcalar[d], kanit_b[d])
        kanit_ortusme[d] = ortusme(ra, rb) if ra and rb else 0.0
    sonuc.update({
        "ayni_madde": da == db,
        "ortak_madde": bool(ortak),
        "ortak_belge": bool({belge(d) for d in da} & {belge(d) for d in db}),
        "kanit_ortusme": kanit_ortusme,
        "ayni_kanit": bool(ortak) and all(v >= KANIT_ESIK for v in kanit_ortusme.values()),
    })
    return sonuc


def ozetle(karsilastirmalar: list[dict], tohum: int = 0) -> dict:
    """Bütün sorular için κ'lar, ikisinin de cevaplı dediği sorularda oranlar."""
    k = karsilastirmalar
    ikisi = [x for x in k if x["cevapli_altin"] and x["cevapli_ikinci"]]
    ortak = [x for x in ikisi if x["ortak_madde"]]
    return {
        "n": len(k),
        "cevaplanabilirlik": kappa_araligi([x["cevapli_altin"] for x in k],
                                           [x["cevapli_ikinci"] for x in k], tohum=tohum),
        "tur": kappa_araligi([x["tur_altin"] for x in k], [x["tur_ikinci"] for x in k], tohum=tohum),
        "ikisi_cevapli": len(ikisi),
        "ayni_madde": oran_araligi([x["ayni_madde"] for x in ikisi], tohum=tohum),
        "ortak_madde": oran_araligi([x["ortak_madde"] for x in ikisi], tohum=tohum),
        "ortak_belge": oran_araligi([x["ortak_belge"] for x in ikisi], tohum=tohum),
        "ayni_kanit_ortak_maddede": oran_araligi([x["ayni_kanit"] for x in ortak], tohum=tohum),
    }


def ornek_sec(sorular: list[dict], yazan: str, sayilar: dict[str, int], tohum: int) -> list[str]:
    """Bir yazarın test sorularından türe göre katmanlı, tekrar üretilebilir seçim."""
    rng = random.Random(f"{tohum}-{yazan}")
    secilen = []
    for tur, adet in sayilar.items():
        havuz = sorted(s["id"] for s in sorular
                       if s["bolum"] == "test" and s["yazan"] == yazan and s["tur"] == tur)
        if len(havuz) < adet:
            raise ValueError(f"{yazan}: {tur} türünde {len(havuz)} soru var, {adet} isteniyor")
        secilen += rng.sample(havuz, adet)
    return sorted(secilen)

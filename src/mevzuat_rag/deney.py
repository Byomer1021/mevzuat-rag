"""Araştırma sorusunun deneyi (K-022): iki parçalama koşulu, aynı arama, aynı sorular.

Dizin yalnız PDF parçaları; web, takvim ve form iki koşulda aynı ama mutlak
sayıları bozuyor (olcumler §10). Birincil soru kümesi: cevaplanabilir ve
bütün dayanakları madde yapılı belgelerde olan sorular; koşullar yalnız orada
ayrışıyor. Diğer PDF dayanaklı sorular ayrıca raporlanır.
"""

from collections.abc import Callable

import numpy as np

from mevzuat_rag.degerlendirme import (
    Kume,
    bootstrap_araligi,
    eslestirilmis_bootstrap,
    ilk_tam_sira,
    kanitlar,
    kapsam,
    mcnemar,
)

DENEY_DISI = ("web", "takvim", "form")
MADDE_TURLERI = ("madde", "gecici", "ek")

Arayici = Callable[[str, int], list[str]]  # (soru, k) -> parça kimlikleri, sırayla


def deney_parcalari(parcalar: list[dict]) -> list[dict]:
    return [p for p in parcalar if p["tur"] not in DENEY_DISI]


def soru_kumeleri(sorular: list[dict], madde_parcalari: list[dict]) -> dict[str, list[dict]]:
    """Cevaplanabilir sorular: `tum_pdf` (dayanakları deney dizininde) ve onun
    alt kümesi `birincil` (dayanakları madde yapılı belgelerde)."""
    pdf = {p["id"] for p in deney_parcalari(madde_parcalari)}
    madde_belgeleri = {p["belge_id"] for p in madde_parcalari if p["tur"] in MADDE_TURLERI}
    cevapli = [s for s in sorular if s["tur"] != "cevapsiz" and s["dayanak"]]
    tum = [s for s in cevapli if all(d in pdf for d in s["dayanak"])]
    birincil = [s for s in tum if all(d.split("/")[0] in madde_belgeleri for d in s["dayanak"])]
    return {"birincil": birincil, "tum_pdf": tum}


def calistir(sorular: list[dict], kumeler: dict[str, list[dict]], arayicilar: dict[str, Arayici],
             dayanak_parcalari: dict[str, dict], k_listesi: tuple[int, ...] = (1, 5, 10)) -> dict:
    """Her soruyu her koşulda arar, kanıt kapsamını ölçer. `kumeler` ve
    `arayicilar` aynı anahtarları taşır; iki koşul varsa ilk ikisi karşılaştırılır
    (a − b). Tek koşul: yalnız o koşulun ölçüleri ve güven aralıkları."""
    kume = {ad: Kume(ps) for ad, ps in kumeler.items()}
    kmax = max(k_listesi)
    satirlar = []
    for s in sorular:
        ks = kanitlar(s, dayanak_parcalari)
        satir = {"id": s["id"], "tur": s["tur"], "dayanak": s["dayanak"]}
        for ad in kumeler:
            ids = arayicilar[ad](s["soru"], kmax)
            satir[ad] = {"getirilen": ids,
                         "kapsam": {str(k): kapsam(kume[ad], ks, ids[:k]) for k in k_listesi},
                         "sira": ilk_tam_sira(kume[ad], ks, ids)}
        satirlar.append(satir)

    def dizi(ad: str, k: int) -> np.ndarray:
        return np.array([r[ad]["kapsam"][str(k)] for r in satirlar], float)

    def rr(ad: str) -> np.ndarray:
        return np.array([1 / r[ad]["sira"] if r[ad]["sira"] else 0.0 for r in satirlar])

    sonuc = {"n": len(satirlar), "k": list(k_listesi), "ozet": {}, "aralik": {}, "fark": {},
             "sorular": satirlar}
    if not satirlar:
        return sonuc
    for ad in kumeler:
        olculer = {**{f"R@{k}": dizi(ad, k) for k in k_listesi}, f"MRR@{kmax}": rr(ad)}
        sonuc["ozet"][ad] = {o: round(float(v.mean()), 4) for o, v in olculer.items()}
        sonuc["aralik"][ad] = {o: bootstrap_araligi(v) for o, v in olculer.items()}
    if len(kumeler) < 2:
        return sonuc
    a, b = list(kumeler)[:2]
    for k in k_listesi:
        sonuc["fark"][f"R@{k}"] = eslestirilmis_bootstrap(dizi(a, k), dizi(b, k))
    sonuc["fark"][f"MRR@{kmax}"] = eslestirilmis_bootstrap(rr(a), rr(b))
    sonuc["mcnemar_R@5"] = mcnemar(dizi(a, 5), dizi(b, 5)) if 5 in k_listesi else None
    sonuc["karsilastirma"] = f"{a} - {b}"
    return sonuc

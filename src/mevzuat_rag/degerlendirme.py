"""Arama değerlendirmesi: kanıt kapsamı, Recall@k, MRR, eşleştirilmiş bootstrap.

Doğru sayma ölçütü (K-022). Sorunun her dayanağı için yazılmış kanıt alıntısı
(testset.py), getirilen ilk k parçanın birleşiminde *tamamen* yer alıyorsa o
dayanak bulunmuştur. Ölçüt parçalamadan bağımsız: madde parçasında da sabit
parçada da belgenin aynı karakter aralığı aranır. Alıntı iki sabit parçaya
bölünmüşse ikisinin de ilk k içinde olması gerekir. Başka belgedeki aynı
metin sayılmaz; sistem kaynak gösterecek, doğru kaynak da ölçünün parçası.

Konumu olmayan parçalarda (web, takvim, form) alıntı parçanın metninde aranır;
bu parçalar iki koşulda aynı olduğu için karşılaştırmayı etkilemez.
"""

from dataclasses import dataclass

import numpy as np
from scipy.stats import binomtest

from mevzuat_rag.testset import alinti_kalibi


@dataclass(frozen=True)
class Kanit:
    belge_id: str
    bas: int  # belgenin birleşik metninde; -1: konum yok, metinde aranır
    son: int
    alinti: str


def kanitlar(soru: dict, dayanak_parcalari: dict[str, dict]) -> list[Kanit]:
    """Alıntıları belge içi konuma çevirir. dayanak_parcalari: madde kümesi, kimlik → parça."""
    out = []
    for d, k in zip(soru["dayanak"], soru["kanit"], strict=True):
        p = dayanak_parcalari[d]
        m = alinti_kalibi(k).search(p["metin"])
        if m is None:
            raise ValueError(f"{soru['id']}: kanıt {d} metninde yok")
        if p.get("bas", -1) >= 0:
            out.append(Kanit(p["belge_id"], p["bas"] + m.start(), p["bas"] + m.end(), k))
        else:
            out.append(Kanit(p["belge_id"], -1, -1, k))
    return out


class Kume:
    """Bir parçalama koşulunun bütün parçaları. Her parçanın aralığı bir sonraki
    parçanın başına kadar genişletilir: aradaki yalnızca boşluk (parçalar belgeyi
    kayıpsız örtüyor, onisle denetimi), komşu iki parça kesintisiz sayılsın."""

    def __init__(self, parcalar: list[dict]):
        self.parca = {p["id"]: p for p in parcalar}
        self.aralik: dict[str, tuple[int, int]] = {}
        belgeler: dict[str, list[dict]] = {}
        for p in parcalar:
            if p.get("bas", -1) >= 0:
                belgeler.setdefault(p["belge_id"], []).append(p)
        for ps in belgeler.values():
            ps.sort(key=lambda p: p["bas"])
            for p, sonraki in zip(ps, ps[1:] + [None], strict=True):
                self.aralik[p["id"]] = (p["bas"], sonraki["bas"] if sonraki else p["son"])

    def kapsar_mi(self, kanit: Kanit, ids: list[str]) -> bool:
        ayni = [i for i in ids if self.parca[i]["belge_id"] == kanit.belge_id]
        if kanit.bas < 0:
            kalip = alinti_kalibi(kanit.alinti)
            return any(kalip.search(self.parca[i]["metin"]) for i in ayni)
        konum = kanit.bas
        for a, b in sorted(self.aralik[i] for i in ayni if i in self.aralik):
            if a > konum:
                break  # boşluk: alıntının bir kısmı getirilmedi
            konum = max(konum, b)
            if konum >= kanit.son:
                return True
        return konum >= kanit.son


def kapsam(kume: Kume, ks: list[Kanit], ids: list[str]) -> float:
    """Kanıtların ne kadarı bu parçalarda (tek dayanaklıda 0 ya da 1)."""
    return sum(kume.kapsar_mi(k, ids) for k in ks) / len(ks)


def ilk_tam_sira(kume: Kume, ks: list[Kanit], ids: list[str]) -> int | None:
    """Bütün kanıtların kapsandığı en küçük k (1'den); hiç kapsanmıyorsa None."""
    for k in range(1, len(ids) + 1):
        if all(kume.kapsar_mi(x, ids[:k]) for x in ks):
            return k
    return None


def recall_at_k(kume: Kume, kanit_listesi: list[list[Kanit]], sonuclar: list[list[str]],
                k: int) -> np.ndarray:
    """Soru başına kanıt kapsamı; ortalaması Recall@k."""
    return np.array([kapsam(kume, ks, ids[:k]) for ks, ids in zip(kanit_listesi, sonuclar,
                                                                    strict=True)])


def mrr(kume: Kume, kanit_listesi: list[list[Kanit]], sonuclar: list[list[str]]) -> np.ndarray:
    siralar = [ilk_tam_sira(kume, ks, ids) for ks, ids in zip(kanit_listesi, sonuclar, strict=True)]
    return np.array([1 / s if s else 0.0 for s in siralar])


def eslestirilmis_bootstrap(a: np.ndarray, b: np.ndarray, n: int = 10_000, tohum: int = 0,
                            guven: float = 0.95) -> dict:
    """Aynı sorular üzerinde a - b ortalama farkı ve yüzdelik güven aralığı.
    Sorular yeniden örneklenir; iki koşul aynı örnekle karşılaştırılır."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape or a.ndim != 1 or len(a) == 0:
        raise ValueError("a ve b aynı uzunlukta, boş olmayan diziler olmalı")
    d = a - b
    rng = np.random.default_rng(tohum)
    ortalamalar = d[rng.integers(0, len(d), size=(n, len(d)))].mean(axis=1)
    alt, ust = np.quantile(ortalamalar, [(1 - guven) / 2, 1 - (1 - guven) / 2])
    return {"fark": float(d.mean()), "alt": float(alt), "ust": float(ust), "n": len(d)}


def bootstrap_araligi(a: np.ndarray, n: int = 10_000, tohum: int = 0, guven: float = 0.95) -> dict:
    """Tek sistemin ortalaması ve yüzdelik güven aralığı; sorular yeniden örneklenir."""
    a = np.asarray(a, float)
    if a.ndim != 1 or len(a) == 0:
        raise ValueError("a boş olmayan tek boyutlu bir dizi olmalı")
    rng = np.random.default_rng(tohum)
    ortalamalar = a[rng.integers(0, len(a), size=(n, len(a)))].mean(axis=1)
    alt, ust = np.quantile(ortalamalar, [(1 - guven) / 2, 1 - (1 - guven) / 2])
    return {"ortalama": float(a.mean()), "alt": float(alt), "ust": float(ust), "n": len(a)}


def mcnemar(a: np.ndarray, b: np.ndarray) -> dict:
    """İkili sonuçlar (bulundu/bulunamadı) için kesin McNemar: yalnız a'nın ve
    yalnız b'nin bulduğu soru sayısı ve iki yönlü p."""
    a, b = np.asarray(a) >= 1, np.asarray(b) >= 1
    yalniz_a, yalniz_b = int((a & ~b).sum()), int((~a & b).sum())
    p = binomtest(yalniz_a, yalniz_a + yalniz_b, 0.5).pvalue if yalniz_a + yalniz_b else 1.0
    return {"yalniz_a": yalniz_a, "yalniz_b": yalniz_b, "p": float(p)}


def sira_bul(ids: list[str], hedef: str) -> int | None:
    """Kimlik ölçütü (yalnız madde kümesinde anlamlı): hedefin sırası, 1'den."""
    return ids.index(hedef) + 1 if hedef in ids else None

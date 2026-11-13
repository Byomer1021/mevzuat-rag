"""Madde kazancının ne kadarı kanıtın pencereye bölünmemesinden geliyor?

Recall@k'de (degerlendirme.py) kanıt, getirilen parçaların birleşiminde tam
yer alıyorsa bulunmuş sayılır. Pencere sınırı bir kanıt cümlesini ikiye
bölerse sabit koşulda iki pencerenin de ilk k içinde olması gerekir, madde
koşulunda tek parça yeter. Bu modül iki şeyi ölçer: kanıtın kaç pencereye
bölündüğünü (yapısal) ve gevşek bir ölçütle farkın ne kaldığını. Gevşek
ölçütte kanıtla örtüşen herhangi bir parça getirilmişse kanıt bulunmuş
sayılır. Gevşek ölçüt iki koşula da aynı uygulanır.
"""

from __future__ import annotations

from mevzuat_rag.degerlendirme import Kanit, Kume


def ortusen_parcalar(kume: Kume, kanit: Kanit) -> list[str]:
    """Konumlu kanıtla aralığı kesişen parçalar, belge içindeki sırayla."""
    if kanit.bas < 0:
        return []
    return sorted((i for i, (a, b) in kume.aralik.items()
                   if kume.parca[i]["belge_id"] == kanit.belge_id and a < kanit.son and b > kanit.bas),
                  key=lambda i: kume.aralik[i][0])


def bolunmus_mu(kume: Kume, ks: list[Kanit]) -> bool:
    """Kanıtlardan biri bu koşulda birden fazla parçaya yayılıyor mu?"""
    return any(len(ortusen_parcalar(kume, k)) > 1 for k in ks)


def gevsek_kapsar(kume: Kume, kanit: Kanit, ids: list[str]) -> bool:
    """Kanıtla örtüşen parçalardan biri getirildiyse bulunmuş say. Konumsuz
    kanıtlarda (web, takvim, form) sıkı ölçütle aynı."""
    if kanit.bas < 0:
        return kume.kapsar_mi(kanit, ids)
    secili = set(ids)
    return any(i in secili for i in ortusen_parcalar(kume, kanit))


def gevsek_kapsam(kume: Kume, ks: list[Kanit], ids: list[str]) -> float:
    return sum(gevsek_kapsar(kume, k, ids) for k in ks) / len(ks)

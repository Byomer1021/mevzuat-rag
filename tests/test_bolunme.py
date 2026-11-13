from mevzuat_rag.bolunme import bolunmus_mu, gevsek_kapsam, gevsek_kapsar, ortusen_parcalar
from mevzuat_rag.degerlendirme import Kanit, Kume, kapsam

METIN = "a" * 30


def parca(id_, bas, son, belge="b"):
    return {"id": id_, "belge_id": belge, "bas": bas, "son": son, "metin": METIN[bas:son]}


PENCERE = Kume([parca("b/s1", 0, 10), parca("b/s2", 10, 20), parca("b/s3", 20, 30), parca("c/s1", 0, 30, "c")])
BOLUNMUS = Kanit("b", 5, 15, "x")  # s1 ve s2'ye yayılıyor
TEK = Kanit("b", 21, 28, "x")


def test_ortusen_parcalar_belge_ici_sirali():
    assert ortusen_parcalar(PENCERE, BOLUNMUS) == ["b/s1", "b/s2"]
    assert ortusen_parcalar(PENCERE, TEK) == ["b/s3"]
    assert ortusen_parcalar(PENCERE, Kanit("b", -1, -1, "x")) == []


def test_bolunmus_mu():
    assert bolunmus_mu(PENCERE, [TEK, BOLUNMUS])
    assert not bolunmus_mu(PENCERE, [TEK])


def test_gevsek_bir_parca_yeter_siki_yetmez():
    assert gevsek_kapsar(PENCERE, BOLUNMUS, ["b/s2"])
    assert kapsam(PENCERE, [BOLUNMUS], ["b/s2"]) == 0.0
    assert kapsam(PENCERE, [BOLUNMUS], ["b/s1", "b/s2"]) == 1.0


def test_gevsek_baska_belge_sayilmaz():
    assert not gevsek_kapsar(PENCERE, BOLUNMUS, ["c/s1"])


def test_gevsek_kapsam_orani():
    assert gevsek_kapsam(PENCERE, [BOLUNMUS, TEK], ["b/s1"]) == 0.5

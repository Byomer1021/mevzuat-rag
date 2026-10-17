import numpy as np
import pytest

from mevzuat_rag.degerlendirme import (
    Kume,
    eslestirilmis_bootstrap,
    ilk_tam_sira,
    kanitlar,
    kapsam,
    mcnemar,
    recall_at_k,
)

# Belge metni: "Devam MADDE 1 aaa bbb. MADDE 2 ccc ddd eee." Konumlar elle.
BELGE = "Devam MADDE 1 aaa bbb. MADDE 2 ccc ddd eee."
MADDE = [
    {"id": "d/m1", "belge_id": "d", "metin": BELGE[0:22], "bas": 0, "son": 22},
    {"id": "d/m2", "belge_id": "d", "metin": BELGE[23:43], "bas": 23, "son": 43},
    {"id": "w/k1-1", "belge_id": "w", "metin": "Soru? Cevap burada yazıyor.", "bas": -1, "son": -1},
]
# Sabit koşul: kesimler maddenin ortasından geçiyor, aralarda tek boşluk
SABIT = [
    {"id": "d/s1", "belge_id": "d", "metin": BELGE[0:13], "bas": 0, "son": 13},
    {"id": "d/s2", "belge_id": "d", "metin": BELGE[14:30], "bas": 14, "son": 30},
    {"id": "d/s3", "belge_id": "d", "metin": BELGE[31:43], "bas": 31, "son": 43},
    MADDE[2],
]
DAYANAK = {p["id"]: p for p in MADDE}


def soru(dayanak, kanit):
    return {"id": "q1", "dayanak": dayanak, "kanit": kanit}


def test_kanit_konumu():
    (k,) = kanitlar(soru(["d/m2"], ["ccc ddd"]), DAYANAK)
    assert (k.belge_id, BELGE[k.bas:k.son]) == ("d", "ccc ddd")


def test_madde_kumesinde_kanit_maddesiyle_bulunur():
    ks, kume = kanitlar(soru(["d/m2"], ["ccc ddd"]), DAYANAK), Kume(MADDE)
    assert kapsam(kume, ks, ["d/m2"]) == 1 and kapsam(kume, ks, ["d/m1"]) == 0


def test_sabit_kumede_bolunen_kanit_iki_parcayi_ister():
    # "bbb. MADDE 2 ccc" s2 ile s3'e bölünüyor
    ks, kume = kanitlar(soru(["d/m2"], ["MADDE 2 ccc ddd"]), DAYANAK), Kume(SABIT)
    assert kapsam(kume, ks, ["d/s2"]) == 0
    assert kapsam(kume, ks, ["d/s3", "d/s2"]) == 1  # sıra önemsiz, aradaki boşluk sayılmaz


def test_komsu_olmayan_parcalar_boslugu_kapatmaz():
    ks, kume = kanitlar(soru(["d/m1"], ["Devam MADDE 1 aaa bbb."]), DAYANAK), Kume(SABIT)
    assert kapsam(kume, ks, ["d/s1", "d/s3"]) == 0
    assert kapsam(kume, ks, ["d/s1", "d/s2"]) == 1


def test_baska_belgedeki_ayni_metin_sayilmaz():
    kopya = {"id": "e/m1", "belge_id": "e", "metin": BELGE[23:43], "bas": 23, "son": 43}
    ks, kume = kanitlar(soru(["d/m2"], ["ccc ddd"]), DAYANAK), Kume(MADDE + [kopya])
    assert kapsam(kume, ks, ["e/m1"]) == 0


def test_konumsuz_parcada_metin_aranir():
    ks = kanitlar(soru(["w/k1-1"], ["Cevap burada"]), DAYANAK)
    assert kapsam(Kume(SABIT), ks, ["w/k1-1"]) == 1


def test_cok_dayanakli_kismi_kapsam_ve_ilk_tam_sira():
    ks, kume = kanitlar(soru(["d/m1", "d/m2"], ["aaa bbb", "ddd eee"]), DAYANAK), Kume(MADDE)
    assert kapsam(kume, ks, ["d/m2"]) == 0.5
    assert ilk_tam_sira(kume, ks, ["w/k1-1", "d/m2", "d/m1"]) == 3
    assert ilk_tam_sira(kume, ks, ["d/m2"]) is None


def test_recall_at_k_ilk_k_ile_sinirli():
    ks = [kanitlar(soru(["d/m2"], ["ccc ddd"]), DAYANAK)]
    kume = Kume(MADDE)
    assert recall_at_k(kume, ks, [["d/m1", "d/m2"]], k=1).tolist() == [0.0]
    assert recall_at_k(kume, ks, [["d/m1", "d/m2"]], k=2).tolist() == [1.0]


def test_bootstrap_fark_ve_aralik():
    a = np.array([1, 1, 1, 0] * 25, float)
    assert eslestirilmis_bootstrap(a, a)["fark"] == 0
    s = eslestirilmis_bootstrap(a, np.zeros(100))
    assert s["fark"] == pytest.approx(0.75) and s["alt"] < 0.75 < s["ust"] and s["alt"] > 0.6
    assert eslestirilmis_bootstrap(a, np.zeros(100)) == s  # aynı tohum, aynı sonuç
    with pytest.raises(ValueError):
        eslestirilmis_bootstrap(a, np.zeros(99))


def test_mcnemar():
    a = np.array([1] * 10 + [0] * 2 + [1] * 50)
    b = np.array([0] * 10 + [1] * 2 + [1] * 50)
    r = mcnemar(a, b)
    assert (r["yalniz_a"], r["yalniz_b"]) == (10, 2) and r["p"] == pytest.approx(0.0386, abs=1e-3)
    assert mcnemar(a, a)["p"] == 1.0

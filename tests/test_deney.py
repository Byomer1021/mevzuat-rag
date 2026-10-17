import pytest

from mevzuat_rag.deney import calistir, deney_parcalari, soru_kumeleri

BELGE = "Devam MADDE 1 aaa bbb. MADDE 2 ccc ddd eee."
MADDE = [
    {"id": "d/m1", "belge_id": "d", "tur": "madde", "metin": BELGE[0:22], "bas": 0, "son": 22},
    {"id": "d/m2", "belge_id": "d", "tur": "madde", "metin": BELGE[23:43], "bas": 23, "son": 43},
    {"id": "r/p1", "belge_id": "r", "tur": "paragraf", "metin": "Rehber metni burada.", "bas": 0, "son": 20},
    {"id": "w/k1-1", "belge_id": "w", "tur": "web", "metin": "Soru? Cevap.", "bas": -1, "son": -1},
]
SABIT = [
    {"id": "d/s1", "belge_id": "d", "tur": "sabit", "metin": BELGE[0:13], "bas": 0, "son": 13},
    {"id": "d/s2", "belge_id": "d", "tur": "sabit", "metin": BELGE[14:30], "bas": 14, "son": 30},
    {"id": "d/s3", "belge_id": "d", "tur": "sabit", "metin": BELGE[31:43], "bas": 31, "son": 43},
    MADDE[2], MADDE[3],
]


def soru(qid, dayanak, kanit, tur="tek"):
    return {"id": qid, "soru": qid, "tur": tur, "dayanak": dayanak, "kanit": kanit, "bolum": "dev"}


def test_deney_dizini_web_icermez():
    assert [p["id"] for p in deney_parcalari(MADDE)] == ["d/m1", "d/m2", "r/p1"]


def test_soru_kumeleri():
    ss = [soru("q1", ["d/m2"], ["ccc ddd"]), soru("q2", ["r/p1"], ["Rehber metni"]),
          soru("q3", ["w/k1-1"], ["Cevap."]), soru("q4", [], [], tur="cevapsiz")]
    k = soru_kumeleri(ss, MADDE)
    assert [s["id"] for s in k["birincil"]] == ["q1"]
    assert [s["id"] for s in k["tum_pdf"]] == ["q1", "q2"]


def test_calistir_iki_kosulu_ayni_olcutle_puanlar():
    # q1'in kanıtı "MADDE 2 ccc ddd" s2 ile s3'e bölünüyor
    ss = [soru("q1", ["d/m2"], ["MADDE 2 ccc ddd"]), soru("q2", ["d/m1"], ["aaa bbb."])]
    sahte = {
        "madde": {"q1": ["d/m2", "d/m1"], "q2": ["d/m2", "d/m1"]},
        "sabit": {"q1": ["d/s3", "d/s1", "d/s2"], "q2": ["d/s2", "d/s1"]},
    }
    arayicilar = {ad: (lambda s, k, ad=ad: sahte[ad][s][:k]) for ad in sahte}
    r = calistir(ss, {"madde": MADDE, "sabit": SABIT}, arayicilar, {p["id"]: p for p in MADDE},
                 k_listesi=(1, 5))
    q1, q2 = r["sorular"]
    assert q1["madde"]["kapsam"] == {"1": 1.0, "5": 1.0} and q1["madde"]["sira"] == 1
    assert q1["sabit"]["kapsam"] == {"1": 0.0, "5": 1.0} and q1["sabit"]["sira"] == 3
    assert q2["madde"]["sira"] == 2 and q2["sabit"]["sira"] == 1
    assert r["ozet"]["madde"] == {"R@1": 0.5, "R@5": 1.0, "MRR@5": 0.75}
    assert r["ozet"]["sabit"]["MRR@5"] == pytest.approx((1 / 3 + 1) / 2, abs=1e-4)
    assert r["fark"]["R@1"]["fark"] == 0 and r["karsilastirma"] == "madde - sabit"


def test_calistir_bos():
    r = calistir([], {"madde": MADDE, "sabit": SABIT}, {}, {})
    assert r["n"] == 0 and r["ozet"] == {}

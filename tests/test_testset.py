import pytest

from mevzuat_rag.testset import dogrula, ekle, oku, ozet, yeni_id

PARCALAR = {"a/m1", "a/m2", "b/m1"}


def soru(**kw):
    s = {"id": "q001", "soru": "Devamsızlık sınırı nedir?", "tur": "tek",
         "referans_cevap": "%30", "dayanak": ["a/m1"], "etiketler": ["sayi"],
         "yazan": "omer", "bolum": "dev"}
    s.update(kw)
    return s


def test_gecerli_soru():
    assert dogrula(soru(), PARCALAR) == []


@pytest.mark.parametrize("kw, parca", [
    ({"dayanak": ["a/m1", "a/m2"]}, "tam bir parça"),
    ({"tur": "cok"}, "en az iki"),
    ({"tur": "cevapsiz"}, "dayanak boş olmalı"),
    ({"tur": "cevapsiz", "dayanak": []}, "referans cevap boş olmalı"),
    ({"referans_cevap": " "}, "referans cevap boş"),
    ({"dayanak": ["a/m9"]}, "bilinmeyen parça: a/m9"),
    ({"tur": "cok", "dayanak": ["a/m1", "a/m1"]}, "tekrar"),
    ({"soru": "  "}, "soru boş"),
    ({"tur": "kolay"}, "tur şunlardan"),
    ({"bolum": "egitim"}, "bolum şunlardan"),
])
def test_gecersiz_sorular(kw, parca):
    assert any(parca in h for h in dogrula(soru(**kw), PARCALAR))


def test_ayni_id_reddedilir():
    assert any("zaten var" in h for h in dogrula(soru(), PARCALAR, {"q001"}))


def test_eksik_alan():
    s = soru()
    del s["bolum"]
    assert dogrula(s, PARCALAR) == ["eksik alan: bolum"]


def test_cevapsiz_gecerli():
    assert dogrula(soru(tur="cevapsiz", dayanak=[], referans_cevap=""), PARCALAR) == []


def test_ekle_oku_yeni_id(tmp_path):
    yol = tmp_path / "sorular.jsonl"
    assert oku(yol) == [] and yeni_id([]) == "q001"
    ekle(yol, soru())
    ekle(yol, soru(id="q002", tur="cok", dayanak=["a/m1", "b/m1"]))
    sorular = oku(yol)
    assert [s["id"] for s in sorular] == ["q001", "q002"]
    assert yeni_id(sorular) == "q003"
    oz = ozet(sorular)
    assert oz["tur"] == {"tek": 1, "cok": 1} and oz["belge"] == {"a": 2, "b": 1}

import pytest

from mevzuat_rag.testset import (
    dogrula,
    ekle,
    hepsini_yaz,
    iceri_al,
    kanitlari_ayir,
    oku,
    ozet,
    yeni_id,
)

PARCALAR = {
    "a/m1": "Devam\nMADDE 1- (1) Teorik derslerde en az %70\ndevam zorunluluğu aranır.",
    "a/m2": "MADDE 2- (1) Sınavlar yazılı yapılır.",
    "b/m1": "MADDE 1- (1) Staj süresi yirmi iş günüdür.",
}
KANIT = "Teorik derslerde en az %70 devam zorunluluğu aranır."  # satır sonu boşluk sayılır


def soru(**kw):
    s = {"id": "q001", "soru": "Devamsızlık sınırı nedir?", "tur": "tek",
         "referans_cevap": "%30", "dayanak": ["a/m1"], "kanit": [KANIT], "etiketler": ["sayi"],
         "yazan": "omer", "bolum": "dev"}
    s.update(kw)
    return s


def test_gecerli_soru():
    assert dogrula(soru(), PARCALAR) == []


@pytest.mark.parametrize("kw, parca", [
    ({"dayanak": ["a/m1", "a/m2"]}, "tam bir parça"),
    ({"tur": "cok"}, "en az iki"),
    ({"tur": "cevapsiz"}, "dayanak boş olmalı"),
    ({"tur": "cevapsiz", "dayanak": [], "kanit": []}, "referans cevap boş olmalı"),
    ({"tur": "cevapsiz", "dayanak": [], "referans_cevap": ""}, "kanıt boş olmalı"),
    ({"kanit": []}, "her dayanak için bir kanıt"),
    ({"kanit": ["%70"]}, "en az 20 karakter"),
    ({"kanit": ["Sınavlar yazılı yapılır ve"]}, "metninde birebir yok"),
    ({"kanit": ["teorik derslerde en az %70 devam"]}, "metninde birebir yok"),  # büyük harf
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
    assert dogrula(soru(tur="cevapsiz", dayanak=[], kanit=[], referans_cevap=""), PARCALAR) == []


def test_cok_dayanakli_kanitlar_sirayla():
    kanitlar = [KANIT, "Staj süresi yirmi iş günüdür."]
    assert dogrula(soru(tur="cok", dayanak=["a/m1", "b/m1"], kanit=kanitlar), PARCALAR) == []
    hatalar = dogrula(soru(tur="cok", dayanak=["b/m1", "a/m1"], kanit=kanitlar), PARCALAR)
    assert len(hatalar) == 2 and all("birebir yok" in h for h in hatalar)


def test_kanit_kutusu_bos_satirla_ayrilir():
    # tek alıntı içindeki satır sonu ayırmaz, boş satır ayırır
    assert kanitlari_ayir("bir\niki\n\n  üç  \n\n\n") == ["bir\niki", "üç"]


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


def defter_satiri(yerel_id, **kw):
    # defterin dışa aktardığı biçim: id yok, yerel_id ve tarihler var
    s = {k: v for k, v in soru(**kw).items() if k != "id"}
    return {**s, "yerel_id": yerel_id, "olusturma": "2026-10-18T10:00:00Z"}


def test_iceri_al_ekler_atlar_gunceller():
    mevcut = [soru()]  # q001 Streamlit'ten
    gelen = [defter_satiri("veysel-a", yazan="veysel"),
             defter_satiri("veysel-b", yazan="veysel", soru="Staj kaç gün?",
                           dayanak=["b/m1"], kanit=["Staj süresi yirmi iş günüdür."])]
    sorular, defter, rapor = iceri_al(mevcut, gelen, PARCALAR, {})
    assert rapor == ["q002 eklendi (veysel)", "q003 eklendi (veysel)"]
    assert [s["id"] for s in sorular] == ["q001", "q002", "q003"]
    assert defter == {"veysel-a": "q002", "veysel-b": "q003"}
    assert "yerel_id" not in sorular[1] and sorular[2]["yazan"] == "veysel"

    # aynı dışa aktarım ikinci kez: değişiklik yok
    tekrar, defter2, rapor2 = iceri_al(sorular, gelen, PARCALAR, defter)
    assert tekrar == sorular and defter2 == defter and all("aynı" in r for r in rapor2)

    # defterde düzenlenen soru yerinde güncellenir, kimliği değişmez
    gelen[1]["referans_cevap"] = "Yirmi iş günü."
    son, _, rapor3 = iceri_al(tekrar, gelen[1:], PARCALAR, defter)
    assert son[2]["id"] == "q003" and son[2]["referans_cevap"] == "Yirmi iş günü."
    assert len(son) == 3 and "güncellendi" in rapor3[0]


def test_iceri_al_hatali_soruyu_almaz():
    gelen = [defter_satiri("x-1", kanit=["burada olmayan bir cümle, uzun"]),
             {k: v for k, v in defter_satiri("x-2").items() if k != "yerel_id"}]
    sorular, defter, rapor = iceri_al([], gelen, PARCALAR, {})
    assert sorular == [] and defter == {}
    assert "birebir yok" in rapor[0] and "yerel_id yok" in rapor[1]


def test_hepsini_yaz_sirayi_ve_alanlari_korur(tmp_path):
    yol = tmp_path / "s.jsonl"
    hepsini_yaz(yol, [soru(), {**soru(id="q002"), "fazla": 1}])
    assert [s["id"] for s in oku(yol)] == ["q001", "q002"] and "fazla" not in oku(yol)[1]

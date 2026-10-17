from mevzuat_rag.uretim import BILMIYORUM, ayristir, istem, kunye

ADLAR = {"lisans-yonetmelik": "Lisans Yönetmeliği", "web-sss": "SSS sayfaları"}
M23 = {"id": "lisans-yonetmelik/m23", "belge_id": "lisans-yonetmelik", "tur": "madde",
       "madde": "23", "baslik": "Devam durumu", "sayfa_bas": 5, "sayfa_son": 5,
       "metin": "MADDE 23– (1) Teorik derslerde en az %70 devam zorunluluğu aranır."}
SSS = {"id": "web-sss/k6313-14", "belge_id": "web-sss", "tur": "web", "madde": None,
       "baslik": "Sıkça Sorulan Sorular", "bolum": "Öğrenci İşleri", "sayfa_bas": 1, "sayfa_son": 1,
       "tarih": "", "metin": "Teorik derslere devam zorunluluğu en az %70."}


def test_kunye():
    assert kunye(M23, ADLAR) == "Lisans Yönetmeliği, Madde 23 (Devam durumu), s. 5"
    assert kunye(SSS, ADLAR) == "Öğrenci İşleri · Sıkça Sorulan Sorular"
    iki_sayfa = {**M23, "madde": None, "tur": "paragraf", "sayfa_son": 6}
    assert kunye(iki_sayfa, ADLAR) == "Lisans Yönetmeliği, s. 5-6"


def test_istem_numarali_kaynaklar_ve_soru():
    m = istem("Devamsızlık sınırı ne?", [M23, SSS], ADLAR)
    assert [x["role"] for x in m] == ["system", "user"] and BILMIYORUM in m[0]["content"]
    assert m[1]["content"].startswith("Kaynaklar:\n\n[1] Lisans Yönetmeliği, Madde 23")
    assert "\n\n[2] Öğrenci İşleri" in m[1]["content"]
    assert m[1]["content"].endswith("Soru: Devamsızlık sınırı ne?")


def test_ayristir_atiflar():
    ids = [M23["id"], SSS["id"]]
    r = ayristir("Teorik derslerde en az %70 devam gerekir [1]. SSS de aynısını söylüyor [2][1].", ids)
    assert r == {"bilmiyorum": False, "atiflar": ids, "gecersiz_atif": [], "atifsiz": False}
    r = ayristir("Yüzde 70 [3].", ids)
    assert r["atiflar"] == [] and r["gecersiz_atif"] == [3]
    assert ayristir("Yüzde 70.", ids)["atifsiz"]


def test_ayristir_bilmiyorum():
    ids = [M23["id"]]
    assert ayristir("BİLMİYORUM: Bu bilgi elimdeki belgelerde yok.", ids)["bilmiyorum"]
    assert ayristir("  bilmiyorum: yok", ids)["bilmiyorum"]
    assert ayristir("BILMIYORUM. Belgelerde yok.", ids)["bilmiyorum"]  # İ yerine I
    r = ayristir("Bilmiyorum diyemem, %70 [1].", ids)
    assert not r["bilmiyorum"] and r["atiflar"] == ids

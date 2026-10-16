from mevzuat_rag.kisisel import tara, tc_gecerli

# Geçerli sağlama hanelerine sahip, uydurma bir numara (algoritmayla üretildi)
GECERLI_TC = "10000000146"


def test_tc_saglama():
    assert tc_gecerli(GECERLI_TC)
    assert not tc_gecerli("10000000147")  # son hane bozuk
    assert not tc_gecerli("01234567890")  # sıfırla başlayamaz


def test_tc_bulunur():
    assert tara(f"T.C. Kimlik No: {GECERLI_TC}").riskli


def test_rastgele_11_hane_tc_sayilmaz():
    b = tara("Belge no 12345678901")
    assert b.tc == 0


def test_ogrenci_listesi_riskli():
    liste = "Adı Soyadı Numara\nA. B. 1801042631\nC. D. 1901042117\nE. F. 171044073"
    b = tara(liste)
    assert b.numara == 3 and b.ad_soyad and b.riskli


def test_tek_telefon_numarasi_riskli_degil():
    assert not tara("Santral: 2626051000. Bilgi için arayınız.").riskli


def test_ad_soyad_ve_bir_numara_riskli():
    assert tara("Adı Soyadı: X Y\nÖğrenci No: 1801042631").riskli


def test_yonetmelik_metni_riskli_degil():
    metin = ("MADDE 23 – (1) Öğrenciler derslerin en az %70'ine devam etmek zorundadır. "
             "Resmî Gazete 30.09.2024 sayı 32678.")
    assert not tara(metin).riskli

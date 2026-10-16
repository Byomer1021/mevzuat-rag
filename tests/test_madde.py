import pytest

from mevzuat_rag.madde import madde_basliklari


@pytest.mark.parametrize(
    "satir, no, tur",
    [
        ("MADDE 8- (1) Staj yeri bulma sorumluluğu öğrenciye aittir.", 8, "madde"),
        ("MADDE-7 – Fakülte Staj Komisyonu Üst Kurulunun başkanlığını", 7, "madde"),
        ("Madde 3. (1) Ölçme Seçme ve Yerleştirme Merkezi tarafından", 3, "madde"),
        ("Madde 4- Bu Yönerge’de geçen;", 4, "madde"),
        ("MADDE 12 – (1) Öğrenci", 12, "madde"),
        ("MADDE 1. Bu esasların amacı", 1, "madde"),
        ("GEÇİCİ MADDE 1- (1) Bu Yönetmelik", 1, "gecici"),
        ("GEÇİCİ MADDE 2- (Ek:RG-16/7/2023-32250)", 2, "gecici"),
        ("GEÇİCİ MADDE – Bu yönergenin", None, "gecici"),
        ("EK MADDE 1 – (Ek:RG-21/9/2013-28772) (Değişik:RG-2/5/2014-28988)", 1, "ek"),
    ],
)
def test_belgelerde_gorulen_bicimler(satir, no, tur):
    [b] = madde_basliklari("Önceki satır\n" + satir + "\nSonraki satır")
    assert (b.no, b.tur) == (no, tur)


@pytest.mark.parametrize(
    "metin",
    [
        "Yükseköğretim Kanununun 46. maddesi ile",
        "Yönetmeliğin 6 ncı maddesinin 3 üncü fıkrası saklı kalmak",
        "bu madde 5 kapsamında",  # küçük harf, satır başı değil
        "Ek-1 MADDE 5'te belirtilen",  # satır başında değil
        "ek madde 1 kapsamında başvuru",  # metin içi atıf
    ],
)
def test_metin_ici_atiflar_baslik_sayilmaz(metin):
    assert madde_basliklari(metin) == []


def test_sira_metindeki_konuma_gore():
    metin = "MADDE 1- a\nGEÇİCİ MADDE – b\nEK MADDE 1 – c\nMADDE 2- d"
    assert [(b.no, b.tur) for b in madde_basliklari(metin)] == [
        (1, "madde"), (None, "gecici"), (1, "ek"), (2, "madde")]

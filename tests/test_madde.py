import pytest

from mevzuat_rag.madde import madde_basliklari


@pytest.mark.parametrize(
    "satir, no, gecici",
    [
        ("MADDE 8- (1) Staj yeri bulma sorumluluğu öğrenciye aittir.", 8, False),
        ("MADDE-7 – Fakülte Staj Komisyonu Üst Kurulunun başkanlığını", 7, False),
        ("Madde 3. (1) Ölçme Seçme ve Yerleştirme Merkezi tarafından", 3, False),
        ("Madde 4- Bu Yönerge’de geçen;", 4, False),
        ("MADDE 12 – (1) Öğrenci", 12, False),
        ("GEÇİCİ MADDE 1- (1) Bu Yönetmelik", 1, True),
        ("GEÇİCİ MADDE – Bu yönergenin", None, True),
    ],
)
def test_belgelerde_gorulen_bicimler(satir, no, gecici):
    [b] = madde_basliklari("Önceki satır\n" + satir + "\nSonraki satır")
    assert (b.no, b.gecici) == (no, gecici)


@pytest.mark.parametrize(
    "metin",
    [
        "Yükseköğretim Kanununun 46. maddesi ile",
        "Yönetmeliğin 6 ncı maddesinin 3 üncü fıkrası saklı kalmak",
        "bu madde 5 kapsamında",  # küçük harf, satır başı değil
        "Ek-1 MADDE 5'te belirtilen",  # satır başında değil
    ],
)
def test_metin_ici_atiflar_baslik_sayilmaz(metin):
    assert madde_basliklari(metin) == []


def test_sira_metindeki_konuma_gore():
    metin = "MADDE 1- a\nGEÇİCİ MADDE – b\nMADDE 2- c"
    assert [(b.no, b.gecici) for b in madde_basliklari(metin)] == [(1, False), (None, True), (2, False)]

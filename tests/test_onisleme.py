import pymupdf
import pytest

from mevzuat_rag.onisleme import sayfayi_temizle


@pytest.fixture
def sayfa():
    """GTÜ belgesi gibi: üstte başlık tablosu, altta form numarası, arada
    madde, tablo satırı ve paragraf boşluğu."""
    d = pymupdf.open()
    s = d.new_page(width=595, height=842)

    def yaz(x, y, t):
        s.insert_text((x, y), t, fontsize=10)

    # başlık tablosu: satırlar birbirine değmiyor (gerçek belgelerdeki gibi)
    yaz(60, 50, "T.C. GEBZE TEKNIK UNIVERSITESI")
    yaz(400, 50, "Doküman No")
    yaz(480, 50, "YÖ-0001")
    yaz(400, 70, "Revizyon No")
    yaz(480, 70, "3")
    yaz(400, 90, "Sayfa")
    yaz(480, 90, "4-2")
    # gövde
    yaz(60, 130, "Amac")
    yaz(60, 143, "MADDE 1- (1) Bu yonergenin amaci budur.")
    yaz(200, 200, "0-30")  # tablo satırı: aynı yükseklikte iki hücre
    yaz(300, 200, "F4")
    yaz(60, 213, "Kapsam")
    yaz(60, 800, "Form No: FR-0356 Yayın Tarihi: 23.11.2017")
    yield s
    d.close()


def test_baslik_ve_altlik_atilir(sayfa):
    metin = sayfayi_temizle(sayfa).metin
    for iz in ["Doküman No", "YÖ-0001", "Revizyon No", "Sayfa", "4-2", "T.C.", "Form No"]:
        assert iz not in metin


def test_govde_sirasi_ve_satirlari_korunur(sayfa):
    metin = sayfayi_temizle(sayfa).metin
    assert "Amac\nMADDE 1- (1) Bu yonergenin amaci budur." in metin


def test_ayni_yukseklikteki_hucreler_sekmeyle_birlesir(sayfa):
    assert "0-30\tF4" in sayfayi_temizle(sayfa).metin


def test_buyuk_dikey_bosluk_paragraf_siniri(sayfa):
    metin = sayfayi_temizle(sayfa).metin
    assert "budur.\n\n0-30" in metin  # 143 -> 200: paragraf arası
    assert "F4\nKapsam" in metin  # 200 -> 213: aynı paragraf


def test_atilanlar_denetim_icin_kaydedilir(sayfa):
    atilan = sayfayi_temizle(sayfa).atilan
    assert "Doküman No" in atilan and any(a.startswith("Form No:") for a in atilan)

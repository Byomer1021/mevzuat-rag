import itertools

import pytest

from mevzuat_rag.onisleme import Sayfa
from mevzuat_rag.parcalama import (
    katalog_parcala,
    madde_parcala,
    paragraf_parcala,
    sabit_parcala,
    takvim_parcala,
    web_parcala,
)


def bosluksuz(s):
    return "".join(s.split())


@pytest.fixture
def sayfalar():
    return [
        Sayfa(1, "BİRİNCİ BÖLÜM\nGenel Hükümler\nAmaç\nMADDE 1- (1) Amaç budur.\n"
                 "Kapsam\nMADDE 2- (1) Kapsam şudur ve"),
        # YÖ-0002'deki durum: tablonun son satırının hemen ardından başlıksız madde
        Sayfa(2, "sonraki sayfada sürer.\nNotlar\nMADDE 3- (1) Notlar:\n"
                 "51 - 59\tF1\tBaşarısız\n0-30\tF4\tBaşarısız\n\n"
                 "MADDE 4- (1) Başlıksız madde.\n"
                 "6/2/2023 Tarihli depremlere ilişkin hükümleri\n"
                 "GEÇİCİ MADDE 1– (1) Geçiş.\nÖğretim planları"),
        Sayfa(3, "MADDE 5 – (1) Planlar.\nSeviye Tespit Sınavı\n(ÖLİST)\nMadde 6. (1) Sınav."),
    ]


@pytest.fixture
def parcalar(sayfalar):
    return {p.id: p for p in madde_parcala("b", sayfalar)}


def test_kimlikler_ve_turler(parcalar):
    assert list(parcalar) == ["b/m1", "b/m2", "b/m3", "b/m4", "b/g1", "b/m5", "b/m6"]
    assert parcalar["b/g1"].tur == "gecici" and parcalar["b/g1"].madde == "geçici 1"


def test_bolum_ve_baslik(parcalar):
    assert parcalar["b/m1"].bolum == "BİRİNCİ BÖLÜM Genel Hükümler"
    assert parcalar["b/m1"].baslik == "Amaç"
    assert parcalar["b/m2"].baslik == "Kapsam"


def test_tablo_satiri_baslik_sayilmaz_ve_onceki_maddede_kalir(parcalar):
    # YÖ-0002: "0-30 F4 Başarısız" başlıksız m5'in başlığı sanılıyordu
    assert parcalar["b/m4"].baslik == ""
    assert parcalar["b/m3"].metin.endswith("0-30\tF4\tBaşarısız")


def test_rakamla_baslayan_baslik(parcalar):
    assert parcalar["b/g1"].baslik == "6/2/2023 Tarihli depremlere ilişkin hükümleri"


def test_onceki_sayfada_kalan_baslik(parcalar):
    # YN-0001 m13: başlık 2. sayfanın sonunda, madde 3. sayfada
    m5 = parcalar["b/m5"]
    assert m5.baslik == "Öğretim planları" and m5.metin.startswith("Öğretim planları")
    assert (m5.sayfa_bas, m5.sayfa_son) == (3, 3)


def test_kisaltma_satiri_basliga_eklenir(parcalar):
    assert parcalar["b/m6"].baslik == "Seviye Tespit Sınavı (ÖLİST)"


def test_sayfa_araligi(parcalar):
    assert (parcalar["b/m2"].sayfa_bas, parcalar["b/m2"].sayfa_son) == (1, 2)
    assert (parcalar["b/m1"].sayfa_bas, parcalar["b/m1"].sayfa_son) == (1, 1)


def test_parcalar_metni_kayipsiz_ortuyor(sayfalar, parcalar):
    hepsi = "".join(p.metin for p in parcalar.values())
    assert bosluksuz(hepsi) == bosluksuz("\n".join(s.metin for s in sayfalar))


@pytest.mark.parametrize("parcala", [
    lambda s: madde_parcala("b", s),
    lambda s: paragraf_parcala("b", s, hedef=40),
    lambda s: sabit_parcala("b", s, boyut=50, ortusme=0),
])
def test_konum_belge_metnindeki_aralik(sayfalar, parcala):
    # degerlendirme.py kanıtın kapsanmasını bu aralıklarla hesaplıyor
    belge = "\n".join(s.metin for s in sayfalar)
    ps = parcala(sayfalar)
    assert all(p.metin == belge[p.bas:p.son] for p in ps)
    ardisik = list(itertools.pairwise(ps))
    assert all(a.son <= b.bas for a, b in ardisik)  # sıralı, örtüşmesiz
    assert all(not belge[a.son:b.bas].strip() for a, b in ardisik)  # arada yalnız boşluk


def test_ek_madde_kendi_parcasi():
    # YÖK geçiş yönetmeliği: "Ek Madde-1 ile yatay geçiş" ayrı bir madde
    s = [Sayfa(1, "Yürürlükten kaldırılan yönetmelik\nMADDE 25 – (1) Kaldırılmıştır.\n"
                  "Merkezi yerleştirme puanıyla yatay geçiş\n"
                  "EK MADDE 1 – (Ek:RG-21/9/2013-28772)\n(1) Öğrencinin puanı...\n"
                  "Yürürlük\nMADDE 26 – (1) Yürürlüğe girer.")]
    ps = {p.id: p for p in madde_parcala("yok", s)}
    assert list(ps) == ["yok/m25", "yok/e1", "yok/m26"]
    e1 = ps["yok/e1"]
    assert (e1.tur, e1.madde, e1.baslik) == ("ek", "ek 1", "Merkezi yerleştirme puanıyla yatay geçiş")
    assert "Kaldırılmıştır" in ps["yok/m25"].metin and "EK MADDE" not in ps["yok/m25"].metin


def test_madde_yoksa_bos_doner():
    assert madde_parcala("x", [Sayfa(1, "Bu belge madde içermez.")]) == []


def test_paragraf_parcala_hedefe_kadar_birlestirir():
    s = [Sayfa(1, "aaaa\n\nbbbb\n\ncccc"), Sayfa(2, "dddd")]
    ps = paragraf_parcala("x", s, hedef=12)
    assert [p.metin for p in ps] == ["aaaa\n\nbbbb", "cccc\ndddd"]
    assert (ps[1].sayfa_bas, ps[1].sayfa_son) == (1, 2)


def test_paragraf_parcala_bosluksuz_uzun_blogu_satirlara_boler():
    # öğretim planı tablosu: boş satır yok, satırlar sekmeli
    tablo = "\n".join(f"CSE {100 + i}\tDers {i}\t3\t0\t0\t3\t5" for i in range(40))
    s = [Sayfa(1, "Kısa giriş paragrafı.\n\n" + tablo)]
    ps = paragraf_parcala("x", s, hedef=120)
    assert len(ps) > 5 and all(len(p.metin) <= 120 for p in ps)
    assert bosluksuz("".join(p.metin for p in ps)) == bosluksuz(s[0].metin)
    assert all(p.metin.startswith(("Kısa", "CSE ")) for p in ps)  # satır ortasından kesilmez


def test_paragraf_parcala_kisa_paragraf_satirlarina_bolunmez():
    s = [Sayfa(1, "satır bir\nsatır iki\nsatır üç")]
    assert [p.metin for p in paragraf_parcala("x", s, hedef=20)] == ["satır bir\nsatır iki\nsatır üç"]


def test_sabit_parcala_boyut_ve_ortusme():
    kelimeler = [f"k{i}" for i in range(200)]
    s = [Sayfa(1, " ".join(kelimeler[:100])), Sayfa(2, " ".join(kelimeler[100:]))]
    ps = sabit_parcala("x", s, boyut=120, ortusme=30)
    assert all(len(p.metin) <= 120 for p in ps)
    assert set(kelimeler) <= set(" ".join(p.metin for p in ps).split())
    assert ps[0].metin.split()[-1] in ps[1].metin.split()  # örtüşme
    assert ps[0].sayfa_bas == 1 and ps[-1].sayfa_son == 2


def test_sabit_parcala_gecersiz_ortusme():
    with pytest.raises(ValueError):
        sabit_parcala("x", [Sayfa(1, "a b c")], boyut=10, ortusme=10)


def test_web_soru_cevabiyla_kalir():
    uzun_cevap = "Cevap " * 100  # hedefin üstünde; yine de sorusundan ayrılmaz
    oge = {"id": "k1957", "birim": "Bilgisayar Mühendisliği", "baslik": "SSS", "url": "https://x",
           "metin": f"Giriş paragrafı.\n\n1. Staj kaç gün?\n\n{uzun_cevap}\n\n"
                    "2. Yaz okulunda staj yapılır mı?\n\nEvet.\n\nEk not."}
    ps = web_parcala("web-sss", oge, hedef=60)
    assert [p.metin.split("\n\n")[0] for p in ps] == [
        "Giriş paragrafı.", "1. Staj kaç gün?", "2. Yaz okulunda staj yapılır mı?"]
    assert ps[1].metin.endswith(uzun_cevap.strip())
    assert ps[2].metin == "2. Yaz okulunda staj yapılır mı?\n\nEvet.\n\nEk not."
    assert ps[0].id == "web-sss/k1957-1" and ps[0].url == "https://x" and ps[0].bolum == oge["birim"]


def test_katalog_yalniz_ogrenci_formlari_ve_tekil_kimlik():
    tsv = ("kod\tad\trevizyon\turl\n"
           "FR-0853\tKayıt Dondurma Başvuru Formu\tR0\thttps://x/FR-0853.docx\n"
           "FR-0127\tDoğum Dilekçe\tR1\thttps://x/FR-0127.docx\n"
           "FR-0284\tMimarlık Staj Dilekçe Sicil Fişi (Türkçe)\tR0\thttps://x/a.docx\n"
           "FR-0284\tMimarlık Staj Dilekçe Sicil Fişi - İngilizce\tR0\thttps://x/b.docx\n")
    ps = katalog_parcala("form-katalogu", tsv)
    assert [p.id for p in ps] == ["form-katalogu/FR-0853", "form-katalogu/FR-0284",
                                  "form-katalogu/FR-0284-2"]
    assert ps[0].tur == "form" and ps[0].baslik == "Kayıt Dondurma Başvuru Formu"
    assert "https://x/FR-0853.docx" in ps[0].metin


def test_takvim_satirlari():
    tsv = ("lisans_onlisans\ttarih\tlisansustu\n"
           "2026-2027 AKADEMİK TAKVİM\t\t\n"
           "LİSANS/ÖNLİSANS\tTARİHLER\tLİSANSÜSTÜ\n"
           "Derslerin Başlaması\t21 Eylül 2026\tDerslerin Başlaması\n"
           "\t01-30 Haziran 2026\tDoktora Yeterlik Sınavları\n")
    ps = takvim_parcala("t", tsv)
    assert [p.id for p in ps] == ["t/r1", "t/r2"]
    assert ps[0].bolum == "2026-2027 AKADEMİK TAKVİM"
    assert ps[0].metin == ("Tarih: 21 Eylül 2026\nLisans/önlisans: Derslerin Başlaması\n"
                           "Lisansüstü: Derslerin Başlaması")
    assert "Lisans/önlisans" not in ps[1].metin

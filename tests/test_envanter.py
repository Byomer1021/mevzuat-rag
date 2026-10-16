import importlib.util
from pathlib import Path

import pytest

_yol = Path(__file__).resolve().parents[1] / "scripts" / "envanter.py"
_spec = importlib.util.spec_from_file_location("envanter", _yol)
envanter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(envanter)


@pytest.mark.parametrize("baslik, dosya, beklenen", [
    ("Staj Başvuru Formu", "staj_form.pdf", "form"),
    # sınav kelimesi geçse de esaslar mevzuattır
    ("Ders Muafiyet Sınavı Uygulama Esasları", "x.pdf", "mevzuat"),
    ("2022-23 Seminer Kuralları V2", "seminer.pdf", "mevzuat"),
    # ilk sürümde "diger"e düşüyorlardı
    ("2025-2026 1. Ek ders Sınavı", "ek.pdf", "sinav-ders-programi"),
    ("Tek Ders Sınavı", "tds.pdf", "sinav-ders-programi"),
    ("2026-2027 Güz Dönemi Final Sınav Takvimi V4", "v4_final programı.pdf", "sinav-ders-programi"),
    ("Bilgisayar Mühendisliği Bölümü Öğretim Planı (2026)", "plan.pdf", "ogretim-plani"),
    ("ÖNEMLİ: STAJ DEFTERİ KLAVUZU", "klavuz.pdf", "rehber"),
    ("Yaz Staj Sonuçları V2", "sonuc.pdf", "ilan-sonuc"),
    # 60'lık örneklemde yanlış çıkanlar (olcumler §7)
    ("2022 - 2023 Yılı Staj Sonuçları", "Staj Sonuçları Duyuru revize.pdf", "ilan-sonuc"),
    ("24.01.2023 LİSANSÜSTÜ İNGİLİZCE SINAV SONUÇLARI", "x.pdf", "ilan-sonuc"),
    ("tıklayınız", "12.06.2026 SINIF LİSTELERİ.pdf", "ilan-sonuc"),  # ayrışmış İ
    ("TÜRK EĞİTİM VAKFI BURSU", "TEV-YURTDISI-BURS_ILANI-2019.pdf", "ilan-sonuc"),
    ("/fileman/x/v9_schedule_all_courses.pdf", "v9_schedule_all_courses.pdf", "sinav-ders-programi"),
    ("Serbest Seçmeli Dersler", "2020_serbest_secmeli_dersler.pdf", "ogretim-plani"),
    ("Deney Kılavuzu EM9 Rapor", "Exp9 2026 V2.pdf", "ders-materyali"),
])
def test_tur(baslik, dosya, beklenen):
    assert envanter.tur(baslik, dosya) == beklenen


@pytest.mark.parametrize("metin, riskli", [
    ("Yaz Staj Sonuçları V2", True),
    ("ÇAP Kabul Edilen Öğrenciler Listesi", True),
    ("495-496 GRUPLAR", True),
    ("Bilgisayar Mühendisliği Bölümü Öğretim Planı (2026)", False),
    ("Staj Defteri Nasıl Doldurulur?", False),
])
def test_kisisel_veri_riski(metin, riskli):
    assert bool(envanter.KISISEL_VERI.search(envanter.kucuk(metin))) == riskli


def test_yil_en_buyugu_alir():
    assert envanter.yil("2025-2026 Bahar", "x_2027.pdf") == 2027
    assert envanter.yil("Seminer Kuralları", "kural.pdf") is None
    assert envanter.yil("20251 numaralı", "") is None  # beş haneli sayı yıl değil

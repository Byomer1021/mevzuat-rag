import pytest

from mevzuat_rag.formlar import ogrenci_formu


@pytest.mark.parametrize("ad", [
    "Kayıt Dondurma Başvuru Formu",
    "Lisans Ara Sınav/Final Mazeret Sınavı Talep Dilekçesi",
    "Not İtiraz Dilekçesi",
    "Merkezi Yatay Geçiş Ek Madde 1 Başvuru Formu",
    "Muafiyet Sınav Formu",
    "Staj Fişi",
    # ilk kurallarda yanlışlıkla dışlananlar
    "Tek Ders Sınav Dilekçesi",  # "ek ders" kalıbı "tek ders"in içinde eşleşiyordu
    "Lisans/Lisansüstü İlişik Kesme Formu",
    "Staj Degerlendirme Anketi",
    "Stajyerin Kurumu Degerlendirme Anketi",
    "Öğrenci Toplulukları Genel Kurul Toplantı Tutanağı",
    "Psikolojik Taciz ile Mücadele Birimi Başvuru Formu",
])
def test_ogrenci_formu(ad):
    assert ogrenci_formu(ad)


@pytest.mark.parametrize("ad", [
    "Doğum Dilekçe",  # ilk kurallarda "dilekçe" yüzünden içerideydi
    "Profesör ve Doçent Atama Dilekçesi",
    "Emeklilik Talep Dilekçesi",
    "Ders Devam Çizelgesi",  # hocanın formu
    "Ek Ders Çarşaf Listesi",
    "YL-DR Ders Saydırma Formu",  # lisansüstü kapsam dışı
    "Öğrenci Memnuniyet Anketi",
    "Mal ve Hizmet Alımı Ödemeleri Ön Mali Kontrol Formu",
    "Öğrenim Durumu Değişikliği Dilekçesi",  # personelin maaş işlemi
    "GTÜ SEM Tasarım ve Bilim Yaz Okulu İzin Formu",  # lise öğrencilerine yönelik
])
def test_ogrenci_formu_degil(ad):
    assert not ogrenci_formu(ad)

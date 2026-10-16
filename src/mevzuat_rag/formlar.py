"""Kalite Ofisi form listesinden öğrencinin kullandığı formları seçer.

Bilgi tabanı formların içeriğini değil kataloğunu taşır: kod, ad,
revizyon, bağlantı (K-020). "Kayıt dondurmak için hangi formu
doldurmalıyım?" sorusunun cevabı mevzuatta yok: 532 parçanın yalnızca 6'sında
bir FR- kodu geçiyor ve kayıt dondurmayı düzenleyen YN-0001 m19 hiçbir formu
adlandırmıyor (olcumler §8).

Bir form, adında öğrenciye işaret eden bir kelime geçiyor ve idari/personel/
lisansüstü/anket işareti geçmiyorsa öğrenci formu sayılır. Kararsız kalınan
form dışarıda kalır.
"""

import re
import unicodedata

_OGRENCI = re.compile(
    r"öğrenci|ogrenci|staj|kayıt|ders|muafiyet|intibak|mezuniyet|diploma|transkript|"
    r"çift anadal|çap\b|yandal|yan dal|yatay geçiş|dikey geçiş|\baf\b|burs|erasmus|"
    r"değişim|danışman|dilekçe|dondurma|ilişik|engelli|topluluk|kısmi zamanlı|"
    r"endüstriyel uygulama|müfredat dışı|gtü ?1\d\d|gtu ?1\d\d|hazırlık|yaz okulu|"
    r"yaz öğretimi|itiraz|mazeret|bitirme|kimlik kartı|katkı payı|öğrenim ücreti|"
    r"not düzeltme|sınav sonuc|özel öğrenci|misafir öğrenci|psikolojik taciz",
)
_DISLA = re.compile(
    r"personel|akademik kadro|görevlendirme|maaş|ödeme|ödenek|mali|satın ?alma|ihale|piyasa|"
    r"fiyat|anket|memnuniyet|jüri|\btez\b|tez |doktora|\bdr\b|\byl\b|yüksek lisans|lisansüstü|"
    r"enstitü|\bbap\b|hakem|cihaz|demirbaş|taşınır|araç|yakıt|enerji|iş sağlığı|kaza|stok|"
    r"arşiv|kalite|iç denetim|uygunsuzluk|düzeltici|hizmet ?içi|toplantı|\bek ders|"
    r"sınav görevli|gözetmen|öğretim elemanı|öğretim üyesi|ders yükü|ders görevlendirme|"
    r"yemekhane|ders dağılım|ders programı talep|"
    # ilk listede "dilekçe"/"ders" yüzünden girmiş personel ve birim formları
    r"araştırma görevlisi|öğretim görevlisi|profesör|doçent|atama|atanma|kadro|unvan|"
    r"emeklilik|naklen|işçi|doğum|evlenme|pasaport|misafirhane|döner sermaye|"
    r"danışmanlık işi|nmr|analiz|bakım|etik kurul|patent|özel hesab|teşvik|"
    r"hizmet birleştirme|yoklama|devam çizelgesi|ders içeri|yeni ders|ders planı uygunluk|"
    r"ders performans|derslik programı|komisyon kararı|kurumda çalıştığına|eğitim içeriği|"
    r"eğitim kayıtları|ücret iade|shçek|aydek|doküman/kayıt|kısmi zamanlı araştırmacı|"
    r"öğrenim durumu değişikliği|vermek üzere|gtü ?sem\b|gtüsem",
)


# Dışlama kuralına takılan ama öğrencinin doldurduğu formlar (olcumler §8):
# "Lisans/Lisansüstü İlişik Kesme", "Personel/Öğrenci" ortak formları, staj
# dosyasındaki anketler (FR-0080/0185/0186; Staj Yönergesi bunlara atıf yapar),
# öğrenci topluluklarının toplantı ve kuruluş belgeleri.
_ISTISNA = re.compile(
    r"lisans/lisansüstü|personel/öğrenci|öğrenci/personel|staj.*anket|stajyer.*anket|"
    r"öğrenci topluluğu|öğrenci toplulukları genel|topluluk kuruluş|mesai saati dışı öğrenci",
)


def kucuk(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return s.replace("I", "ı").replace("İ", "i").lower()


def ogrenci_formu(ad: str) -> bool:
    a = kucuk(ad)
    if not _OGRENCI.search(a):
        return False
    return not _DISLA.search(a) or bool(_ISTISNA.search(a))

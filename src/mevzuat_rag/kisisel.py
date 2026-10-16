"""Metinde kişisel veri izi arar. Bilgi tabanı kişisel veri içermez (proje
tanımı); taramadan alınan her belge ve sayfa buradan geçer (K-019).

Başlıktan tespit güvenilmez çıktı: "Devamsızlıktan Kalanlar" listeleri
başlıktan işaretlenmedi (olcumler §7). Burada içeriğe bakılıyor:

- TC kimlik no: 11 hane, sağlama haneleri tutmalı (rastgele 11 haneli sayı
  elenir).
- öğrenci no: 9-10 haneli sayı. Telefon da bu biçimde olabilir; bu yüzden
  tek başına değil, en az OGRENCI_NO_ESIK farklı numara olunca sayılır.
- "Adı Soyadı" sütun başlığı: liste işareti.
- öğrenci e-postası: kişi adına @gtu.edu.tr adresi (personelinkiler de bu
  biçimde; yalnızca sayımla birlikte değerlendirilir).
"""

import re
from dataclasses import dataclass

_TC = re.compile(r"(?<!\d)([1-9]\d{10})(?!\d)")
_NUMARA = re.compile(r"(?<!\d)(\d{9,10})(?!\d)")
_AD_SOYAD = re.compile(r"ad[ıi]?\s*(ve\s*)?soyad", re.IGNORECASE)
OGRENCI_NO_ESIK = 3


def tc_gecerli(s: str) -> bool:
    d = [int(c) for c in s]
    if len(d) != 11 or d[0] == 0:
        return False
    on = (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10
    return d[9] == on and d[10] == sum(d[:10]) % 10


@dataclass
class Bulgu:
    tc: int
    numara: int
    ad_soyad: bool

    @property
    def riskli(self) -> bool:
        return self.tc > 0 or self.numara >= OGRENCI_NO_ESIK or (self.ad_soyad and self.numara > 0)


def tara(metin: str) -> Bulgu:
    tc = {m for m in _TC.findall(metin) if tc_gecerli(m)}
    numara = set(_NUMARA.findall(metin)) - tc
    return Bulgu(len(tc), len(numara), bool(_AD_SOYAD.search(metin)))

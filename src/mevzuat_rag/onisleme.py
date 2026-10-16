"""PDF'ten temiz sayfa metni: kalite formu başlığı ve altlığı çıkarılır.

GTÜ belgelerinin her sayfasında bir başlık tablosu (T.C., belge adı, Doküman
No, Yayın/Revizyon Tarihi, Revizyon No, Sayfa) ve bir altlık (Form No: FR-…)
var. Bunlar metnin %6-10'u ve sayfa sonunda maddelerin ortasına giriyor
(olcumler §3).

Başlık tablosunun alt kenarı belgeden belgeye değişiyor, sabit bir eşik
tutmuyor; "Sayfa 7-3" gibi her sayfada değişen satırlar da tekrar eden satır
kuralına takılmıyor. Bu yüzden başlık içerikten bulunuyor: "Doküman No" ve
"Revizyon No" satırları ile bunlara değen satırlar başlık, "Form No:" ile
başlayan satır ve altındakiler altlık.

Her şey satır düzeyinde yapılıyor, blok düzeyinde değil. PyMuPDF'in blok
sınır kutusu metninden geniş olabiliyor: YÖ-0002'de m5-m6 bloğu, tablonun üst
kenarından başlıyor görünüyor ve bloklara göre sıralayınca tablo m6'nın
arkasına düşüyordu (olcumler §4). Satırların kutusu kendi metnini sarıyor.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

_SIMGE = re.compile("[-]")

BASLIK_IZLERI = ("Doküman No", "Revizyon No")
# Tablonun son satırındaki "Sayfa" hücresi: satır kutuları birbirine değmediği
# için üstteki satırlardan yayılarak bulunamıyor, kendisi de tohum olmalı.
# Yalnız başına geçerli değil: başka biçimde bir belgede altlıktaki "Sayfa"
# satırı, üstündeki bütün sayfayı başlık sandırırdı.
BASLIK_HUCRELERI = ("Sayfa",)
ALTLIK_IZI = "Form No:"
# Başlık ve altlık yalnızca bu bölgelerde aranır (sayfa yüksekliğine oranla).
# 13 belgede başlık tohumları en fazla %16'ya, altlık en az %91'e iniyor
# (olcumler §5); bölgeler pay bırakıyor. Bölge dışında kalan "Form No:" veya
# "Sayfa" gövde metnidir, dokunulmaz.
BASLIK_BOLGESI = 0.25
ALTLIK_BOLGESI = 0.85
# Eklerdeki formların kendi altlığı sayfanın ortasında kalabiliyor (YÖ-0046
# s7: "Form No: FR-0458 Yayın Tarihi:08.10.2018 Değ.No:0"). Kalıbın tamamı
# gövde metninde geçmez; yalnızca o satır atılır, altındakiler değil.
ALTLIK_KALIBI = re.compile(r"^Form No:\s*FR-\d{3,4}\b.*Yay.n Tarihi", re.IGNORECASE)
SATIR_TOLERANS = 2.0  # pt; aynı yükseklikteki satırlar (tablo hücreleri) tek satır
# Satır arası boşluk dağılımı iki tepeli: 0-3 pt'de 1907 aralık (paragraf
# içi), 10-15 pt'de 263 (paragraf arası), 5-9 pt'de yalnızca 19 (olcumler §4).
PARAGRAF_ARALIGI = 6.0


@dataclass
class Sayfa:
    no: int  # 1'den başlar
    metin: str
    atilan: list[str] = field(default_factory=list)  # denetim için


@dataclass
class _Satir:
    x0: float
    y0: float
    y1: float
    metin: str


def _satirlar(sayfa: pymupdf.Page) -> list[_Satir]:
    out = []
    for blok in sayfa.get_text("dict")["blocks"]:
        for satir in blok.get("lines", []):
            # Symbol/Wingdings madde imleri özel kullanım alanında (U+F0B7, U+F076…)
            metin = _SIMGE.sub("•", "".join(s["text"] for s in satir["spans"]))
            if metin.strip():
                x0, y0, _, y1 = satir["bbox"]
                out.append(_Satir(x0, y0, y1, " ".join(metin.split())))
    return out


def sayfayi_temizle(sayfa: pymupdf.Page) -> Sayfa:
    satirlar = _satirlar(sayfa)
    baslik_siniri = sayfa.rect.height * BASLIK_BOLGESI
    altlik_siniri = sayfa.rect.height * ALTLIK_BOLGESI
    atilan: set[int] = set()

    altlik = [i for i, s in enumerate(satirlar)
              if s.metin.startswith(ALTLIK_IZI) and s.y0 >= altlik_siniri]
    if altlik:
        ust = min(satirlar[i].y0 for i in altlik)
        atilan |= {i for i, s in enumerate(satirlar) if s.y0 >= ust}
    atilan |= {i for i, s in enumerate(satirlar) if ALTLIK_KALIBI.match(s.metin)}

    ust_bolge = [i for i, s in enumerate(satirlar) if i not in atilan and s.y0 < baslik_siniri]
    izler = [i for i in ust_bolge if any(iz in satirlar[i].metin for iz in BASLIK_IZLERI)]
    tohum = izler + ([i for i in ust_bolge if satirlar[i].metin in BASLIK_HUCRELERI]
                     if izler else [])
    if tohum:
        alt = max(satirlar[i].y1 for i in tohum)
        atilan |= set(tohum)
        degisti = True
        while degisti:  # başlığa değen satırlar başlığın parçası; bölge dışına taşmaz
            degisti = False
            for i in ust_bolge:
                if i not in atilan and satirlar[i].y0 < alt:
                    atilan.add(i)
                    alt = max(alt, satirlar[i].y1)
                    degisti = True

    kalan = sorted((s for i, s in enumerate(satirlar) if i not in atilan),
                   key=lambda s: (s.y0, s.x0))
    sirali: list[list[_Satir]] = []
    for s in kalan:
        if sirali and abs(s.y0 - sirali[-1][0].y0) <= SATIR_TOLERANS:
            sirali[-1].append(s)
        else:
            sirali.append([s])

    cikti, onceki_alt = [], None
    for g in sirali:
        if onceki_alt is not None and min(s.y0 for s in g) - onceki_alt > PARAGRAF_ARALIGI:
            cikti.append("")  # paragraf sınırı
        # Birden fazla hücreden oluşan satır (tablo satırı) sekmeyle birleşir;
        # parçalayıcı sekmeli satırı madde başlığı saymaz ("0-30 F4 Başarısız").
        cikti.append("\t".join(s.metin for s in sorted(g, key=lambda s: s.x0)))
        onceki_alt = max(s.y1 for s in g)
    return Sayfa(sayfa.number + 1, "\n".join(cikti), [satirlar[i].metin for i in sorted(atilan)])


def pdf_sayfalari(yol: Path) -> list[Sayfa]:
    with pymupdf.open(yol) as d:
        return [sayfayi_temizle(s) for s in d]

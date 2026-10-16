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

from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

BASLIK_IZLERI = ("Doküman No", "Revizyon No")
# Tablonun son satırındaki "Sayfa" hücresi: satır kutuları birbirine değmediği
# için üstteki satırlardan yayılarak bulunamıyor, kendisi de tohum olmalı.
BASLIK_HUCRELERI = ("Sayfa",)
ALTLIK_IZI = "Form No:"
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
            metin = "".join(s["text"] for s in satir["spans"])
            if metin.strip():
                x0, y0, _, y1 = satir["bbox"]
                out.append(_Satir(x0, y0, y1, " ".join(metin.split())))
    return out


def sayfayi_temizle(sayfa: pymupdf.Page) -> Sayfa:
    satirlar = _satirlar(sayfa)
    atilan: set[int] = set()

    altlik = [i for i, s in enumerate(satirlar) if s.metin.startswith(ALTLIK_IZI)]
    if altlik:
        ust = min(satirlar[i].y0 for i in altlik)
        atilan |= {i for i, s in enumerate(satirlar) if s.y0 >= ust}

    tohum = [i for i, s in enumerate(satirlar)
             if i not in atilan and (any(iz in s.metin for iz in BASLIK_IZLERI)
                                     or s.metin in BASLIK_HUCRELERI)]
    if tohum:
        alt = max(satirlar[i].y1 for i in tohum)
        atilan |= set(tohum)
        degisti = True
        while degisti:  # başlığa değen satırlar başlığın parçası
            degisti = False
            for i, s in enumerate(satirlar):
                if i not in atilan and s.y0 < alt:
                    atilan.add(i)
                    alt = max(alt, s.y1)
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

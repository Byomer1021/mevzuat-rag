"""Mevzuat metninde madde başlıklarını bulur.

Belgelerde görülen biçimler (olcumler §2, §6):

    MADDE 8- (1) ...        yönetmelikler, çoğu yönerge
    MADDE-7 – ...           YÖ-0019'da tek bir madde
    Madde 3. (1) ...        YÖ-0002
    Madde 4- ...            YÖ-0025
    MADDE 1. ...            YÖ-0094
    GEÇİCİ MADDE 1- ...     numaralı geçici madde
    GEÇİCİ MADDE – ...      numarasız geçici madde (YÖ-0007)
    EK MADDE 1 – ...        sonradan eklenmiş madde (YÖK geçiş yönetmeliği;
                            "Ek Madde-1 ile yatay geçiş" bu)
    MADDE 12a: ...          harfli alt madde (YÖ-0018); "MADDE 5/A –" de olur
    Madde 11 Engelsiz ...   ayraçsız; büyük harfle başlık gelmeli (YÖ-0001)
    Madde 9. 20 (yirmi) ... noktadan sonra rakam (YÖ-0084)

Başlık satır başında aranır; metin içindeki "5 inci maddesi" gibi atıflar
küçük harfle ve numaradan sonra geldiği için eşleşmez.
"""

import re
from dataclasses import dataclass

_ON = r"(?P<on>(?:GEÇİCİ|Geçici|EK|Ek)\s+)?"
_MADDE = r"(?:MADDE|Madde)"
# Noktalı biçimde ("Madde 3. (1)", "MADDE 1. Bu esasların", "Madde 9. 20 iş
# günü" YÖ-0084) noktadan sonra "(", büyük harf ya da rakam gelir. Satır başına
# düşmüş atıfta küçük harf gelir: "Madde 4a. kapsamında…" (YÖ-0018); o başlık
# değildir. Ayraçsız biçimde ("Madde 11 Engelsiz GTÜ Birimi…" YÖ-0001) büyük harf şart.
_BUYUK = "A-ZÇĞİÖŞÜ"
_AYRAC = rf"(?:\s*[-–—:]|\s*\.(?=\s*[({_BUYUK}0-9])|\s+(?=[{_BUYUK}]))"

NUMARALI = re.compile(
    rf"^[ \t]*{_ON}{_MADDE}(?:\s+|\s*[-–]\s*)(?P<no>\d+)(?:/?(?P<harf>[a-zA-ZçğıöşüÇĞİÖŞÜ]))?{_AYRAC}",
    re.MULTILINE,
)
NUMARASIZ = re.compile(
    rf"^[ \t]*(?P<on>(?:GEÇİCİ|Geçici|EK|Ek)\s+){_MADDE}\s*[-–—:]", re.MULTILINE
)


@dataclass(frozen=True)
class Baslik:
    no: int | None  # numarasız geçici/ek maddede None
    tur: str  # madde | gecici | ek
    konum: int  # metindeki karakter konumu
    harf: str = ""  # "12a" → "a"; alt madde

    @property
    def etiket(self) -> str:
        return f"{self.no}{self.harf.lower()}" if self.no is not None else ""


def _tur(on: str | None) -> str:
    if not on:
        return "madde"
    return "ek" if on.strip().lower() == "ek" else "gecici"


def madde_basliklari(metin: str) -> list[Baslik]:
    bulunan = [Baslik(int(m["no"]), _tur(m["on"]), m.start(), m["harf"] or "")
               for m in NUMARALI.finditer(metin)]
    bulunan += [Baslik(None, _tur(m["on"]), m.start()) for m in NUMARASIZ.finditer(metin)]
    return sorted(bulunan, key=lambda b: b.konum)

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

Başlık satır başında aranır; metin içindeki "5 inci maddesi" gibi atıflar
küçük harfle ve numaradan sonra geldiği için eşleşmez.
"""

import re
from dataclasses import dataclass

_ON = r"(?P<on>(?:GEÇİCİ|Geçici|EK|Ek)\s+)?"
_MADDE = r"(?:MADDE|Madde)"
_AYRAC = r"\s*[-–—:.]"

NUMARALI = re.compile(
    rf"^[ \t]*{_ON}{_MADDE}(?:\s+|\s*[-–]\s*)(?P<no>\d+){_AYRAC}", re.MULTILINE
)
NUMARASIZ = re.compile(
    rf"^[ \t]*(?P<on>(?:GEÇİCİ|Geçici|EK|Ek)\s+){_MADDE}\s*[-–—:]", re.MULTILINE
)


@dataclass(frozen=True)
class Baslik:
    no: int | None  # numarasız geçici/ek maddede None
    tur: str  # madde | gecici | ek
    konum: int  # metindeki karakter konumu


def _tur(on: str | None) -> str:
    if not on:
        return "madde"
    return "ek" if on.strip().lower() == "ek" else "gecici"


def madde_basliklari(metin: str) -> list[Baslik]:
    bulunan = [Baslik(int(m["no"]), _tur(m["on"]), m.start()) for m in NUMARALI.finditer(metin)]
    bulunan += [Baslik(None, _tur(m["on"]), m.start()) for m in NUMARASIZ.finditer(metin)]
    return sorted(bulunan, key=lambda b: b.konum)

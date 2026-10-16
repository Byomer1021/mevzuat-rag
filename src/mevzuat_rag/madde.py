"""Mevzuat metninde madde başlıklarını bulur.

GTÜ belgelerinde görülen biçimler (olcumler §2):

    MADDE 8- (1) ...        yönetmelikler, çoğu yönerge
    MADDE-7 – ...           YÖ-0019'da tek bir madde
    Madde 3. (1) ...        YÖ-0002
    Madde 4- ...            YÖ-0025
    GEÇİCİ MADDE 1- ...     numaralı geçici madde
    GEÇİCİ MADDE – ...      numarasız geçici madde (YÖ-0007)

Başlık satır başında aranır; metin içindeki "5 inci maddesi" gibi atıflar
küçük harfle ve numaradan sonra geldiği için eşleşmez.
"""

import re
from dataclasses import dataclass

_GECICI = r"(?:GEÇİCİ|Geçici)\s+"
_MADDE = r"(?:MADDE|Madde)"
_AYRAC = r"\s*[-–—:.]"

NUMARALI = re.compile(
    rf"^[ \t]*(?P<gecici>{_GECICI})?{_MADDE}(?:\s+|\s*[-–]\s*)(?P<no>\d+){_AYRAC}", re.MULTILINE
)
NUMARASIZ_GECICI = re.compile(rf"^[ \t]*{_GECICI}{_MADDE}\s*[-–—:]", re.MULTILINE)


@dataclass(frozen=True)
class Baslik:
    no: int | None  # numarasız geçici maddede None
    gecici: bool
    konum: int  # metindeki karakter konumu


def madde_basliklari(metin: str) -> list[Baslik]:
    bulunan = [Baslik(int(m["no"]), bool(m["gecici"]), m.start()) for m in NUMARALI.finditer(metin)]
    bulunan += [Baslik(None, True, m.start()) for m in NUMARASIZ_GECICI.finditer(metin)]
    return sorted(bulunan, key=lambda b: b.konum)

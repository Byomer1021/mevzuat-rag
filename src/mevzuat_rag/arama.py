"""BM25 araması: Türkçe küçük harf, isteğe bağlı kök bulma, belge başlığı öneki.

Dizine giren metin, parçanın kendi metni ve (varsayılan olarak) önünde
belgenin adı. Belge adı iki koşulda da sabit tutulur: aynı adlı maddeleri
taşıyan bölüm belgeleri (15 ayrı staj esası gibi) ancak adla ayrılır, ve
Türk kanunları üzerindeki karşılaştırmada en büyük etki bu önekten geldi
(kararlar K-022).

Kök bulucu Snowball'un Türkçesi. Hatalı olduğu bilinen yerler var: "devam"
→ "deva", "kanun" → "kan" (olcumler §10). Bu yüzden ham tokenlar varsayılan.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

_KELIME = re.compile(r"\w+")
# Python'un lower()'ı Türkçe değil: "I" → "i" (olmalı "ı"), "İ" → "i" + birleşen nokta.
_TR_BUYUK = str.maketrans({"I": "ı", "İ": "i"})


def kucult(metin: str) -> str:
    return metin.translate(_TR_BUYUK).lower()


def tokenlar(metin: str) -> list[str]:
    return _KELIME.findall(kucult(metin))


class _Kokleyici:
    def __init__(self):
        import snowballstemmer

        self._st = snowballstemmer.stemmer("turkish")
        self._onbellek: dict[str, str] = {}

    def __call__(self, ts: list[str]) -> list[str]:
        out = []
        for t in ts:
            k = self._onbellek.get(t)
            if k is None:
                k = self._onbellek[t] = self._st.stemWord(t)
            out.append(k)
        return out


@dataclass(frozen=True)
class Sonuc:
    id: str
    skor: float
    sira: int  # 1'den başlar


class BM25Dizin:
    def __init__(self, parcalar: Iterable[dict], belge_adlari: dict[str, str] | None = None,
                 kok: bool = False, k1: float = 1.5, b: float = 0.75):
        self.parcalar = list(parcalar)
        self.ids = [p["id"] for p in self.parcalar]
        self._kok = _Kokleyici() if kok else None
        adlar = belge_adlari or {}
        belgeler = [self._isle(f"{adlar.get(p['belge_id'], '')}\n{p['metin']}")
                    for p in self.parcalar]
        self._bm25 = BM25Okapi(belgeler, k1=k1, b=b)

    def _isle(self, metin: str) -> list[str]:
        ts = tokenlar(metin)
        return self._kok(ts) if self._kok else ts

    def ara(self, sorgu: str, k: int = 10) -> list[Sonuc]:
        skorlar = self._bm25.get_scores(self._isle(sorgu))
        # eşit skorlarda sıra kimliğe göre sabit kalsın diye kararlı sıralama
        sira = np.argsort(-skorlar, kind="stable")[:k]
        return [Sonuc(self.ids[i], float(skorlar[i]), n) for n, i in enumerate(sira, 1)]

"""Arama: BM25 (Türkçe küçük harf, isteğe bağlı kök bulma) ve yoğun arama (e5).
İkisinde de dizine giren metin belge adı öneki ve parçanın kendisi.

Dizine giren metin, parçanın kendi metni ve (varsayılan olarak) önünde
belgenin adı. Belge adı iki koşulda da sabit tutulur: aynı adlı maddeleri
taşıyan bölüm belgeleri (15 ayrı staj esası gibi) ancak adla ayrılır, ve
Türk kanunları üzerindeki karşılaştırmada en büyük etki bu önekten geldi
(kararlar K-022).

Kök bulucu Snowball'un Türkçesi. Hatalı olduğu bilinen yerler var: "devam"
→ "deva", "kanun" → "kan" (olcumler §10). Bu yüzden ham tokenlar varsayılan.
"""

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

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


E5 = "intfloat/multilingual-e5-base"


def gomme_metni(parca: dict, belge_adlari: dict[str, str] | None) -> str:
    """Dizine giren metin, BM25 ile aynı: belge adı (varsa) ve parça."""
    ad = (belge_adlari or {}).get(parca["belge_id"], "")
    return f"{ad}\n{parca['metin']}" if ad else parca["metin"]


class YogunDizin:
    """e5 ailesi: parçalar "passage: ", sorgu "query: " önekiyle, normalize
    vektörlerde kosinüs. Vektörler metin özetine göre `onbellek`e yazılır;
    aynı metinler için model bir daha çalışmaz."""

    def __init__(self, parcalar: Iterable[dict], belge_adlari: dict[str, str] | None = None,
                 model: str = E5, onbellek: Path | None = None, toplu: int = 32,
                 cihaz: str = "cpu"):
        # Varsayılan CPU: geliştirme makinesinin GTX 1080'i yük altında düşüyor ve
        # ekranı götürüyor (K-002, 2026-10-17). GPU yalnız açıkça istenirse.
        from sentence_transformers import SentenceTransformer

        self.parcalar = list(parcalar)
        self.ids = [p["id"] for p in self.parcalar]
        self.model = SentenceTransformer(model, device=cihaz)
        metinler = ["passage: " + gomme_metni(p, belge_adlari) for p in self.parcalar]
        ozet = hashlib.sha256("\x00".join([model, *metinler]).encode()).hexdigest()[:16]
        yol = onbellek / f"{model.replace('/', '__')}_{ozet}.npy" if onbellek else None
        if yol and yol.exists():
            self.vektorler = np.load(yol)
        else:
            self.vektorler = self.model.encode(metinler, batch_size=toplu, normalize_embeddings=True,
                                               convert_to_numpy=True, show_progress_bar=False)
            if yol:
                yol.parent.mkdir(parents=True, exist_ok=True)
                np.save(yol, self.vektorler)

    def ara(self, sorgu: str, k: int = 10) -> list[Sonuc]:
        q = self.model.encode(["query: " + sorgu], normalize_embeddings=True, convert_to_numpy=True)[0]
        skorlar = self.vektorler @ q
        sira = np.argsort(-skorlar, kind="stable")[:k]
        return [Sonuc(self.ids[i], float(skorlar[i]), n) for n, i in enumerate(sira, 1)]

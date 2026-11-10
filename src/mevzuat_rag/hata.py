"""Taban sistemin hatalarını kategorilere ayırır (ara rapor; proje kartı alanı 9).

Bir soru, kanıtı ilk 5 parçada tam kapsanmadıysa hatadır. Kategori, ilk 5
parçaya ve kanıtın parçalara bölünüşüne bakan kurallarla bu sırayla atanır;
ilk tutan kural kazanır:

1. cok_kismi: çok dayanaklı soruda kanıtların bir kısmı geldi.
2. bolunmus: kanıt iki ya da daha çok parçaya bölünmüş, bir kısmı geldi.
3. dogru_belge: doğru belgeden parça geldi, kanıtı taşıyan gelmedi.
4. benzer_belge: doğru belge yok, adı ona benzeyen başka belge var (başka
   bölümün staj esasları, 2017 öncesi yönetmelik gibi).
5. madde_disi: ilk 5'in en az 3'ü madde yapısı olmayan belgelerden (rehber,
   SSS PDF'i, öğretim planı); bu parçalar iki koşulda aynı.
6. baska_belge: geri kalan, başka konudaki yönetmelik ve yönergeler.
"""

from mevzuat_rag.arama import tokenlar
from mevzuat_rag.degerlendirme import Kanit, Kume

KATEGORILER = {
    "cok_kismi": "Multi-article question: only part of the evidence came back",
    "bolunmus": "Evidence split across windows: one part came back",
    "dogru_belge": "Right document, wrong window",
    "benzer_belge": "Look-alike document: another unit's rules or an older version",
    "madde_disi": "Guides, FAQ PDFs and curricula fill the top 5",
    "baska_belge": "Rules on another topic",
}
_DURAK = {"ve", "ile", "için", "gebze", "teknik", "üniversitesi", "gtü", "bir"}
# Aynı konudaki belgeler bölüm bölüm tekrar ediyor; adlarında bu kelimelerden biri ortak
_KONU = {"staj", "yaz", "yatay", "erasmus", "burs", "hazırlık", "muafiyet", "intibak", "kütüphane",
         "disiplin", "çift", "yandal", "değişim", "yurt", "otopark", "engelli"}


def baslik_kelimeleri(ad: str) -> set[str]:
    return set(tokenlar(ad)) - _DURAK


def benzer_mi(a: str, b: str) -> bool:
    ka, kb = baslik_kelimeleri(a), baslik_kelimeleri(b)
    if not ka or not kb:
        return False
    return len(ka & kb) / len(ka | kb) >= 0.4 or bool(ka & kb & _KONU)


def kanit_parcalari(kume: Kume, kanit: Kanit) -> list[str]:
    """Kanıtın karakter aralığına değen parçalar (konumu olan kanıtlarda)."""
    if kanit.bas < 0:
        return []
    return [i for i, (a, b) in kume.aralik.items()
            if kume.parca[i]["belge_id"] == kanit.belge_id and a < kanit.son and kanit.bas < b]


def kategori(ids: list[str], ks: list[Kanit], kume: Kume, adlar: dict[str, str],
             madde_belgeleri: set[str], k: int = 5) -> str:
    ilk = ids[:k]
    bulunan = [kume.kapsar_mi(x, ilk) for x in ks]
    if len(ks) > 1 and any(bulunan):
        return "cok_kismi"
    for x, b in zip(ks, bulunan, strict=True):
        ps = [] if b else kanit_parcalari(kume, x)
        if len(ps) >= 2 and any(p in ilk for p in ps):
            return "bolunmus"
    altin = {x.belge_id for x in ks}
    belgeler = [kume.parca[i]["belge_id"] for i in ilk]
    if altin & set(belgeler):
        return "dogru_belge"
    if any(benzer_mi(adlar.get(b, ""), adlar.get(g, "")) for b in belgeler for g in altin):
        return "benzer_belge"
    if sum(b not in madde_belgeleri for b in belgeler) >= 3:
        return "madde_disi"
    return "baska_belge"

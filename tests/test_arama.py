from mevzuat_rag.arama import BM25Dizin, kucult, tokenlar

PARCALAR = [
    {"id": "a/m1", "belge_id": "a", "metin": "Devam\nMADDE 1- Teorik derslerde en az %70 devam zorunludur."},
    {"id": "a/m2", "belge_id": "a", "metin": "Sınavlar\nMADDE 2- Ara sınav ve yarıyıl sonu sınavı yapılır."},
    {"id": "b/m1", "belge_id": "b", "metin": "Süre\nMADDE 1- Staj süresi yirmi iş günüdür."},
    {"id": "c/m1", "belge_id": "c", "metin": "Süre\nMADDE 1- Staj süresi otuz iş günüdür."},
]


def test_turkce_kucuk_harf():
    assert kucult("IĞDIR İSTANBUL") == "ığdır istanbul"
    assert tokenlar("MADDE 23– (1) Teorik derslerde %70") == ["madde", "23", "1", "teorik",
                                                             "derslerde", "70"]


def test_bm25_ilgili_maddeyi_one_alir():
    d = BM25Dizin(PARCALAR)
    assert d.ara("ara sınav ne zaman yapılır", k=1)[0].id == "a/m2"
    sonuc = d.ara("devam zorunluluğu", k=4)
    assert sonuc[0].id == "a/m1" and [s.sira for s in sonuc] == [1, 2, 3, 4]


def test_belge_adi_ayni_maddeleri_ayirir():
    # İki bölümün staj esası aynı cümleyle başlıyor; ancak belge adıyla ayrılır.
    adlar = {"b": "Bilgisayar Mühendisliği Staj Esasları", "c": "Kimya Bölümü Staj Esasları"}
    assert BM25Dizin(PARCALAR, adlar).ara("kimya staj süresi", k=1)[0].id == "c/m1"
    assert BM25Dizin(PARCALAR, adlar).ara("bilgisayar staj süresi", k=1)[0].id == "b/m1"


def test_kok_bulma_ekleri_eslestirir():
    # üç belge: ikide BM25Okapi'nin idf'i tek belgede geçen terime 0 veriyor
    ps = [{"id": "x/m1", "belge_id": "x", "metin": "Sınavlara itiraz edilebilir."},
          {"id": "x/m2", "belge_id": "x", "metin": "Kayıt yenileme yapılır."},
          {"id": "x/m3", "belge_id": "x", "metin": "Danışman onayı gerekir."}]
    assert BM25Dizin(ps).ara("sınav", k=2)[0].skor == 0  # "sınavlara" ≠ "sınav"
    kok = BM25Dizin(ps, kok=True).ara("sınav", k=2)
    assert kok[0].id == "x/m1" and kok[0].skor > 0

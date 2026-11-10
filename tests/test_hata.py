from mevzuat_rag.degerlendirme import Kume, kanitlar
from mevzuat_rag.hata import benzer_mi, kanit_parcalari, kategori

BELGE = "Devam MADDE 1 aaa bbb. MADDE 2 ccc ddd eee."
MADDE = [
    {"id": "d/m1", "belge_id": "d", "tur": "madde", "metin": BELGE[0:22], "bas": 0, "son": 22},
    {"id": "d/m2", "belge_id": "d", "tur": "madde", "metin": BELGE[23:43], "bas": 23, "son": 43},
]
SABIT = [
    {"id": "d/s1", "belge_id": "d", "tur": "sabit", "metin": BELGE[0:13], "bas": 0, "son": 13},
    {"id": "d/s2", "belge_id": "d", "tur": "sabit", "metin": BELGE[14:30], "bas": 14, "son": 30},
    {"id": "d/s3", "belge_id": "d", "tur": "sabit", "metin": BELGE[31:43], "bas": 31, "son": 43},
    {"id": "e/s1", "belge_id": "e", "tur": "sabit", "metin": "Başka staj esası.", "bas": 0, "son": 17},
    {"id": "r/p1", "belge_id": "r", "tur": "paragraf", "metin": "Rehber.", "bas": 0, "son": 7},
    {"id": "r/p2", "belge_id": "r", "tur": "paragraf", "metin": "Rehber 2.", "bas": 8, "son": 17},
    {"id": "r/p3", "belge_id": "r", "tur": "paragraf", "metin": "Rehber 3.", "bas": 18, "son": 27},
    {"id": "x/s1", "belge_id": "x", "tur": "sabit", "metin": "Otopark.", "bas": 0, "son": 8},
]
KUME = Kume(SABIT)
DAYANAK = {p["id"]: p for p in MADDE}
ADLAR = {"d": "Makine Mühendisliği Staj Esasları", "e": "Harita Mühendisliği Staj Esasları",
         "r": "Öğrenci El Kitabı", "x": "Otopark Yönergesi"}
MADDELI = {"d", "e", "x"}


def ks(dayanak, kanit):
    return kanitlar({"id": "q", "dayanak": dayanak, "kanit": kanit}, DAYANAK)


def test_bolunen_kanitin_parcalari():
    assert sorted(kanit_parcalari(KUME, ks(["d/m2"], ["MADDE 2 ccc ddd"])[0])) == ["d/s2", "d/s3"]


def test_kategoriler_sirayla():
    iki = ks(["d/m1", "d/m2"], ["aaa bbb.", "ccc ddd eee."])
    assert kategori(["d/s2", "x/s1"], iki, KUME, ADLAR, MADDELI) == "cok_kismi"
    bolunmus = ks(["d/m2"], ["MADDE 2 ccc ddd"])
    assert kategori(["d/s3", "x/s1"], bolunmus, KUME, ADLAR, MADDELI) == "bolunmus"
    tek = ks(["d/m2"], ["ccc ddd eee."])
    assert kategori(["d/s1", "x/s1"], tek, KUME, ADLAR, MADDELI) == "dogru_belge"
    assert kategori(["e/s1", "x/s1"], tek, KUME, ADLAR, MADDELI) == "benzer_belge"
    assert kategori(["r/p1", "r/p2", "r/p3", "x/s1"], tek, KUME, ADLAR, MADDELI) == "madde_disi"
    assert kategori(["x/s1", "r/p1"], tek, KUME, ADLAR, MADDELI) == "baska_belge"


def test_benzer_belge_adlari():
    assert benzer_mi("Makine Mühendisliği Staj Esasları", "Havacılık Fakültesi Staj Yönergesi")
    assert benzer_mi("Ön Lisans ve Lisans Eğitim-Öğretim Yönetmeliği",
                     "Lisans Eğitim ve Öğretim Yönetmeliği (2017 Öncesi Girişli Öğrenciler İçin)")
    assert not benzer_mi("Otopark Yönergesi", "Kütüphane Yönergesi")

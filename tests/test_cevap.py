from mevzuat_rag.cevap import olc
from mevzuat_rag.degerlendirme import Kume

BELGE = "Devam MADDE 1 aaa bbb. MADDE 2 ccc ddd eee."
PARCALAR = [
    {"id": "d/m1", "belge_id": "d", "tur": "madde", "metin": BELGE[0:22], "bas": 0, "son": 22},
    {"id": "d/m2", "belge_id": "d", "tur": "madde", "metin": BELGE[23:43], "bas": 23, "son": 43},
]
SORULAR = [
    {"id": "q1", "soru": "s1", "tur": "tek", "referans_cevap": "ccc", "dayanak": ["d/m2"],
     "kanit": ["ccc ddd"], "bolum": "dev"},
    {"id": "q2", "soru": "s2", "tur": "tek", "referans_cevap": "aaa", "dayanak": ["d/m1"],
     "kanit": ["aaa bbb."], "bolum": "dev"},
    {"id": "q3", "soru": "s3", "tur": "cevapsiz", "referans_cevap": "", "dayanak": [], "kanit": [],
     "bolum": "dev"},
]
PAKET = [{"id": "q1", "kaynaklar": ["d/m1", "d/m2"]}, {"id": "q2", "kaynaklar": ["d/m1", "d/m2"]},
         {"id": "q3", "kaynaklar": ["d/m1"]}]


def test_olc():
    cevaplar = [
        {"id": "q1", "cevap": "ccc ddd [2]."},              # doğru kaynağı anıyor
        {"id": "q2", "cevap": "BİLMİYORUM: Bu bilgi yok."},  # kanıt getirildiği hâlde
        {"id": "q3", "cevap": "Uydurma bir cevap [1]."},     # cevapsızda konuştu
    ]
    ozet, satirlar = olc(SORULAR, PAKET, cevaplar, Kume(PARCALAR), {p["id"]: p for p in PARCALAR})
    assert ozet["cevapsizda_bilmiyorum"] == 0.0 and ozet["cevaplida_bilmiyorum"] == 0.5
    assert ozet["kanit_varken_bilmiyorum"] == 1 and ozet["atif_kaniti_kapsar"] == 1.0
    assert satirlar[0]["atiflar"] == ["d/m2"] and satirlar[0]["atif_kaniti_kapsar"] is True
    assert satirlar[2]["kanit_getirildi"] is None


def test_olc_yanlis_atif_ve_eksik_cevap():
    ozet, satirlar = olc(SORULAR, PAKET, [{"id": "q1", "cevap": "ccc [1]. ayrıca [7]"}],
                         Kume(PARCALAR), {p["id"]: p for p in PARCALAR})
    assert ozet["eksik_cevap"] == 2 and ozet["atif_kaniti_kapsar"] == 0.0
    assert satirlar[0]["gecersiz_atif"] == [7] and ozet["gecersiz_atifli_cevap"] == 1

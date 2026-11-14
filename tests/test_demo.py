"""Demo: kaynak bağlantıları, arama + üretici akışı ve arayüz (BM25 ile, tarayıcısız)."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from mevzuat_rag.arama import BM25Dizin
from mevzuat_rag.demo import K_BELGE, K_WEB, BilgiTabani, adres, cevapla, sec, uretici_yukle

KOK = Path(__file__).resolve().parents[1]
PARCALAR = KOK / "data" / "processed" / "parcalar_madde.jsonl"


def parca(id_, tur="madde", metin="", **ek):
    p = {"id": id_, "belge_id": id_.split("/")[0], "tur": tur, "metin": metin, "madde": None,
         "baslik": "", "bolum": "", "sayfa_bas": 1, "sayfa_son": 1, "url": "", "tarih": ""}
    return p | ek


def test_pdf_adresi_sayfaya_gider_ve_kodlanir():
    p = parca("y/m23", url="https://www.gtu.edu.tr/Yönetmelikler/YN-0001 Lisans R7.pdf",
              sayfa_bas=7, sayfa_son=8)
    assert adres(p, {}) == ("https://www.gtu.edu.tr/Y%C3%B6netmelikler/YN-0001%20Lisans%20R7.pdf"
                            "#page=7")


def test_web_adresinde_sayfa_yok():
    p = parca("web-sss/k1-1", tur="web",
              url="https://www.gtu.edu.tr/kategori/1957/0/display.aspx?languageId=1")
    assert adres(p, {}) == "https://www.gtu.edu.tr/kategori/1957/0/display.aspx?languageId=1"


def test_parcada_adres_yoksa_belgenin_adresi():
    p = parca("akademik-takvim/r1", tur="takvim")
    kaynaklar = {"akademik-takvim": {"url": "https://www.gtu.edu.tr/takvim"}}
    assert adres(p, kaynaklar) == "https://www.gtu.edu.tr/takvim"
    assert adres(p, {}) is None


@pytest.fixture
def bt():
    ps = [parca("y/m23", metin="Teorik derslerde en az %70 devam zorunluluğu aranır.",
                madde="23", baslik="Devam durumu"),
          parca("y/m24", metin="Kayıt dondurma en fazla iki yarıyıl olabilir.", madde="24"),
          parca("staj/m3", metin="Staj yirmi iş günüdür.", madde="3")]
    return BilgiTabani(ps, {p["id"]: p for p in ps}, {}, {"y": "Lisans Yönetmeliği"}, {})


def test_kaynaklar_iki_havuzdan_once_belgeler():
    ps = {i: parca(i, tur=t) for i, t in [("sss/1", "web"), ("sss/2", "web"), ("y/m1", "madde"),
                                           ("sss/3", "web"), ("y/p4", "paragraf")]}
    siralama = list(ps)
    assert sec(siralama, ps, 3, 2) == ["y/m1", "y/p4", "sss/1", "sss/2"]
    assert sec(siralama, ps, 1, 0) == ["y/m1"]


def test_uretici_yoksa_yalniz_kaynak_ve_istem(bt):
    s = cevapla("devam zorunluluğu yüzde kaç", BM25Dizin(bt.parcalar, bt.adlar), bt,
                k_belge=2, k_web=0)
    assert [p["id"] for p in s["kaynaklar"]][:1] == ["y/m23"]
    assert len(s["kaynaklar"]) == 2
    assert s["cevap"] is None and s["ayrisim"] is None
    assert "[1] Lisans Yönetmeliği, Madde 23 (Devam durumu), s. 1" in s["mesajlar"][1]["content"]


def test_uretici_istemi_alir_cevabin_atiflari_ayrisir(bt):
    gelen = []

    def sahte(mesajlar):
        gelen.append(mesajlar)
        return "Teorik derslerde en az %70 devam gerekir [1]. Ayrıca [9]."

    s = cevapla("devam zorunluluğu yüzde kaç", BM25Dizin(bt.parcalar, bt.adlar), bt,
                k_belge=2, k_web=0, uretici=sahte)
    assert gelen == [s["mesajlar"]]
    assert s["ayrisim"]["atiflar"] == ["y/m23"]
    assert s["ayrisim"]["gecersiz_atif"] == [9]
    assert not s["ayrisim"]["bilmiyorum"]


def test_uretici_yukle():
    assert uretici_yukle(None) is None and uretici_yukle("") is None
    assert uretici_yukle("json:dumps") is json.dumps
    with pytest.raises(ValueError):
        uretici_yukle("json")


@pytest.mark.skipif(not PARCALAR.exists(), reason="önce scripts/onisle.py çalışmalı")
def test_arayuz_ornek_soruyla_kaynaklari_gosterir(monkeypatch):
    monkeypatch.setenv("DEMO_ARAMA", "bm25")
    monkeypatch.delenv("DEMO_URETICI", raising=False)
    at = AppTest.from_file(str(KOK / "app" / "demo.py"), default_timeout=120).run()
    assert not at.exception
    next(b for b in at.button if b.label.startswith("Derslere devam")).click().run()
    assert not at.exception
    assert any("bağlı değil" in i.value for i in at.info)
    kaynaklar = [e for e in at.expander if e.label.startswith("[")]
    assert len(kaynaklar) == K_BELGE + K_WEB  # varsayılan: 5 belge + 2 web
    assert [h.value for h in at.main.subheader] == ["Yönetmelik ve yönergeler",
                                                    "Sık sorulan sorular ve birim sayfaları"]
    assert at.text_input(key="soru").value == "Derslere devam zorunluluğu yüzde kaç?"

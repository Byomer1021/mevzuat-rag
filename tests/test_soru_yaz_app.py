"""Soru yazma aracını tarayıcısız çalıştırır (Streamlit AppTest)."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

KOK = Path(__file__).resolve().parents[1]
UYGULAMA = KOK / "app" / "soru_yaz.py"
PARCALAR = KOK / "data" / "processed" / "parcalar_madde.jsonl"

pytestmark = pytest.mark.skipif(not PARCALAR.exists(), reason="önce scripts/onisle.py çalışmalı")


@pytest.fixture
def uygulama(tmp_path, monkeypatch):
    dosya = tmp_path / "sorular.jsonl"
    monkeypatch.setenv("SORU_DOSYASI", str(dosya))
    at = AppTest.from_file(str(UYGULAMA), default_timeout=60).run()
    assert not at.exception
    return at, dosya


def kaydet(at):
    next(b for b in at.button if b.label == "Kaydet").click().run()


def test_arama_parcayi_bulur(uygulama):
    at, _ = uygulama
    arama = next(t for t in at.text_input if t.label.startswith("Ara"))
    arama.input("devam durumu").run()
    assert any("lisans-yonetmelik/m23" in str(o) for o in at.selectbox[1].options)


def test_hatali_soru_kaydedilmez_ve_yazilan_korunur(uygulama):
    at, dosya = uygulama
    at.text_area(key="f_soru").input("Devamsızlık sınırı nedir?")
    kaydet(at)  # tek maddeli ama dayanak yok, cevap yok
    assert any("tam bir parça" in e.value for e in at.error)
    assert not dosya.exists()
    assert at.text_area(key="f_soru").value == "Devamsızlık sınırı nedir?"


def test_gecerli_soru_kaydedilir_ve_form_bosalir(uygulama):
    at, dosya = uygulama
    at.text_area(key="f_soru").input("Derslere devam zorunlu mu?")
    at.text_area(key="f_cevap").input("Evet, ders bilgi formundaki oranda.")
    at.multiselect(key="f_dayanak").set_value(["lisans-yonetmelik/m23"])
    kaydet(at)
    assert not at.exception and not at.error
    satirlar = [json.loads(s) for s in dosya.read_text(encoding="utf-8").splitlines()]
    assert satirlar == [{
        "id": "q001", "soru": "Derslere devam zorunlu mu?", "tur": "tek",
        "referans_cevap": "Evet, ders bilgi formundaki oranda.",
        "dayanak": ["lisans-yonetmelik/m23"], "etiketler": [], "yazan": "omer", "bolum": "dev",
    }]
    assert at.text_area(key="f_soru").value == ""
    assert any("q001 kaydedildi" in s.value for s in at.success)

import json

import pytest

from mevzuat_rag import hazir_cevap


def yaz(yol, satirlar):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in satirlar), encoding="utf-8")


M1 = [{"role": "system", "content": "kurallar"}, {"role": "user", "content": "Kaynaklar: [1] ... Soru: devam?"}]
M2 = [{"role": "system", "content": "kurallar"}, {"role": "user", "content": "Kaynaklar: [1] ... Soru: büt?"}]


@pytest.fixture
def kok(tmp_path):
    yaz(tmp_path / "results/istem/dev-e5-demo.jsonl", [{"id": "q1", "mesajlar": M1}, {"id": "q2", "mesajlar": M2}])
    yaz(tmp_path / "results/cevap/ham/dev-e5-demo__Model.jsonl",
        [{"_ust": {"model": "Model"}}, {"id": "q1", "cevap": "En az %70 [1]."}])
    return tmp_path


def test_paket_yolu_adlandirmadan(kok):
    assert hazir_cevap.paket_yolu(kok / "x/dev-e5-demo__Qwen3-4B.jsonl", kok) == kok / "results/istem/dev-e5-demo.jsonl"


def test_yukle_istemle_eslesir(kok):
    tablo = hazir_cevap.yukle([kok / "results/cevap/ham/dev-e5-demo__Model.jsonl"], kok)
    assert tablo == {hazir_cevap.ozet(M1): "En az %70 [1]."}


def test_ozet_anahtar_sirasindan_bagimsiz():
    assert hazir_cevap.ozet([{"role": "user", "content": "a"}]) == hazir_cevap.ozet([{"content": "a", "role": "user"}])


def test_uret_bulunmayan_istemde_sabit_not(kok, monkeypatch):
    monkeypatch.setattr(hazir_cevap, "KOK", kok)
    hazir_cevap._tablo.cache_clear()
    monkeypatch.setenv("DEMO_CEVAPLAR", "results/cevap/ham/dev-e5-demo__Model.jsonl")
    assert hazir_cevap.uret(M1) == "En az %70 [1]."
    assert hazir_cevap.uret(M2) == hazir_cevap.YOK
    hazir_cevap._tablo.cache_clear()


def test_uret_tanimsiz_ortam(monkeypatch):
    monkeypatch.delenv("DEMO_CEVAPLAR", raising=False)
    with pytest.raises(RuntimeError):
        hazir_cevap.uret(M1)

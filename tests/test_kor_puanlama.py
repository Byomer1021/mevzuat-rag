import importlib.util
import json
from pathlib import Path

from openpyxl import load_workbook

KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("kor_puanlama", KOK / "scripts" / "kor_puanlama.py")
kp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kp)


def ozet_dosyasi(yol: Path, model: str, ad: str, sorular: list[dict]) -> Path:
    yol.write_text(json.dumps({"paket": {"ad": ad}, "uretim": {"model": model}, "sorular": sorular},
                              ensure_ascii=False), encoding="utf-8")
    return yol


def test_olustur_ve_hesapla(tmp_path):
    s = [{"id": "q1", "tur": "tek", "soru": "Devam?", "referans_cevap": "%70", "cevap": "En az %70 [1]."},
         {"id": "q2", "tur": "cevapsiz", "soru": "Ring?", "referans_cevap": "", "cevap": "BİLMİYORUM: yok."}]
    a = ozet_dosyasi(tmp_path / "a.json", "M1", "paket-a", s)
    b = ozet_dosyasi(tmp_path / "b.json", "M2", "paket-b", s)
    tablo, anahtar = tmp_path / "kor.xlsx", tmp_path / "anahtar.json"
    kp.olustur([a, b], tablo, anahtar)

    wb = load_workbook(tablo)
    assert wb.sheetnames == ["nasıl", "puanla"]
    ws = wb["puanla"]
    metin = " ".join(str(h.value) for satir in ws.iter_rows() for h in satir)
    assert "M1" not in metin and "paket-a" not in metin
    assert kp.CEVAPSIZ in metin
    for satir in ws.iter_rows(min_row=2):
        satir[4].value = "doğru" if satir[0].value % 2 else "Yanlış"
    wb.save(tablo)

    sonuc = kp.hesapla(tablo, anahtar)
    assert not sonuc["bos"] and not sonuc["gecersiz"]
    toplam = sum(sum(c.values()) for v in sonuc["sonuc"].values() for c in v.values())
    assert toplam == 4 and set(sonuc["sonuc"]) == {"M1 | paket-a", "M2 | paket-b"}


def test_hesapla_gecersiz_ve_bos(tmp_path):
    s = [{"id": "q1", "tur": "tek", "soru": "S", "referans_cevap": "R", "cevap": "C"}]
    a = ozet_dosyasi(tmp_path / "a.json", "M1", "p", s)
    tablo, anahtar = tmp_path / "kor.xlsx", tmp_path / "anahtar.json"
    kp.olustur([a, a], tablo, anahtar)
    wb = load_workbook(tablo)
    wb["puanla"]["E2"].value = "belki"
    wb.save(tablo)
    sonuc = kp.hesapla(tablo, anahtar)
    assert sonuc["gecersiz"] == [(1, "belki")] and sonuc["bos"] == [2]

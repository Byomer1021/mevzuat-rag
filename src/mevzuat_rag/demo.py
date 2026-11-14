"""Demo: soru → arama → (bağlıysa) dil modeli → kaynaklı cevap.

Arama, istem ve kaynak gösterimi burada; dil modeli takılıp çıkarılan bir
parça (`Uretici`: sohbet mesajları → cevap metni). Bağlı değilse demo yalnız
bulunan kaynakları ve modele gidecek istemi gösterir. Bir üretici şöyle
bağlanır:

    DEMO_URETICI=paket.modul:fonksiyon uv run streamlit run app/demo.py

Demo bütün bilgi tabanında arar (web, takvim, form dahil). Deneyin dizini
yalnız PDF'tir (K-022); o, karşılaştırmanın dizini, sistemin değil.

Kaynaklar iki havuzdan seçilir: önce belgeler (yönetmelik, yönerge, takvim,
form), sonra web (SSS ve birim sayfaları). Tek listede genel sorularda ilk 5'in
hepsi SSS çıkıyor, çünkü SSS öğrencinin diliyle yazılmış; madde hiç gelmiyor
(K-025).
"""

import csv
import importlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from mevzuat_rag.arama import BM25Dizin, YogunDizin
from mevzuat_rag.testset import parcalari_oku
from mevzuat_rag.uretim import SAYFALI, ayristir, istem

Uretici = Callable[[list[dict]], str]
KOK = Path(__file__).resolve().parents[2]
# Modele giden kaynak sayısı (K-025). 2026-11-14'te belge 3'ten 5'e çıktı:
# dev'de kanıt 43 cevaplı sorunun 20'sinden 25'inde modele gidiyor (olcumler §18).
K_BELGE, K_WEB = 5, 2
UYARI = ("Resmî danışmanlık değildir. Cevaplar GTÜ'nün yayımlanmış yönetmelik, yönerge ve "
         "sayfalarından derlenir; karar vermeden önce kaynağı açıp okuyun, gerekirse ilgili "
         "birime danışın.")


@dataclass
class BilgiTabani:
    parcalar: list[dict]
    parca: dict[str, dict]
    kaynaklar: dict[str, dict]  # belge_id → data/kaynaklar.csv satırı
    adlar: dict[str, str]  # belge_id → başlık; dizine giren önek
    surum: dict  # bilgi tabanı ve parça sürümü (results/onisleme.json)


def bilgi_tabani(kok: Path = KOK) -> BilgiTabani:
    """Madde koşulundaki bütün parçalar: sistemin kendisi bu koşulla çalışır."""
    parcalar = parcalari_oku(kok / "data" / "processed" / "parcalar_madde.jsonl")
    with (kok / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        kaynaklar = {r["belge_id"]: r for r in csv.DictReader(f)}
    rapor = kok / "results" / "onisleme.json"
    surum = {}
    if rapor.exists():
        r = json.loads(rapor.read_text(encoding="utf-8"))
        surum = {k: r.get(k) for k in ("bilgi_tabani_surumu", "parca_surumu")}
    return BilgiTabani(parcalar, {p["id"]: p for p in parcalar}, kaynaklar,
                       {b: r["baslik"] for b, r in kaynaklar.items()}, surum)


def dizin_kur(arama: str, bt: BilgiTabani, kok: Path = KOK, cihaz: str = "cpu"):
    """Deneydeki ve istem paketindeki kurulumun aynısı; e5 vektörleri aynı önbellekten."""
    if arama == "bm25":
        return BM25Dizin(bt.parcalar, bt.adlar)
    if arama == "e5":
        return YogunDizin(bt.parcalar, bt.adlar, onbellek=kok / ".cache" / "gomme", cihaz=cihaz)
    raise ValueError(f"bilinmeyen arama: {arama}")


def adres(p: dict, kaynaklar: dict[str, dict]) -> str | None:
    """Kaynağı açan bağlantı: PDF'te parçanın başladığı sayfa, web'de sayfanın
    kendisi. Parçada adres yoksa (takvim, form) belgenin adresi."""
    url = p.get("url") or kaynaklar.get(p["belge_id"], {}).get("url") or ""
    if not url:
        return None
    # Adreslerde boşluk ve Türkçe harf var ("YÖ-0087 Bilgisayar ... R1.pdf")
    url = quote(url, safe=":/?=&%#+,;@")
    if p["tur"] in SAYFALI and p.get("sayfa_bas"):
        url += f"#page={p['sayfa_bas']}"
    return url


def web_mi(p: dict) -> bool:
    return p["tur"] == "web"


def sec(siralama: list[str], parca: dict[str, dict], k_belge: int, k_web: int) -> list[str]:
    """Bütün bilgi tabanının sıralamasından ilk k_belge belge parçası, ardından
    ilk k_web web parçası."""
    belge = [i for i in siralama if not web_mi(parca[i])][:k_belge]
    web = [i for i in siralama if web_mi(parca[i])][:k_web]
    return belge + web


def cevapla(soru: str, dizin, bt: BilgiTabani, k_belge: int = K_BELGE, k_web: int = K_WEB,
            uretici: Uretici | None = None) -> dict:
    """Arar, istemi kurar; üretici varsa cevabı alıp atıflarını ayrıştırır."""
    # Tam sıralama ucuz: iki aramada da bütün parçalar zaten puanlanıyor
    siralama = [s.id for s in dizin.ara(soru, len(bt.parcalar))]
    ids = sec(siralama, bt.parca, k_belge, k_web)
    kaynaklar = [bt.parca[i] for i in ids]
    mesajlar = istem(soru, kaynaklar, bt.adlar)
    sonuc = {"soru": soru, "kaynaklar": kaynaklar, "mesajlar": mesajlar,
             "cevap": None, "ayrisim": None}
    if uretici is not None:
        cevap = uretici(mesajlar)
        sonuc.update(cevap=cevap, ayrisim=ayristir(cevap, ids))
    return sonuc


def uretici_yukle(tanim: str | None) -> Uretici | None:
    """"paket.modul:fonksiyon" → çağrılabilir. Boşsa None: yalnız arama."""
    if not tanim:
        return None
    modul, _, ad = tanim.partition(":")
    if not modul or not ad:
        raise ValueError(f"üretici 'paket.modul:fonksiyon' biçiminde olmalı: {tanim!r}")
    return getattr(importlib.import_module(modul), ad)

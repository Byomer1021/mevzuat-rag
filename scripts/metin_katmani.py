"""Her PDF'in metin katmanını ölçer: metin çıkıyor mu, Türkçe karakterler
sağlam mı, madde başlıkları sayılabiliyor mu. İki çıkarıcıyla (PyMuPDF,
pdfplumber) ayrı ayrı. Sonuç: results/metin_katmani.csv, olcumler §2.

    uv run python scripts/metin_katmani.py
"""

import csv
import sys
import time
from collections import Counter
from pathlib import Path

import pdfplumber
import pymupdf

from mevzuat_rag.madde import madde_basliklari

KOK = Path(__file__).resolve().parents[1]
RAW = KOK / "data" / "raw"
CIKTI = KOK / "results" / "metin_katmani.csv"

TURKCE = set("çğıöşüÇĞİÖŞÜ")
# cp1254 metni latin-1 sanılınca: ı→ý, ş→þ, ğ→ð, İ→Ý, Ş→Þ, Ğ→Ð
BOZUK = set("ýþðÝÞÐ�")
AZ_METIN = 100  # bu kadar karakterden az sayfa: boş, görsel veya taranmış


def tekrar_eden_oran(sayfalar: list[str]) -> float:
    """Sayfaların en az yarısında geçen satırların (kalite formu başlığı,
    sayfa altı) toplam metindeki payı. Temizlenmezse parçalara gürültü girer."""
    if len(sayfalar) < 2:
        return 0.0
    satirlar = [{s.strip() for s in p.splitlines() if s.strip()} for p in sayfalar]
    sayac = Counter(s for kume in satirlar for s in kume)
    tekrar = {s for s, n in sayac.items() if n >= max(2, len(sayfalar) / 2)}
    toplam = sum(len(s.strip()) for p in sayfalar for s in p.splitlines())
    gurultu = sum(len(s.strip()) for p in sayfalar for s in p.splitlines() if s.strip() in tekrar)
    return round(gurultu / toplam, 4) if toplam else 0.0


def cikar_pymupdf(yol: Path) -> list[str]:
    with pymupdf.open(yol) as d:
        return [s.get_text() for s in d]


def cikar_pdfplumber(yol: Path) -> list[str]:
    with pdfplumber.open(yol) as d:
        return [s.extract_text() or "" for s in d.pages]


def olc(sayfalar: list[str]) -> dict:
    metin = "\n".join(sayfalar)
    harf = sum(c.isalpha() for c in metin)
    ozel = sum(0xE000 <= ord(c) <= 0xF8FF for c in metin)  # özel kullanım alanı: font eşlemesi yok
    basliklar = madde_basliklari(metin)
    asil = sorted({b.no for b in basliklar if not b.gecici})
    gecici = [b for b in basliklar if b.gecici]
    eksik = sorted(set(range(1, max(asil) + 1)) - set(asil)) if asil else []
    return {
        "sayfa": len(sayfalar),
        "karakter": len(metin),
        "az_metinli_sayfa": sum(len(s.strip()) < AZ_METIN for s in sayfalar),
        "turkce_harf_orani": round(sum(c in TURKCE for c in metin) / harf, 4) if harf else 0,
        "bozuk_karakter": sum(c in BOZUK for c in metin) + ozel,
        "tekrar_eden_oran": tekrar_eden_oran(sayfalar),
        "madde_baslik": len(basliklar),
        "madde_max": max(asil) if asil else 0,
        "madde_eksik": " ".join(map(str, eksik)),
        "gecici_madde": len(gecici),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        kaynaklar = [s for s in csv.DictReader(f) if s["dosya"].endswith(".pdf")]

    satirlar = []
    for s in kaynaklar:
        yol = RAW / s["dosya"]
        for ad, cikar in [("pymupdf", cikar_pymupdf), ("pdfplumber", cikar_pdfplumber)]:
            t0 = time.perf_counter()
            sayfalar = cikar(yol)
            sure = time.perf_counter() - t0
            satirlar.append({"belge_id": s["belge_id"], "cikarici": ad,
                             **olc(sayfalar), "sure_s": round(sure, 2)})

    CIKTI.parent.mkdir(exist_ok=True)
    with CIKTI.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(satirlar)

    basliklar = ["belge_id", "cikarici", "sayfa", "karakter", "az_metinli_sayfa",
                 "turkce_harf_orani", "bozuk_karakter", "tekrar_eden_oran",
                 "madde_baslik", "madde_max",
                 "madde_eksik", "gecici_madde", "sure_s"]
    print("\t".join(basliklar))
    for r in satirlar:
        print("\t".join(str(r[b]) for b in basliklar))


if __name__ == "__main__":
    main()

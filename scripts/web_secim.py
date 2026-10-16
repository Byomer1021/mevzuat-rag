"""Taramadan çıkan sayfa ve duyuru metinlerinden bilgi tabanına girecekleri
seçer ve data/raw/web/'e üç koleksiyon olarak yazar (K-021).

    uv run python scripts/tara.py        # önce: results/tarama/web_metinleri.jsonl
    uv run python scripts/web_secim.py

- sss.jsonl: başlığı SSS olan bütün sayfalar.
- sayfalar.jsonl: öğrenciyi ilgilendiren konu sayfaları (başlıktan).
- duyurular.jsonl: bu akademik yılın duyuruları (DUYURU_BASLANGIC ve sonrası).

Kişisel veri izi taşıyan metin hiçbir koleksiyona girmez.
"""

import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

from mevzuat_rag import kisisel

KOK = Path(__file__).resolve().parents[1]
GIRDI = KOK / "results" / "tarama" / "web_metinleri.jsonl"
CIKTI = KOK / "data" / "raw" / "web"

# 2026-2027 akademik yılı; ağustos güz kaydı duyurularını da kapsasın diye
DUYURU_BASLANGIC = date(2026, 8, 1)
EN_AZ_KARAKTER = 200  # bundan kısa konu sayfası çoğunlukla bağlantı listesi

SSS = re.compile(r"sıkça|sık sorulan|s\.s\.s|\bsss\b|sorular")
KONU = re.compile(
    r"staj|çap|çift ana ?dal|yan ?dal|yatay geçiş|dikey geçiş|burs|erasmus|değişim|mevlana|"
    r"farabi|kayıt|mezuniyet|diploma|harç|katkı payı|öğrenim ücret|yemek|yurt|barınma|hazırlık|"
    r"muafiyet|intibak|sınav|\baf\b|engelli|danışman|psikolojik|sağlık|topluluk|kısmi zamanlı|"
    r"kimlik kart|e-?posta|bitirme|uzmanlık alan|ders seçim|ders planı|öğretim planı|öğrenci|"
    r"spor|kütüphane|servis|ulaşım|transkript|belge talep|aday",
)
DISLA = re.compile(
    r"lisansüstü|yüksek lisans|doktora|\btez\b|hakkında|misyon|vizyon|akademik kadro|personel|"
    r"iletişim|laboratuvar|araştırma|yönetim|kurul|komisyon|organizasyon|tarihçe|bidr|"
    r"değerlendirme raporu|akreditasyon|müdek|fedek|paydaş|danışma kurulu|haber|etkinlik|"
    r"seminer|konferans|sempozyum|aday öğrenci|tanıtım|sayılarla|mezunlarımız",
)
AYLAR = {"Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6, "Temmuz": 7,
         "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12}


def kucuk(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return s.replace("I", "ı").replace("İ", "i").lower()


def tarih(s: str) -> date | None:
    m = re.match(r"(\d{1,2}) (\w+) (\d{4})", s or "")
    if not m or m.group(2) not in AYLAR:
        return None
    return date(int(m.group(3)), AYLAR[m.group(2)], int(m.group(1)))


def kimlik(m: dict) -> str:
    """Kalıcı kimlik: duyuruda duyuru no, sayfada kategori no."""
    if m["duyuru_id"]:
        return f"d{m['duyuru_id']}"
    k = re.search(r"/kategori/(\d+)/", m["url"])
    return f"k{k.group(1)}" if k else re.sub(r"\W+", "-", m["url"])[-40:]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    metinler = [json.loads(s) for s in GIRDI.read_text(encoding="utf-8").splitlines() if s.strip()]
    koleksiyon = {"sss": [], "sayfalar": [], "duyurular": []}
    neden = Counter()
    for m in metinler:
        b = kucuk(m["baslik"])
        if kisisel.tara(m["metin"]).riskli:
            neden["kişisel veri"] += 1
            continue
        if m["tur"] == "sayfa":
            if SSS.search(b):
                hedef = "sss"
            elif KONU.search(b) and not DISLA.search(b) and len(m["metin"]) >= EN_AZ_KARAKTER:
                hedef = "sayfalar"
            else:
                neden["konu dışı / kısa sayfa"] += 1
                continue
        else:
            t = tarih(m["tarih"])
            if not t or t < DUYURU_BASLANGIC:
                neden["eski duyuru"] += 1
                continue
            if DISLA.search(b):
                neden["konu dışı duyuru"] += 1
                continue
            hedef = "duyurular"
        koleksiyon[hedef].append({"id": kimlik(m), **{k: m[k] for k in
                                  ("birim", "baslik", "tarih", "url", "metin")}})

    CIKTI.mkdir(parents=True, exist_ok=True)
    for ad, ogeler in koleksiyon.items():
        # Aynı duyuru/sayfa birden çok birimde yayımlanabiliyor (d31429: üç birim);
        # tek öğe olur, birimleri birleşir.
        tekil: dict[str, dict] = {}
        for o in ogeler:
            if o["id"] in tekil:
                t = tekil[o["id"]]
                t["birim"] = "; ".join(sorted(set(t["birim"].split("; ")) | {o["birim"]}))
                neden["birden çok birimde (birleştirildi)"] += 1
            else:
                tekil[o["id"]] = o
        ogeler = sorted(tekil.values(), key=lambda x: x["id"])
        with (CIKTI / f"{ad}.jsonl").open("w", encoding="utf-8", newline="\n") as f:
            for o in ogeler:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
        print(f"{ad}: {len(ogeler)} öğe, {sum(len(o['metin']) for o in ogeler)} karakter")
    print("dışarıda:", dict(neden))


if __name__ == "__main__":
    main()

"""Tarama çıktısını (scripts/tara.py) tekil belge envanterine çevirir ve
türlerine ayırır. Belge indirmez; neyin bilgi tabanına girebileceğine karar
vermek için.

    uv run python scripts/envanter.py [results/tarama/belgeler.csv]

Çıktı: results/tarama/envanter.csv ve ekrana özet.

Türler başlık ve dosya adındaki kelimelerden kural tabanlı çıkarılıyor; ilk
eşleşen kural kazanır. Kurallar kaba ve yanılabilir; karar verilmeden önce
örneklere elle bakılır (olcumler §7).
"""

import csv
import re
import sys
import unicodedata
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]


def kucuk(s: str) -> str:
    """Eşleşme için küçük harf. İki tuzak (olcumler §7): URL'den gelen dosya
    adlarında "İ" ayrışmış olabiliyor (I + U+0307), NFC birleştirir; büyük
    harfli ASCII ad ("BURS_ILANI") Türkçe kuralla "ılanı" olur, bu yüzden
    düz lower() hali de eklenir."""
    s = unicodedata.normalize("NFC", s)
    return s.replace("I", "ı").replace("İ", "i").lower() + " " + s.lower()


# (tür, desen) — sıra önemli, ilk eşleşen kazanır: "staj başvuru formu" form,
# "Ders Muafiyet Sınavı Uygulama Esasları" mevzuat sayılır, sınav programı değil.
KURALLAR = [
    # FR-0356 gibi: Kalite Ofisi'nin form kodu
    ("form", (r"\bform|dilekçe|dilekce|şablon|sablon|template|örneği\b|ornegi|format\b|taahhüt|"
              r"beyan|\bfr-\d{3,4}")),
    ("mevzuat", (r"yönetmeli|yonetmeli|yönerge|yonerge|esasları|esaslari|usul|ilkeler|"
                 r"kuralları|kurallar|prosedür|prosedur|regulation|directive")),
    # sonuç/liste sınavdan önce: "İngilizce Sınav Sonuçları" bir sonuç listesi
    ("ilan-sonuc", r"sonuç|sonuc|listesi|listeleri|\bliste\b|kabul edilen|randevu|girecek öğrenci"),
    # \bvize: "revize" içinde eşleşmesin
    ("sinav-ders-programi", (r"sınav|sinav|\bvize|final|bütünleme|butunleme|ders program|"
                             r"ders_prog|exam|midterm|schedule|derslik|sınıf bilgi")),
    ("ogretim-plani", (r"öğretim plan|ogretim_?plan|ders plan|müfredat|mufredat|curriculum|"
                       r"focus track|uzmanlık alan|ders katalog|seçmeli ders|secmeli|çap|cap_|"
                       r"yandal|yan dal")),
    ("ders-materyali", r"deney|lab report|ders not|lecture|ödev|homework|poster|syllabus"),
    ("rehber", (r"rehber|kılavuz|klavuz|kilavuz|sıkça sorulan|sss\b|nasıl|nasil|el kitabı|"
                r"bilgilendirme|guide")),
    ("ilan-sonuc", (r"ilan|duyuru|başvuru|basvuru|sonuç|sonuc|liste|kontenjan|kabul edilen|"
                    r"yerleş|aday|seçim|secim|takvim|announcement")),
]
# Sonuç/kabul/grup listeleri öğrenci adı ve numarası taşır: kişisel veri.
# Bilgi tabanı kişisel veri içermez (proje tanımı); bunlar indirilmez.
# Kelime sınırları gerekli: IGNORECASE "ı" ile "i"yi eş sayıyor, "asil" yoksa
# "nasıl"ın içinde eşleşiyordu (test_envanter).
KISISEL_VERI = re.compile(r"sonuç|sonuc|kabul edilen|listesi|listeleri|\bliste\b|yerleş|\basil\b|"
                          r"\byedek\b|\bgruplar|grup listesi|kazanan|\bresults?\b|randevu|"
                          r"girecek öğrenci", re.IGNORECASE)
KALITE_KODU = re.compile(r"\b(Y[ÖO]|YN)[-_ ]?0*(\d{1,4})", re.IGNORECASE)
REVIZYON = re.compile(r"[_ -]R(\d+)\b")


def tur(baslik: str, dosya_adi: str) -> str:
    t = kucuk(f"{baslik} {dosya_adi}")
    for ad, desen in KURALLAR:
        if re.search(desen, t):
            return ad
    return "diger"


def yil(*metinler: str) -> int | None:
    yillar = [int(y) for m in metinler for y in re.findall(r"(?<!\d)(20[12]\d)(?!\d)", m)]
    return max(yillar) if yillar else None


def dizin_kodlari() -> dict[str, str]:
    """GTÜ dizinindeki yürürlükteki revizyonlar: {"YÖ-0019": "R4", ...}"""
    out = {}
    for ad in ["yonetmelikler", "yonergeler"]:
        with (KOK / "data/raw/dizin" / f"{ad}.tsv").open(encoding="utf-8", newline="") as f:
            for d in csv.DictReader(f, delimiter="\t"):
                if d["dil"] == "Türkçe":
                    out[d["kod"]] = d["revizyon"]
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    girdi = (Path(sys.argv[1]) if len(sys.argv) > 1 else KOK / "results/tarama/belgeler.csv").resolve()
    with girdi.open(encoding="utf-8", newline="") as f:
        satirlar = list(csv.DictReader(f))
    with (KOK / "data/kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        bilgi_tabaninda = {urllib.parse.unquote(s["url"]) for s in csv.DictReader(f)}
    yururlukte = dizin_kodlari()

    tekil: dict[str, dict] = {}
    birimler, kaynaklar = defaultdict(set), defaultdict(set)
    for s in satirlar:
        url = s["url"]
        birimler[url].add(s["birim"])
        kaynaklar[url].add(s["kaynak_tur"])
        e = tekil.setdefault(url, dict(s))
        if len(s["baslik"]) > len(e["baslik"]):  # en açıklayıcı başlık
            e["baslik"] = s["baslik"]
        if s["tarih"] and not e["tarih"]:
            e["tarih"] = s["tarih"]

    envanter = []
    for url, e in tekil.items():
        dosya_adi = urllib.parse.unquote(url.rsplit("/", 1)[-1])
        t = tur(e["baslik"], dosya_adi)
        durum = ""
        if urllib.parse.unquote(url) in bilgi_tabaninda:
            durum = "bilgi-tabaninda"
        elif m := KALITE_KODU.search(dosya_adi):
            # /kalite/ klasöründe olmak yetmez: oradakilerin çoğu FR- formu (804'ün 782'si)
            kod = f"{'YN' if m.group(1).upper() == 'YN' else 'YÖ'}-{int(m.group(2)):04d}"
            r = REVIZYON.search(dosya_adi)
            if kod in yururlukte and r and f"R{r.group(1)}" != yururlukte[kod]:
                durum = f"eski-revizyon ({kod} R{r.group(1)}, yürürlükte {yururlukte[kod]})"
            else:
                durum = f"dizin-belgesi ({kod})"
        envanter.append({
            "tur": t, "durum": durum,
            "kisisel_veri_riski": "evet" if KISISEL_VERI.search(kucuk(f"{e['baslik']} {dosya_adi}")) else "",
            "yil": yil(e["baslik"], dosya_adi, e["tarih"]) or "",
            "tarih": e["tarih"], "baslik": e["baslik"], "dosya_adi": dosya_adi,
            "birimler": "; ".join(sorted(birimler[url])), "kaynak": "; ".join(sorted(kaynaklar[url])),
            "uzanti": e["uzanti"], "url": url,
        })
    envanter.sort(key=lambda x: (x["tur"], -(x["yil"] or 0), x["baslik"]))

    cikti = girdi.with_name("envanter" + girdi.stem.removeprefix("belgeler") + ".csv")
    with cikti.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(envanter[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(envanter)

    print(f"{len(satirlar)} bağlantı -> {len(envanter)} tekil dosya -> {cikti.relative_to(KOK)}")
    print("tür:", dict(Counter(e["tur"] for e in envanter).most_common()))
    print("durum:", dict(Counter(e["durum"].split(" (")[0] or "yeni" for e in envanter).most_common()))
    print("kişisel veri riski:", sum(e["kisisel_veri_riski"] == "evet" for e in envanter))
    yillar = Counter("yok" if not e["yil"] else ("2025+" if e["yil"] >= 2025 else "<2025") for e in envanter)
    print("yıl:", dict(yillar))
    for t in [k for k, _ in Counter(e["tur"] for e in envanter).most_common()]:
        print(f"\n## {t}")
        for e in [x for x in envanter if x["tur"] == t][:8]:
            print(f"  {e['yil']!s:4} | {e['baslik'][:60]:60} | {e['birimler'][:30]}")


if __name__ == "__main__":
    main()

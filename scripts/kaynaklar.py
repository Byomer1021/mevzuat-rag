"""Bilgi tabanının kaynakları: GTÜ mevzuat dizini, indirme, güncellik kontrolü.

    uv run python scripts/kaynaklar.py dizin     # GTÜ dizinini data/raw/dizin/ altına kaydet
    uv run python scripts/kaynaklar.py indir     # kaynaklar.csv'deki belgeleri indir, sha256 yaz
    uv run python scripts/kaynaklar.py kontrol   # kaynaklar.csv'deki revizyonlar hâlâ yürürlükte mi

Dizin (Kalite Ofisi'nin yönetmelik ve yönerge tabloları), hangi revizyonun
yürürlükte olduğunu söyleyen resmî kaynak. 'kontrol', yönetmelik
güncellendiğinde sonuçların eski metne dayandığını fark etmenin yolu.
"""

import argparse
import csv
import hashlib
import html
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
RAW = KOK / "data" / "raw"
DIZIN = RAW / "dizin"
KAYNAKLAR = KOK / "data" / "kaynaklar.csv"

SITE = "https://www.gtu.edu.tr"
DIZIN_SAYFALARI = {
    "yonetmelikler": "/kategori/3074/0/display.aspx?languageId=1",
    "yonergeler": "/kategori/3075/0/display.aspx?languageId=1",
}
DIZIN_SUTUNLARI = [
    "kod", "ad", "dil", "karar_tarihi", "karar_no",
    "ilk_yayin", "revizyon_tarihi", "revizyon", "url",
]
UA = {"User-Agent": "Mozilla/5.0 (mevzuat-rag ders projesi)"}


def getir(adres: str) -> bytes:
    url = adres if adres.startswith("http") else SITE + adres
    p = urllib.parse.urlsplit(url)
    # Dizindeki yollar Türkçe karakter ve boşluk içeriyor; bazıları zaten kodlu.
    yol = urllib.parse.quote(urllib.parse.unquote(p.path))
    url = urllib.parse.urlunsplit(p._replace(path=yol))
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def hucre_metni(hucre: str) -> str:
    # split() &nbsp; dahil tüm Unicode boşlukları tek boşluğa indirir
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", hucre)).split())


def dizin_satirlari(sayfa: bytes):
    t = sayfa.decode("utf-8", errors="replace")
    for satir in re.findall(r"<tr>(.*?)</tr>", t, re.DOTALL):
        metin = [hucre_metni(h) for h in re.findall(r"<td[^>]*>(.*?)</td>", satir, re.DOTALL)]
        if len(metin) < 9 or not re.match(r"^Y[NÖ]-\d{4}$", metin[0]):
            continue
        # Bazı satırlarda belgeden önce bir form sayfasına bağlantı var
        # ("FR-0638 için tıklayınız", YÖ-0048/YÖ-0093); dosya bağlantısı tercih edilir.
        linkler = [html.unescape(h) for h in re.findall(r'href="([^"]+)"', satir)]
        dosya = [h for h in linkler if re.search(r"\.(pdf|docx?)$", h, re.IGNORECASE)]
        link = (dosya or linkler or [""])[0]
        yield dict(zip(DIZIN_SUTUNLARI, [*metin[:8], link]))


def takvim_tsv(sayfa: bytes) -> str:
    """Akademik takvim sayfasındaki tabloyu TSV'ye çevirir.

    Sayfanın HTML'i her istekte farklı byte'larla geliyor (olcumler §2); özet
    ancak tablonun metninden alınırsa değişikliği gösterir.
    """
    t = sayfa.decode("utf-8", errors="replace")
    tablo = next(tb for tb in re.findall(r"<table.*?</table>", t, re.DOTALL) if "AKADEM" in tb)
    satirlar = ["lisans_onlisans\ttarih\tlisansustu"]
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tablo, re.DOTALL):
        hucre = [hucre_metni(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.DOTALL)]
        if len(hucre) == 3:
            satirlar.append("\t".join(hucre))
        elif any(hucre):  # tek hücreli satır: başlık
            satirlar.append(hucre[0] + "\t\t")
    return "\n".join(satirlar) + "\n"


def dizin_cek() -> dict[str, list[dict]]:
    return {ad: list(dizin_satirlari(getir(yol))) for ad, yol in DIZIN_SAYFALARI.items()}


def sha256(veri: bytes) -> str:
    return hashlib.sha256(veri).hexdigest()


def kaynaklari_oku() -> list[dict]:
    with KAYNAKLAR.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def kaynaklari_yaz(satirlar: list[dict]) -> None:
    with KAYNAKLAR.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(satirlar)


def cmd_dizin(_):
    DIZIN.mkdir(parents=True, exist_ok=True)
    bugun = time.strftime("%Y-%m-%d")
    for ad, satirlar in dizin_cek().items():
        yol = DIZIN / f"{ad}.tsv"
        with yol.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=DIZIN_SUTUNLARI + ["cekildi"],
                               delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows({**s, "cekildi": bugun} for s in satirlar)
        print(f"{ad}: {len(satirlar)} satır -> {yol.relative_to(KOK)}")


def cmd_indir(args):
    satirlar = kaynaklari_oku()
    for s in satirlar:
        hedef = RAW / s["dosya"]
        if hedef.exists() and s["sha256"] and sha256(hedef.read_bytes()) == s["sha256"]:
            print(f"  var     {s['belge_id']}")
            continue
        veri = getir(s["url"])
        if hedef.suffix == ".tsv":
            veri = takvim_tsv(veri).encode("utf-8")
        elif hedef.suffix == ".pdf" and not veri.startswith(b"%PDF"):
            sys.exit(f"HATA {s['belge_id']}: PDF değil, ilk baytlar {veri[:20]!r}")
        ozet = sha256(veri)
        if s["sha256"] and ozet != s["sha256"] and not args.guncelle:
            # Sonuçlar kayıtlı sürüme bağlı; sessizce üzerine yazmak onları geçersiz kılar.
            print(f"  DEĞİŞMİŞ {s['belge_id']}: kayıtlı {s['sha256'][:12]}, indirilen {ozet[:12]}."
                  " Üzerine yazılmadı (--guncelle ile yazılır).")
            continue
        hedef.write_bytes(veri)
        s["sha256"], s["indirme_tarihi"] = ozet, time.strftime("%Y-%m-%d")
        print(f"  indi    {s['belge_id']}  {len(veri) / 1024:.0f} KB  {ozet[:12]}")
    kaynaklari_yaz(satirlar)


def metin_ozeti(veri: bytes, sonek: str) -> str:
    """Belgenin içeriğinin özeti. mevzuat.gov.tr PDF'i ve takvim sayfası her
    istekte farklı byte'larla geliyor (olcumler §2, §6); dizinde revizyonu
    olmayan belgelerde değişiklik ancak metinden anlaşılır."""
    if sonek == ".pdf":
        import pymupdf  # yalnızca burada gerekiyor

        with pymupdf.open(stream=veri, filetype="pdf") as d:
            veri = "".join("".join(s.get_text().split()) for s in d).encode("utf-8")
    return sha256(veri)


def cmd_kontrol(_):
    yururlukte = {d["kod"]: d for ad in dizin_cek().values() for d in ad if d["dil"] == "Türkçe"}
    eski = 0
    for s in kaynaklari_oku():
        if s["kod"] == "-":
            sonek = Path(s["dosya"]).suffix
            yeni = getir(s["url"])
            if sonek == ".tsv":
                yeni = takvim_tsv(yeni).encode("utf-8")
            if metin_ozeti(yeni, sonek) == metin_ozeti((RAW / s["dosya"]).read_bytes(), sonek):
                print(f"  güncel  {s['belge_id']} (dizinde değil; metin aynı)")
            else:
                print(f"  DEĞİŞMİŞ {s['belge_id']}: kaynaktaki metin elimizdekinden farklı")
                eski += 1
            continue
        d = yururlukte.get(s["kod"])
        if d is None:
            print(f"  YOK     {s['belge_id']} ({s['kod']}): dizinden kalkmış")
            eski += 1
        elif d["revizyon"] != s["revizyon"]:
            print(f"  ESKİ    {s['belge_id']} ({s['kod']}): elimizde {s['revizyon']},"
                  f" yürürlükte {d['revizyon']} ({d['revizyon_tarihi']})")
            eski += 1
        else:
            print(f"  güncel  {s['belge_id']} ({s['kod']} {s['revizyon']})")
    sys.exit(1 if eski else 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(required=True)
    alt.add_parser("dizin").set_defaults(f=cmd_dizin)
    p = alt.add_parser("indir")
    p.add_argument("--guncelle", action="store_true", help="değişmiş belgenin üzerine yaz")
    p.set_defaults(f=cmd_indir)
    alt.add_parser("kontrol").set_defaults(f=cmd_kontrol)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()

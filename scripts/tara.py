"""GTÜ sitesinde birimlerin (bölüm, fakülte, Öğrenci İşleri…) sayfalarını ve
duyurularını tarar, bulunan belgelerin envanterini çıkarır. Belge indirmez.

    uv run python scripts/tara.py                 # bütün birimler
    uv run python scripts/tara.py --birim 91      # yalnızca bir birim

Site Next.js: menü ve duyuru içerikleri sayfaya gömülü veride. Bir birimin
ana sayfası menüsünü (title, adress) ve "Duyurular → Tümü" bağlantısını
veriyor. Duyuru listesi her duyuruyu <li><a> olarak listeliyor: kimi doğrudan
dosyaya, kimi detay sayfasına (/icerik/<kategori>/<id>/). Detay sayfaları
yalnızca DETAY_ID_MIN'den yeni duyurular için çekilir (olcumler §7).

Çıktı: results/tarama/belgeler.csv (her dosya bağlantısı bir satır) ve
results/tarama/duyurular.csv (her duyuru bir satır). Sayfalar
.cache/tarama/ altında saklanır; yeniden çalıştırınca siteye tekrar gidilmez.
"""

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from mevzuat_rag import web

KOK = Path(__file__).resolve().parents[1]
ONBELLEK = KOK / ".cache" / "tarama"
CIKTI = KOK / "results" / "tarama"
SITE = "https://www.gtu.edu.tr"
UA = {"User-Agent": "Mozilla/5.0 (mevzuat-rag ders projesi)"}
BEKLE = 0.5  # saniye, istekler arası
# Kimlikler zamanla artıyor: 8890 Ekim 2019, 28134 9 Şubat 2026, 31792 8 Ekim
# 2026 (ayda ~450). 25500 kabaca Eylül 2025: geçen akademik yılın başı. Tarih
# her detay sayfasından ayrıca okunuyor; eşik yalnızca ne kadar çekileceği.
DETAY_ID_MIN = 25500

# Lisans öğrencisini ilgilendiren birimler. Araştırma enstitüleri, merkezler,
# idari birimler ve Lisansüstü Eğitim Enstitüsü kapsam dışı (K-018).
BIRIMLER = {
    1007: "Öğrenci İşleri Daire Başkanlığı",
    1012: "Sağlık Kültür ve Spor Daire Başkanlığı",
    2128: "Uluslararası İlişkiler Koordinatörlüğü",
    6967: "Uluslararası Öğrenciler Koordinatörlüğü",
    3130: "Kariyer ve Profesyonel Gelişim Merkezi",
    1250: "Engelsiz GTÜ Birimi",
    6503: "Öğrenci Toplulukları Koordinatörlüğü",
    9580: "Öğrenci Başarı ve Destek Koordinatörlüğü",
    1013: "Kütüphane ve Dokümantasyon Daire Başkanlığı",
    48: "Yabancı Diller Bölümü",
    51: "Beden Eğitimi ve Spor Bölümü",
    41: "Mühendislik Fakültesi",
    42: "Fakülte 42",
    43: "Fakülte 43",
    44: "Fakülte 44",
    3783: "Fakülte 3783",
    4295: "Meslek Yüksekokulu",
    91: "Bilgisayar Mühendisliği",
    301: "Elektronik Mühendisliği",
    302: "Makine Mühendisliği",
    303: "Harita Mühendisliği",
    304: "Malzeme Bilimi ve Mühendisliği",
    305: "Çevre Mühendisliği",
    306: "Kimya Mühendisliği",
    307: "Biyomühendislik",
    2333: "İnşaat Mühendisliği",
    2334: "Endüstri Mühendisliği",
    3807: "Uçak Mühendisliği",
    2471: "Endüstriyel Tasarım",
    3822: "Yönetim Bilişim Sistemleri",
    6739: "Veri Bilimi ve Analitiği",
    560: "Matematik",
    561: "Kimya",
    562: "Fizik",
    563: "Moleküler Biyoloji ve Genetik",
    564: "Mimarlık",
    565: "Şehir ve Bölge Planlama",
    566: "İşletme",
    567: "İktisat",
    568: "Strateji Bilimi",
}

DOSYA = re.compile(r"\.(pdf|docx?|xlsx?|pptx?)$", re.IGNORECASE)
AYLAR = "Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık"
TARIH = re.compile(rf"\b(\d{{1,2}}) ({AYLAR}) (20\d\d)\b")

_son_istek = 0.0


def mutlak(adres: str) -> str:
    adres = html.unescape(adres).replace("\\u0026", "&")
    adres = re.sub(r"^/tr(/Files/)", r"\1", adres)  # "/tr/Files/…" de çalışıyor, tekilleştir
    return urllib.parse.urljoin(SITE + "/", adres)


def getir(url: str) -> str:
    global _son_istek
    ONBELLEK.mkdir(parents=True, exist_ok=True)
    yol = ONBELLEK / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    if yol.exists():
        return yol.read_text(encoding="utf-8")
    time.sleep(max(0.0, BEKLE - (time.time() - _son_istek)))
    p = urllib.parse.urlsplit(url)
    istek_url = urllib.parse.urlunsplit(p._replace(path=urllib.parse.quote(urllib.parse.unquote(p.path))))
    for deneme in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(istek_url, headers=UA), timeout=60) as r:
                metin = r.read().decode("utf-8", errors="replace")
            break
        except Exception as e:  # noqa: BLE001  (ağ hatası: iki kez daha dene, sonra boş geç)
            if deneme == 2:
                print(f"    ! {url}: {e}", file=sys.stderr)
                metin = ""
            time.sleep(2)
    _son_istek = time.time()
    if metin:  # başarısız istek önbelleğe yazılmaz; sonraki çalıştırmada yeniden denenir
        yol.write_text(metin, encoding="utf-8")
    return metin


def menu(sayfa: str) -> list[tuple[str, str]]:
    """Gömülü menü verisinden (başlık, adres) çiftleri; yalnız site içi kategori sayfaları."""
    t = sayfa.replace('\\"', '"')
    out = []
    for baslik, adres in re.findall(r'"title":"((?:[^"\\]|\\.)*)","adress":"([^"]*)"', t):
        try:
            baslik = json.loads(f'"{baslik}"')
        except json.JSONDecodeError:
            pass
        if "gtu.edu.tr/" in adres and "/kategori/" in adres or adres.startswith("/"):
            out.append((baslik.strip(), mutlak(adres)))
    return list(dict.fromkeys(out))


def duyuru_listesi_adresi(sayfa: str) -> str | None:
    m = re.search(r'Duyurular<a [^>]*href="([^"]+)"', sayfa)
    return mutlak(m.group(1)) if m else None


def baglantilar(sayfa: str) -> list[tuple[str, str]]:
    """Sayfadaki dosya bağlantıları: (adres, bağlantı metni). HTML çapalarından
    ve gömülü veriden; metni bulunamazsa dosya adı."""
    out = {}
    for adres, metin in re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', sayfa, re.DOTALL):
        if DOSYA.search(adres.split("?")[0]):
            out.setdefault(mutlak(adres), " ".join(html.unescape(re.sub(r"<[^>]+>", " ", metin)).split()))
    t = sayfa.replace('\\"', '"')
    for adres in re.findall(r'"href":"([^"]+)"', t):
        if DOSYA.search(adres.split("?")[0]):
            out.setdefault(mutlak(adres), "")
    return [(a, m or urllib.parse.unquote(a.rsplit("/", 1)[-1])) for a, m in out.items()
            if "aydinlatma-metni" not in a.lower() and "ayd%c4%b1nlatma" not in a.lower()]


def liste_ogeleri(sayfa: str) -> list[tuple[str, str]]:
    return [(mutlak(a), " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m)).split()))
            for a, m in re.findall(r'<li class="hover:underline"><a href="([^"]+)">(.*?)</a></li>', sayfa, re.DOTALL)]


def sayfa_basligi(sayfa: str) -> str:
    m = re.search(r"<title>(.*?)</title>", sayfa, re.DOTALL)
    return " ".join(html.unescape(m.group(1)).split()) if m else ""


def detay_tarihi(sayfa: str) -> str:
    govde = re.sub(r"<script.*?</script>", " ", sayfa, flags=re.DOTALL)
    m = TARIH.search(" ".join(html.unescape(re.sub(r"<[^>]+>", " ", govde)).split()))
    return " ".join(m.groups()) if m else ""


def birim_tara(kimlik: int, ad: str, belgeler: list, duyurular: list, gorulen: set,
               metinler: list) -> None:
    ana = getir(f"{SITE}/kategori/{kimlik}/3/display.aspx")
    if not ana:
        return
    ad = ad if not ad.startswith("Fakülte ") else (sayfa_basligi(ana).split("|")[0].strip() or ad)
    print(f"  {kimlik} {ad}", flush=True)

    def kaydet(adres, metin, kaynak_tur, kaynak, tarih="", duyuru_id=""):
        anahtar = (adres, kaynak)
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            belgeler.append({"birim_id": kimlik, "birim": ad, "kaynak_tur": kaynak_tur,
                             "kaynak": kaynak, "duyuru_id": duyuru_id, "tarih": tarih,
                             "baslik": metin, "uzanti": DOSYA.search(adres.split("?")[0]).group(1).lower(),
                             "url": adres})

    for a, m in baglantilar(ana):
        kaydet(a, m, "birim-anasayfa", f"{SITE}/kategori/{kimlik}/3/display.aspx")
    for baslik, adres in menu(ana):
        if DOSYA.search(adres.split("?")[0]):
            kaydet(adres, baslik, "menu", f"{SITE}/kategori/{kimlik}/3/display.aspx")
            continue
        sayfa = getir(adres)
        for a, m in baglantilar(sayfa):
            kaydet(a, m, "menu-sayfasi", adres)
        if "/kategori/" in adres and (metin := web.zengin_metin(sayfa)):
            metinler.append({"birim_id": kimlik, "birim": ad, "tur": "sayfa", "duyuru_id": "",
                             "tarih": "", "baslik": baslik, "url": adres, "metin": metin})

    liste_adresi = duyuru_listesi_adresi(ana)
    if not liste_adresi:
        return
    for adres, baslik in liste_ogeleri(getir(liste_adresi)):
        m = re.search(r"/icerik/\d+/(\d+)/", adres)
        if DOSYA.search(adres.split("?")[0]):
            kaydet(adres, baslik, "duyuru-listesi", liste_adresi)
            duyurular.append({"birim_id": kimlik, "birim": ad, "duyuru_id": "", "tarih": "",
                              "baslik": baslik, "url": adres, "ek_sayisi": 1})
        elif m:
            did, tarih, ek = int(m.group(1)), "", ""
            if did >= DETAY_ID_MIN:
                detay = getir(adres)
                tarih = detay_tarihi(detay)
                ekler = baglantilar(detay)
                ek = len(ekler)
                for a, mt in ekler:
                    kaydet(a, mt, "duyuru-detay", adres, tarih, did)
                d_baslik, d_metin, _ = web.duyuru(detay)
                if d_metin:
                    metinler.append({"birim_id": kimlik, "birim": ad, "tur": "duyuru",
                                     "duyuru_id": did, "tarih": tarih,
                                     "baslik": d_baslik or baslik, "url": adres, "metin": d_metin})
            duyurular.append({"birim_id": kimlik, "birim": ad, "duyuru_id": did, "tarih": tarih,
                              "baslik": baslik, "url": adres, "ek_sayisi": ek})
        else:  # başka bir sayfaya bağlantı; sayım listeyle tutsun diye kaydediliyor
            duyurular.append({"birim_id": kimlik, "birim": ad, "duyuru_id": "", "tarih": "",
                              "baslik": baslik, "url": adres, "ek_sayisi": ""})


def yaz(yol: Path, satirlar: list[dict]) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("w", encoding="utf-8", newline="") as f:
        if satirlar:
            w = csv.DictWriter(f, fieldnames=list(satirlar[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(satirlar)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--birim", type=int, action="append", help="yalnızca bu birim(ler)")
    args = ap.parse_args()
    secim = {k: v for k, v in BIRIMLER.items() if not args.birim or k in args.birim}

    belgeler, duyurular, gorulen, metinler = [], [], set(), []
    for kimlik, ad in secim.items():
        birim_tara(kimlik, ad, belgeler, duyurular, gorulen, metinler)
    sonek = "" if not args.birim else "_" + "_".join(map(str, args.birim))
    yaz(CIKTI / f"belgeler{sonek}.csv", belgeler)
    yaz(CIKTI / f"duyurular{sonek}.csv", duyurular)
    # Sayfa ve duyuru metinleri: önbellekten yeniden üretilir, depoya girmez
    # (.gitignore). Bilgi tabanına seçilenler data/raw/web/'e yazılır (K-020).
    tekil = list({m["url"]: m for m in metinler}.values())
    with (CIKTI / f"web_metinleri{sonek}.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for m in tekil:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    tekil = len({b["url"] for b in belgeler})
    print(f"{len(secim)} birim, {len(duyurular)} duyuru, {len(belgeler)} bağlantı ({tekil} tekil dosya)")


if __name__ == "__main__":
    main()

"""Temiz sayfa metnini parçalara böler.

- madde bazlı: her madde bir parça; başlığı ("Amaç") ve varsa bölüm başlığı
  ("BİRİNCİ BÖLÜM ...") maddenin önündeki satırlardan alınır.
- paragraf: madde yapısı olmayan belge (YÖ-0087) için yedek; paragraflar
  hedef uzunluğa kadar birleştirilir.
- sabit: taban sistem için; maddeye bakmadan sabit uzunlukta, örtüşmeli.

Her parça başladığı ve bittiği sayfayı taşır; cevapta kaynak göstermek için.
"""

import bisect
import itertools
import re
from dataclasses import asdict, dataclass

from mevzuat_rag.madde import madde_basliklari
from mevzuat_rag.onisleme import Sayfa

BOLUM = re.compile(
    r"^(BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ|ALTINCI|YEDİNCİ|SEKİZİNCİ|DOKUZUNCU|ONUNCU)"
    r"\s+BÖLÜM\b"
)
BASLIK_MAX = 90  # bundan uzun satır madde başlığı sayılmaz
GERI_MAX = 6  # maddenin önünde en fazla bu kadar satır geriye bakılır


@dataclass
class Parca:
    id: str  # "yatay-gecis/m5", "/g1" geçici, "/e1" ek, "/p2" paragraf, "/s3" sabit
    belge_id: str
    tur: str  # madde | gecici | ek | giris | paragraf | sabit | takvim
    madde: str | None  # "5", "geçici 1", "geçici", "ek 1"
    baslik: str
    bolum: str
    sayfa_bas: int
    sayfa_son: int
    metin: str

    def sozluk(self) -> dict:
        return asdict(self)


class _Metin:
    """Sayfaları tek metne birleştirir, konumdan sayfa numarasına çevirir."""

    def __init__(self, sayfalar: list[Sayfa]):
        self.baslar, parcalar, konum = [], [], 0
        for s in sayfalar:
            self.baslar.append(konum)
            parcalar.append(s.metin)
            konum += len(s.metin) + 1
        self.nolar = [s.no for s in sayfalar]
        self.metin = "\n".join(parcalar)

    def sayfa(self, konum: int) -> int:
        return self.nolar[bisect.bisect_right(self.baslar, konum) - 1]

    def araligi(self, bas: int, son: int) -> tuple[int, int]:
        # son: dışlayıcı; baştaki ve sondaki boşluklar (sayfa sınırındaki "\n"
        # dahil) sayfa hesabına katılmaz
        while bas < son and self.metin[bas].isspace():
            bas += 1
        while son > bas and self.metin[son - 1].isspace():
            son -= 1
        return self.sayfa(bas), self.sayfa(max(bas, son - 1))


KISALTMA = re.compile(r"^\([A-ZÇĞİÖŞÜ]{2,}\)$")  # "(ÖLİST)": üstteki başlığın devamı


def _baslik_satiri_mi(satir: str) -> bool:
    s = satir.strip()
    if KISALTMA.match(s):
        return True
    if not s or "\t" in s or len(s) > BASLIK_MAX or s.endswith((".", ",", ";")):
        return False  # sekme: tablo satırı (onisleme)
    # "6/2/2023 Tarihli depremlere ilişkin hükümleri" rakamla başlıyor;
    # "F4", "78 – 85" gibi tablo hücreleri ise üç harfli bir kelime içermiyor.
    if not (s[0].isupper() or s[0].isdigit()) or not re.search(r"[^\W\d_]{3,}", s):
        return False
    return not re.match(r"^(\(?\d+[).]|[a-zçğıöşü]\)|·|-)", s)


def _geriye_baslik(metin: str, konum: int, alt_sinir: int) -> tuple[int, list[str]]:
    """Madde başlığının önündeki başlık satırlarını bulur: (yeni başlangıç, satırlar).

    Önce boş satırlarla ayrılmış başlık benzeri satır grupları toplanır
    (en yakını önce). Bir grupta "… BÖLÜM" varsa o satırdan itibaren hepsi
    alınır. Yoksa yalnızca maddeye en yakın tek satır başlıktır. Bu sınır
    önemli: YÖ-0002'de önceki maddenin not tablosunun son hücreleri ("F4",
    "Başarısız") kısa ve büyük harfli olduğu için başlık gibi görünüyor.
    """
    gruplar: list[list[tuple[int, str]]] = [[]]  # (satır başı, satır)
    bas, bakilan = konum, 0
    while bakilan < GERI_MAX and bas > alt_sinir:
        onceki = metin.rfind("\n", alt_sinir, bas - 1)
        satir_bas = alt_sinir if onceki < 0 else onceki + 1
        satir = metin[satir_bas:bas]
        bas = satir_bas
        if not satir.strip():
            if gruplar[-1]:
                gruplar.append([])
            continue
        if not _baslik_satiri_mi(satir):
            break
        gruplar[-1].insert(0, (satir_bas, satir.strip()))
        bakilan += 1

    gruplar = [g for g in gruplar if g]
    for g in reversed(gruplar):  # en uzaktaki bölüm başlığından itibaren al
        for k, (sb, s) in enumerate(g):
            if BOLUM.match(s):
                alinan = g[k:] + [x for g2 in reversed(gruplar[: gruplar.index(g)]) for x in g2]
                return sb, [s for _, s in alinan]
    if gruplar:
        g = gruplar[0]
        if KISALTMA.match(g[-1][1]) and len(g) > 1:  # "… Tespit Sınavı" + "(ÖLİST)"
            return g[-2][0], [f"{g[-2][1]} {g[-1][1]}"]
        sb, s = g[-1]
        return sb, [s]
    return konum, []


def _bolum_ve_baslik(satirlar: list[str]) -> tuple[str, str]:
    for i, s in enumerate(satirlar):
        if BOLUM.match(s):
            # "BİRİNCİ BÖLÜM" + bölüm adı; kalan son satır maddenin başlığı
            bolum = " ".join(satirlar[i : i + 2])
            kalan = satirlar[i + 2 :]
            return bolum, kalan[-1] if kalan else ""
    return "", satirlar[-1] if satirlar else ""


def madde_parcala(belge_id: str, sayfalar: list[Sayfa]) -> list[Parca]:
    m = _Metin(sayfalar)
    basliklar = madde_basliklari(m.metin)
    if not basliklar:
        return []

    baslangiclar, bilgiler, alt_sinir = [], [], 0
    for b in basliklar:
        bas, satirlar = _geriye_baslik(m.metin, b.konum, alt_sinir)
        baslangiclar.append(bas)
        bilgiler.append((b, *_bolum_ve_baslik(satirlar)))
        alt_sinir = b.konum + 1

    parcalar = []
    giris = m.metin[: baslangiclar[0]].strip()
    if giris:
        s1, s2 = m.araligi(0, baslangiclar[0])
        parcalar.append(Parca(f"{belge_id}/giris", belge_id, "giris", None, "", "", s1, s2, giris))

    on_ek = {"madde": ("m", ""), "gecici": ("g", "geçici"), "ek": ("e", "ek")}
    sira: dict[str, int] = {}
    for i, (b, bolum, baslik) in enumerate(bilgiler):
        bas = baslangiclar[i]
        son = baslangiclar[i + 1] if i + 1 < len(baslangiclar) else len(m.metin)
        sira[b.tur] = sira.get(b.tur, 0) + 1
        harf, ad = on_ek[b.tur]
        pid, tur = f"{belge_id}/{harf}{b.no or sira[b.tur]}", b.tur
        madde = " ".join(x for x in (ad, str(b.no) if b.no else "") if x)
        # Başlangıç sayfası "MADDE N"nin olduğu sayfa: başlık ("Öğretim
        # planları") bazen önceki sayfanın son satırında kalıyor (YN-0001 m13).
        s1, s2 = m.sayfa(b.konum), m.araligi(bas, son)[1]
        parcalar.append(Parca(pid, belge_id, tur, madde, baslik, bolum, s1, s2,
                              m.metin[bas:son].strip()))
    return parcalar


def paragraf_parcala(belge_id: str, sayfalar: list[Sayfa], hedef: int) -> list[Parca]:
    m = _Metin(sayfalar)
    sinirlar = [0] + [x.end() for x in re.finditer(r"\n\s*\n", m.metin)] + [len(m.metin)]
    paragraflar = [(a, b) for a, b in itertools.pairwise(sinirlar) if m.metin[a:b].strip()]

    gruplar: list[tuple[int, int]] = []
    for a, b in paragraflar:
        if gruplar and b - gruplar[-1][0] <= hedef:
            gruplar[-1] = (gruplar[-1][0], b)
        else:
            gruplar.append((a, b))

    out = []
    for k, (a, b) in enumerate(gruplar, 1):
        s1, s2 = m.araligi(a, b)
        out.append(Parca(f"{belge_id}/p{k}", belge_id, "paragraf", None, "", "", s1, s2,
                         m.metin[a:b].strip()))
    return out


def takvim_parcala(belge_id: str, tsv: str) -> list[Parca]:
    """Akademik takvim TSV'sinin her satırı bir parça. Tarihi boş satırlar
    bölüm başlığı sayılır ve sonraki satırlara 'bolum' olarak taşınır."""
    satirlar = [(s.split("\t") + ["", ""])[:3] for s in tsv.splitlines()[1:]]  # 1. satır: sütun adları
    out, bolum = [], ""
    for lisans, tarih, lisansustu in satirlar:
        if not tarih:
            bolum = lisans
            continue
        if tarih == "TARİHLER":  # tablonun kendi başlık satırı
            continue
        metin = "\n".join(x for x in [
            f"Tarih: {tarih}",
            f"Lisans/önlisans: {lisans}" if lisans else "",
            f"Lisansüstü: {lisansustu}" if lisansustu else "",
        ] if x)
        out.append(Parca(f"{belge_id}/r{len(out) + 1}", belge_id, "takvim", None, "", bolum,
                         1, 1, metin))
    return out


def sabit_parcala(belge_id: str, sayfalar: list[Sayfa], boyut: int, ortusme: int) -> list[Parca]:
    """Maddeye bakmadan sabit uzunlukta (karakter) parçalar; kesim kelime sınırına çekilir."""
    if not 0 <= ortusme < boyut:
        raise ValueError("ortusme, 0 ile boyut arasında olmalı")
    m = _Metin(sayfalar)
    metin, out, bas, k = m.metin, [], 0, 0
    while bas < len(metin):
        son = min(bas + boyut, len(metin))
        if son < len(metin):
            bosluk = metin.rfind(" ", bas + boyut // 2, son)
            son = bosluk if bosluk > 0 else son
        k += 1
        s1, s2 = m.araligi(bas, son)
        out.append(Parca(f"{belge_id}/s{k}", belge_id, "sabit", None, "", "", s1, s2,
                         metin[bas:son].strip()))
        if son >= len(metin):
            break
        yeni = son - ortusme
        if ortusme:
            bosluk = metin.find(" ", yeni, son)
            yeni = bosluk + 1 if bosluk >= 0 else yeni
        bas = max(yeni, bas + 1)
    return out

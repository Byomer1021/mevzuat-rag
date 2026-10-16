"""Ön işlem: bütün kaynakları parçalara böler, data/processed/'e yazar ve
sonucu denetler. Sonuç: results/onisleme.json, olcumler §4, §9.

    uv run python scripts/onisle.py

PDF'ler temizlenir ve maddelere (madde yoksa paragraflara) bölünür; takvim
satır satır, form kataloğu form form, web koleksiyonları öğe öğe parçalanır.
Her kaynağın metni kişisel veri için ayrıca taranır.
"""

import csv
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

from mevzuat_rag import kisisel
from mevzuat_rag.madde import madde_basliklari
from mevzuat_rag.onisleme import pdf_sayfalari
from mevzuat_rag.parcalama import (
    katalog_parcala,
    madde_parcala,
    paragraf_parcala,
    takvim_parcala,
    web_parcala,
)

KOK = Path(__file__).resolve().parents[1]
RAW = KOK / "data" / "raw"
CIKTI = KOK / "data" / "processed" / "parcalar_madde.jsonl"
RAPOR = KOK / "results" / "onisleme.json"
MADDE_TURLERI = ("madde", "gecici", "ek")
# Yalnızca başlık tablosuna özgü izler. "Yayın Tarihi", "Revizyon Tarihi" gövdede
# de geçiyor (CHEM 492 esaslarının sonundaki not), yanlış alarm veriyordu.
IZLER = ["Doküman No", "Revizyon No"]
ALTLIK_IZI = re.compile(r"Form No:\s*FR-\d{3,4}.*Yayın Tarihi")
# Bundan az asıl madde başlığı varsa belge madde yapısında sayılmaz: öğretim
# planında geçen tek bir "Geçici Madde" bütün tabloları o maddeye yığıyordu.
MADDE_MIN = 3
MADDESIZ_TURLER = ("ogretim-plani",)
ATILAN_SAYFA_MAX = 400  # boşluksuz karakter


def bilgi_tabani_surumu(kaynaklar: list[dict]) -> str:
    """Kaynakların (kimlik, sha256) çiftlerinden kısa özet. Belge eklenir,
    çıkarılır ya da değişirse özet değişir; her ölçüm bunu taşır ki farklı
    bilgi tabanlarıyla alınmış sonuçlar karşılaştırılmasın (K-016)."""
    ozet = "\n".join(sorted(f"{s['belge_id']}:{s['sha256']}" for s in kaynaklar))
    return hashlib.sha256(ozet.encode()).hexdigest()[:12]


def bosluksuz(metin: str) -> str:
    return "".join(metin.split())


def aralik_dogru(p, sayfa_metni: dict[int, str]) -> bool:
    """Parça, verilen sayfa aralığının birleşiminde geçmeli; aralık bir uçtan
    daraltılınca geçmemeli (yani aralık hem yeterli hem en dar).

    Madde parçalarında kontrol "MADDE N"den başlar: başlık satırı önceki
    sayfada kalabilir, sayfa_bas ise maddenin kendisinin sayfasıdır."""
    metin = p.metin
    if p.tur in MADDE_TURLERI:
        metin = metin[madde_basliklari(metin)[0].konum:]
    metin = bosluksuz(metin)

    def birlesik(a, b):
        return "".join(sayfa_metni[i] for i in range(a, b + 1))

    if metin not in birlesik(p.sayfa_bas, p.sayfa_son):
        return False
    if p.sayfa_son > p.sayfa_bas:
        return (metin not in birlesik(p.sayfa_bas + 1, p.sayfa_son)
                and metin not in birlesik(p.sayfa_bas, p.sayfa_son - 1))
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with (KOK / "data" / "kaynaklar.csv").open(encoding="utf-8", newline="") as f:
        kaynaklar = list(csv.DictReader(f))

    temiz, atilan_say, parcalar, sorunlar = {}, Counter(), [], []
    atilan_kar = kalan_kar = 0
    for s in kaynaklar:
        if not s["dosya"].endswith(".pdf"):
            continue
        sayfalar = pdf_sayfalari(RAW / s["dosya"])
        temiz[s["belge_id"]] = sayfalar
        for sy in sayfalar:
            # sayıları maskeleyerek grupla: "Sayfa 7-3" ile "Sayfa 7-4" aynı kalıp
            atilan_say.update(re.sub(r"\d", "#", a) for a in sy.atilan)
            a, k = sum(len(bosluksuz(x)) for x in sy.atilan), len(bosluksuz(sy.metin))
            atilan_kar, kalan_kar = atilan_kar + a, kalan_kar + k
            # Kapsama denetimi temizlenmiş metne bakar; temizliğin gövdeyi
            # silmesini göremez. Başlık+altlık boyutu sabit: 52 sayfada
            # 174-259 karakter (olcumler §5). Oran değil mutlak sayı, çünkü kısa
            # son sayfalarda başlık metnin yarısı olabiliyor (%48).
            if a > ATILAN_SAYFA_MAX:
                sorunlar.append(f"{s['belge_id']} s{sy.no}: {a} karakter atıldı")
            for iz in IZLER:
                if iz in sy.metin:
                    sorunlar.append(f"{s['belge_id']} s{sy.no}: temiz metinde '{iz}' kaldı")
            if ALTLIK_IZI.search(sy.metin):
                sorunlar.append(f"{s['belge_id']} s{sy.no}: temiz metinde form altlığı kaldı")
            if re.search(r"Sayfa\s+\d+\s*-\s*\d+", sy.metin):
                sorunlar.append(f"{s['belge_id']} s{sy.no}: temiz metinde 'Sayfa N-M' kaldı")

    tur = {s["belge_id"]: s["tur"] for s in kaynaklar}
    madde_parcalari = {}
    for b, sy in temiz.items():
        ps = [] if tur[b] in MADDESIZ_TURLER else madde_parcala(b, sy)
        if sum(p.tur == "madde" for p in ps) < MADDE_MIN:
            ps = []  # madde yapısında değil; aşağıda paragraflara bölünür
        madde_parcalari[b] = ps
    uzunluklar = [len(p.metin) for ps in madde_parcalari.values() for p in ps
                  if p.tur in MADDE_TURLERI]
    hedef = int(statistics.median(uzunluklar))

    adres = {s["belge_id"]: s["url"] for s in kaynaklar}
    ozetler: dict[str, list[str]] = {}
    for b, ps in madde_parcalari.items():
        if not ps:  # madde yapısı yok (YÖ-0087, rehberler, öğretim planları)
            ps = paragraf_parcala(b, temiz[b], hedef)
            madde_parcalari[b] = ps
        tam = "\n".join(x.metin for x in temiz[b])
        # kapsama: parçalar temiz metnin tamamını kayıpsız ve tekrarsız örtmeli
        if bosluksuz("".join(p.metin for p in ps)) != bosluksuz(tam):
            sorunlar.append(f"{b}: parçalar temiz metni birebir örtmüyor")
        if (bulgu := kisisel.tara(tam)).riskli:
            sorunlar.append(f"{b}: kişisel veri izi {bulgu}")
        ozetler.setdefault(hashlib.sha256(bosluksuz(tam).encode()).hexdigest(), []).append(b)
        sayfa_metni = {x.no: bosluksuz(x.metin) for x in temiz[b]}
        for p in ps:
            p.url = adres[b]
            if not aralik_dogru(p, sayfa_metni):
                sorunlar.append(f"{p.id}: sayfa aralığı {p.sayfa_bas}-{p.sayfa_son} tutmuyor")
        parcalar += ps

    web_ogesi = 0
    for s in kaynaklar:
        yol = RAW / s["dosya"]
        if s["tur"] == "takvim":
            parcalar += takvim_parcala(s["belge_id"], yol.read_text(encoding="utf-8"))
        elif s["tur"] == "katalog":
            parcalar += katalog_parcala(s["belge_id"], yol.read_text(encoding="utf-8"))
        elif s["tur"] == "koleksiyon":
            for satir in yol.read_text(encoding="utf-8").splitlines():
                oge = json.loads(satir)
                web_ogesi += 1
                ps = web_parcala(s["belge_id"], oge, hedef)
                if bosluksuz("".join(p.metin for p in ps)) != bosluksuz(oge["metin"]):
                    sorunlar.append(f"{s['belge_id']}/{oge['id']}: parçalar metni örtmüyor")
                if (bulgu := kisisel.tara(oge["metin"])).riskli:
                    sorunlar.append(f"{s['belge_id']}/{oge['id']}: kişisel veri izi {bulgu}")
                parcalar += ps

    kimlikler = Counter(p.id for p in parcalar)
    sorunlar += [f"{i}: parça kimliği {n} kez" for i, n in kimlikler.items() if n > 1]

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    with CIKTI.open("w", encoding="utf-8", newline="\n") as f:
        for p in parcalar:
            f.write(json.dumps(p.sozluk(), ensure_ascii=False) + "\n")

    maddeler = [p for p in parcalar if p.tur in MADDE_TURLERI]
    q = statistics.quantiles(uzunluklar, n=10)
    rapor = {
        "bilgi_tabani_surumu": bilgi_tabani_surumu(kaynaklar),
        "belge_sayisi": len(kaynaklar),
        "atilan_karakter_orani": round(atilan_kar / (atilan_kar + kalan_kar), 4),
        "atilan_blok_kaliplari": dict(atilan_say.most_common()),
        "parca_turleri": dict(Counter(p.tur for p in parcalar)),
        "madde_basliksiz": [p.id for p in maddeler if not p.baslik],
        "madde_cok_sayfali": sum(p.sayfa_son > p.sayfa_bas for p in maddeler),
        "madde_uzunluk": {"min": min(uzunluklar), "p10": int(q[0]), "medyan": hedef,
                          "p90": int(q[-1]), "max": max(uzunluklar),
                          "2000_ustu": sum(x > 2000 for x in uzunluklar)},
        "paragraf_hedefi": hedef,
        "kaynak_turleri": dict(Counter(s["tur"] for s in kaynaklar)),
        "web_ogesi": web_ogesi,
        # aynı metni taşıyan farklı kaynaklar (aynı belge iki adreste olabilir)
        "ayni_metinli_kaynaklar": [v for v in ozetler.values() if len(v) > 1],
        "sorunlar": sorunlar,
    }
    RAPOR.parent.mkdir(exist_ok=True)
    RAPOR.write_text(json.dumps(rapor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
    print(f"\n{len(parcalar)} parça -> {CIKTI.relative_to(KOK)}")


if __name__ == "__main__":
    main()

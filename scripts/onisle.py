"""Ön işlem: PDF'leri temizler, maddelere böler, data/processed/'e yazar ve
sonucu denetler. Sonuç: results/onisleme.json, olcumler §4.

    uv run python scripts/onisle.py
"""

import csv
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

from mevzuat_rag.madde import madde_basliklari
from mevzuat_rag.onisleme import pdf_sayfalari
from mevzuat_rag.parcalama import madde_parcala, paragraf_parcala, takvim_parcala

KOK = Path(__file__).resolve().parents[1]
RAW = KOK / "data" / "raw"
CIKTI = KOK / "data" / "processed" / "parcalar_madde.jsonl"
RAPOR = KOK / "results" / "onisleme.json"
IZLER = ["Doküman No", "Form No", "Revizyon No", "Yayın Tarihi", "Revizyon Tarihi"]
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
    if p.tur in ("madde", "gecici"):
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
            if re.search(r"Sayfa\s+\d+\s*-\s*\d+", sy.metin):
                sorunlar.append(f"{s['belge_id']} s{sy.no}: temiz metinde 'Sayfa N-M' kaldı")

    madde_parcalari = {b: madde_parcala(b, sy) for b, sy in temiz.items()}
    uzunluklar = [len(p.metin) for ps in madde_parcalari.values() for p in ps
                  if p.tur in ("madde", "gecici")]
    hedef = int(statistics.median(uzunluklar))

    for b, ps in madde_parcalari.items():
        if not ps:  # madde yapısı yok (YÖ-0087)
            ps = paragraf_parcala(b, temiz[b], hedef)
            madde_parcalari[b] = ps
        # kapsama: parçalar temiz metnin tamamını kayıpsız ve tekrarsız örtmeli
        if bosluksuz("".join(p.metin for p in ps)) != bosluksuz("\n".join(x.metin for x in temiz[b])):
            sorunlar.append(f"{b}: parçalar temiz metni birebir örtmüyor")
        sayfa_metni = {x.no: bosluksuz(x.metin) for x in temiz[b]}
        for p in ps:
            if not aralik_dogru(p, sayfa_metni):
                sorunlar.append(f"{p.id}: sayfa aralığı {p.sayfa_bas}-{p.sayfa_son} tutmuyor")
        parcalar += ps

    takvim = next(s for s in kaynaklar if s["belge_id"] == "akademik-takvim")
    takvim_parcalari = takvim_parcala("akademik-takvim",
                                      (RAW / takvim["dosya"]).read_text(encoding="utf-8"))
    parcalar += takvim_parcalari

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    with CIKTI.open("w", encoding="utf-8", newline="\n") as f:
        for p in parcalar:
            f.write(json.dumps(p.sozluk(), ensure_ascii=False) + "\n")

    maddeler = [p for p in parcalar if p.tur in ("madde", "gecici")]
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
        "sorunlar": sorunlar,
    }
    RAPOR.parent.mkdir(exist_ok=True)
    RAPOR.write_text(json.dumps(rapor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
    print(f"\n{len(parcalar)} parça -> {CIKTI.relative_to(KOK)}")


if __name__ == "__main__":
    main()

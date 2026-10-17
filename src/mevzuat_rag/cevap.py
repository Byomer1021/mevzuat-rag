"""Üretilen cevapların ölçümü (K-005 pilotu ve demo): cevaplamama, atıf,
atıfların kanıtı kapsaması. Doğruluk elle puanlanır; bunun için tablo çıkar.
"""

from mevzuat_rag.degerlendirme import Kume, kanitlar
from mevzuat_rag.uretim import ayristir


def olc(sorular: list[dict], paket: list[dict], cevaplar: list[dict], kume: Kume,
        dayanak_parcalari: dict[str, dict]) -> tuple[dict, list[dict]]:
    """Döner: (özet, soru başına satırlar). `paket` istem paketinin satırları,
    `kume` paketin üretildiği parça kümesi."""
    soru = {s["id"]: s for s in sorular}
    cevap = {c["id"]: c for c in cevaplar}
    satirlar = []
    for p in paket:
        s, c = soru[p["id"]], cevap.get(p["id"])
        if c is None:
            continue
        a = ayristir(c["cevap"], p["kaynaklar"])
        cevapli = s["tur"] != "cevapsiz"
        kapsar = None
        if cevapli and not a["bilmiyorum"]:
            ks = kanitlar(s, dayanak_parcalari)
            kapsar = all(kume.kapsar_mi(k, a["atiflar"]) for k in ks)
        satirlar.append({
            "id": s["id"], "tur": s["tur"], "soru": s["soru"],
            "referans_cevap": s["referans_cevap"], "cevap": c["cevap"],
            "bilmiyorum": a["bilmiyorum"], "atiflar": a["atiflar"],
            "gecersiz_atif": a["gecersiz_atif"], "atifsiz": a["atifsiz"],
            "kanit_getirildi": all(kume.kapsar_mi(k, p["kaynaklar"])
                                   for k in kanitlar(s, dayanak_parcalari)) if cevapli else None,
            "atif_kaniti_kapsar": kapsar,
        })

    def oran(pay, payda):
        return round(pay / payda, 3) if payda else None

    cevapsiz = [r for r in satirlar if r["tur"] == "cevapsiz"]
    cevapli = [r for r in satirlar if r["tur"] != "cevapsiz"]
    konusan = [r for r in cevapli if not r["bilmiyorum"]]
    ozet = {
        "soru": len(satirlar), "eksik_cevap": len(paket) - len(satirlar),
        "cevapsiz": len(cevapsiz),
        "cevapsizda_bilmiyorum": oran(sum(r["bilmiyorum"] for r in cevapsiz), len(cevapsiz)),
        "cevapli": len(cevapli),
        "cevaplida_bilmiyorum": oran(sum(r["bilmiyorum"] for r in cevapli), len(cevapli)),
        # arama kanıtı getirdiği hâlde "bilmiyorum": modelin kaçırdığı
        "kanit_varken_bilmiyorum": sum(r["bilmiyorum"] and r["kanit_getirildi"] for r in cevapli),
        "atifsiz_cevap": oran(sum(r["atifsiz"] for r in konusan), len(konusan)),
        "gecersiz_atifli_cevap": sum(bool(r["gecersiz_atif"]) for r in satirlar),
        "atif_kaniti_kapsar": oran(sum(bool(r["atif_kaniti_kapsar"]) for r in konusan), len(konusan)),
    }
    return ozet, satirlar

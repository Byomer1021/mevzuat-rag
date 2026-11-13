"""Bölünme analizi: madde kazancının ne kadarı kanıtın pencereye bölünmemesinden?

    uv run python scripts/bolunme.py results/deney/e5-dev.json [--kume birincil] [--k 5]

Deney sonucundaki getirilen listelerden çalışır, yeniden arama yapmaz.
Çıktı: results/bolunme/<ad>.json ve .md. Ayrıntı: src/mevzuat_rag/bolunme.py.
"""

import argparse
import json
import sys
from pathlib import Path

from mevzuat_rag.bolunme import bolunmus_mu, gevsek_kapsam
from mevzuat_rag.degerlendirme import (
    Kume,
    bootstrap_araligi,
    eslestirilmis_bootstrap,
    kanitlar,
    kapsam,
    mcnemar,
)
from mevzuat_rag.deney import deney_parcalari
from mevzuat_rag.testset import oku, parcalari_oku

KOK = Path(__file__).resolve().parents[1]
ISLENMIS = KOK / "data" / "processed"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sonuc", type=Path)
    ap.add_argument("--kume", default="birincil")
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()

    r = json.loads(a.sonuc.read_text(encoding="utf-8"))
    madde = parcalari_oku(ISLENMIS / "parcalar_madde.jsonl")
    sabit = parcalari_oku(ISLENMIS / "parcalar_sabit.jsonl")
    kume = {"madde": Kume(deney_parcalari(madde)), "sabit": Kume(deney_parcalari(sabit))}
    dayanak = {p["id"]: p for p in madde}
    sorular = {s["id"]: s for s in oku(KOK / r["konfigurasyon"]["sorular"])}
    satirlar = r["sonuclar"][a.kume]["sorular"]
    kosullar = [k for k in ("madde", "sabit") if k in satirlar[0]]

    tablo = []
    for row in satirlar:
        ks = kanitlar(sorular[row["id"]], dayanak)
        x = {"id": row["id"], "bolunmus_sabit": bolunmus_mu(kume["sabit"], ks),
             "bolunmus_madde": bolunmus_mu(kume["madde"], ks)}
        for k in kosullar:
            ids = row[k]["getirilen"][:a.k]
            siki = kapsam(kume[k], ks, ids)
            if abs(siki - row[k]["kapsam"][str(a.k)]) > 1e-9:
                sys.exit(f"{row['id']} {k}: yeniden hesaplanan kapsam sonuç dosyasındakiyle aynı değil")
            x[k] = {"siki": siki, "gevsek": gevsek_kapsam(kume[k], ks, ids)}
        tablo.append(x)

    n = len(tablo)
    ozet = {"kaynak": str(a.sonuc.relative_to(KOK) if a.sonuc.is_relative_to(KOK) else a.sonuc),
            "kume": a.kume, "k": a.k, "n": n,
            "bolunmus_sabit": sum(x["bolunmus_sabit"] for x in tablo),
            "bolunmus_madde": sum(x["bolunmus_madde"] for x in tablo), "olcu": {}}
    for olcu in ("siki", "gevsek"):
        o = {k: bootstrap_araligi([x[k][olcu] for x in tablo]) for k in kosullar}
        if len(kosullar) == 2:
            m, s = ([x[k][olcu] for x in tablo] for k in kosullar)
            o["fark"] = eslestirilmis_bootstrap(m, s)
            o["mcnemar"] = mcnemar(m, s)
            yalniz_madde = [x["id"] for x in tablo if x["madde"][olcu] >= 1 and x["sabit"][olcu] < 1]
            o["yalniz_madde"] = yalniz_madde
            o["yalniz_madde_bolunmus"] = [q for q in yalniz_madde
                                          if next(x for x in tablo if x["id"] == q)["bolunmus_sabit"]]
        ozet["olcu"][olcu] = o

    hedef = KOK / "results" / "bolunme"
    hedef.mkdir(parents=True, exist_ok=True)
    ad = a.sonuc.stem + ("" if a.kume == "birincil" else f"-{a.kume}")
    (hedef / f"{ad}.json").write_text(json.dumps({"ozet": ozet, "sorular": tablo}, ensure_ascii=False,
                                                 indent=1) + "\n", encoding="utf-8")

    def ort(o):
        return f"{o['ortalama']:.3f} [{o['alt']:.3f}, {o['ust']:.3f}]"

    md = [f"# Bölünme analizi: {ad}", "",
          (f"Kaynak `{ozet['kaynak']}`, küme {a.kume}, n = {n}, R@{a.k}. Kanıtı pencere sınırında bölünen "
          f"soru: {ozet['bolunmus_sabit']} (madde koşulunda {ozet['bolunmus_madde']})."), "",
          "| ölçüt | " + " | ".join(kosullar) + (" | fark [95%] | McNemar (yalnız madde / yalnız sabit, p) |"
                                                 if len(kosullar) == 2 else " |"),
          "|---|" + "---|" * len(kosullar) + ("---|---|" if len(kosullar) == 2 else "")]
    for olcu, adi in (("siki", "sıkı (kanıt tam kapsanmalı)"), ("gevsek", "gevşek (örtüşen bir parça yeter)")):
        o = ozet["olcu"][olcu]
        satir = f"| {adi} | " + " | ".join(ort(o[k]) for k in kosullar) + " |"
        if len(kosullar) == 2:
            f, mc = o["fark"], o["mcnemar"]
            satir += (f" {f['fark']:+.3f} [{f['alt']:+.3f}, {f['ust']:+.3f}] | {mc['yalniz_a']} / {mc['yalniz_b']}, "
                      f"p = {mc['p']:.3f} |")
        md.append(satir)
    if len(kosullar) == 2:
        s = ozet["olcu"]["siki"]
        md += ["", (f"Sıkı ölçütte yalnız maddenin bulduğu {len(s['yalniz_madde'])} sorudan kanıtı bölünmüş olan: "
               f"{len(s['yalniz_madde_bolunmus'])} ({', '.join(s['yalniz_madde_bolunmus']) or '-'}).")]
    (hedef / f"{ad}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

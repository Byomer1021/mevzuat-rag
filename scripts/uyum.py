"""Etiket uyumu (K-026): örneklem, ikinci etiketlerin alınması, hesap.

    uv run python scripts/uyum.py ornek                  # 40 soruyu seçer, listeleri yazar
    uv run python scripts/uyum.py al veysel defter.json  # Soru Defteri dışa aktarımını alır
    uv run python scripts/uyum.py hesapla                # results/uyum.json ve uyum.md

Veysel, Muhammed'in yazdığı 20 test sorusunu, Muhammed de Veysel'in 20
sorusunu etiketler. İkinci etiketçi altın etiketi görmez. Etiketleme
talimatı: docs/uyum-etiketleme.md.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from mevzuat_rag.testset import dogrula, dondurma_denetle, oku, parcalari_oku
from mevzuat_rag.uyum import KANIT_ESIK, karsilastir, ornek_sec, ozetle

KOK = Path(__file__).resolve().parents[1]
SORULAR = KOK / "data" / "testset" / "sorular.jsonl"
DONDURMA = KOK / "data" / "testset" / "dondurma.json"
KLASOR = KOK / "data" / "uyum"
ORNEK = KLASOR / "ornek.json"
TOHUM = 0
ATAMA = {"veysel": "muhammed", "muhammed": "veysel"}  # etiketçi: kimin sorularını etiketler
SAYILAR = {"tek": 14, "cok": 3, "cevapsiz": 3}
ADLAR = {"veysel": "Veysel", "muhammed": "Muhammed"}


def kucuk(s: str) -> str:
    return " ".join(s.replace("I", "ı").replace("İ", "i").lower().split())


def test_sorulari() -> list[dict]:
    sorular = oku(SORULAR)
    dondurma = json.loads(DONDURMA.read_text(encoding="utf-8")) if DONDURMA.exists() else None
    if sorun := dondurma_denetle(sorular, dondurma):
        sys.exit(sorun)
    return sorular


def ornek(args):
    if ORNEK.exists() and not args.yeniden:
        sys.exit(f"{ORNEK.relative_to(KOK)} zaten var. Etiketler görülmeden önce seçildi, yeniden "
                 "seçmek için --yeniden.")
    sorular = test_sorulari()
    konum = {s["id"]: s for s in sorular}
    atama = {kisi: ornek_sec(sorular, yazan, SAYILAR, TOHUM) for kisi, yazan in ATAMA.items()}
    KLASOR.mkdir(parents=True, exist_ok=True)
    ORNEK.write_text(json.dumps({
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "tohum": TOHUM, "sayilar": SAYILAR,
        "test_ozeti": json.loads(DONDURMA.read_text(encoding="utf-8"))["ozet"], "atama": atama,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for kisi, idler in atama.items():
        satirlar = [f"{ADLAR[kisi]} için {len(idler)} soru. Talimat: docs/uyum-etiketleme.md", ""]
        satirlar += [f"{i}. {q}  {konum[q]['soru']}" for i, q in enumerate(idler, 1)]
        (KLASOR / f"liste_{kisi}.txt").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
        print(f"{kisi}: {len(idler)} soru -> data/uyum/liste_{kisi}.txt")


def disari_aktarim(yol: Path) -> list[dict]:
    metin = yol.read_text(encoding="utf-8-sig").strip()
    if metin.startswith("["):
        return json.loads(metin)
    return [json.loads(s) for s in metin.splitlines() if s.strip()]


def al(args):
    kisi = args.kisi
    atanan = json.loads(ORNEK.read_text(encoding="utf-8"))["atama"][kisi]
    sorular = {s["id"]: s for s in oku(SORULAR)}
    metinden = {kucuk(sorular[q]["soru"]): q for q in atanan}
    parcalar = {p["id"]: p["metin"] for p in parcalari_oku(KOK / "data" / "processed" / "parcalar_madde.jsonl")}
    alinan, rapor = {}, []
    for yol in args.dosyalar:
        for g in disari_aktarim(Path(yol)):
            etiket = [e for e in g.get("etiketler", []) if re.fullmatch(r"q\d{3}", e.strip().lower())]
            qid = next((e.strip().lower() for e in etiket if e.strip().lower() in atanan), None)
            qid = qid or metinden.get(kucuk(g.get("soru", "")))
            if qid is None:
                continue
            aday = {"id": qid, "soru": g["soru"], "tur": g.get("tur"), "dayanak": g.get("dayanak", []),
                    "kanit": g.get("kanit", []), "etiketler": [], "yazan": kisi, "bolum": "test",
                    "referans_cevap": "" if g.get("tur") == "cevapsiz" else "-"}
            if hatalar := dogrula(aday, parcalar):
                rapor.append(f"{qid} alınmadı: {'; '.join(hatalar)}")
                continue
            if qid in alinan and alinan[qid]["guncelleme"] >= g.get("guncelleme", ""):
                continue
            alinan[qid] = {"id": qid, "tur": aday["tur"], "dayanak": aday["dayanak"], "kanit": aday["kanit"],
                           "yazan": kisi, "guncelleme": g.get("guncelleme", "")}
    eksik = [q for q in atanan if q not in alinan]
    hedef = KLASOR / f"{kisi}.jsonl"
    hedef.write_text("".join(json.dumps(alinan[q], ensure_ascii=False) + "\n" for q in atanan if q in alinan),
                     encoding="utf-8")
    print("\n".join(rapor))
    print(f"{kisi}: {len(alinan)}/{len(atanan)} soru alındı -> {hedef.relative_to(KOK)}"
          + (f"; eksik: {', '.join(eksik)}" if eksik else ""))


def yuzde(o: dict) -> str:
    if o["oran"] is None:
        return "tanımsız (n = 0)"
    return f"{o['oran']:.0%} [{o['alt']:.0%}, {o['ust']:.0%}] (n = {o['n']})"


def kappa(o: dict) -> str:
    k = "tanımsız" if o["kappa"] is None else f"{o['kappa']:.2f}"
    return f"{k} [{o['alt']:.2f}, {o['ust']:.2f}], ham uyum {o['ham_uyum']:.0%} (n = {o['n']})"


def hesapla(args):
    ornek_ = json.loads(ORNEK.read_text(encoding="utf-8"))
    sorular = {s["id"]: s for s in test_sorulari()}
    parcalar = {p["id"]: p["metin"] for p in parcalari_oku(KOK / "data" / "processed" / "parcalar_madde.jsonl")}
    karsilastirmalar, eksik = [], []
    for kisi, idler in ornek_["atama"].items():
        yol = KLASOR / f"{kisi}.jsonl"
        ikinci = {}
        if yol.exists():
            ikinci = {g["id"]: g for g in map(json.loads, yol.read_text(encoding="utf-8").splitlines()) if g}
        for q in idler:
            if q in ikinci:
                karsilastirmalar.append(dict(karsilastir(sorular[q], ikinci[q], parcalar), etiketci=kisi))
            else:
                eksik.append(q)
    if not karsilastirmalar:
        sys.exit("hiç ikinci etiket yok: önce `uyum.py al`")
    ozet = ozetle(karsilastirmalar, tohum=TOHUM)
    (KOK / "results" / "uyum.json").write_text(json.dumps(
        {"ornek": ornek_, "eksik": eksik, "ozet": ozet, "sorular": karsilastirmalar},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    satirlar = [
        "# Etiket uyumu (K-026)", "",
        f"Örneklem {ORNEK.relative_to(KOK).as_posix()} ({ornek_['tarih']}, tohum {ornek_['tohum']}), "
        f"karşılaştırılan {ozet['n']} soru" + (f", etiketi gelmeyen {len(eksik)}: {', '.join(eksik)}" if eksik else "")
        + ". Altın: dondurulmuş test seti. İkinci: soruyu yazmamış ekip üyesi. Aralıklar 10 000 bootstrap, "
        f"tohum {TOHUM}.", "",
        "| ölçü | değer |", "|---|---|",
        f"| cevaplanabilirlik, Cohen's κ | {kappa(ozet['cevaplanabilirlik'])} |",
        f"| soru türü (tek/çok/cevapsız), Cohen's κ | {kappa(ozet['tur'])} |",
        f"| ikisinin de cevaplı dediği soru | {ozet['ikisi_cevapli']} |",
        f"| aynı madde kümesi | {yuzde(ozet['ayni_madde'])} |",
        f"| en az bir ortak madde | {yuzde(ozet['ortak_madde'])} |",
        f"| en az bir ortak belge | {yuzde(ozet['ortak_belge'])} |",
        f"| ortak maddede aynı kanıt cümlesi (örtüşme ≥ {KANIT_ESIK:.0%}) | {yuzde(ozet['ayni_kanit_ortak_maddede'])} |",
        "", "## Uyuşmayanlar", "",
        "| soru | etiketçi | tür (altın / ikinci) | dayanak altın | dayanak ikinci |", "|---|---|---|---|---|",
    ]
    for x in karsilastirmalar:
        if x["tur_altin"] != x["tur_ikinci"] or (x.get("ortak_madde") is False) or x.get("ayni_kanit") is False:
            satirlar.append(f"| {x['id']} | {x['etiketci']} | {x['tur_altin']} / {x['tur_ikinci']} | "
                            f"{', '.join(x['dayanak_altin']) or '-'} | {', '.join(x['dayanak_ikinci']) or '-'} |")
    (KOK / "results" / "uyum.md").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print("\n".join(satirlar[:14]))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    alt = ap.add_subparsers(dest="komut", required=True)
    o = alt.add_parser("ornek")
    o.add_argument("--yeniden", action="store_true")
    o.set_defaults(f=ornek)
    a = alt.add_parser("al")
    a.add_argument("kisi", choices=sorted(ATAMA))
    a.add_argument("dosyalar", nargs="+")
    a.set_defaults(f=al)
    alt.add_parser("hesapla").set_defaults(f=hesapla)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()

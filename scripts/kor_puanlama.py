"""Model ve düzen adı gizli, karışık sıralı elle doğruluk puanlaması (K-005 pilotu).

    uv run python scripts/kor_puanlama.py olustur results/cevap/A.json results/cevap/B.json ...
    uv run python scripts/kor_puanlama.py hesapla

olustur: cevap_ozet.py çıktılarındaki bütün cevapları tek bir Excel
tablosunda karıştırır, model ve düzen adını çıkarır:
results/cevap/kor_puanlama.xlsx. Hangi satırın nereden geldiği
results/cevap/kor_anahtar.json'da (puanlayan açmasın). Puanlayan "Puan"
sütununda açılır listeden doğru / kısmen / yanlış seçer.

hesapla: doldurulmuş tabloyu anahtarla birleştirir, model ve düzen başına
sayar: results/cevap/kor_sonuc.json.
"""

import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

KOK = Path(__file__).resolve().parents[1]
KLASOR = KOK / "results" / "cevap"
TABLO, ANAHTAR = KLASOR / "kor_puanlama.xlsx", KLASOR / "kor_anahtar.json"
TOHUM = 0
PUANLAR = {"doğru": "dogru", "dogru": "dogru", "kısmen": "kismen", "kismen": "kismen",
           "yanlış": "yanlis", "yanlis": "yanlis"}
SUTUNLAR = [("No", 6), ("Soru", 38), ("Olması gereken cevap", 45), ("Modelin cevabı", 80), ("Puan", 12),
            ("Not (isteğe bağlı)", 28)]
CEVAPSIZ = "Bu sorunun cevabı belgelerde yok. Doğru davranış: 'bilmiyorum' demek."
TALIMAT = [
    "Her satırda bir soru, olması gereken cevap ve modelin cevabı var.",
    "Puan sütununda açılır listeden seç:",
    "  doğru  = olması gereken cevaptaki bilgiyi veriyor. Fazladan doğru bilgi sorun değil.",
    "  kısmen = bilginin bir kısmı eksik ya da yanında yanlış bir şey söylüyor.",
    "  yanlış = yanlış ya da ilgisiz cevap. Cevabı olan soruda 'bilmiyorum' demesi de yanlış.",
    ("Cevabı olmayan sorularda (olması gereken cevapta yazıyor): 'bilmiyorum' dediyse doğru, "
    "bir cevap uydurduysa yanlış."),
    "Cevaptaki [1], [2] gibi numaralar kaynak numarası, puanlarken görmezden gel.",
    ("Aynı soru birkaç kez gelecek, her seferinde farklı bir modelin ya da ayarın cevabı. Hangisi "
    "olduğu bilerek gizlendi."),
    "Emin olamadığın satıra en yakın puanı ver, istersen nota bir şey yaz.",
    "Bitince dosyayı kaydet, kapat. Sonra: uv run python scripts/kor_puanlama.py hesapla",
]


def satir_yuksekligi(degerler: list[str]) -> float:
    satirlar = max(sum(math.ceil(max(len(p), 1) / (genislik * 1.15)) for p in str(d).split("\n"))
                   for d, (_, genislik) in zip(degerler, SUTUNLAR, strict=True))
    return min(15 * max(satirlar, 1) + 4, 409)


def olustur(yollar: list[Path], tablo: Path = TABLO, anahtar_yolu: Path = ANAHTAR, yeniden: bool = False):
    if tablo.exists() and not yeniden:
        sys.exit(f"{tablo} zaten var; puanlama başladıysa ezilmesin. Yeniden üretmek için --yeniden.")
    satirlar = []
    for yol in yollar:
        d = json.loads(yol.read_text(encoding="utf-8"))
        kaynak = f"{d['uretim'].get('model') or yol.stem} | {d['paket'].get('ad', '?')}"
        satirlar += [{"kaynak": kaynak, **r} for r in d["sorular"]]
    random.Random(TOHUM).shuffle(satirlar)

    wb = Workbook()
    ws = wb.active
    ws.title = "puanla"
    ws.append([ad for ad, _ in SUTUNLAR])
    for i, (_, genislik) in enumerate(SUTUNLAR, 1):
        ws.column_dimensions[chr(64 + i)].width = genislik
    anahtar = {}
    for no, r in enumerate(satirlar, 1):
        ref = CEVAPSIZ if r["tur"] == "cevapsiz" else r["referans_cevap"]
        degerler = [no, r["soru"], ref, r["cevap"], "", ""]
        ws.append(degerler)
        ws.row_dimensions[no + 1].height = satir_yuksekligi([str(x) for x in degerler])
        anahtar[str(no)] = {"kaynak": r["kaynak"], "id": r["id"], "tur": r["tur"]}
    sarmala = Alignment(wrap_text=True, vertical="top")
    sari = PatternFill("solid", fgColor="FFF2B3")
    for satir in ws.iter_rows(min_row=1):
        for h in satir:
            h.alignment = sarmala
        if satir[0].row > 1:
            satir[4].fill = sari
    for h in ws[1]:
        h.font = Font(bold=True)
    ws.freeze_panes = "B2"
    liste = DataValidation(type="list", formula1='"doğru,kısmen,yanlış"', allow_blank=True,
                           showErrorMessage=True, errorTitle="Geçersiz puan",
                           error="Listeden seç: doğru, kısmen ya da yanlış")
    ws.add_data_validation(liste)
    liste.add(f"E2:E{len(satirlar) + 1}")
    nasil = wb.create_sheet("nasıl")
    for metin in TALIMAT:
        nasil.append([metin])
    nasil.column_dimensions["A"].width = 120
    wb.move_sheet("nasıl", offset=-1)
    wb.active = 1
    tablo.parent.mkdir(parents=True, exist_ok=True)
    wb.save(tablo)
    anahtar_yolu.write_text(json.dumps({"tohum": TOHUM, "satirlar": anahtar}, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
    print(f"{len(satirlar)} cevap -> {tablo} (anahtar ayrı: {anahtar_yolu.name})")


def hesapla(tablo: Path = TABLO, anahtar_yolu: Path = ANAHTAR) -> dict:
    anahtar = json.loads(anahtar_yolu.read_text(encoding="utf-8"))["satirlar"]
    ws = load_workbook(tablo, read_only=True)["puanla"]
    sayim, bos, gecersiz = {}, [], []
    for no, *_, puan, _not in ws.iter_rows(min_row=2, values_only=True):
        if no is None:
            continue
        p = PUANLAR.get(str(puan or "").strip().lower())
        if not str(puan or "").strip():
            bos.append(no)
            continue
        if p is None:
            gecersiz.append((no, puan))
            continue
        a = anahtar[str(no)]
        tur = "cevapsiz" if a["tur"] == "cevapsiz" else "cevapli"
        sayim.setdefault(a["kaynak"], {"cevapli": Counter(), "cevapsiz": Counter()})[tur][p] += 1
    sonuc = {k: {t: dict(c) for t, c in v.items()} for k, v in sorted(sayim.items())}
    cikti = {"sonuc": sonuc, "bos": bos, "gecersiz": gecersiz}
    (tablo.parent / "kor_sonuc.json").write_text(json.dumps(cikti, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
    for k, v in sonuc.items():
        print(k, v)
    if bos or gecersiz:
        print(f"puanlanmamış {len(bos)} satır; geçersiz değer: {gecersiz}")
    return cikti


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if a != "--yeniden"]
    if len(args) >= 2 and args[0] == "olustur":
        olustur([Path(p) for p in args[1:]], yeniden="--yeniden" in sys.argv)
    elif args == ["hesapla"]:
        hesapla()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

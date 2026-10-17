"""docs/oneri.md'yi dersin öneri formuna (docx) yazar.

    uv run --with python-docx python scripts/oneri_docx.py SABLON.docx CIKTI.docx [punto]

Şablon dersin Teams'teki NLP_Project_Proposal_Template_2026Fall.docx dosyası;
depoya girmez. Şablonun yönerge kısmı silinir, çıktı "Proposal form"
başlığından başlar. Kutuların sabit yüksekliği kaldırılır, metin kadar uzar;
iki sayfa sınırı PDF'e çevirdikten sonra kontrol edilmeli.
"""

import re
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml.ns import qn
from docx.shared import Pt

KOK = Path(__file__).resolve().parents[1]
KAYNAK = KOK / "docs" / "oneri.md"
# anahtar → (tablo, satır, sütun); tablo numaraları şablondaki sırayla
KUTULAR = {"team": (3, 0, 1), "members": (3, 1, 1),
           **{str(i): (3 + i, 1, 0) for i in range(1, 11)}}
TURLER = ("Model", "Evaluation", "System")


def bolumler(md: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for blok in re.split(r"^## ", md, flags=re.MULTILINE)[1:]:
        anahtar, _, govde = blok.partition("\n")
        paragraflar = [" ".join(s.strip() for s in p.splitlines() if s.strip())
                       for p in re.split(r"\n\s*\n", govde) if p.strip()]
        out[anahtar.strip()] = paragraflar
    return out


def yaz(hucre, paragraflar: list[str], punto: float) -> None:
    ilk = hucre.paragraphs[0]
    for p in hucre.paragraphs[1:]:
        p._element.getparent().remove(p._element)
    for r in list(ilk.runs):
        r._element.getparent().remove(r._element)
    for i, metin in enumerate(paragraflar):
        p = ilk if i == 0 else hucre.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        metin = metin.replace("`", "")
        for parca in re.split(r"(\*\*.+?\*\*|\*[^*]+?\*)", metin):
            if not parca:
                continue
            if parca.startswith("**"):
                run = p.add_run(parca[2:-2])
                run.bold = True
            elif parca.startswith("*"):
                run = p.add_run(parca[1:-1])
                run.italic = True
            else:
                run = p.add_run(parca)
            run.font.size = Pt(punto)


def tur_isaretle(hucre, tur: str) -> None:
    """'☐ System' → '☒ System'. Kutu ve ad ayrı run'larda olabilir."""
    son_kutu = None
    for p in hucre.paragraphs:
        for r in p.runs:
            if "☐" in r.text:
                son_kutu = r
            if tur in r.text and son_kutu is not None:
                i = son_kutu.text.rfind("☐")
                son_kutu.text = son_kutu.text[:i] + "☒" + son_kutu.text[i + 1:]
                return
    raise ValueError(f"proje türü bulunamadı: {tur}")


def main():
    sablon, cikti = Path(sys.argv[1]), Path(sys.argv[2])
    punto = float(sys.argv[3]) if len(sys.argv) > 3 else 9
    b = bolumler(KAYNAK.read_text(encoding="utf-8"))
    d = docx.Document(sablon)

    govde = d.element.body
    elemanlar = list(govde.iterchildren())
    # itertext() alternatif içerikteki kopyaları da verir; yalnız w:t'lere bakılır
    bas = next((i for i, el in enumerate(elemanlar) if el.tag == qn("w:p")
                and "".join(t.text or "" for t in el.iter(qn("w:t"))).strip() == "Proposal form"),
               None)
    if bas is None:
        raise ValueError("şablonda 'Proposal form' başlığı yok")
    for el in elemanlar[:bas]:
        govde.remove(el)
    baslik = elemanlar[bas]
    for br in list(baslik.iter(qn("w:br"))):
        br.getparent().remove(br)
    ppr = baslik.find(qn("w:pPr"))
    if ppr is not None and (pb := ppr.find(qn("w:pageBreakBefore"))) is not None:
        ppr.remove(pb)

    for anahtar, (t, s, c) in KUTULAR.items():
        hucre = d.tables[t - 3].rows[s].cells[c]
        yaz(hucre, b[anahtar], punto)
        if anahtar not in ("team", "members"):
            satir = d.tables[t - 3].rows[s]
            satir.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
            satir.height = Pt(14)
    tur = b["type"][0]
    if tur not in TURLER:
        raise ValueError(f"type şunlardan biri olmalı: {TURLER}")
    tur_isaretle(d.tables[0].rows[2].cells[1], tur)
    d.save(cikti)
    print(f"{cikti} ({punto} punto)")


if __name__ == "__main__":
    main()

"""Test seti: şema denetimi, okuma, ekleme, dağılım özeti.

Şema: data/README.md. Dayanak, parça kimliğiyle verilir (K-014); denetim
kimliğin parcalar_madde.jsonl'da gerçekten var olduğuna da bakar.
"""

import json
from collections import Counter
from pathlib import Path

TURLER = ("tek", "cok", "cevapsiz")
BOLUMLER = ("dev", "test")
# Hata analizi kırılımları için öneri; serbest etiket de olur.
ETIKET_ONERILERI = ("tarih", "sure", "sayi", "not", "istisna", "kosul", "tanim", "basvuru")
ALANLAR = ("id", "soru", "tur", "referans_cevap", "dayanak", "etiketler", "yazan", "bolum")


def parcalari_oku(yol: Path) -> list[dict]:
    with yol.open(encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


def oku(yol: Path) -> list[dict]:
    if not yol.exists():
        return []
    with yol.open(encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


def yeni_id(sorular: list[dict]) -> str:
    sayilar = [int(s["id"][1:]) for s in sorular if s.get("id", "").startswith("q")]
    return f"q{max(sayilar, default=0) + 1:03d}"


def dogrula(soru: dict, parca_idleri: set[str], mevcut_idler: set[str] = frozenset()) -> list[str]:
    hatalar = []
    eksik = [a for a in ALANLAR if a not in soru]
    if eksik:
        return [f"eksik alan: {', '.join(eksik)}"]
    if soru["id"] in mevcut_idler:
        hatalar.append(f"{soru['id']} zaten var")
    if not soru["soru"].strip():
        hatalar.append("soru boş")
    if soru["tur"] not in TURLER:
        hatalar.append(f"tur şunlardan biri olmalı: {', '.join(TURLER)}")
    if soru["bolum"] not in BOLUMLER:
        hatalar.append(f"bolum şunlardan biri olmalı: {', '.join(BOLUMLER)}")
    dayanak = soru["dayanak"]
    bilinmeyen = [d for d in dayanak if d not in parca_idleri]
    if bilinmeyen:
        hatalar.append(f"bilinmeyen parça: {', '.join(bilinmeyen)}")
    if len(set(dayanak)) != len(dayanak):
        hatalar.append("dayanakta tekrar var")
    if soru["tur"] == "tek" and len(dayanak) != 1:
        hatalar.append("tek maddeli soruda dayanak tam bir parça olmalı")
    if soru["tur"] == "cok" and len(dayanak) < 2:
        hatalar.append("çok maddeli soruda en az iki dayanak olmalı")
    if soru["tur"] == "cevapsiz":
        if dayanak:
            hatalar.append("cevapsız soruda dayanak boş olmalı")
        if soru["referans_cevap"].strip():
            hatalar.append("cevapsız soruda referans cevap boş olmalı")
    elif not soru["referans_cevap"].strip():
        hatalar.append("referans cevap boş")
    return hatalar


def ekle(yol: Path, soru: dict) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({a: soru[a] for a in ALANLAR}, ensure_ascii=False) + "\n")


def ozet(sorular: list[dict]) -> dict:
    belgeler = Counter(d.split("/")[0] for s in sorular for d in set(s["dayanak"]))
    return {
        "toplam": len(sorular),
        "tur": dict(Counter(s["tur"] for s in sorular)),
        "bolum": dict(Counter(s["bolum"] for s in sorular)),
        "belge": dict(belgeler.most_common()),
        "etiket": dict(Counter(e for s in sorular for e in s["etiketler"]).most_common()),
    }

"""Test seti: şema denetimi, okuma, ekleme, dağılım özeti.

Şema: data/README.md. Dayanak, parça kimliğiyle verilir (K-014); denetim
kimliğin parcalar_madde.jsonl'da gerçekten var olduğuna da bakar.

Her dayanağın yanında bir kanıt alıntısı var: cevabı taşıyan cümle, parçanın
metninden birebir. Sabit uzunluklu parçalar madde sınırına uymadığı için
"doğru parça geldi mi" sorusu kimlikle değil bu alıntıyla cevaplanır
(degerlendirme.py, K-022). Alıntı boşluk farkı gözetmeden aranır; satır sonu
ile boşluk aynı sayılır.
"""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

TURLER = ("tek", "cok", "cevapsiz")
BOLUMLER = ("dev", "test")
# Hata analizi kırılımları için öneri; serbest etiket de olur.
ETIKET_ONERILERI = ("tarih", "sure", "sayi", "not", "istisna", "kosul", "tanim", "basvuru")
ALANLAR = ("id", "soru", "tur", "referans_cevap", "dayanak", "kanit", "etiketler", "yazan",
           "bolum")
KANIT_MIN = 20  # karakter; "%70" gibi tek başına bir değer kanıt değil, cümlesi gerekir


def alinti_kalibi(alinti: str) -> re.Pattern:
    return re.compile(r"\s+".join(re.escape(t) for t in alinti.split()))


def kanitlari_ayir(metin: str) -> list[str]:
    """Formdaki kanıt kutusu: dayanak sırasıyla, aralarında boş satır."""
    return [k.strip() for k in re.split(r"\n\s*\n", metin) if k.strip()]


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


def dogrula(soru: dict, parcalar: dict[str, str], mevcut_idler: set[str] = frozenset()) -> list[str]:
    """parcalar: kimlik → metin."""
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
    bilinmeyen = [d for d in dayanak if d not in parcalar]
    if bilinmeyen:
        hatalar.append(f"bilinmeyen parça: {', '.join(bilinmeyen)}")
    if len(set(dayanak)) != len(dayanak):
        hatalar.append("dayanakta tekrar var")
    if soru["tur"] == "tek" and len(dayanak) != 1:
        hatalar.append("tek maddeli soruda dayanak tam bir parça olmalı")
    if soru["tur"] == "cok" and len(dayanak) < 2:
        hatalar.append("çok maddeli soruda en az iki dayanak olmalı")
    kanit = soru["kanit"]
    if soru["tur"] == "cevapsiz":
        if dayanak:
            hatalar.append("cevapsız soruda dayanak boş olmalı")
        if kanit:
            hatalar.append("cevapsız soruda kanıt boş olmalı")
        if soru["referans_cevap"].strip():
            hatalar.append("cevapsız soruda referans cevap boş olmalı")
        return hatalar
    if not soru["referans_cevap"].strip():
        hatalar.append("referans cevap boş")
    if len(kanit) != len(dayanak):
        hatalar.append(f"her dayanak için bir kanıt alıntısı olmalı: {len(dayanak)} dayanak, "
                       f"{len(kanit)} kanıt")
        return hatalar
    for d, k in zip(dayanak, kanit, strict=True):
        if len(k.strip()) < KANIT_MIN:
            hatalar.append(f"{d}: kanıt en az {KANIT_MIN} karakter olmalı (cümlenin kendisi)")
        elif d in parcalar and not alinti_kalibi(k).search(parcalar[d]):
            hatalar.append(f"{d}: kanıt bu parçanın metninde birebir yok")
    return hatalar


def ekle(yol: Path, soru: dict) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({a: soru[a] for a in ALANLAR}, ensure_ascii=False) + "\n")


def hepsini_yaz(yol: Path, sorular: list[dict]) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("w", encoding="utf-8", newline="\n") as f:
        for s in sorular:
            f.write(json.dumps({a: s[a] for a in ALANLAR}, ensure_ascii=False) + "\n")


def iceri_al(mevcut: list[dict], gelenler: list[dict], parcalar: dict[str, str],
             defter: dict[str, str]) -> tuple[list[dict], dict[str, str], list[str]]:
    """Soru defterinden (app/soru_defteri.html) dışa aktarılan soruları katar.

    Defterde her soru tarayıcıda yazıldığı anki `yerel_id`'yi taşır; `defter`
    yerel_id → test setindeki kimlik eşlemesidir. Aynı satır iki kez gelirse
    atlanır, defterde sonradan düzenlenmişse test setindeki soru yerinde
    güncellenir (kimliği değişmez). Şemaya uymayan soru alınmaz ve raporda
    nedeniyle yazılır. Döner: (yeni liste, yeni defter, rapor satırları).
    """
    sorular = [dict(s) for s in mevcut]
    defter = dict(defter)
    konum = {s["id"]: i for i, s in enumerate(sorular)}
    rapor = []
    for g in gelenler:
        yid = g.get("yerel_id")
        if not yid:
            rapor.append(f"atlandı, yerel_id yok: {str(g.get('soru', ''))[:50]}")
            continue
        qid = defter.get(yid)
        aday = {a: g.get(a) for a in ALANLAR if a != "id"}
        aday["id"] = qid or yeni_id(sorular)
        diger = {s["id"] for s in sorular} - {aday["id"]}
        if hatalar := dogrula(aday, parcalar, diger):
            rapor.append(f"alınmadı ({g.get('yazan', '?')}): {aday['soru'][:60]!r}: "
                         + "; ".join(hatalar))
            continue
        if qid is None:
            sorular.append({a: aday[a] for a in ALANLAR})
            konum[aday["id"]] = len(sorular) - 1
            defter[yid] = aday["id"]
            rapor.append(f"{aday['id']} eklendi ({aday['yazan']})")
        elif {a: aday[a] for a in ALANLAR} == {a: sorular[konum[qid]][a] for a in ALANLAR}:
            rapor.append(f"{qid} zaten var, aynı")
        else:
            sorular[konum[qid]] = {a: aday[a] for a in ALANLAR}
            rapor.append(f"{qid} güncellendi ({aday['yazan']})")
    return sorular, defter, rapor


def bolum_ozeti(sorular: list[dict], bolum: str) -> str:
    """Bir bölümün soruları değişti mi? Kimliğe göre sıralı, alan sırası sabit JSON'un sha256'sı."""
    secili = sorted((s for s in sorular if s["bolum"] == bolum), key=lambda s: s["id"])
    metin = "\n".join(json.dumps({k: s.get(k) for k in ALANLAR}, ensure_ascii=False) for s in secili)
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def dondurma_denetle(sorular: list[dict], dondurma: dict | None) -> str | None:
    """Test seti dondurulmuş ve dondurulduğu hâlinde mi? Sorun varsa açıklaması, yoksa None."""
    if dondurma is None:
        return "test seti dondurulmadı: önce scripts/test_dondur.py"
    simdiki = bolum_ozeti(sorular, "test")
    if simdiki != dondurma["ozet"]:
        n = sum(s["bolum"] == "test" for s in sorular)
        return (f"test seti dondurulduğu hâlinde değil: {dondurma['tarih']} tarihinde "
                f"{dondurma['n']} soru, özet {dondurma['ozet'][:12]}; şimdi {n} soru, "
                f"özet {simdiki[:12]}")
    return None


def ozet(sorular: list[dict]) -> dict:
    belgeler = Counter(d.split("/")[0] for s in sorular for d in set(s["dayanak"]))
    return {
        "toplam": len(sorular),
        "tur": dict(Counter(s["tur"] for s in sorular)),
        "bolum": dict(Counter(s["bolum"] for s in sorular)),
        "belge": dict(belgeler.most_common()),
        "etiket": dict(Counter(e for s in sorular for e in s["etiketler"]).most_common()),
    }

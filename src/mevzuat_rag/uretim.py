"""Cevap üretimi: istem, kaynak biçimi, cevabın ayrıştırılması (K-005).

Modelden bağımsız. Arama burada (CPU) çalışır ve her soru için hazır bir
istem paketi yazılır (scripts/istem_paketi.py); model Colab'da çalışır
(notebooks/cevap_uret.ipynb) ve cevapları geri verir.

Model kaynakları numarayla anar: "[2]". Numara parçaya, parça kullanıcıya
gösterilen künyeye ("Lisans Yönetmeliği, Madde 23, s. 5") çevrilir. Cevap
yoksa model sabit bir cümleyle başlar; cevaplamama bununla ölçülür.
"""

import re

from mevzuat_rag.arama import kucult

BILMIYORUM = "BİLMİYORUM"
_BILMIYORUM = re.compile(r"b[iı]lm[iı]yorum\s*[:.!]")
SISTEM = (
    "Gebze Teknik Üniversitesi'nin lisans mevzuatıyla ilgili öğrenci sorularını cevaplıyorsun.\n"
    "Kurallar:\n"
    "1. Yalnız aşağıda numaralı verilen kaynaklara dayan; kendi bilgini kullanma.\n"
    "2. Her cümlenin sonuna dayandığı kaynağın numarasını köşeli parantezle yaz: [1], [2].\n"
    f"3. Kaynaklarda cevap yoksa yalnız şunu yaz: {BILMIYORUM}: Bu bilgi elimdeki belgelerde yok.\n"
    "4. Kısa yaz. Sayı, süre, oran ve koşulları kaynaktaki gibi aktar.\n"
    "5. Kaynaklar farklı öğrenci grupları ya da programlar için farklı kurallar veriyorsa "
    "ve soru hangisini sorduğunu belirtmiyorsa, farkı söyle."
)
SAYFALI = ("madde", "gecici", "ek", "giris", "paragraf", "sabit")
_ATIF = re.compile(r"\[(\d{1,2})\]")


def kunye(p: dict, belge_adlari: dict[str, str]) -> str:
    """Kaynağın kullanıcıya gösterilen adı."""
    ad = belge_adlari.get(p["belge_id"], p["belge_id"])
    if p["tur"] == "web":
        parcalar = [p.get("bolum") or "", p.get("baslik") or "", p.get("tarih") or ""]
        return " · ".join(x for x in parcalar if x) or ad
    if p["tur"] == "takvim":
        return f"{ad} · {p.get('bolum') or 'takvim'}"
    if p["tur"] == "form":
        return f"{ad} · {p.get('baslik') or ''}"
    yer = []
    if p.get("madde"):
        yer.append(f"Madde {p['madde']}" + (f" ({p['baslik']})" if p.get("baslik") else ""))
    if p["tur"] in SAYFALI and p.get("sayfa_bas"):
        s1, s2 = p["sayfa_bas"], p.get("sayfa_son", p["sayfa_bas"])
        yer.append(f"s. {s1}" if s1 == s2 else f"s. {s1}-{s2}")
    return ", ".join([ad, *yer])


def istem(soru: str, parcalar: list[dict], belge_adlari: dict[str, str]) -> list[dict]:
    """Sohbet biçiminde istem: sistem kuralları + numaralı kaynaklar + soru."""
    kaynaklar = "\n\n".join(f"[{i}] {kunye(p, belge_adlari)}\n{p['metin']}"
                            for i, p in enumerate(parcalar, 1))
    return [{"role": "system", "content": SISTEM},
            {"role": "user", "content": f"Kaynaklar:\n\n{kaynaklar}\n\nSoru: {soru}"}]


def ayristir(cevap: str, kaynak_idleri: list[str]) -> dict:
    """Cevaptan cevaplamama ve atıfları çıkarır. Geçersiz numara (kaynak
    sayısının dışında) ayrıca döner; model olmayan bir kaynağı anmış demektir."""
    metin = cevap.strip()
    # "BİLMİYORUM: ..." ya da "Bilmiyorum." ile başlar; "Bilmiyorum diyemem, ..." sayılmaz
    bilmiyorum = bool(_BILMIYORUM.match(kucult(metin)))
    numaralar = [int(n) for n in _ATIF.findall(metin)]
    gecerli = [n for n in dict.fromkeys(numaralar) if 1 <= n <= len(kaynak_idleri)]
    return {
        "bilmiyorum": bilmiyorum,
        "atiflar": [kaynak_idleri[n - 1] for n in gecerli],
        "gecersiz_atif": sorted({n for n in numaralar if not 1 <= n <= len(kaynak_idleri)}),
        "atifsiz": not bilmiyorum and not numaralar,
    }

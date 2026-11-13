import pytest

from mevzuat_rag.uyum import (
    aralik,
    cohen_kappa,
    kappa_araligi,
    karsilastir,
    oran_araligi,
    ornek_sec,
    ortusme,
    ozetle,
)

METIN = "MADDE 1- (1) Birinci cümle burada. (2) İkinci cümle de şurada duruyor."
PARCALAR = {"y/m1": METIN, "y/m2": "Başka bir madde metni burada yazıyor.", "z/m1": "Diğer belge metni."}


def soru(id_, tur, dayanak=(), kanit=()):
    return {"id": id_, "tur": tur, "dayanak": list(dayanak), "kanit": list(kanit)}


def test_kappa_bilinen_ornek():
    # gözlenen 0.75, beklenen (2·1 + 2·3) / 16 = 0.5 → κ = 0.5
    assert cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == pytest.approx(0.5)


def test_kappa_tam_uyum_ve_tanimsiz():
    assert cohen_kappa(["a", "b", "a"], ["a", "b", "a"]) == pytest.approx(1.0)
    assert cohen_kappa(["a", "a"], ["a", "a"]) is None


def test_kappa_uzunluk_farki():
    with pytest.raises(ValueError):
        cohen_kappa([1], [1, 0])


def test_kappa_araligi_tanimsizlari_atlar():
    r = kappa_araligi([True] * 9 + [False], [True] * 9 + [False], n=200)
    assert r["kappa"] == pytest.approx(1.0)
    assert r["atlanan"] > 0 and r["ham_uyum"] == 1.0


def test_oran_araligi_bos():
    assert oran_araligi([])["oran"] is None
    assert oran_araligi([True, False])["oran"] == pytest.approx(0.5)


def test_aralik_ve_ortusme():
    a = aralik(METIN, "Birinci   cümle\nburada.")
    assert METIN[a[0]:a[1]] == "Birinci cümle burada."
    assert aralik(METIN, "yok böyle bir cümle") is None
    assert ortusme((0, 10), (5, 30)) == pytest.approx(0.5)
    assert ortusme((0, 10), (20, 30)) == 0.0


def test_karsilastir_ayni_madde_ayni_kanit():
    x = karsilastir(soru("q1", "tek", ["y/m1"], ["Birinci cümle burada."]),
                    soru("q1", "tek", ["y/m1"], ["(1) Birinci cümle burada."]), PARCALAR)
    assert x["ayni_madde"] and x["ortak_belge"] and x["ayni_kanit"]


def test_karsilastir_ayni_belge_farkli_madde():
    x = karsilastir(soru("q1", "tek", ["y/m1"], ["Birinci cümle burada."]),
                    soru("q1", "tek", ["y/m2"], ["Başka bir madde metni burada"]), PARCALAR)
    assert not x["ortak_madde"] and x["ortak_belge"] and not x["ayni_kanit"]


def test_karsilastir_farkli_cumle_ayni_madde():
    x = karsilastir(soru("q1", "tek", ["y/m1"], ["Birinci cümle burada."]),
                    soru("q1", "tek", ["y/m1"], ["İkinci cümle de şurada duruyor."]), PARCALAR)
    assert x["ortak_madde"] and not x["ayni_kanit"]


def test_karsilastir_cevapsiz_tarafta_madde_olcusu_yok():
    x = karsilastir(soru("q1", "cevapsiz"), soru("q1", "tek", ["z/m1"], ["Diğer belge metni."]), PARCALAR)
    assert x["cevapli_altin"] is False and "ayni_madde" not in x


def test_ozetle():
    k = [karsilastir(soru("q1", "tek", ["y/m1"], ["Birinci cümle burada."]),
                     soru("q1", "tek", ["y/m1"], ["Birinci cümle burada."]), PARCALAR),
         karsilastir(soru("q2", "cevapsiz"), soru("q2", "cevapsiz"), PARCALAR),
         karsilastir(soru("q3", "tek", ["y/m2"], ["Başka bir madde metni burada"]),
                     soru("q3", "cevapsiz"), PARCALAR)]
    o = ozetle(k)
    assert o["n"] == 3 and o["ikisi_cevapli"] == 1
    assert o["ayni_madde"]["oran"] == 1.0
    assert o["cevaplanabilirlik"]["ham_uyum"] == pytest.approx(2 / 3)


def test_ornek_sec_katmanli_ve_tekrar_uretilebilir():
    sorular = [{"id": f"q{i:03d}", "bolum": "test", "yazan": "a", "tur": t}
               for i, t in enumerate(["tek"] * 10 + ["cok"] * 4 + ["cevapsiz"] * 3, 1)]
    sorular.append({"id": "q900", "bolum": "dev", "yazan": "a", "tur": "tek"})
    s1 = ornek_sec(sorular, "a", {"tek": 3, "cok": 2, "cevapsiz": 1}, tohum=0)
    assert s1 == ornek_sec(sorular, "a", {"tek": 3, "cok": 2, "cevapsiz": 1}, tohum=0)
    turu = {s["id"]: s["tur"] for s in sorular}
    assert sorted(turu[q] for q in s1).count("tek") == 3 and "q900" not in s1
    with pytest.raises(ValueError):
        ornek_sec(sorular, "a", {"cevapsiz": 4}, tohum=0)

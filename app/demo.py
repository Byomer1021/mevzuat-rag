"""Demo: GTÜ lisans mevzuatı hakkında soru sor, dayandığı madde ve sayfayla cevap al.

    uv run streamlit run app/demo.py
    DEMO_ARAMA=bm25 uv run streamlit run app/demo.py                    # e5 yerine BM25, anında açılır
    DEMO_URETICI=paket.modul:fonksiyon uv run streamlit run app/demo.py  # dil modeli bağlı

Dil modeli bağlı değilse bulunan kaynakları ve modele gidecek istemi
gösterir. e5 dizini ilk açılışta kurulur; CPU'da uzun sürer, bir kez.
Önceden kurmak için: uv run python scripts/demo_dizin.py
"""

import os

if not os.environ.get("DEMO_CIHAZ"):  # GPU'yu torch yüklenmeden gizle (K-002)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import streamlit as st

from mevzuat_rag.demo import (
    KOK,
    UYARI,
    adres,
    bilgi_tabani,
    cevapla,
    dizin_kur,
    uretici_yukle,
    web_mi,
)
from mevzuat_rag.uretim import kunye

ARAMA = os.environ.get("DEMO_ARAMA", "e5")
CIHAZ = os.environ.get("DEMO_CIHAZ", "cpu")
ORNEKLER = ["Derslere devam zorunluluğu yüzde kaç?",
            "Kaç dönem kayıt dondurabilirim?",
            "Tek ders sınavına kimler girebilir?"]

st.set_page_config(page_title="GTÜ Mevzuat Asistanı", layout="centered")

if not (KOK / "data" / "processed" / "parcalar_madde.jsonl").exists():
    st.error("Parçalar yok. Önce: uv run python scripts/onisle.py")
    st.stop()


@st.cache_resource(show_spinner="Bilgi tabanı ve arama dizini yükleniyor…")
def hazirla(arama: str, cihaz: str):
    bt = bilgi_tabani()
    return bt, dizin_kur(arama, bt, cihaz=cihaz)


@st.cache_resource
def uretici(tanim: str | None):
    return uretici_yukle(tanim)


bt, dizin = hazirla(ARAMA, CIHAZ)
uret = uretici(os.environ.get("DEMO_URETICI"))


def sor(metin: str | None = None):
    """Örnek düğmesi ya da form: soruyu kutuya yazar ve sorulmuş sayar."""
    if metin is not None:
        st.session_state.soru = metin
    st.session_state.sorulan = st.session_state.get("soru", "").strip()


with st.sidebar:
    st.subheader("Ayarlar")
    k_belge = st.slider("Yönetmelik ve yönergelerden", 0, 8, 3)
    k_web = st.slider("Web sayfalarından (SSS)", 0, 5, 2)
    st.caption(f"Arama: {ARAMA} · {len(bt.parcalar)} parça · {len(bt.kaynaklar)} kaynak")
    if bt.surum:
        st.caption(f"Bilgi tabanı {bt.surum['bilgi_tabani_surumu']} · "
                   f"parçalar {bt.surum['parca_surumu']}")
    st.caption("Dil modeli: " + ("bağlı" if uret else "bağlı değil, yalnız arama"))

st.title("GTÜ Mevzuat Asistanı")
st.caption("Lisans yönetmelikleri, yönergeler ve birim sayfaları üzerinden. "
           "Her cevap dayandığı madde ve sayfayla gelir.")
st.info(UYARI)

for sutun, ornek in zip(st.columns(len(ORNEKLER)), ORNEKLER, strict=True):
    sutun.button(ornek, on_click=sor, args=(ornek,), width="stretch")

with st.form("sor"):
    st.text_input("Sorun", key="soru", placeholder="ör. Kaç dönem kayıt dondurabilirim?")
    st.form_submit_button("Sor", type="primary", on_click=sor)

sorulan = st.session_state.get("sorulan", "")
if sorulan:
    with st.spinner("Aranıyor…"):
        s = cevapla(sorulan, dizin, bt, k_belge=k_belge, k_web=k_web, uretici=uret)
    ayr = s["ayrisim"]
    if s["cevap"] is None:
        st.info("Dil modeli henüz bağlı değil. Cevap aşağıdaki kaynaklardan üretilecek.")
    elif ayr["bilmiyorum"]:
        st.warning(s["cevap"])
    else:
        st.markdown(s["cevap"])
        if ayr["gecersiz_atif"]:
            st.caption("Cevap, listede olmayan bir kaynak numarası anıyor: "
                       + ", ".join(f"[{n}]" for n in ayr["gecersiz_atif"]))
        if ayr["atifsiz"]:
            st.caption("Cevap hiçbir kaynağa atıf yapmıyor; dikkatle okuyun.")

    atiflar = set(ayr["atiflar"]) if ayr else set()
    for i, p in enumerate(s["kaynaklar"], 1):
        onceki = s["kaynaklar"][i - 2] if i > 1 else None
        if onceki is None or web_mi(onceki) != web_mi(p):
            st.subheader("Sık sorulan sorular ve birim sayfaları" if web_mi(p)
                         else "Yönetmelik ve yönergeler")
        etiket = f"[{i}] {kunye(p, bt.adlar)}"
        if p["id"] in atiflar:
            etiket += " · cevapta kullanıldı"
        with st.expander(etiket, expanded=i == 1):
            st.text(p["metin"])
            if url := adres(p, bt.kaynaklar):
                st.markdown(f"[Kaynağı aç]({url})")
    with st.expander("Dil modeline giden istem"):
        for m in s["mesajlar"]:
            st.caption(m["role"])
            st.code(m["content"], language=None, wrap_lines=True)

"""Test seti sorusu yazma aracı.

    uv run streamlit run app/soru_yaz.py

Solda maddeleri ara ve oku, sağda soruyu yaz, dayanak maddeleri seç. Her
kayıt şemaya göre denetlenip data/testset/sorular.jsonl'a eklenir.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from mevzuat_rag.testset import (
    BOLUMLER,
    ETIKET_ONERILERI,
    TURLER,
    dogrula,
    ekle,
    oku,
    ozet,
    parcalari_oku,
    yeni_id,
)

KOK = Path(__file__).resolve().parents[1]
PARCALAR = KOK / "data" / "processed" / "parcalar_madde.jsonl"
SORULAR = Path(os.environ.get("SORU_DOSYASI", KOK / "data" / "testset" / "sorular.jsonl"))
TUR_ADI = {"tek": "tek madde", "cok": "çok maddeli", "cevapsiz": "cevapsız"}


def kucuk(s: str) -> str:
    # Türkçe: "I".lower() "i" verir, "İ".lower() birleşik nokta bırakır
    return s.replace("I", "ı").replace("İ", "i").lower()


def etiket(p: dict) -> str:
    ad = p["baslik"] or (p["metin"].split("\n")[0][:50] if p["tur"] == "takvim" else "")
    return f"{p['id']} · {ad}" if ad else p["id"]


FORM_VARSAYILAN = {"f_soru": "", "f_cevap": "", "f_dayanak": [], "f_etiketler": []}

st.set_page_config(page_title="Soru yaz", layout="wide")
# Başarılı kayıttan sonra form boşaltılır; hatada yazılanlar korunur. Widget
# durumu ancak widget oluşturulmadan önce değiştirilebildiği için burada.
if st.session_state.pop("temizle", False):
    st.session_state.update(FORM_VARSAYILAN)
if mesaj := st.session_state.pop("mesaj", None):
    st.success(mesaj)
if not PARCALAR.exists():
    st.error("Parçalar yok. Önce: uv run python scripts/onisle.py")
    st.stop()

parcalar = parcalari_oku(PARCALAR)
parca = {p["id"]: p for p in parcalar}
sorular = oku(SORULAR)

sol, sag = st.columns([5, 4], gap="large")

with sol:
    st.subheader("Maddeler")
    belgeler = ["hepsi"] + sorted({p["belge_id"] for p in parcalar})
    belge = st.selectbox("Belge", belgeler)
    aranan = st.text_input("Ara (metin veya başlık)")
    adaylar = [p for p in parcalar
               if (belge == "hepsi" or p["belge_id"] == belge)
               and (not aranan or kucuk(aranan) in kucuk(p["baslik"] + " " + p["metin"]))]
    st.caption(f"{len(adaylar)} parça")
    if adaylar:
        secili = st.selectbox("Parça", [p["id"] for p in adaylar],
                              format_func=lambda i: etiket(parca[i]))
        p = parca[secili]
        st.markdown(f"**{p['id']}** · sayfa {p['sayfa_bas']}"
                    + (f"-{p['sayfa_son']}" if p["sayfa_son"] != p["sayfa_bas"] else "")
                    + (f" · {p['bolum']}" if p["bolum"] else ""))
        st.text(p["metin"])

with sag:
    st.subheader(f"Yeni soru ({yeni_id(sorular)})")
    with st.form("soru"):
        soru = st.text_area("Soru", key="f_soru", placeholder="Bir öğrencinin soracağı gibi yaz.")
        tur = st.radio("Tür", TURLER, key="f_tur", format_func=TUR_ADI.get, horizontal=True)
        cevap = st.text_area("Referans cevap", key="f_cevap", help="Cevapsız soruda boş bırak.")
        dayanak = st.multiselect("Dayanak parçalar", list(parca), key="f_dayanak",
                                 format_func=lambda i: etiket(parca[i]))
        etiketler = st.multiselect("Etiketler", ETIKET_ONERILERI, key="f_etiketler",
                                   accept_new_options=True)
        c1, c2 = st.columns(2)
        bolum = c1.selectbox("Bölüm", BOLUMLER, key="f_bolum")
        yazan = c2.text_input("Yazan", key="f_yazan", value="omer")
        kaydet = st.form_submit_button("Kaydet", type="primary")

    if kaydet:
        kayit = {"id": yeni_id(sorular), "soru": soru.strip(), "tur": tur,
                 "referans_cevap": cevap.strip(), "dayanak": dayanak,
                 "etiketler": etiketler, "yazan": yazan.strip(), "bolum": bolum}
        hatalar = dogrula(kayit, set(parca), {s["id"] for s in sorular})
        if hatalar:
            for h in hatalar:
                st.error(h)
        else:
            ekle(SORULAR, kayit)
            st.session_state.update(temizle=True, mesaj=f"{kayit['id']} kaydedildi.")
            st.rerun()

st.divider()
oz = ozet(sorular)
st.subheader(f"Durum: {oz['toplam']} soru")
if sorular:
    a, b, c = st.columns(3)
    a.write({TUR_ADI[k]: v for k, v in oz["tur"].items()})
    b.write(oz["bolum"])
    c.write(oz["belge"])
    st.dataframe(pd.DataFrame(sorular[::-1])[["id", "tur", "soru", "dayanak", "etiketler", "bolum"]],
                 hide_index=True, width="stretch")

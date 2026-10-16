import importlib

import pytest

import mevzuat_rag


def test_paket_import_ediliyor():
    assert mevzuat_rag.__version__


# transformers/sentence-transformers torch surumunu import aninda kontrol
# ediyor; uyumsuz bir kilit dosyasi burada yakalanir, ilk deneyde degil.
@pytest.mark.parametrize(
    "modul",
    ["fitz", "pdfplumber", "faiss", "rank_bm25", "sentence_transformers", "streamlit"],
)
def test_cekirdek_kutuphaneler_import_ediliyor(modul):
    importlib.import_module(modul)

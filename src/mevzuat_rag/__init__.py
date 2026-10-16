"""Üniversite mevzuatı için kaynak gösteren Türkçe RAG soru-cevap sistemi."""

from dotenv import load_dotenv

# HF_HOME gibi ortam degiskenleri huggingface_hub import edilmeden once
# yuklenmeli; bu yuzden paket ilk import edildiginde okunuyor.
load_dotenv(override=False)

__version__ = "0.1.0"

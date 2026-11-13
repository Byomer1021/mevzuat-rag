"""Önceden üretilmiş cevaplarla demo üreticisi (K-005: canlı demoda Colab yok).

    $env:DEMO_URETICI = "mevzuat_rag.hazir_cevap:uret"
    $env:DEMO_CEVAPLAR = "results/cevap/ham/dev-e5-demo__Qwen3-4B-Instruct-2507.jsonl"
    uv run streamlit run app/demo.py

Colab defteri (notebooks/cevap_uret.ipynb) cevap dosyasını
`<paket>__<model>.jsonl` diye adlandırır. Paket, results/istem/<paket>.jsonl.
Paketteki her sorunun istemi (sohbet mesajları) özetlenir ve cevabıyla
eşlenir. Demo aynı soruyu aynı aramayla sorduğunda istem birebir aynıdır,
cevap bulunur. İstem farklıysa (başka soru, başka kaynak sayısı) sabit bir
not döner, demo kaynakları yine gösterir. Birden çok cevap dosyası
`os.pathsep` ile ayrılır (Windows'ta `;`).
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
YOK = "Bu soru için önceden üretilmiş cevap yok. Kaynaklar aşağıda."


def ozet(mesajlar: list[dict]) -> str:
    return hashlib.sha256(json.dumps(mesajlar, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _jsonl(yol: Path) -> list[dict]:
    return [json.loads(s) for s in yol.read_text(encoding="utf-8-sig").splitlines() if s.strip()]


def paket_yolu(cevap_yolu: Path, kok: Path = KOK) -> Path:
    ad = cevap_yolu.name.split("__")[0]
    return kok / "results" / "istem" / f"{ad}.jsonl"


def yukle(cevap_yollari: list[Path], kok: Path = KOK) -> dict[str, str]:
    """istem özeti → cevap. Sonraki dosya öncekinin aynı istemli cevabını ezer."""
    tablo = {}
    for cy in cevap_yollari:
        cevaplar = {c["id"]: c["cevap"] for c in _jsonl(cy) if "_ust" not in c}
        for s in _jsonl(paket_yolu(cy, kok)):
            if s["id"] in cevaplar:
                tablo[ozet(s["mesajlar"])] = cevaplar[s["id"]]
    return tablo


@lru_cache(maxsize=1)
def _tablo(tanim: str) -> dict[str, str]:
    yollar = [Path(p) if Path(p).is_absolute() else KOK / p for p in tanim.split(os.pathsep) if p.strip()]
    return yukle(yollar, KOK)


def uret(mesajlar: list[dict]) -> str:
    """Demo üreticisi (demo.Uretici): istemin önceden üretilmiş cevabı."""
    tanim = os.environ.get("DEMO_CEVAPLAR", "")
    if not tanim:
        raise RuntimeError("DEMO_CEVAPLAR boş: Colab'dan gelen cevap dosyasının yolunu ver")
    return _tablo(tanim).get(ozet(mesajlar), YOK)

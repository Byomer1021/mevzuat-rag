"""Ortamı ölçer ve kaydeder: Python, paket sürümleri, GPU.

GPU için "görünüyor" yetmez: Pascal (sm_61) desteği düşmüş bir torch
derlemesi cuda.is_available() = True der, ilk kernel'de patlar. Bu yüzden
GPU'da gerçek bir matris çarpımı yapıp CPU sonucuyla karşılaştırıyoruz.

Kullanım:
    uv run python scripts/ortam_kontrol.py [--kaydet results/ortam.json]
"""

import argparse
import importlib.metadata as md
import json
import os
import platform
import sys
import time
from pathlib import Path

import mevzuat_rag  # noqa: F401  (.env'i, dolayısıyla HF_HOME'u yükler)

PAKETLER = [
    "torch", "sentence-transformers", "transformers", "faiss-cpu", "rank-bm25",
    "pymupdf", "pdfplumber", "numpy", "pandas", "scikit-learn", "streamlit",
]


def paket_surumleri():
    out = {}
    for p in PAKETLER:
        try:
            out[p] = md.version(p)
        except md.PackageNotFoundError:
            out[p] = None
    return out


def gpu_kontrol():
    import torch

    sonuc = {
        "torch_cuda_derlemesi": torch.version.cuda,
        "cuda_gorunuyor": torch.cuda.is_available(),
    }
    if not sonuc["cuda_gorunuyor"]:
        return sonuc

    sonuc["gpu"] = torch.cuda.get_device_name(0)
    major, minor = torch.cuda.get_device_capability(0)
    sonuc["compute_capability"] = f"sm_{major}{minor}"
    sonuc["derlemedeki_mimariler"] = torch.cuda.get_arch_list()
    sonuc["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)

    # Gercek bir kernel calistir, sonucu CPU ile karsilastir.
    try:
        g = torch.Generator().manual_seed(0)
        a = torch.randn(2048, 2048, generator=g)
        b = torch.randn(2048, 2048, generator=g)
        cpu = a @ b
        a_g, b_g = a.cuda(), b.cuda()
        (a_g @ b_g).sum().item()  # isinma
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        gpu = a_g @ b_g
        torch.cuda.synchronize()
        sonuc["matmul_2048_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        sonuc["cpu_ile_max_fark"] = float((gpu.cpu() - cpu).abs().max())
        sonuc["kernel_calisti"] = True
    except RuntimeError as e:  # "no kernel image is available" burada yakalanir
        sonuc["kernel_calisti"] = False
        sonuc["hata"] = f"{type(e).__name__}: {e}"
    return sonuc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kaydet", type=Path, help="Sonucu JSON olarak bu dosyaya yaz")
    args = ap.parse_args()

    rapor = {
        "zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hf_home": os.environ.get("HF_HOME"),
        "paketler": paket_surumleri(),
        "gpu": gpu_kontrol(),
    }
    metin = json.dumps(rapor, ensure_ascii=False, indent=2)
    print(metin)
    if args.kaydet:
        args.kaydet.parent.mkdir(parents=True, exist_ok=True)
        args.kaydet.write_text(metin + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

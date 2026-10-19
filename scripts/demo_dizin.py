"""Demonun e5 dizinini önceden kurar: CPU'da bir kez uzun sürer, sonra önbellekten.

    uv run python scripts/demo_dizin.py

Demo (app/demo.py) aynı kurulumu kullandığı için ilk açılışta beklemez.
"""

import os
import sys
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # GPU'yu torch yüklenmeden gizle (K-002)

from mevzuat_rag.demo import bilgi_tabani, dizin_kur


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t = time.time()
    bt = bilgi_tabani()
    dizin_kur("e5", bt)
    print(f"{len(bt.parcalar)} parça, {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()

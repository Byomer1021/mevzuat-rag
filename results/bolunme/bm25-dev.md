# Bölünme analizi: bm25-dev

Kaynak `results\deney\bm25-dev.json`, küme birincil, n = 37, R@5. Kanıtı pencere sınırında bölünen soru: 10 (madde koşulunda 0).

| ölçüt | madde | sabit | fark [95%] | McNemar (yalnız madde / yalnız sabit, p) |
|---|---|---|---|---|
| sıkı (kanıt tam kapsanmalı) | 0.149 [0.054, 0.270] | 0.176 [0.068, 0.297] | -0.027 [-0.162, +0.081] | 2 / 3, p = 1.000 |
| gevşek (örtüşen bir parça yeter) | 0.149 [0.054, 0.270] | 0.230 [0.108, 0.365] | -0.081 [-0.189, +0.027] | 1 / 4, p = 0.375 |

Sıkı ölçütte yalnız maddenin bulduğu 2 sorudan kanıtı bölünmüş olan: 2 (q003, q018).

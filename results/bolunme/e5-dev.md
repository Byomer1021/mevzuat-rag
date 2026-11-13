# Bölünme analizi: e5-dev

Kaynak `results\deney\e5-dev.json`, küme birincil, n = 37, R@5. Kanıtı pencere sınırında bölünen soru: 10 (madde koşulunda 0).

| ölçüt | madde | sabit | fark [95%] | McNemar (yalnız madde / yalnız sabit, p) |
|---|---|---|---|---|
| sıkı (kanıt tam kapsanmalı) | 0.595 [0.432, 0.757] | 0.365 [0.216, 0.527] | +0.230 [+0.108, +0.378] | 9 / 0, p = 0.004 |
| gevşek (örtüşen bir parça yeter) | 0.595 [0.432, 0.757] | 0.392 [0.243, 0.554] | +0.203 [+0.081, +0.338] | 8 / 0, p = 0.008 |

Sıkı ölçütte yalnız maddenin bulduğu 9 sorudan kanıtı bölünmüş olan: 4 (q018, q021, q035, q048).

# Veri

## Bilgi tabanı: `raw/` ve `kaynaklar.csv`

İndirilen her PDF `raw/` altına girer ve `kaynaklar.csv`'ye bir satır olarak
yazılır. Gerekçe: [K-004](../docs/kararlar.md).

| sütun | anlamı |
|---|---|
| `belge_id` | kısa, kalıcı kimlik: `lisans-yonetmelik`, `yatay-gecis`, ... |
| `baslik` | belgenin resmî adı |
| `tur` | `yonetmelik`, `yonerge`, `takvim`, `diger` |
| `url` | indirildiği adres |
| `surum_tarihi` | belgenin üzerindeki son değişiklik / kabul tarihi |
| `indirme_tarihi` | YYYY-MM-DD |
| `dosya` | `raw/` altındaki dosya adı |
| `sha256` | dosyanın özeti; sonuçlar bu sürüme bağlıdır |
| `metin_katmani` | `var`, `yok` (taranmış, OCR gerekir), `kismi` |
| `notlar` | |

`processed/` (PDF'ten çıkan metin ve parçalar) koddan yeniden üretilir ve
depoya girmez.

## Test seti: `testset/`

JSONL, satır başına bir soru:

```json
{
  "id": "q001",
  "soru": "Devamsızlık sınırı nedir?",
  "tur": "tek",
  "referans_cevap": "...",
  "dayanak": [{"belge_id": "lisans-yonetmelik", "madde": "21", "fikra": "1", "sayfa": 9}],
  "etiketler": ["sayi"],
  "yazan": "...",
  "bolum": "dev"
}
```

- `tur`: `tek` (tek madde), `cok` (birden fazla madde veya belge), `cevapsiz`.
- `cevapsiz` sorularda `dayanak` boş liste, `referans_cevap` boş.
- `etiketler`: hata analizinde soru türüne göre kırılım için. Örnek:
  `tarih`, `istisna`, `sayi`, `kosul`, `tanim`.
- `bolum`: `dev` veya `test` ([K-007](../docs/kararlar.md), öneri).
- İkinci etiketçinin bağımsız işaretlemesi ayrı dosyada tutulur; uyum
  (Cohen's Kappa) [olcumler.md](../docs/olcumler.md)'ye yazılır.

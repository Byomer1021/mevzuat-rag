# Veri

## Bilgi tabanı: `raw/` ve `kaynaklar.csv`

Bilgi tabanındaki her belge `kaynaklar.csv`'de bir satır, dosyası `raw/`
altında. Hangi belgelerin neden seçildiği: [K-009](../docs/kararlar.md).
Neden depoda oldukları: [K-004](../docs/kararlar.md).

```powershell
uv run python scripts/kaynaklar.py dizin     # GTÜ Kalite Ofisi dizinini raw/dizin/'e kaydet
uv run python scripts/kaynaklar.py indir     # eksik belgeleri indir, sha256 yaz
uv run python scripts/kaynaklar.py kontrol   # elimizdeki revizyonlar hâlâ yürürlükte mi
```

| sütun | anlamı |
|---|---|
| `belge_id` | kısa, kalıcı kimlik: `lisans-yonetmelik`, `yatay-gecis`, ... |
| `kod` | GTÜ doküman kodu: `YN-0001`, `YÖ-0013`; dizinde olmayan için `-` |
| `baslik` | dizindeki resmî ad |
| `tur` | `yonetmelik`, `yonerge`, `esaslar`, `takvim` |
| `revizyon` | dizindeki revizyon no: `R7` |
| `surum_tarihi` | dizindeki revizyon tarihi; R0 ise ilk yayın tarihi |
| `url` | indirildiği adres |
| `indirme_tarihi` | YYYY-MM-DD |
| `dosya` | `raw/` altındaki dosya: `<belge_id>_<revizyon>.pdf` |
| `sha256` | dosyanın özeti; sonuçlar bu sürüme bağlı |
| `metin_katmani` | boş; ölçüm sonucu [results/metin_katmani.csv](../results/metin_katmani.csv)'de |
| `notlar` | |

- `raw/dizin/` GTÜ dizininin çekildiği günkü hali; hangi revizyonun yürürlükte
  olduğunun kanıtı.
- Akademik takvimin PDF'i yok. Sayfadaki tablo `akademik-takvim-2026-2027.tsv`
  olarak saklanır, çünkü ham HTML her istekte farklı geliyor
  ([K-011](../docs/kararlar.md)).
- `processed/` (temizlenmiş metin ve parçalar) koddan yeniden üretilir ve
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

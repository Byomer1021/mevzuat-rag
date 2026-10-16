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
- `processed/` koddan yeniden üretilir ve depoya girmez:
  `uv run python scripts/onisle.py` → `processed/parcalar_madde.jsonl`.

## Parçalar: `processed/parcalar_madde.jsonl`

Satır başına bir parça ([K-014](../docs/kararlar.md)):

| alan | anlamı |
|---|---|
| `id` | `lisans-yonetmelik/m23`, `/g1` geçici, `/p2` paragraf, `/r40` takvim satırı, `/giris` |
| `belge_id` | kaynaklar.csv'deki kimlik |
| `tur` | `madde`, `gecici`, `paragraf`, `takvim`, `giris` |
| `madde` | `"23"`, `"geçici 1"`; madde olmayan parçada `null` |
| `baslik` | madde başlığı ("Devam durumu"); yoksa boş |
| `bolum` | "ÜÇÜNCÜ BÖLÜM Sınavlar, …"; takvimde bölüm satırı |
| `sayfa_bas`, `sayfa_son` | maddenin başladığı ("MADDE N"nin olduğu) ve bittiği sayfa |
| `metin` | temizlenmiş metin; tablo hücreleri sekmeyle ayrılır |

## Test seti: `testset/`

JSONL, satır başına bir soru:

```json
{
  "id": "q001",
  "soru": "Devamsızlık sınırı nedir?",
  "tur": "tek",
  "referans_cevap": "...",
  "dayanak": ["lisans-yonetmelik/m23"],
  "etiketler": ["sayi"],
  "yazan": "...",
  "bolum": "dev"
}
```

- `tur`: `tek` (tek madde), `cok` (birden fazla madde veya belge), `cevapsiz`.
- `dayanak`: parça kimlikleri ([K-014](../docs/kararlar.md)). `tek` için
  bir, `cok` için en az iki, `cevapsiz` için boş liste; `referans_cevap`
  da boş.
- `etiketler`: hata analizinde soru türüne göre kırılım için. Örnek:
  `tarih`, `istisna`, `sayi`, `kosul`, `tanim`.
- `bolum`: `dev` veya `test` ([K-007](../docs/kararlar.md), öneri).
- İkinci etiketçinin bağımsız işaretlemesi ayrı dosyada tutulur; uyum
  (Cohen's Kappa) [olcumler.md](../docs/olcumler.md)'ye yazılır.

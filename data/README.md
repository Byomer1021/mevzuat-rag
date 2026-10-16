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
| `tur` | `yonetmelik`, `yonerge`, `esaslar`, `mevzuat`, `rehber`, `sss`, `ogretim-plani`, `takvim`, `katalog` (form listesi), `koleksiyon` (web içerik) |
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
- Kaynakların dördü gruba ayrılıyor: Kalite dizini belgeleri (`kod` dolu),
  site taramasından seçilenler (`notlar`'da hangi birimin hangi sayfası),
  form kataloğu (`form-katalogu.tsv`) ve web koleksiyonları
  (`raw/web/*.jsonl`). Seçimin gerekçesi:
  [K-020](../docs/kararlar.md), [K-021](../docs/kararlar.md).
- Web koleksiyonları siteden indirilmez, taramadan üretilir:
  `uv run python scripts/tara.py` (önbellekten) sonra
  `uv run python scripts/web_secim.py`. `kaynaklar.csv`'de `url`'leri
  "yerel:" ile başlar.
- Akademik takvimin PDF'i yok. Sayfadaki tablo `akademik-takvim-2026-2027.tsv`
  olarak saklanır, çünkü ham HTML her istekte farklı geliyor
  ([K-011](../docs/kararlar.md)).
- `processed/` koddan yeniden üretilir ve depoya girmez:
  `uv run python scripts/onisle.py` → `processed/parcalar_madde.jsonl`.

## Yeni belge ekleme

Önce [K-016](../docs/kararlar.md)'ya bak: belge eklemenin test setine ve
önceki sonuçlara etkisi var.

1. **Satırı ekle.** GTÜ dizinindeyse önce `kaynaklar.py dizin` ile dizini
   tazele, `raw/dizin/*.tsv`'den kod, ad, revizyon, tarih ve URL'yi
   `kaynaklar.csv`'ye yeni bir satır olarak ekle; `sha256` boş kalsın.
   Dizinde değilse (ör. bir YÖK yönetmeliği) `kod` ve `revizyon` `-`.
2. `uv run python scripts/kaynaklar.py indir`: belge iner, sha256 yazılır.
3. `uv run python scripts/metin_katmani.py`: metin katmanı var mı, madde
   başlıkları 1..N eksiksiz bulunuyor mu?
4. `uv run python scripts/onisle.py`: `sorunlar` boş olmalı.
   `atilan_blok_kaliplari`'nda yeni kalıp varsa bak; gövde metni
   olmamalı. `bilgi_tabani_surumu` değişir.
5. Yeni belgenin madde başlıklarına göz at.
6. Test setindeki **cevapsız soruları yeniden kontrol et**: yeni belge
   birinin cevabını içerebilir.
7. [olcumler.md](../docs/olcumler.md)'ye kısa bir bölüm,
   [kararlar.md](../docs/kararlar.md)'ye gerekçe.

Temizlik kuralları GTÜ kalite formuna göre yazıldı. Kalite formu olmayan bir
belgede hiçbir şey atılmaz, ki istenen de bu. Biçimi farklı bir başlığı
olan belgede ise başlık metinde kalır; bunu 4. adım gösterir.

## Parçalar: `processed/parcalar_madde.jsonl`

Satır başına bir parça ([K-014](../docs/kararlar.md)):

| alan | anlamı |
|---|---|
| `id` | `lisans-yonetmelik/m23`, `/m12a` alt madde, `/g1` geçici, `/e1` ek, `/p2` paragraf, `/r40` takvim satırı, `form-katalogu/FR-0853`, `web-sss/k1957-3`, `web-duyurular/d31441-1`, `/giris` |
| `belge_id` | kaynaklar.csv'deki kimlik |
| `tur` | `madde`, `gecici`, `ek`, `paragraf`, `takvim`, `form`, `web`, `giris` |
| `madde` | `"23"`, `"12a"`, `"geçici 1"`, `"ek 1"`; madde olmayan parçada `null` |
| `baslik` | madde başlığı ("Devam durumu"), form adı ya da web sayfasının başlığı; yoksa boş |
| `bolum` | "ÜÇÜNCÜ BÖLÜM Sınavlar, …"; takvimde bölüm satırı; web parçasında birim |
| `sayfa_bas`, `sayfa_son` | maddenin başladığı ("MADDE N"nin olduğu) ve bittiği sayfa; web ve formda 1 |
| `metin` | temizlenmiş metin; tablo hücreleri sekmeyle ayrılır |
| `url` | kaynağın adresi; web parçasında sayfanın kendi adresi |
| `tarih` | duyuru tarihi ("8 Ekim 2026"); diğerlerinde boş |

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

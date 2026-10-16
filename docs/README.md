# Dokümantasyon

Bu klasör projenin kaydı. Amaç şu: rapor yazılırken hiçbir sayının, kararın
veya başarısız denemenin hafızadan yeniden kurulması gerekmesin.

## Ne nereye yazılır

| dosya | ne zaman | içerik |
|---|---|---|
| [gunluk/YYYY-MM-DD.md](gunluk/) | çalışılan her gün | yapılanlar, çıkan sonuçlar, takılınan yerler, sıradaki iş |
| [olcumler.md](olcumler.md) | her ölçümde | numaralı bölüm: ne ölçüldü, nasıl, sonuç, ne anlama geliyor |
| [kararlar.md](kararlar.md) | her tasarım kararında | K-NNN: karar, seçenekler, gerekçe, neyle değişir |
| [on-rapor.md](on-rapor.md) | hafta 2 sonunda kesinleşir | kapsam, kısıtlar, plan, açık sorular |
| [proje-tanimi.md](proje-tanimi.md) | değişmez | başlangıçta verilen tanım |
| `raporlar/` | ara ve final rapor | ileride |

Ölçümlerin ham çıktısı `results/` altına JSON/CSV olarak kaydedilir;
`olcumler.md` onların okunur özetidir.

## Kurallar

1. **Ölçülmemiş sayı yazılmaz.** Raporda veya README'de geçen her sayının
   `olcumler.md`'de bir bölümü vardır. Tahmin gerekiyorsa "tahmin" diye
   işaretlenir.
2. **Her ölçüm yeniden üretilebilir.** Bölümde hangi betiğin, hangi
   konfigürasyonun, hangi test seti sürümünün kullanıldığı yazar.
3. **Başarısız denemeler de yazılır.** Raporun hata analizi bölümü buradan
   beslenecek; "denendi, işe yaramadı, çünkü..." en az bir başarı kadar değerli.
4. **Seni pohpohlayan sayıyı iki kez kontrol et.** Beklenenden iyi çıkan bir
   sonuç, önce sızıntı (test sorusuna göre ayar yapılmış olması), yanlış
   eşleşme veya yanlış payda için kontrol edilir.
5. **Günlük kısa tutulur.** Ayrıntı `olcumler.md` ve `kararlar.md`'ye gider,
   günlük onlara bağlantı verir.
6. Ön rapor kesinleştikten sonra değişmez; kapsam değişiklikleri
   `kararlar.md`'ye yeni bir kayıt olarak girer.

## Günlük şablonu

```markdown
# YYYY-MM-DD: <tek cümlelik başlık>

## Yapılanlar
## Sonuçlar
<!-- ölçüm varsa: olcumler.md §N -->
## Takılınanlar
## Sırada
```

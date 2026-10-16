# Soru Yazma Rehberi

Test setinin sorularını yazan herkes için. Araç:

```powershell
uv run streamlit run app/soru_yaz.py
```

Solda maddeleri arayıp okursun, sağda soruyu yazıp dayanak maddeleri
seçersin. Her kayıt şemaya göre denetlenir ve `data/testset/sorular.jsonl`
dosyasına eklenir. Dosyayı elle düzenlersen denetim için:
`uv run python scripts/testset_kontrol.py`.

## En önemli kural: önce soru, sonra madde

Soruyu maddeyi okumadan, bir öğrencinin soracağı gibi yaz. Cevabı maddeden
**sonra** bul.

Maddeye bakarak yazılan soru maddenin kelimelerini tekrar eder ("devam
zorunluluğu", "mazeret sınavı") ve aramayı olduğundan iyi gösterir. Gerçek
bir öğrenci "devamsızlıktan kalır mıyım", "rapor alırsam sınava sonra
girebilir miyim" diye sorar. Sistemin ölçülmesi gereken şey bu farkı
kapatabilmesi.

İyi kaynaklar: kendi başına gelenler, arkadaşlarının sorduğu, öğrenci
gruplarında dönen sorular.

Aynı nedenle soruları dil modeline yazdırmıyoruz: hem kelimeleri belgeden
alır, hem de sonuçta cevabı yine bir dil modeli verecek.

## Türler ve hedef dağılım (dev bölümü, 50 soru)

| tür | ne | hedef |
|---|---|---|
| tek | cevap tek bir maddede ("Bir dersten en fazla kaç saat devamsızlık yapabilirim?") | ~28 |
| çok | iki veya daha fazla madde gerekir; mümkünse farklı belgelerden ("Çift anadal yaparken stajı iki bölümde de yapmam gerekir mi?") | ~13 |
| cevapsız | belgelerde cevabı yok ("Kütüphane kaçta kapanıyor?", "Burs başvurusu ne zaman?") | 8-10 (%15-20) |

Cevapsız sorular halüsinasyonu en doğrudan ölçen sorular. En değerlileri
konusu belgelere **yakın** olanlar. "Erasmus hibesi ayda ne kadar?":
Erasmus yönergesi iki maddede hibeden söz ediyor ama tutar vermiyor. "Burs
başvurusu ne zaman?" ve "Kütüphane kaçta kapanıyor?": danışmanlık m6
"danışman burslar ve kütüphane hakkında bilgi verir" diyor, "burs" başka üç
maddede daha geçiyor, ama hiçbirinde tarih ya da saat yok. Arama bu
maddeleri getirecek ve model oradan bir cevap uydurmaya yönelecek; ölçmek
istediğimiz an tam olarak bu. Konusu bambaşka olan bir soru ("Kantinde ne
var?") ise kolay bir soru.

Bu örneklerin ömrü bilgi tabanına bağlı. Rehberin ilk sürümündeki "Erasmus'ta
kaç ders saydırabilirim?" örneği, Erasmus yönergesi eklenince cevapsız
olmaktan çıktı (m6: "bir dönemde 30 AKTS … tavsiye edilir"). Bilgi tabanı
bu yüzden sorulardan önce donduruluyor ([K-016](kararlar.md)).

Bir soruyu cevapsız diye işaretlemeden önce aracın arama kutusunda anahtar
kelimelerini dene. Cevap bir yerde çıkarsa soru cevapsız değildir.

## Alanlar

- **Referans cevap:** kısa ve olgusal. Sayı, süre veya koşul varsa aynen
  yaz. Cevapsız soruda boş bırak.
- **Dayanak:** cevabın dayandığı bütün parçalar. Cevap bir istisnaya
  bağlıysa istisnanın olduğu madde de dayanaktır.
- **Etiketler:** hata analizinde kırılım için. `tarih`, `sure`, `sayi`,
  `not`, `istisna`, `kosul`, `tanim`, `basvuru`; gerekirse yenisini yaz.
- **Bölüm:** ilk 50 soru `dev`. `test` sorularını sonra, dev setiyle ayar
  yapılırken bunları görmeden yazacağız ([K-007](kararlar.md)).

## Kapsama

Altta "Durum" tablosu belge başına soru sayısını gösteriyor. Hiç soru almayan
belge kalmasın. Akademik takvim de dahil: tarih soruları sistemin en sık
yanılacağı yerlerden biri olabilir.

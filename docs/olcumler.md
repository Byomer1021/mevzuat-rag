# Ölçüm Günlüğü

Projede ölçülen her şey burada, numaralı bölümler halinde. Amaç sonucu güzel
göstermek değil, **hangi kararın neye dayandığını** kayda geçirmek. Ham
çıktılar `results/` altında.

Her bölüm şu sırayla yazılır: neden ölçüldü, nasıl ölçüldü (betik, komut,
konfigürasyon), sonuç, ne anlama geldiği ve ne anlama gelmediği.

---

## 1. Ortam: GPU görünüyor mu, yoksa gerçekten çalışıyor mu (2026-10-16)

**Neden.** GTX 1080 Pascal mimarisinde (sm_61). torch'un bir derlemesi bu
mimari için kernel içermiyorsa `torch.cuda.is_available()` yine `True` döner
ve hata ilk gerçek işlemde, büyük ihtimalle bir deneyin ortasında çıkar. Bu
yüzden "görünüyor" ile "çalışıyor" ayrı ölçüldü.

**Nasıl.** `uv run python scripts/ortam_kontrol.py --kaydet results/ortam.json`.
Betik GPU'da 2048×2048 float32 matris çarpımı yapıp sonucu aynı girdinin CPU
sonucuyla karşılaştırıyor. Ham çıktı: [results/ortam.json](../results/ortam.json).

**Sonuç.**

| | değer |
|---|---|
| Python | 3.12.10 |
| torch | 2.7.1+cu118 |
| derlemedeki mimariler | sm_37, sm_50, sm_60, **sm_61**, sm_70, sm_75, sm_80, sm_86, sm_90 |
| GPU | GeForce GTX 1080, sm_61, 8.0 GB |
| sürücü | 526.47 (nvidia-smi'ye göre en fazla CUDA 12.0) |
| GPU'da kernel çalıştı | **evet** |
| GPU ile CPU sonucu arasındaki en büyük mutlak fark | 5.2 × 10⁻⁴ |

Fark beklenen büyüklükte: her eleman 2048 çarpımın toplamı, tipik büyüklüğü
√2048 ≈ 45. Bu da göreli olarak ~10⁻⁵ eder; float32'de toplama sırasının
farklı olmasından beklenen düzey bu.

**Ne anlama gelmiyor.** Betik matris çarpımının süresini de yazıyor (iki
çalıştırmada 3.93 ve 2.83 ms), ama bu tek örnek. Isınma ve tekrar yapılmadan
alınmış bir sayı hız ölçümü sayılmaz, burada yalnızca kernel'in çalıştığının
kanıtı olarak duruyor. Gömme hızı, gerçek model ve gerçek parçalarla ayrıca
ölçülecek.

GPU'nun **uzun süreli yük altında** kararlı olup olmadığı da bu ölçümün
konusu değil. Önceki bir projede (trafikisaret) bu kart eğitim yükünde düştü.
Bu projede yük yalnızca çıkarım; ilk tam gömme çalıştırmasında kayda geçecek.

### Kurulumun yan ölçümleri

| | değer |
|---|---|
| `uv sync --all-extras`, önbellek boşken | 233 s, 117 paket |
| `.venv` boyutu | 5.81 GB |
| uv önbelleği (`D:\.cache\uv`) | 5.84 GB |
| D'nin boş alanındaki gerçek azalma | 6.0 GB (587.1 → 581.1) |
| C'nin boş alanı, kurulumdan önce ve sonra | 13.0 → 13.0 GB |

`.venv` ile önbellek toplamda 11.6 GB görünüyor ama disk 6.0 GB azaldı: aynı
sürücüde uv dosyaları hardlink'liyor, aynı byte'lar iki yerde sayılıyor.
Önbellek C'de olsaydı hardlink sürücüler arası çalışmayacağı için kopya
düşecekti; C'nin değişmemesi yönlendirmenin tuttuğunu gösteriyor
([K-003](kararlar.md)).

İlk `pytest` çalıştırması (çekirdek kütüphanelerin import testi) 123 s,
ikincisi 12.8 s sürdü. Farkın ilk import'taki bytecode derlemesinden
kaynaklandığını tahmin ediyorum. Doğrulamadım.

---

## 2. Kaynaklar: hangi sürüm yürürlükte, indirilen ne (2026-10-16)

**Neden.** Aynı yönetmeliğin birden fazla revizyonu (YN-0001 için R1, R5, R6,
R7) gtu.edu.tr'nin farklı klasörlerinde hâlâ duruyor ve aramada hepsi
çıkıyor. Hangisinin yürürlükte olduğunu bilmeden indirilen bir PDF eski
olabilir.

**Nasıl.** Kurumsal Gelişim ve Kalite Ofisi'nin iki dizin sayfası her belge
için kod, ad, dil, karar tarihi, revizyon numarası ve tarihi ile PDF
bağlantısını veriyor. [scripts/kaynaklar.py](../scripts/kaynaklar.py):

- `dizin`: bu tabloları `data/raw/dizin/` altına TSV olarak kaydeder,
- `indir`: [kaynaklar.csv](../data/kaynaklar.csv)'deki belgeleri indirir,
  `%PDF` başlığını kontrol eder, sha256'yı yazar; kayıtlı özetle uyuşmayan
  bir dosyanın üzerine yazmaz,
- `kontrol`: elimizdeki revizyonu dizindekiyle karşılaştırır.

**Sonuç.**

| | değer |
|---|---|
| dizin satırı | 20 yönetmelik, 154 yönerge (127'si Türkçe; İngilizce çeviriler ayrı satır) |
| seçilen | 13 PDF + akademik takvim ([K-009](kararlar.md)) |
| 13 PDF | 52 sayfa, 3.4 MB |
| `%PDF` başlık kontrolü | 13/13 geçti |
| `indir` ikinci kez | 14/14 "var", hiçbiri yeniden inmedi |
| `kontrol` | 13/13 güncel. Aynı gün indirildiği için şimdilik anlamsız, değeri haftalar sonra |

**Akademik takvim sayfası her istekte farklı geliyor.** 2026-2027 takvimi PDF
olarak yayımlanmamış, sayfada HTML tablo olarak duruyor. Sayfanın ham
HTML'i üç ayrı indirmede üç farklı sha256 verdi (`f0393ac5…`, `23fa07d3…`,
`a43b0454…`); neyin değiştiğine bakmadım. Ham HTML'in özeti bu yüzden
değişikliği gösteremez. Tablo TSV'ye çıkarıldı (152 satır; sütunlar
lisans/önlisans, tarih, lisansüstü). TSV'nin özeti üç indirmede aynı:
`b455abf0…` ([K-011](kararlar.md)).

**Burs yönergesi yok.** Proje tanımı bilgi tabanına "burs yönergeleri"
koyuyor. GTÜ dizininin 174 satırının hiçbirinde "burs" geçmiyor. Burs
bilgisi Öğrenci İşleri'nin duyuru sayfalarında; mevzuat olarak yayımlanmamış.

---

## 3. Metin katmanı: OCR gerekiyor mu, madde başlıkları bulunabiliyor mu (2026-10-16)

**Neden.** Proje tanımının ilk riski taranmış PDF'ler. Madde bazlı parçalama da
madde başlıklarının çıkarılan metinde bulunabilmesine bağlı.

**Nasıl.** [scripts/metin_katmani.py](../scripts/metin_katmani.py) her PDF'i
PyMuPDF ve pdfplumber ile ayrı ayrı çıkarıyor. Ham sonuç:
[results/metin_katmani.csv](../results/metin_katmani.csv).

**Sonuç: OCR gerekmiyor.**

| | PyMuPDF | pdfplumber |
|---|---|---|
| belge / sayfa | 13 / 52 | 13 / 52 |
| 100 karakterden az metinli sayfa | 0 | 0 |
| bozuk Türkçe karakter (`ý þ ð Ý Þ Ð`, U+FFFD, özel kullanım alanı) | 0 | 0 |
| Türkçe harf oranı (`çğıöşü…` / tüm harfler) | 0.108–0.134 | aynı |
| toplam karakter | 161 926 | 157 276 |
| madde başlığı | 229 | 229 |
| süre, 13 belge (tek çalıştırma) | 0.29 s | 8.28 s |

`ý þ ð`, cp1254 metnin latin-1 sanılmasıyla ortaya çıkan bozulmanın (ı→ý,
ş→þ, ğ→ð) izi; Türkçe PDF'lerde sık görülür. Bu belgelerde hiç yok.

### Madde başlıkları: dört biçim ve numarasız geçici madde

İlk regex (`MADDE N-`) üç belgede hiç başlık bulamadı, birinde de 7. maddeyi
kaçırdı. Belgelerde görülen biçimler:

| biçim | nerede |
|---|---|
| `MADDE 8- (1) …` | yönetmelikler, yönergelerin çoğu |
| `MADDE-7 – …` | YÖ-0019'da tek bir madde |
| `Madde 3. (1) …` | YÖ-0002 |
| `Madde 4- …` | YÖ-0025 |
| `GEÇİCİ MADDE – …` (numarasız) | YÖ-0007 |

7. madde için önce "belgede numaralandırma 6'dan 8'e atlıyor" diye
düşündüm. Sayfanın görüntüsü `MADDE-7 –` biçimini gösterdi; hata
regex'teydi. Düzeltilmiş tanıyıcı
[src/mevzuat_rag/madde.py](../src/mevzuat_rag/madde.py)'da, beş biçim ve
metin içi atıflar ("6 ncı maddesinin") için 12 testle birlikte. Sonuç:

- Madde yapısı olan 12 belgenin hepsinde asıl maddeler 1'den N'e
  **boşluksuz ve tekrarsız**: toplam 227 asıl ve 2 geçici madde.
- Her belgede bulunan son madde Yürütme, Yürürlük veya Yürürlükten
  Kaldırılan Yönerge. Sonda kaçan bir madde yok.
- **YÖ-0087 (Bilgisayar Müh. staj esasları) madde yapısında değil:** iki
  sayfalık madde imli bir liste. Madde bazlı parçalayıcı bu belge için
  paragraf veya madde imi tabanlı bir yedeğe ihtiyaç duyacak.

**Ne göstermiyor.** Başlıkların sayısı ve sırası doğru, ama her maddenin
gövdesinin doğru sınırlandığı ayrıca kontrol edilmedi. Bu, parçalayıcı
yazılınca yapılacak.

### Sayfa başlığı gürültüsü: metnin %6-10'u

Her sayfada tekrarlanan kalite formu başlığı ve altlığı (`T.C.`, `Doküman
No`, `Revizyon`, `Form No: FR-…`) çıkarılan metnin **%6.1 ile %10.3'ü**
(ortanca %8.0). Sayfa sonunda maddenin ortasına giriyor: YÖ-0019'da MADDE
8'in (1) ve (2) fıkraları arasında 14 satırlık bir başlık/altlık bloğu var.
Temizlenmezse sabit uzunluklu parçalara ve gömmelere gürültü olarak girer.

Ölçüm sezgisel bir kurala dayanıyor: sayfaların en az yarısında geçen satır,
başlık sayılıyor. İki belgede yakalanan satırlara elle bakıldı; hepsi başlık
veya altlıktı. Tek başına duran revizyon ve sayfa numaraları ("7", "2") da bu
kurala takılıyor.

### İki çıkarıcı aynı içeriği veriyor

13 belgenin hepsinde, boşluk dışındaki karakterlerin sayısı ve kümesi iki
çıkarıcıda aynı. Fark sıralamada ve başlık tablosundan geliyor: PyMuPDF
tabloyu sütun sütun okuyor, pdfplumber satır satır okurken hücreleri
karıştırıyor (`DokümanNoYN-0001T.C.YayınTarihi…`). Tekrar eden başlık satırları
atılınca gövde metinleri %97.7-99.9 benzer (difflib oranı). Kalan farkın
kaynağına bakmadım.

Bu derlemde "hangi PDF çıkarıcı" sorusu bir deney ekseni olmuyor
([K-010](kararlar.md)).

---

## 4. Ön işlem: başlık temizliği ve madde bazlı parçalama (2026-10-16)

**Neden.** §3'te bulunan kalite formu başlığı maddelerin ortasına giriyor.
Madde bazlı parçalama hem bir deney koşulu hem de test setinin
"dayanak madde" alanının işaret edeceği kimlik listesi.

**Nasıl.** [onisleme.py](../src/mevzuat_rag/onisleme.py) başlık ve altlığı
atıyor. [parcalama.py](../src/mevzuat_rag/parcalama.py) madde bazlı, paragraf
ve sabit uzunluklu parçalıyor.
[scripts/onisle.py](../scripts/onisle.py) bütün belgeleri işleyip
`data/processed/parcalar_madde.jsonl`'a yazıyor ve sonucu denetliyor. Ham
sonuç: [results/onisleme.json](../results/onisleme.json).

**Sonuç.**

| | değer |
|---|---|
| atılan metin | %7.7; temiz metinde başlık izi ve "Sayfa N-M" kalmadı |
| atılan başlık izleri | "Doküman No", "Yayın Tarihi", "Revizyon No", "Sayfa", "Form No" her biri 52 kez: 52 sayfanın her birinde bir |
| parçalar | 227 madde + 2 geçici madde + 1 giriş + 4 paragraf (YÖ-0087) + 150 takvim satırı = 384 |
| kapsama | 13/13 belgede parçalar temiz metni kayıpsız ve tekrarsız örtüyor |
| sayfa aralığı | 234/234 PDF parçasında aralık hem yeterli hem en dar |
| başlığı bulunan madde | 187/229 |
| birden çok sayfaya yayılan madde | 23 |
| madde uzunluğu (karakter) | min 16, p10 154, medyan 365, p90 1396, max 4142; 2000'in üstünde 11 madde |

Atılan 44 farklı satır kalıbının hepsine bakıldı: belge adları, kodlar,
tarihler, revizyon ve sayfa numaraları; gövde metni yok. Başlıksız 42
maddenin 6'sına elle bakıldı (çift anadal m6 ve m8, yan dal m5 ve m13,
yatay geçiş m7, hazırlık m5). Altısının da önünde gerçekten başlık yok,
doğrudan önceki maddenin cümlesi geliyor.

### Yol boyunca bulunan hatalar

İlk çalıştırmanın denetimi temiz görünüyordu. Aşağıdakiler eski ve yeni
çıktının parça parça karşılaştırılmasıyla ve sayfa görüntülerine bakılarak
bulundu.

1. **Tablo yanlış maddeye düştü.** YÖ-0002'nin not tablosu m4'ün altında
   duruyor (sayfa görüntüsüyle doğrulandı), ama çıkarılan metinde m6'nın
   sonundaydı. PyMuPDF m5-m6'nın blok kutusunu tablonun üst kenarından
   başlatıyor (y0 540.9'a karşı tablonun 541.3'ü). Blok yerine satır
   düzeyine geçildi. Eski çıktının 383 parçasından 4'ünün metni değişti:
   tablonun taşındığı iki madde, tablosu artık satır satır okunan bir madde
   ve YÖ-0087'nin paragraf gruplaması (bir parça daha eklendi). Başlıklar ve
   sayfa aralıkları aynı kaldı.
2. **Başlık tablosunun satırları birbirine değmiyor.** Satır düzeyinde
   "Revizyon No" ve "Sayfa" satırları "Doküman No"dan yayılarak bulunamadı.
   Kendileri de tohum yapıldı.
3. **Denetimim bir kalıntıyı kaçırdı.** Satır düzeyine geçince "Sayfa 10-3"
   temiz metne sızdı ve bir madde başlığı sanıldı: YN-0001 m13'ün başlığı
   "Sayfa 10-3" oldu, asıl başlık "Öğretim planları" m12'ye kaydı. Denetim
   yalnızca sabit izlere bakıyordu; karşılaştırma yakaladı. Denetime "Sayfa
   N-M" kalıbı eklendi.
4. **Tablo hücreleri başlık sanıldı.** "F4", "Başarısız" ve tek satıra
   birleşmiş "0-30 F4 Başarısız" kısa ve büyük harfle başlıyor. Artık başlık
   için en az üç harfli bir kelime gerekiyor, tablo satırları sekmeyle
   birleşiyor ve sekmeli satır başlık sayılmıyor. Boş satırın ötesine
   yalnızca "… BÖLÜM" başlığına ulaşmak için geçiliyor.
5. **Kaçan başlıklar.** "6/2/2023 Tarihli depremlere ilişkin hükümleri"
   rakamla başladığı için, "Önlisans-Lisans İngilizce Seviye Tespit Sınavı
   (ÖLİST)" iki satıra bölündüğü için kaçıyordu.
6. **Kendi kontrolüm iki kez yanlıştı.** Sayfa aralığı kontrolü, sayfa
   sınırını aşan parçalarda ve başlığı önceki sayfada kalan maddelerde
   yanlış alarm verdi. Kontrol konuma dayalı hale getirildi: parça, aralığın
   birleşiminde bulunmalı, aralık bir uçtan daraltılınca bulunmamalı.
   Maddenin başlangıç sayfası artık "MADDE N"nin sayfası; kaynak gösterirken
   kullanılacak sayfa bu.

**Paragraf sınırı eşiği ölçüldü, tahmin edilmedi.** Satır düzeyinde bloklar
arasındaki boş satırlar kayboldu. Bütün sayfalarda satır arası dikey boşluk
dağılımı iki tepeli çıktı: 0-3 pt'de 1907 aralık (paragraf içi), 10-15
pt'de 263 (paragraf arası), aradaki 5-9 pt'de yalnızca 19. Eşik 6 pt.

**Testler mutasyonla denendi.** 37 testin tamamı ilk çalıştırmada geçti. Üç
düzeltme bilerek geri alındı: "Sayfa" tohumu, sekme kuralı ve rakamla
başlayan başlık. İlk fikstür sekme kuralının geri alınmasını
**yakalamadı**, çünkü tablonun ardından başlıklı bir madde geliyordu. Gerçek
hatadaki gibi başlıksız bir madde eklendikten sonra üç mutasyonun üçü de
yakalanıyor.

**Ne göstermiyor / bilinen sınırlar.**

- YÖ-0019 m1'de bölüm adı ile madde başlığı yer değiştirmiş görünüyor
  ("BİRİNCİ BÖLÜM Amaç", başlık "Başlangıç Hükümleri"). Belgenin kendi metin
  sırası böyle; düzeltilmedi.
- YÖ-0087'nin paragraf parçaları dengesiz: 1844, 563, 3355 ve 76 karakter.
  Sonuncusu onay tablosu.
- Uzunluğu 2000 karakteri aşan 11 madde var. Gömme modelinin token sınırına
  takılabilirler (multilingual-e5 için 512 token). Türkçe token sayısı
  ölçülmedi; model seçilirken (hafta 3) bakılacak.
- Belgelerin sonundaki onay tabloları ("Yönergenin Görüşüldüğü Senato
  Kararı") son maddenin parçasına giriyor.

---

## 5. Başka biçimde bir belge eklenirse temizlik ne yapar (2026-10-16)

**Neden.** Bilgi tabanına sonradan belge eklenebilir
([K-016](kararlar.md)). Temizlik kuralları ise yalnızca GTÜ kalite formuna
göre yazılmıştı.

**Bulunan risk.** "Sayfa" hücresi ve "Form No:" satırı, sayfanın neresinde
olursa olsun başlık/altlık tohumu sayılıyordu. Mevcut 13 belgede ikisi de
yalnızca tabloda geçtiği için zararsızdı (§4: her biri tam 52 kez atıldı).
Başka biçimde bir belgede, altlıkta tek başına duran bir "Sayfa" satırı
üstündeki bütün sayfayı başlık sandırırdı. Kapsama denetimi bunu göremez,
çünkü parçaları temizlenmiş metinle karşılaştırıyor.

**Ölçüm ve önlem.** 52 sayfanın hepsi 842 pt. Başlık tohumlarının en alt
kenarı y=133'te (%16), altlığın en üst kenarı y=762.7'de (%91). Bu yüzden:

- başlık yalnızca sayfanın üst %25'inde, altlık yalnızca alt %15'inde
  aranıyor;
- "Sayfa" hücresi ancak aynı sayfada "Doküman No" veya "Revizyon No" varsa
  tohum sayılıyor.

Değişiklikten sonra 13 belgenin çıktısı byte düzeyinde aynı. Yeni bir test,
kalite formu olmayan bir sayfada gövdedeki "Form No:" satırının ve
altlıktaki "Sayfa"nın hiçbir şey sildirmediğini kontrol ediyor. İki bölge
sınırı ayrı ayrı kaldırılınca test kırılıyor.

**Denetime eklenen: sayfa başına atılan karakter.** 52 sayfada 174-259
arası (medyan 196). Önce oran kullanmayı düşündüm ve "sayfa başına en çok
~%20 atılıyor" diye tahmin ettim. Ölçünce en yüksek oran %48 çıktı: YÖ-0013'ün
son sayfasında yalnızca 218 karakter gövde var. Başlık ve altlığın boyutu
sabit olduğu için eşik mutlak bir sayı: 400 karakter.

**Bilgi tabanı sürümü.** Bütün kaynakların sha256'larından tek bir özet;
`results/onisleme.json`'da duruyor. Şu an `adf8b2efb4e1`; belge eklenince
ya da değişince değişir.

---

## 6. Sekiz belge eklendi: 22 kaynak (2026-10-16)

**Ne eklendi** ([K-017](kararlar.md)): YN-0009 (2017 öncesi girişliler),
YÖ-0042 Erasmus, YÖ-0044 Engelli Öğrenciler, YÖ-0093 Endüstriyel
Uygulamalar, YÖ-0094 GTU 101, YÖ-0100 GTU 110, YÖ-0116 Program Dışı Öğrenme
ve YÖK'ün geçiş/çift anadal/yan dal yönetmeliği (mevzuat.gov.tr'den güncel,
birleştirilmiş metin).

**Yol üstünde bulunanlar.**

- **Dizin ayrıştırıcısı yanlış bağlantı alıyordu.** YÖ-0048 ve YÖ-0093
  satırlarında belgeden önce bir form sayfasının bağlantısı var ("FR-0638
  için tıklayınız"); ayrıştırıcı ilk bağlantıyı alıyordu. Artık dosya
  bağlantısını tercih ediyor. Eski ve yeni dizin karşılaştırıldı: önceki 13
  belgenin hiçbirinin bağlantısı değişmedi.
- **EK MADDE tanınmıyordu.** YÖK yönetmeliğinin üç ek maddesi var ve
  bunlardan biri öğrencilerin en çok sorduğu "Ek Madde-1 ile yatay geçiş".
  Sayım denetimi bunu göremezdi, çünkü ek maddelerin kendi numaralandırması
  var ve asıl maddelerde boşluk bırakmıyorlar. Metinde "EK/GEÇİCİ MADDE"
  aranınca bulundu. Tanıyıcı artık `ek` türünü (`/e1`) de tanıyor.
- **mevzuat.gov.tr'nin PDF'i de her istekte farklı:** üç indirmede üç ayrı
  sha256. `kaynaklar.py kontrol`, dizinde olmayan belgeleri artık çıkarılan
  metnin özetiyle karşılaştırıyor. Byte'ları her seferinde değişen YÖK
  PDF'i için sonuç "metin aynı"; yöntem işe yarıyor.

**Sonuç.**

| | değer |
|---|---|
| kaynak | 21 PDF + takvim = 22 |
| yeni 8 belgede metin katmanı | 8/8 var, bozuk karakter 0 |
| madde başlıkları | 21 PDF'in 20'sinde 1..N eksiksiz; YÖ-0087'de madde yapısı yok |
| madde | 366 asıl + 5 geçici + 3 ek |
| başlık izleri | 84'er kez atıldı: 84 kalite formlu sayfanın her birinde bir. Formu olmayan YÖK belgesinden hiçbir şey atılmadı |
| parça | 532: 374 madde, 150 takvim satırı, 4 paragraf, 4 giriş |
| kapsama / sayfa aralığı / kalıntı | sorun yok |
| madde uzunluğu | medyan 395, p90 1683, max 8685 karakter; 2000'in üstünde 27 madde |
| `kontrol` | 22/22 güncel |
| bilgi tabanı sürümü | `b86309a098a2` |

**Bilinen sınırlar.**

- Erasmus yönergesi birkaç uzun maddeden oluşuyor (m6: 8685 karakter, 6.1,
  6.2 diye giden alt maddeler). Madde bazlı parçalamada bu parça tek bir
  gömme vektörüne sığmayabilir. Alt madde/fıkra düzeyinde bölme 3. haftada
  bir seçenek olarak değerlendirilecek.
- Endüstriyel Uygulamalar (18 madde) ve GTU 110'un (5/6 madde) maddelerinde
  başlık yok. Örneklenen maddelerde bu doğrulandı: madde doğrudan "MADDE 2-
  (1)…" diye başlıyor.

---

## 7. Site taraması: birimlerin sayfaları ve duyuruları (2026-10-16)

**Neden.** Ömer Can: bölüm, fakülte ve Öğrenci İşleri sayfalarının
duyurularında da belgeler var. Bilgi tabanına aday olanların neler olduğunu
görmek gerekiyordu.

**Nasıl.** [scripts/tara.py](../scripts/tara.py) 40 birimi tarıyor
([K-018](kararlar.md)). Her birim için ana sayfa, gömülü menüdeki bütün
site içi sayfalar ve duyuru listesi çekiliyor; Eylül 2025'ten yeni
duyuruların detay sayfaları da ekleri için. robots.txt yok (404); istekler
arasında 0.5 s bekleniyor. Belge indirilmiyor, yalnızca envanter
çıkarılıyor. [scripts/envanter.py](../scripts/envanter.py) dosyaları
tekilleştirip türlerine ayırıyor. Ham çıktı:
[results/tarama/](../results/tarama/).

**Sonuç.**

| | değer |
|---|---|
| birim | 40; bir sayfa (`kategori/9600`) iki çalıştırmada da HTTP 500 verdi, taranamadı |
| duyuru | 4824 |
| dosya bağlantısı | 4476 → 3253 tekil dosya |
| tekrarlanabilirlik | ikinci çalıştırma (önbellekten) sayıları birebir verdi |
| türler | form 900, sınav/ders programı 840, diğer 623, ilan/sonuç 389, öğretim planı 263, ders materyali 102, mevzuat 90, rehber 46 |
| yıl | 2025 ve sonrası 1105, öncesi 607, yıl yok 1541 |
| kişisel veri riski (başlıktan) | 297 |
| bilgi tabanında zaten olan | 7 |
| yönergelerin eski revizyonu | 12 |

**Sitede eski yönergelere bağlantı var.** 12 bağlantı, yürürlükten kalkmış
revizyonlara gidiyor: Yan Dal Yönergesi R2 (yürürlükte R6), ÇAP R2 (R3),
Yatay Geçiş R3 (R4), Muafiyet ve İntibak R1 (R2), Bilgisayar Müh. Staj
Esasları R0 (R1), Öğrenci Toplulukları R3 ve R4 (R6) ve diğerleri. Bölüm
sayfasından yönergeye ulaşan bir öğrenci eski kuralları okuyor. Bunlar
bilgi tabanına alınmaz; raporda kayda değer bir bulgu.

**Sınıflandırma ne kadar doğru.** Kurallar başlık ve dosya adına bakıyor.
İsabeti iki örneklemde, kuralın verdiği türü kendi etiketimle karşılaştırarak
ölçtüm. Etiketler benim; bağımsız bir etiketçi değil.

| örneklem (60 dosya) | uyum |
|---|---|
| A (tohum 42), kurallar düzeltilmeden önce | 50/60 (%83) |
| B (tohum 7), A'ya bakılarak düzeltilmiş kurallarla | **47/60 (%78)** |

Doğru sayı B: kurallar A'ya bakılarak düzeltildi, A üzerinde yeniden ölçmek
şişirirdi. A'daki hatalar kalıplıydı ve düzeltildi:

- sonuç listeleri "sınav" kelimesi yüzünden sınav programı sayılıyordu;
- "vize", "re**vize**"nin içinde eşleşiyordu;
- URL'den gelen dosya adlarında "İ" ayrışmış (I + U+0307) olabiliyor;
- büyük harfli ASCII "ILANI" Türkçe küçültmeyle "ılanı" oluyordu;
- kişisel veri kalıbındaki "asil", "nas**ıl**"ın içinde eşleşiyordu (bunu
  bir test yakaladı).

B'deki hataların çoğu belirsiz durumlar: sunum saatleri ders programı mı,
staj hibe sözleşmesi form mu.

**Ciddi olan: başlıktan kişisel veri tespiti güvenilmez.** B'deki iki
"Devamsızlıktan Kalanlar" listesi işaretlenmedi. Sonuç: hiçbir dosya
yalnızca türüne bakılarak bilgi tabanına alınmaz. İndirilen her belgenin
içeriği öğrenci numarası ve TC kimlik numarası örüntülerine karşı ayrıca
taranır ([K-019](kararlar.md)).

**Ne göstermiyor.** Yalnızca dosyalar envantere girdi. Duyuruların kendi
metinleri ve SSS gibi HTML sayfaları taranmadı. Eylül 2025'ten eski
duyuruların detay sayfalarındaki ekler de çekilmedi; listeden doğrudan
dosyaya bağlananlar ise envanterde.

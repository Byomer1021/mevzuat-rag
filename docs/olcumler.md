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

---

## 8. Bilgi tabanı genişledi: formlar, yönergeler, öğretim planları, web içerik (2026-10-17)

Ömer Can'ın kararıyla ([K-020](kararlar.md), [K-021](kararlar.md)) üç iş
birden: taramadan mevzuat/rehber seçimi, güncel öğretim planları, SSS ve
duyuru metinleri. Formlar ise ölçüme bağlandı.

### Formlar: mevzuat "hangi formu doldurmalıyım?" sorusunu cevaplamıyor

Önceki 532 parçanın yalnızca **6'sında** bir FR- form kodu geçiyor; 16 kodun
çoğu Endüstriyel Uygulamalar ve GTU 101/110'a ait. Kayıt dondurmayı
düzenleyen YN-0001 m19 hiçbir form adlandırmıyor. Oysa "FR-0853 Kayıt
Dondurma Başvuru Formu" var. Formların içeriği değil kataloğu gerekiyor: kod,
ad, bağlantı.

Kaynak, Kalite Ofisi'nin form listesi (`kategori/2382`): 683 Türkçe form,
birime göre gruplanmamış. Öğrenci formu süzgeci
([formlar.py](../src/mevzuat_rag/formlar.py)) adına bakıyor:

| sürüm | seçilen | gözle kontrol |
|---|---|---|
| ilk kurallar | 178 | ~35'i personel formu ("dilekçe" ve "ders" yüzünden: Doğum Dilekçesi, Profesör Atama, Ders Devam Çizelgesi…) |
| dışlama genişletildi | 132 | dışlananlarda 7 gerçek öğrenci formu: "Tek Ders Sınav Dilekçesi" ("ek ders" kalıbı "t**ek ders**"in içinde eşleşiyordu), Lisans/Lisansüstü İlişik Kesme, staj anketleri, topluluk tutanakları |
| istisnalar eklendi | **141** | dışarıda kalanlardan rastgele 25'inin 24'ü doğru dışlanmış (kaçan: Psikolojik Taciz başvurusu, eklendi) |

Prosedürler dizini (`kategori/2943`) de incelendi: 18 prosedürün hepsi kalite,
enerji ve satın alma süreçleri; öğrenciyle ilgisi yok.

### Kaynaklar: 22'den 114'e

| grup | belge | nereden |
|---|---|---|
| Kalite dizini, lisans öğrencisini ilgilendiren | 36 | fakülte ve bölüm staj esasları, dikey geçiş, diploma, yurt, kütüphane, topluluklar, psikolojik danışmanlık, ayrımcılıkla mücadele… |
| taramadan mevzuat ve rehber | 31 | 7592 sayılı af ve uygulama ilkeleri, 7 intibak kuralı, sınav ve mazeret esasları, bitirme kuralları ve kılavuzları, staj rehberleri ve SSS'leri, mezuniyet süreç rehberi, hazırlık öğrenci el kitabı, Düzensiz Öğrenci Rehberi… |
| öğretim planları | 21 | Öğrenci İşleri'nin "Lisans Bölümlerinin Öğretim Planları" sayfası (her programın güncel planı tek yerde) |
| form kataloğu | 1 | 141 öğrenci formu |
| web koleksiyonları | 3 | 31 SSS sayfası, 127 konu sayfası, 43 duyuru (§ aşağıda) |

**Düşenler, nedenleriyle.**

- **YÖ-0011** (Uluslararası Öğrenci Kabul, R7): dizinde bağlantısı boş, tahmin
  edilen adresler 404. Eski revizyon alınmadı.
- **Uçak Mühendisliği öğretim planı:** tamamen görüntü, 0 karakter. OCR
  kurulu değil.
- **"Öğrenim Süresi ve İlişik Kesme Esasları":** başlığa bakıp seçtim; ilk
  satırı "Lisansüstü Öğretim Süresi…". Yanlış seçim, çıkarıldı. Bunun
  üzerine taramadan seçilen 31 belgenin hepsinde lisansüstü terim ağırlığı
  sayıldı. İşaretlenen iki belge (İKT490, KİM 492) lisans dersi; "tez"
  orada bitirme tezi anlamında.

**Metin katmanı ve kişisel veri, 109 PDF.**

| | değer |
|---|---|
| metinsiz belge | 1 (Uçak planı, düştü) |
| gerçek kodlama bozulması (ý þ ð) | 0 |
| Symbol/Wingdings madde imi (özel kullanım alanı) | 12 belgede; ön işlemde "•" olur |
| kişisel veri izi (TC sağlamalı, ≥3 öğrenci no, Adı Soyadı) | 0 |

Ölçüm "bozuk karakter" sayacında madde imleriyle gerçek bozulmayı birlikte
sayıyordu; ilk 21 belgede ikisi de sıfır olduğu için fark görünmemişti.
Ayrıldı.

**Çelişki bulgusu.** Malzeme Bilimi'nin sayfasındaki staj esaslarının dosya
adı "04032026" (4 Mart 2026); dizindeki YÖ-0088'in revizyon tarihi 4 Mart
2024. Dizindeki resmî sürüm alındı.

### Web içerik: SSS, konu sayfaları, duyurular

Sayfa içeriği iki yerde ([web.py](../src/mevzuat_rag/web.py)): duyurularda
gömülü veride bir `"content"` alanında HTML, kategori sayfalarında sunucunun
ürettiği `<div class="rich-text-content">` içinde. İlk denemede başlık
"Sayfa bulunamadı" çıktı: gömülü veride 404 şablonunun h1'i de var; gövdeye
en yakın h1 alınıyor.

| | değer |
|---|---|
| çıkarılan metin | 1452: 1003 kategori sayfası, 449 duyuru |
| SSS sayfası | **31** (Öğrenci İşleri 70 bin karakter, SKS 19 bin, Uluslararası İlişkiler 27 bin, MYO, Yabancı Diller ve bölümler) |
| seçilen konu sayfası | 127 (başlıkta öğrenci konusu, ≥200 karakter; hakkında/kadro/lab/lisansüstü hariç) |
| seçilen duyuru | 43 (1 Ağustos 2026 ve sonrası; 376 eski duyuru dışarıda) |
| birden çok birimde yayımlanan, birleştirilen | 5 |
| kişisel veri yüzünden dışarıda | 1 sayfa |

Duyuru kimlik eşiği (25500) tarihleri kabaca tutturdu; dışarıda kalan en eski
tarih Nisan 2025. Bir duyuruda "Nisan 2027" yazıyor, sayfadaki bir yazım
hatası.

---

## 9. Genişlemenin ön işlemde ortaya çıkardıkları (2026-10-17)

114 kaynakla ilk çalıştırmada denetim yalnızca 3 kalıntı bildirdi. Asıl
hatalar en uzun parçalara ve madde numarası boşluklarına bakınca çıktı.

1. **Yeni madde biçimleri.** Tanıyıcı genişledi; her biri testle sabit:
   - "MADDE 12a:" harfli alt madde (YÖ-0018): 12a ve 12b, 12'ye yığılıp
     17 bin karakterlik bir parça yapıyordu;
   - "Madde 11 Engelsiz GTÜ Birimi" ayraçsız (YÖ-0001);
   - "Madde 9. 20 (yirmi) iş günü" noktadan sonra rakam (YÖ-0084);
   - "EK MADDE 1 –" (§6).
2. **Satır başına düşmüş atıf başlık sanıldı.** "Madde 4a. kapsamında…" 12a'yı
   ikiye bölüp aynı kimliği iki kez üretti; kimlik çakışması denetimi
   yakaladı. Noktalı biçimde noktadan sonra "(", büyük harf ya da rakam
   şartı kondu.
3. **Başıboş başlıklar.** Kimya Mühendisliği'nin öğretim planında geçen tek bir
   "Geçici Madde", bütün ders tablolarını 12 bin karakterlik bir maddeye
   yığıyordu. Belge ancak en az 3 asıl madde başlığı varsa madde bazlı
   bölünüyor; öğretim planları her zaman paragraf bazlı.
4. **Ekteki formların altlığı** sayfanın ortasında kalabiliyor (YÖ-0046 s7).
   Kalite altlığının tam kalıbı, bölgeden bağımsız tek satır olarak atılıyor.
5. **Denetimin yanlış alarmı.** "Revizyon Tarihi", Kimya'nın CHEM 492
   esaslarında belgenin kendi notu olarak geçiyor. Denetim artık yalnızca
   başlık tablosuna özgü izlere ("Doküman No", "Revizyon No", altlık
   kalıbı) bakıyor.

Ayraçsız biçim eklenirken her belgenin başlık sayısı önceki ölçümle
karşılaştırıldı: yalnızca beklenen iki belge ve lisansüstü esaslar değişti.
Sonuncusu yukarıdaki yanlış seçimi ortaya çıkardı.

**Sonuç.**

| | değer |
|---|---|
| kaynak | 114: 109 PDF, takvim, form kataloğu, 3 web koleksiyonu |
| madde yapısında belge | 52; madde numarası boşluğu 0 (7592 alıntısı hariç, madde moduna girmiyor) |
| parça | **4759**: 914 madde (901 asıl, 8 geçici, 5 ek), 1631 paragraf, 1914 web, 150 takvim, 141 form, 9 giriş |
| kapsama / sayfa aralığı / kimlik çakışması / kalıntı / kişisel veri | sorun yok |
| aynı metni taşıyan iki kaynak | yok |
| madde uzunluğu | medyan 395, p90 1580, max 9289; 2000'in üstünde 57 |
| testler | 121 |
| bilgi tabanı sürümü | `b3c7d85cce08` |

**Bilinen sınırlar.**

- **Öğretim planları güz ve bahar dönemini yan yana iki sütunda veriyor.**
  Satır satır okununca iki dönemin dersi aynı satıra düşüyor ("CSE 241 …
  CSE 222 …"). Başlık satırı parçada, ama "CSE 222 hangi dönem?" türü
  sorular için bir hata kaynağı.
- **Kimya CHEM 492 esasları taranmış ve OCR'lanmış bir PDF:** "eğitim-öğreüm",
  "2O24" gibi hatalar ve sondaki imzadan gelen anlamsız karakterler var.
- 207 madde başlıksız; yeni belgelerde örneklenenlerin önünde gerçekten
  başlık yok (Endüstriyel Uygulamalar, GTU 110 gibi).

---

## 10. Araştırma sorusunun iki koşulu ve ilk bakış (2026-10-17)

**Neden.** Dersin öneri formu (21 Ekim) tek ve kontrollü bir karşılaştırma,
adı konmuş bir taban sistem ve kendi verimizden bir "ilk bakış" sayısı
istiyor ([K-022](kararlar.md), [oneri.md](oneri.md)). Soru seti henüz yok;
bu bölüm arama başarısını **ölçmüyor**, iki koşulun ne kadar farklı olduğunu
ve aramanın çalıştığını gösteriyor.

**Nasıl.** `scripts/onisle.py` artık iki küme yazıyor: `parcalar_madde.jsonl`
ve `parcalar_sabit.jsonl`. İkincisinde yalnız madde parçasına bölünen 49
belge sabit uzunlukta, örtüşmesiz kesiliyor; geri kalan her parça aynı. (§9'daki
52, en az bir madde başlığı geçen belge sayısıydı: 7592 alıntısı, Kimya
intibak esasları ve Kimya öğretim planında üçten az asıl madde var,
paragraf bazlı bölünüyorlar.) Her parça artık belgenin birleşik metnindeki
aralığını (`bas`, `son`) taşıyor; `metin == belge[bas:son]` testle sabit.
`scripts/ilk_bakis.py` → `results/ilk_bakis.json`.

**Sabit boyut, parça sayısı eşit olacak şekilde.** Bu 49 belgede toplam
karakter / parça sayısı = 694. Bu boyutla 959 parça çıktı, çünkü kesim kelime
sınırına çekilince parçalar kısalıyor. Sayı eşitlenene kadar büyütüldü:
**721 karakterde 922 parça** (madde koşulu 923).

**Sonuç: koşullar metnin çoğunda ayrışıyor.**

| | değer |
|---|---|
| madde (49 belge) | 914 |
| tek bir sabit parçanın içinde kalan madde | 365 |
| 2 / 3 / 4 / 5 / 6+ parçaya bölünen | 368 / 111 / 35 / 25 / 10 |
| **bölünen madde oranı** | **%60.1** |
| birden çok maddeye değen sabit parça | **570 / 922 (%61.8)** |
| deney dizini (yalnız PDF) | 2554 madde koşulunda, 2553 sabit |
| iki BM25 dizininin kurulması | 0.7 s; sorgu ~5 ms |

**Gösterim sorusu: "Derslere devam zorunluluğu yüzde kaç?"** (dayanak
`lisans-yonetmelik/m23`, 298 karakter, tamamı tek sabit parçada, `s23`).
BM25, belge adı önekli, kök bulmasız.

- **Bütün bilgi tabanı (web dahil):** iki koşulda da ilk üç aynı; ikisi SSS
  cevabı ("Teorik derslere devam zorunluluğu … en az %70"), biri Yabancı
  Diller Bölümü'nün hazırlık programı sayfası (%85). Cevap doğru ama dayanak değil. Web parçaları iki
  koşulda aynı olduğu için karşılaştırmaya bilgi katmıyor, yalnız mutlak
  sayıları bozuyor. **Bu yüzden deneyin dizini yalnız PDF'ler** (K-022).
- **Yalnız PDF:** madde koşulunda m23 **4.**; ilk sırada hazırlık
  yönergesinin %85 devam maddesi (yanlış program için makul bir cevap). Sabit
  koşulda m23'ü bütünüyle içeren s23 **10.**

**Ne anlama gelmiyor.** Tek soru, bizim seçtiğimiz, dev bölümünde sayılıyor;
ortalama bir fark hakkında hiçbir şey söylemiyor. Hazırlık maddesinin öne
çıkması ayrıca bir hata türü: soru programı belirtmiyor.

**Kök bulucu** (`snowballstemmer` 3.1.1, Türkçe; K-013). "yönetmeliğin",
"yönetmelikte" → "yönetmelik"; "derslere" → "ders"; "sınavları" → "sınav".
Ama "devam" → "deva" ve "kanun" → "kan" (agirgol'un Türk kanunlarında
bulduğu hatanın aynısı) ve "devamsızlık" "devam"a inmiyor. Varsayılan
arama kök bulmasız; kök bulma ayrı bir ölçüm.

**Kanıt alıntısı ve değerlendirme kodu.** Test setine `kanit` alanı eklendi
(henüz soru yazılmadığı için şema değişikliği ücretsiz): her dayanağa
maddeden birebir kopyalanmış cevap cümlesi; boşluk farkı gözetilmeden
aranıyor, bulunamazsa kayıt reddediliyor. `degerlendirme.py`: kanıt kapsamı,
Recall@k, MRR, eşleştirilmiş bootstrap, kesin McNemar. 145 test.

*Not (§11):* paragraf düzeltmesinden sonra dizin 3332 parça ve gösterim
sorusunda madde **3.** sırada; yapısal oranlar (%60.1, %61.8) değişmedi.

---

## 11. Yoğun aramanın girdi sınırı ve öğretim planı tabloları (2026-10-17)

**Neden.** Öneri formunun ikinci riski "uzun maddeler 512 tokeni aşabilir,
ölçülmedi" diyordu. Türk kanunlarındaki karşılaştırmada bütün maddenin
pencerelere kaybetmesinin bir nedeni buydu (K-022).

**Nasıl.** `scripts/token_olcum.py`: parça, dizine girdiği biçimiyle
("passage: " + belge adı + metin) `intfloat/multilingual-e5-base`'in kendi
tokenizer'ıyla sayılır; 512'yi aşan parça ve sınırın ötesinde kalan
karakter. Yalnız deney dizini (PDF). → `results/token_olcum.json`.

**İlk ölçüm bir parçalama hatası buldu.** Madde koşulunda 95 parça
sınırı aşıyordu, 52'si iki koşulda ortak paragraf parçasıydı; en uzunu
3753 token. Öğretim planı tablolarında boş satır yok; paragraf bölücü
yalnız boş satırda kestiği için bir plan 13.877 karakterlik tek parça
oluyordu. Düzeltme: hedefin (madde medyanı, 395) iki katından uzun
boşluksuz blok satırlarına bölünüp satırlar hedefe kadar birleştiriliyor
(`parcalama.UZUN_PARAGRAF`, iki testle sabit). Paragraf parçası 1631'den
2409'a, toplam 4759'dan 5537'ye çıktı; denetim temiz.

Kaynak dosyalar değişmediği için bilgi tabanı sürümü `b3c7d85cce08` aynı
kaldı ama paragraf kimlikleri değişti. Bunu yakalamak için ön işlem raporu
artık ayrıca **parça sürümü** taşıyor (kimlik + metin özeti):
`2b5af885972a`. Deney sonuçları ve Soru Defteri bunu da yazıyor. Henüz
soru yazılmamıştı; kimse etkilenmedi.

**Sonuç (düzeltmeden sonra).**

| | madde koşulu | sabit koşulu |
|---|---|---|
| deney dizini | 3332 parça | 3331 parça |
| token medyanı / en uzun | 104 / 2106 | 116 / 287 |
| 512'yi aşan parça | **43, hepsi madde** | **0** |
| sınırın ötesinde kalan metin | %3.0 | %0 |
| karakter / token | 4.03 | 4.03 |

914 maddenin 43'ünün (%4.7) sonu yoğun arama modeline hiç ulaşmıyor; sabit
pencerelerde bu yok. Yoğun aramada madde koşulunun bilinen bir dezavantajı
bu; dayanağı sınırın ötesinde olan test soruları ayrı raporlanacak.

**Gösterim sorusu, BM25** (`scripts/deney.py`, tek soru, duman testi):
madde koşulunda kanıt 3. sırada (MRR 0.333), sabit koşulda 10. sırada
(0.100). Dizin kurulması iki koşul için 0.7 s.

**GPU.** e5 kodlaması GPU'da `CUDA error: unknown error` ile düştü ve
ekran gitti; kart arızalı (K-002). Yoğun arama artık CPU'da.

**e5, CPU'da** (i7-8750H, 6 çekirdek; tek çalıştırma, aynı anda test takımı
da çalıştı): iki dizinin (3332 + 3331 parça) kodlanması **988 s**, sonra
`.cache/gomme/`'den anında. Sorgu 0.3 s. Gösterim sorusunda e5 kanıtı iki
koşulda da **1.** sıraya koydu (BM25: 3. ve 10.). Tek soru; yalnız boru
hattının çalıştığını gösterir.

---

## 12. Dev setinde ilk karşılaştırma (2026-10-19)

**Neden.** Ara rapor (5 Kasım) taban sistemin sayılarını istiyor ve deney
hattı gerçek sorularla ilk kez uçtan uca çalışmalı. Bu bölüm araştırma
sorusunun cevabı **değil**: test seti henüz yok (K-022).

**Nasıl.** 51 dev sorusu (30 tek, 13 çok maddeli, 8 cevapsız), hepsini
Ömer Can Soru Defteri'nde yazdı (`811ac80`). **Birincil küme 37 soru** (28
tek, 9 çok): cevaplanabilir ve bütün dayanakları madde yapılı 49 belgede.
Altısı dışarıda, çünkü dayanaklarından biri SSS (4), akademik takvim (1) ya
da form kataloğu (1). Tüm-PDF kümesi de aynı 37 soru çıktı, ayrıca
raporlanmadı. Dizin yalnız PDF: 3332 madde koşulunda, 3331 sabit. Kapsam:
ilk k parçadan altın belgeye ait olanların birleşimi kanıt alıntısını
örtüyor mu; çok dayanaklı soruda örtülen kanıtların oranı (0.5 gibi
değerler bundan). McNemar ikili: bütün kanıtlar örtüldü mü. Bootstrap 10 000
örnek. `scripts/deney.py`, dört çalıştırma, hepsi CPU →
`results/deney/{bm25,bm25-kok,bm25-onekyok,e5}-dev.json`.

**Sonuç.**

| | madde R@5 | sabit R@5 | fark [%95 GA] | yalnız madde / yalnız sabit, p |
|---|---|---|---|---|
| BM25 | 0.149 | 0.176 | −0.027 [−0.162, +0.081] | 2 / 3, p = 1.00 |
| BM25, kök bulmalı | 0.135 | 0.189 | −0.054 [−0.162, +0.054] | 1 / 3, p = 0.63 |
| BM25, belge adı öneksiz | 0.149 | 0.176 | −0.027 [−0.162, +0.081] | 2 / 3, p = 1.00 |
| **e5** | **0.595** | 0.365 | **+0.230 [+0.108, +0.378]** | **9 / 0, p = 0.004** |

e5'in öteki ölçüleri (madde / sabit, fark [GA]): R@1 0.162 / 0.122, +0.041
[−0.081, +0.176]; R@10 0.635 / 0.459, +0.176 [+0.054, +0.311]; MRR@10
0.335 / 0.197, +0.137 [+0.040, +0.246]. BM25: R@1 0.068 / 0.027, R@10
0.216 / 0.230, MRR@10 0.089 / 0.074. Süre: BM25 dizini 0.8 s; e5 dizini
100.9 s (vektörler önbellekten; sürenin modeli yüklemeye mi gittiğini
ayırmadım), 74 sorgu 8.0 s.

**BM25'te koşulun ayırt edilememesinin bir nedeni ölçüldü.** BM25'in ilk
5'indeki parçaların yalnız %31'i (madde) ve %29'u (sabit) iki koşulun
farklı olduğu 49 belgeden; geri kalanı iki koşulda aynı olan paragraf
parçaları (SSS ve el kitabı PDF'leri, öğretim planları). e5'te bu oran %58
ve %60. Yani BM25'te karşılaştırılan şey getirilenin üçte birinden az.
Altın belgeden gelen parça oranı: BM25 %12 / %14, e5 %27 / %34.

**e5'te ayrışan 9 sorunun hepsini madde koşulu kazandı.** Bunların 4'ünde
kanıt iki sabit pencereye bölünmüştü (q018, q021, q035, q048). Öteki 5'inde
(q001, q019, q025, q031, q032) kanıt tek pencerenin içindeydi ama o pencere
7., 8., 10. sırada ya da ilk 10'un dışındaydı. Bölünme tek açıklama değil;
pencerenin komşu maddelerle karışması bir aday, ölçmedim. Sabit koşul altın
belgeden daha çok parça getiriyor (%34'e %27) ama kanıtlı pencereyi daha az
buluyor. Birincil kümedeki 46 kanıtın 10'u iki ya da daha çok sabit
pencereye bölünüyor. BM25'te ayrışan 5 soru: madde q003, q018; sabit q024,
q036, q038.

**512 token sınırı dev setinde madde koşuluna zarar vermedi.** 46 kanıtın 9'u
512 tokeni aşan bir maddede (§11); dokuzunda da kanıt sınırın içinde, en
yakını sınırdan 118 karakter önce bitiyor (q009, `staj-muhendislik/m9`).

**Eşit k, eşit metin değil.** e5'in ilk 5'i madde koşulunda ortalama 3577
karakter, sabitte 2735 (medyan 2613 ve 2898): uzun maddeler geldiğinde
madde koşulu daha çok metin döndürüyor. Parça sayısı eşit tutulduğu için
ortalama parça boyu iki koşulda aynı; getirilen metin miktarı aynı değil.
Final raporunda ayrıca verilmeli.

**Ne anlama gelmiyor.**

- **Dev seti.** Sorular deney hattı geliştirilirken yazıldı ve görüldü;
  yazan ve dayanakları işaretleyen tek kişi (Ömer Can), uyuşma ölçülmedi.
  Bu sonuca bakılarak parçalama, sabit boyut ya da istem değiştirilirse dev
  artık bağımsız değil. Kararı dört yazarlı test seti verir.
- **n = 37.** BM25'te "fark yok" değil, "bu örneklemde ayırt edilemiyor":
  güven aralığı 24 puan genişliğinde. e5 farkının aralığı sıfırı dışarıda
  bırakıyor ama alt sınırı +0.108: fark 11 puan kadar küçük de olabilir.
- **Kanıt kapsamı bir arama ölçüsü.** Cevabın doğru olup olmadığını
  söylemiyor; dil modeli henüz çalıştırılmadı.
- **BM25'in mutlak düzeyi düşük** (R@5 ~0.15). Soruların günlük dili
  ("agnom", "kulüp", "ff dersim") ile yönetmelik dili arasındaki fark ve
  birbirine benzeyen birim yönergeleri olası nedenler; ölçülmedi, hata
  analizi aracı bunun için.

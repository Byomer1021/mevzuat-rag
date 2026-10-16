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

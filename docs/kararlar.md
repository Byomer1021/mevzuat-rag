# Kararlar

Her tasarım kararı bir kayıt: ne seçildi, alternatifler, gerekçe, neyle
değişir. Değişen karar silinmez, üstü çizilir ve yeni kayda bağlanır.

Durum: **geçerli**, **açık** (karar bekliyor), **öneri** (onay bekliyor),
**değişti** (→ K-NNN).

---

## K-001: Proje konumu ve depo, geçerli (2026-10-16)

- Yerel: `D:\mevzuat-rag`. C'de 13 GB boş alan var, D'de ~580 GB.
- Uzak: `github.com/Byomer1021/mevzuat-rag`, **private**.
- Public'e geçiş, veri lisansı kontrol edildikten sonra (K-004):
  `gh repo edit Byomer1021/mevzuat-rag --visibility public --accept-visibility-change-consequences`.

## K-002: torch 2.7.1 + CUDA 11.8 derlemesi, geçerli (2026-10-16)

**Kısıt.** GPU GTX 1080 (Pascal, sm_61), sürücü 526.47. nvidia-smi bu
sürücünün en fazla CUDA 12.0 desteklediğini söylüyor.

**Seçenekler.**

| | artı | eksi |
|---|---|---|
| **a) cu118, torch 2.7.x** | sürücüyle uyumlu; sm_61 kernel'i içerdiği ve çalıştığı ölçüldü ([olcumler §1](olcumler.md)) | torch 2.7'de kalınıyor |
| b) sürücüyü güncelle, cu12x ile yeni torch | yeni torch özellikleri | önceki projede kararsız davrandığı bilinen bir kartta sürücü değiştirmek; yeni derlemelerin Pascal desteği ayrıca doğrulanmalı. **Denenmedi.** |
| c) yalnız CPU | sürücüden bağımsız | gömme ve reranker çalıştırmaları her deney turunda çok daha yavaş (ölçülmedi) |

**Seçilen: (a).** Gereken yalnızca çıkarım; torch 2.7 bunun için yeterli.
`pyproject.toml`'da `torch>=2.5,<2.8` ve `pytorch-cu118` indeksi sabit.

**Değişirse:** sürücü güncellenirse veya proje bulut GPU'ya taşınırsa.

## K-003: Önbellekler D'de, global ortam değişkeni yok, geçerli (2026-10-16)

- uv önbelleği: `D:\.cache\uv`. Komutla verilir: `$env:UV_CACHE_DIR = "D:\.cache\uv"`.
- HF model önbelleği: `D:\.cache\huggingface`. `.env` dosyasındaki `HF_HOME`
  ile, paket import edildiğinde yüklenir (`src/mevzuat_rag/__init__.py`).

**Neden global değil.** `setx` ile kullanıcı düzeyinde ayarlamak diğer
projelerin önbellek yerini de değiştirir; C'deki mevcut HF önbelleğindeki
modeller onlar için görünmez olur, yeniden inerdi. Proje kendi önbellek yerini
kendi taşıyor.

**Dikkat.** `UV_CACHE_DIR` verilmeden çalıştırılan bir `uv sync` torch'u
(~2.7 GB) yeniden C'ye indirir. Kalıcı olsun istenirse ileride `setx` ile
ayarlanabilir.

## K-004: Ham PDF'ler depoya girer, işlenmiş metin girmez, geçerli (2026-10-16)

**Neden.** Yönetmelik güncellendiğinde eski sürüm siteden kaybolur; oysa her
deney sonucu belgenin belirli bir sürümüne bağlı. PDF'in kendisi ve
`data/kaynaklar.csv`'deki sha256 olmadan sonuç yeniden üretilemez. İşlenmiş
metin ve parçalar koddan yeniden üretilebildiği için depoya girmez.

**Açık nokta.** Belgeler üniversitenin kamuya açık resmî metinleri. Repo
public yapılmadan önce yeniden dağıtımlarının serbest olduğu teyit edilecek.
Bu henüz doğrulanmadı.

## K-005: Cevap üretimindeki dil modeli, açık

Hafta 2 sonundaki bir pilot ölçümle, 2 Kasım'dan (hafta 3) önce karar
verilecek.

**Araştırma sorusunun yarısı dil modelinden bağımsız.** Recall@k ve MRR
yalnızca aramayı ölçer; parçalama ve arama karşılaştırması model seçilmeden
yapılabilir. Dil modeli yalnızca cevap doğruluğunu, sadakati, cevaplamamayı
ve alıntıyı etkiler. Bunun için bütün konfigürasyonlarda **sabit** kalmalı,
yoksa arama farkıyla model farkı birbirine karışır.

**Maliyet: tahmin, ölçülmedi.** Varsayım ~5000 çağrı (dev setinde ayar, 6
konfigürasyon × ~200 soru, birkaç tekrar), çağrı başına ~3000 girdi ve ~300
çıktı tokenı; toplam 15M girdi ve 1.5M çıktı. Fiyatlar Anthropic'in
2026-10-06 tarihli listesinden; kullanmadan önce konsoldan teyit edilmeli.

| model | girdi / çıktı, $ / 1M token | ~5000 çağrı |
|---|---|---|
| Claude Haiku 5.5 (`claude-haiku-5-5`) | 0.10 / 0.50 | ~$2 |
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | 2 / 10 | ~$45 |
| Claude Opus 5.5 (`claude-opus-5-5`) | 4 / 20 | ~$90 |

Bu hesapta olmayanlar:

- Düşünme tokenları çıktı olarak faturalanır; Opus 5.5'te düşünme
  kapatılamıyor.
- Türkçe metnin gerçek token sayısı `count_tokens` ile ölçülmedi.
- Değerlendirmede dil modeli puanlayıcı kullanılırsa onun çağrıları.

Deneyler gecikmeye duyarlı olmadığı için Batch API'ye uygun, o da fiyatı
yarıya indiriyor.

**Tekrarlanabilirlik.** Bu modeller varsayılan dışı bir sıcaklık değerini
kabul etmiyor (400 döner); "sıcaklık 0 ile deterministik" seçeneği yok.
Bunun yerine model kimliği ve efor seviyesi sabitlenir, her cevap diske
kaydedilir, aynı konfigürasyon bir kez iki kez çalıştırılıp tekrarlar arası
fark ölçülür. Konfigürasyonlar arasındaki fark bu gürültüden büyük değilse
anlamlı sayılmaz.

| | artı | eksi |
|---|---|---|
| API | Türkçe talimat takibi güçlü, hızlı, ölçüm haftaları kısalır | maliyet (yukarıda), çıktılar deterministik değil |
| yerelde açık model (GTX 1080, 8 GB) | ücretsiz; NLP dersi için açık model kullanmak artı olabilir | hız ölçülmedi; 7-9B modellerin Türkçe "bilmiyorum" ve madde alıntılama disiplini ölçülmedi; kart daha önce uzun yükte düştü |

**Öneri.** Hafta 2'de dev setinden ~20 soruyla bir pilot. Adaylar Haiku 5.5
ve Sonnet 5.5, isteğe bağlı olarak bir de yerel model. Ölçülecekler: cevapsız
sorularda "bilmiyorum" oranı, madde numarası doğruluğu, soru başına süre ve
gerçek token/maliyet. Haiku farkı kapatıyorsa Haiku seçilir, kapatmıyorsa
Sonnet. Karar Ömer Can'ın; pilotun maliyeti onaydan önce ölçülüp yazılır.

**Açık soru:** dersin hocası açık kaynak model şartı koyuyor mu? Koyuyorsa
tablo tersine döner.

## K-006: RAG çerçevesi (LangChain/LlamaIndex) kullanılmıyor, geçerli (2026-10-16)

Parçalama ve arama doğrudan kütüphanelerle yazılıyor (PyMuPDF, rank-bm25,
sentence-transformers, FAISS).

**Neden.** Deneyin konusu tam olarak parçalama ve arama. Bu adımlar bir
çerçevenin içinde varsayılan ayarlarla kalırsa neyin ölçüldüğü belirsizleşir.
Madde bazlı parçalama (`MADDE 12 –` gibi başlıklarla bölmek) zaten özel kod
gerektiriyor. Ayrıca bağımlılık yüzeyi küçük kalıyor.

**Değişirse:** RAGAS gibi değerlendirme araçları bir çerçeve nesnesi isterse,
yalnızca o katmanda adaptör yazılır.

## K-007: Test seti geliştirme ve test olarak ikiye bölünür, öneri

- **dev:** hafta 1-2'de yazılan ilk ~50 soru. Prompt, `bilmiyorum` eşiği, k,
  parça boyutu gibi her ayar burada yapılır.
- **test:** sonra yazılan ~150+ soru. Konfigürasyonlar bittikten sonra bir kez
  çalıştırılır; rapordaki sayılar buradan gelir.

**Neden.** Aynı sorulara bakarak ayar yapıp aynı sorularla ölçmek, sonucu
olduğundan iyi gösterir. Bu fark raporda "neden bu sayıya güvenilir" sorusunun
cevabı olur. Proje tanımında böyle bir ayrım yok; öneri bize ait.

## K-008: Kapsam ve bağlam, geçerli (2026-10-16)

- **Üniversite:** Gebze Teknik Üniversitesi.
- **Bağlam:** NLP dersi projesi, **tek kişi**.
- **Teslim:** yaklaşık 20-25 Aralık 2026. Plan en erken tarihe, **20
  Aralık**'a göre yapılıyor. Hafta 1, 19 Ekim'de başlıyor; böylece tanımdaki
  10 hafta 9'a iniyor.

**Etkileri.**

- Tanımdaki dört rol tek kişide birleşiyor.
- Cohen's Kappa için ikinci bir etiketçi gerekiyor. Öneri: bir sınıf
  arkadaşı 40-50 soruyu bağımsız olarak etiketlesin. Olmazsa raporda
  sınırlılık olarak yazılır.
- Test seti hedefi alt sınırda: 50 dev + 150 test = 200 soru.

## K-009: Bilgi tabanı 13 belge ve akademik takvim, geçerli (2026-10-16)

Kaynak: GTÜ Kalite Ofisi dizini ([olcumler §2](olcumler.md)). Yalnızca
yürürlükteki Türkçe revizyon alınıyor. Tam liste ve sha256'lar
[data/kaynaklar.csv](../data/kaynaklar.csv)'de.

| konu | belge |
|---|---|
| ana kurallar (devam, sınav, not, itiraz, süre) | YN-0001 Ön Lisans ve Lisans Eğitim-Öğretim Yönetmeliği R7 |
| yaz okulu | YN-0015 Yaz Öğretimi Yönetmeliği R1 |
| hazırlık | YÖ-0002 İngilizce Hazırlık Eğitim-Öğretim ve Sınav Yönergesi R9 |
| çift anadal, yan dal | YÖ-0004 ÇAP Yönergesi R3, YÖ-0012 Yan Dal Programı Yönergesi R6 |
| yatay geçiş | YÖ-0013 Yatay Geçiş Yönergesi R4 |
| muafiyet | YÖ-0007 Muafiyet ve İntibak Yönergesi R2, YÖ-0118 Ders Muafiyet Sınavı Uygulama Esasları R0 |
| staj | YÖ-0019 Mühendislik Fakültesi Staj Yönergesi R4, YÖ-0087 Bilgisayar Müh. Staj Uygulama Esasları R1 |
| azami süre | YÖ-0078 Azami Süreyi Tamamlayan Öğrenciler Usul ve Esasları R3 |
| danışmanlık | YÖ-0066 Öğrenci Danışmanlığı Yönergesi R2 |
| maddi destek | YÖ-0025 Kısmi Zamanlı Öğrenci Çalıştırma Yönergesi R2 |
| tarihler | 2026-2027 Akademik Takvim (HTML tablo) |

**Bilerek seçilen çiftler.** İki staj belgesi (fakülte ve bölüm; YÖ-0087,
YÖ-0019'a açıkça atıf yapıyor) çok belgeli sorular için seçildi. İki muafiyet
belgesi (adları ve konuları yakın) arama için zor bir ayrım sağlıyor.

**Burs.** Tanımda geçiyor ama GTÜ'de burs yönergesi yok
([olcumler §2](olcumler.md)). Öğrencinin maddi destek sorularının mevzuattaki
karşılığı olarak YÖ-0025 alındı.

**Dışarıda bırakılanlar.**

- YN-0009 (2017 öncesi girişliler için eski yönetmelik): aynı sorulara
  çelişen cevaplar üretir. İleride bir "sürüm çatışması" deneyi için aday.
- Lisansüstü yönetmelik ve esasları: kapsam lisans.
- Erasmus (YÖ-0042), engelli öğrenciler (YÖ-0044), dereceye giren mezunlar
  (YÖ-0003): daha seyrek soru konuları. Tanımın üst sınırı 15 belge; yer var,
  gerekirse eklenir.
- İngilizce çeviriler.

## K-010: PDF çıkarıcı PyMuPDF; çıkarıcı karşılaştırması deney ekseninden çıktı, geçerli (2026-10-16)

İki çıkarıcı bu belgelerde aynı karakterleri veriyor; gövde metinleri
%97.7-99.9 benzer ([olcumler §3](olcumler.md)). Tanımdaki "1. belge işleme"
adımı bu derlemde sonucu değiştirecek bir seçim değil. PyMuPDF'in
seçilmesinin iki nedeni var: başlık tablosunu tek blok olarak verdiği için
temizlemesi daha kolay, ayrıca bu çalıştırmada 0.29 s'ye karşı 8.28 s sürdü
(tek ölçüm).

**Değişirse:** tablo içeren veya iki sütunlu bir belge eklenirse
karşılaştırma tekrarlanır.

## K-011: Akademik takvim TSV olarak saklanır, geçerli (2026-10-16)

Takvim sayfasının HTML'i her istekte farklı byte'larla geliyor; ham HTML'in
sha256'sı değişikliği gösteremiyor ([olcumler §2](olcumler.md)). `kaynaklar.py
indir`, sayfadaki tabloyu `data/raw/akademik-takvim-2026-2027.tsv`'ye
çıkarıyor ve özeti bu dosyadan alıyor. Ham HTML saklanmıyor.

## K-012: Sayfa başlığı temizliği her konfigürasyonda yapılır, öneri

Kalite formu başlığı metnin %6-10'u ve maddelerin ortasına giriyor
([olcumler §3](olcumler.md)). Temizlik bir deney değişkeni olarak değil,
bütün konfigürasyonlarda uygulanan bir ön işlem olarak ele alınıyor.
Etkisi taban sistemde **bir kez** ölçülür (temizlikli ve temizliksiz
Recall@k). Ucuz bir ölçüm ve raporda "ön işlem neden gerekli" sorusunu
cevaplar.

## K-013: BM25'e Türkçe kök bulma varyantı, öneri

Türkçe eklemeli bir dil. "yönetmeliğin", "yönetmelikte", "yönetmeliğe" ham
tokenlarla BM25'te üç ayrı terim; soru ile madde aynı kökü farklı eklerle
kullandığında eşleşme kaçar. NLP dersi açısından projenin en doğrudan
Türkçe'ye özgü sorusu bu.

Önerilen deney: BM25'i ham tokenlarla ve kök bulma sonrası ayrı ayrı
çalıştırmak. Yalnızca arama metrikleriyle ölçülür, dil modeli gerektirmez,
bu yüzden ucuz. Aday araçlar `snowballstemmer` (Türkçe kök bulucu) ve
`zeyrek` (Zemberek tabanlı lemmatizer); ikisi de henüz kurulup denenmedi.

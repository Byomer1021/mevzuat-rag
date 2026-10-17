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

**2026-10-17, kısmen doğrulandı.** 5846 sayılı Fikir ve Sanat Eserleri
Kanunu m.31 (mevzuat.gov.tr metninden okundu): "Resmen yayımlanan veya ilan
olunan kanun, Cumhurbaşkanlığı kararnamesi, yönetmelik, tebliğ, genelge ve
kazai kararların çoğaltılması, yayılması, işlenmesi veya her hangi bir
suretle bunlardan faydalanma serbesttir." Yönetmelikler bunun içinde.
Yönerge, usul ve esaslar, rehberler ve web sayfaları listede açıkça yok.
Hukuki görüş değil. Bu yüzden öneri metninde ([oneri.md](oneri.md)) public
depo için plan: kod, sorular ve parça kimlikleri girer, dosyaların yerine
indirme betiği. Private depoda PDF'ler kalıyor; karar repo public
yapılırken kesinleşir.

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

## K-008: Kapsam ve bağlam, değişti → K-023 (2026-10-16)

- **Üniversite:** Gebze Teknik Üniversitesi.
- **Bağlam:** NLP dersi projesi, **tek kişi**. *(K-023: ders 4 kişilik
  takım öngörüyor; durum bilinmiyor.)*
- ~~**Teslim:** yaklaşık 20-25 Aralık 2026. Plan en erken tarihe, **20
  Aralık**'a göre yapılıyor.~~ *(K-023: final 17 Aralık.)* Hafta 1, 19
  Ekim'de başlıyor.

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

## K-012: Sayfa başlığı temizliği her konfigürasyonda yapılır; temizlik geçerli, etki ölçümü öneri (2026-10-16)

Kalite formu başlığı metnin %6-10'u ve maddelerin ortasına giriyor
([olcumler §3](olcumler.md)). Temizlik bir deney değişkeni olarak değil,
bütün konfigürasyonlarda uygulanan bir ön işlem olarak ele alınıyor.
**Uygulandı** ([olcumler §4](olcumler.md)).

**Öneri:** etkisi taban sistemde **bir kez** ölçülsün (temizlikli ve
temizliksiz Recall@k). Ucuz bir ölçüm ve raporda "ön işlem neden gerekli"
sorusunu cevaplar.

## K-013: BM25'e Türkçe kök bulma varyantı, öneri

Türkçe eklemeli bir dil. "yönetmeliğin", "yönetmelikte", "yönetmeliğe" ham
tokenlarla BM25'te üç ayrı terim; soru ile madde aynı kökü farklı eklerle
kullandığında eşleşme kaçar. NLP dersi açısından projenin en doğrudan
Türkçe'ye özgü sorusu bu.

Önerilen deney: BM25'i ham tokenlarla ve kök bulma sonrası ayrı ayrı
çalıştırmak. Yalnızca arama metrikleriyle ölçülür, dil modeli gerektirmez,
bu yüzden ucuz. Aday araçlar `snowballstemmer` (Türkçe kök bulucu) ve
`zeyrek` (Zemberek tabanlı lemmatizer); ikisi de henüz kurulup denenmedi.

**2026-10-17.** `snowballstemmer` 3.1.1 kuruldu, `arama.py`'de `kok=True`
seçeneği. Bilinen hataları: "devam" → "deva", "kanun" → "kan"
([olcumler §10](olcumler.md)). Türk kanunları üzerindeki bir ölçümde aynı
kök bulucu buna rağmen R@10'u göreli %12 artırmış (agirgol/turkish-legal-retrieval).
Araştırma sorusu bu değil (K-022); ek ölçüm olarak kalıyor. `zeyrek`
denenmedi.

## K-014: Satır düzeyinde çıkarma; parça kimliği test setinin dayanağı, geçerli (2026-10-16)

- PDF metni satır düzeyinde çıkarılıyor ve satırlar kendi konumlarına göre
  sıralanıyor. Blok kutusu metinden geniş olabildiği için blok düzeyinde bir
  tablo yanlış maddeye düşüyordu ([olcumler §4](olcumler.md)).
- Her parçanın kalıcı bir kimliği var: `<belge_id>/m<N>` (madde),
  `/g<N>` (geçici madde), `/p<N>` (paragraf), `/r<N>` (takvim satırı).
  Test setindeki `dayanak` alanı bu kimliklere işaret ediyor; Recall@k
  bu kimliklerle hesaplanacak.
- **Sınır:** sabit uzunluklu parçalamada parçalar madde sınırına uymaz.
  Orada bir parçanın "doğru" sayılması için, dayanak maddenin metniyle
  örtüşmesi gerekiyor. ~~Ölçüt hafta 3'te, ilk Recall@k hesaplanmadan önce
  yazılacak.~~ Ölçüt yazıldı: kanıt alıntısı (K-022, 2026-10-17).

## K-015: Sabit parçalama boyutu madde uzunluğuna göre seçilir, ~~öneri~~ değişti → K-022

*(K-022: boyut parça sayısı eşit olacak şekilde, 721 karakter. Medyan
artık 395; onunla 49 belgenin 640.849 karakteri en az ~1620 parça olurdu,
madde koşulunda 923.)*

Sabit ve madde bazlı parçalamanın karşılaştırması adil olsun diye sabit
parça boyutu, madde uzunluğunun medyanı (365 karakter) etrafında seçilsin.
Tek bir keyfi değer (ör. 1000) yerine iki üç değer denensin: medyan ve p90
(1396) gibi. Aksi halde "madde bazlı daha iyi" sonucu "daha uzun parça daha
iyi" sonucundan ayrılamaz.

## K-016: Bilgi tabanı 1 Kasım'da dondurulur, öneri

Belge eklemek teknik olarak kolay ([data/README.md](../data/README.md)),
ama ölçümleri etkiliyor:

- **Cevapsız sorular cevaplı hale gelebilir.** Örneğin Erasmus yönergesi
  eklenirse "Erasmus'ta kaç ders saydırabilirim?" artık cevapsız değildir.
  Etiketler bilgi tabanına göre konuyor.
- **Arama metrikleri değişir.** Her yeni belge yeni çeldiriciler demek; önceki
  ve sonraki Recall@k aynı tabloya konamaz.

Öneri:

- Eklenecek belgeler **dev soruları yazılmadan önce**, en geç hafta 2
  sonunda (1 Kasım) eklenir ve bilgi tabanı o gün dondurulur.
- Dondurmadan sonra eklenen belge yeni bir bilgi tabanı sürümüdür: bütün
  konfigürasyonlar yeniden çalıştırılır, cevapsız sorular yeniden kontrol
  edilir.
- Her ölçüm `bilgi_tabani_surumu`'nu taşır; şu anki sürüm `b3c7d85cce08`
  (114 kaynak, K-020 ve K-021). Farklı sürümlerle alınmış sonuçlar aynı
  tabloya konmaz.
- Tanımın üst sınırı 15 belge; K-017 ile 22'ye, K-020 ile 114'e çıktı,
  gerekçeleri orada.

## K-017: Sekiz belge eklendi, 22 kaynak, geçerli (2026-10-16)

Ömer Can'ın kararıyla K-009'un dışarıda bıraktığı belgelerden şunlar
eklendi: YN-0009 (2017 öncesi girişliler), YÖ-0042 Erasmus, YÖ-0044 Engelli
Öğrenciler, YÖ-0093 Endüstriyel Uygulamalar, YÖ-0094 GTU 101, YÖ-0100 GTU
110, YÖ-0116 Program Dışı Öğrenme ve YÖK geçiş/çift anadal/yan dal
yönetmeliği ([olcumler §6](olcumler.md)).

**Neden tanımın 15 belge sınırının üstüne çıkıldı.** Tanımdaki sınır bir
iş yükü tahmini. Eklenen belgeler öğrencinin gerçekten soracağı konular.
Daha geniş bir bilgi tabanı arama için daha fazla çeldirici demek, ki
araştırma sorusu tam olarak bunu ölçüyor.

**Dikkat gerektirenler.**

- **YN-0009**, 2017 öncesi girişliler için eski kuralları içeriyor ve
  YN-0001 ile aynı konularda farklı hükümler veriyor. Soru 2017 sonrası bir
  öğrenci için sorulmuşsa ondan cevap vermek yanlış olur. Bu, "sürüm
  çatışması" diye ayrı bir hata türü; test setinde birkaç soru bunu
  ölçmeli.
- **YÖK yönetmeliği** üst mevzuat: GTÜ yönergeleri ona atıf yapıyor. "Ek
  Madde-1 ile yatay geçiş" orada. Metinde Danıştay'ın 2026'da yürütmesini
  durdurduğu bir fıkra var (m13); güncellik açısından hassas.
- İlk eklemede rehberin bir cevapsız örneği cevaplı hale geldi (Erasmus).
  K-016'daki dondurma gerekçesi bu.

**Bilinçli olarak eklenmeyenler** aynen geçerli: lisansüstü mevzuat ve
İngilizce çeviriler.

## K-018: Site taramasının kapsamı ve yöntemi, geçerli (2026-10-16)

**Kapsam: lisans öğrencisini ilgilendiren 40 birim** (liste
`scripts/tara.py`'de): Öğrenci İşleri, Sağlık Kültür ve Spor (burs,
yemek, kısmi zamanlı çalışma), Uluslararası İlişkiler (Erasmus),
Uluslararası Öğrenciler, Kariyer Merkezi, Engelsiz GTÜ, Öğrenci
Toplulukları, Öğrenci Başarı ve Destek, Kütüphane, Yabancı Diller, Beden
Eğitimi, 5 fakülte, MYO ve 23 bölüm.

**Dışarıda:** araştırma enstitüleri ve merkezleri, idari birimler (personel,
strateji, hukuk…), Lisansüstü Eğitim Enstitüsü.

**Yöntem.**

- Birimin ana sayfasından gömülü menü ve "Duyurular → Tümü" bağlantısı
  okunuyor; menüdeki her site içi sayfa ve duyuru listesi çekiliyor.
- Duyuruların detay sayfaları yalnızca kimliği 25500'den büyük olanlar için,
  yani kabaca Eylül 2025'ten bu yana olanlar çekiliyor. Daha eskiler zaten
  güncelliğini yitirmiş.
- robots.txt yok; istekler arası 0.5 s. Sayfalar `.cache/tarama/`'da
  tutuluyor, yeniden çalıştırınca siteye gidilmiyor; başarısız istek
  önbelleğe yazılmıyor.
- Belge indirilmiyor; yalnızca envanter ([olcumler §7](olcumler.md)).
- Envanter (`results/tarama/`) sitedeki herkese açık duyuru ve dosya
  başlıklarını içeriyor; bazılarında kişi adı var ("Thesis Presentation of
  …"). Dosya içerikleri yok. Repo private. Public yapılmadan önce bu dosyalar
  gözden geçirilir (K-004 ile birlikte).

## K-019: Taramadan bilgi tabanına ne girer, ~~açık~~ kararlaştı (2026-10-17) → K-020, K-021

Ömer Can: mevzuat/rehber seçimi, öğretim planları ve HTML içerik, üçü de
yapılsın. Formlar "bot hangi formu doldurmalıyım sorusunu zaten
cevaplayabiliyorsa girmesin, gerekiyorsa ona göre ayarla" → ölçüldü, katalog
olarak girdi (K-020). Aşağıdaki tablo öneri hâliyle duruyor.

| tür | dosya | öneri | neden |
|---|---|---|---|
| sınav / ders programı | 840 | **girmez** | dönemlik tablolar; birkaç haftada eskiyor, tarih soruları akademik takvimden |
| ilan / sonuç | 389 | **girmez** | süreli; sonuç ve kabul listeleri öğrenci adı ve numarası içeriyor |
| form | 900 | **girmez** | çoğu boş şablon; bilgi taşımıyor |
| ders materyali, diğer | 725 | **girmez** | deney föyleri, posterler, faaliyet raporları, öğrenci sayıları |
| mevzuat, rehber | 136 | **seçilerek girer** | bölüm esasları, intibak ve sınav kuralları, af uygulama ilkeleri, staj rehberleri, Düzensiz Öğrenci Rehberi; yalnızca güncel sürüm, lisans kapsamı |
| öğretim planı | 263 | **ayrı karar** | "3. dönemde hangi dersler var" türü sorular için değerli; ama ağır tablo, bölüm başına yıllık sürümler. Alınacaksa her bölümün yalnızca güncel planı, PDF tablo çıkarımı ölçüldükten sonra |

Alınacak her belge için:

1. Envanterden elle seçilir; tür sınıflandırması yalnızca ön eleme,
   isabeti %78.
2. İndirildikten sonra metin katmanı ölçülür ve **kişisel veri taraması**
   yapılır (öğrenci no ve TC kimlik no örüntüleri). Başlıktan kişisel veri
   tespiti iki listeyi kaçırdı.
3. `kaynaklar.csv`'ye notunda "site taraması" ve bulunduğu sayfa ile girer.
4. K-016'ya tabi: 1 Kasım'dan sonra eklenen belge yeni bir bilgi tabanı
   sürümüdür.

**Ayrıca açık:** duyuru metinleri ve SSS gibi HTML sayfalar. Bunlar
taranmadı, yalnızca dosyalar envanterde.

## K-020: Kaynak genişletme, 114 kaynak, geçerli (2026-10-17)

**Formlar: içerik değil katalog.** Mevzuat "hangi formu doldurmalıyım?"
sorusunu cevaplamıyor: 532 parçanın 6'sında bir FR- kodu geçiyordu, kayıt
dondurma maddesi hiçbir form adlandırmıyor ([olcumler §8](olcumler.md)). Boş
bir formun alanları bilgi taşımadığı için içerik alınmadı. Kalite Ofisi form
listesinden 141 öğrenci formu, her biri kod, ad ve bağlantıyla bir parça.
Süzgeç `src/mevzuat_rag/formlar.py`'de ve 22 testle sabit.

**Kalite dizininden 36 belge.** Lisans öğrencisini doğrudan ilgilendirenler:
fakülte ve bölüm staj esasları, dikey geçiş, diploma, dereceye giren
mezunlar, Türkçe hazırlık, yurt, kütüphane, spor tesisleri, diş hekimliği,
Engelsiz GTÜ, psikolojik danışmanlık, psikolojik taciz ve ayrımcılıkla
mücadele, öğrenci toplulukları, konsey ve proje takımları, dumansız hava
sahası, bisiklet, güvenlik ve trafik, bilişim politikaları, Mimari Tasarım
dersleri, SGM 216, Öğrenci Başarı ve Destek.

Dışarıda: araştırma merkezleri, personel, lisansüstü ve idari yönergeler.
YÖ-0011'in R7'si dizinde bağlantısız; eski revizyon alınmadı.

**Taramadan 31 belge.** Envanterden elle, yalnızca güncel sürüm ve lisans
kapsamı. Seçimden sonra her belgede lisansüstü terim ağırlığı ölçüldü; bir
yanlış seçim (Lisansüstü Öğretim Süresi Esasları) bununla çıkarıldı.
Dizinde resmî sürümü olan belgelerin bölüm sayfasındaki kopyaları
alınmadı.

**Öğretim planları: 21 program.** Kaynak, Öğrenci İşleri'nin her programın
güncel planını listeleyen sayfası; bölüm sayfalarındaki yıllık sürümler
değil. Mühendislik tamamlama programları dışarıda. Uçak Mühendisliği planı
görüntü, OCR yok, dışarıda. Planlar paragraf bazlı bölünür.

**Her kaynak için zorunlu:** metin katmanı ölçümü ve kişisel veri taraması
(`kisisel.py`; TC sağlamalı, ≥3 öğrenci no, Adı Soyadı). Ön işlem denetimi
taramayı her kaynak için yeniden yapıyor.

**Değişirse:** OCR kurulursa Uçak planı ve taranmış PDF'ler yeniden
değerlendirilir.

## K-021: Web içeriği: SSS, konu sayfaları ve bu yılın duyuruları, geçerli (2026-10-17)

Kurallar `scripts/web_secim.py`'de; çıktı `data/raw/web/` altında üç
koleksiyon.

- **SSS:** başlığı SSS olan bütün sayfalar (31). Gerçek öğrenci soruları ve
  birimlerin resmî cevapları.
- **Konu sayfaları:** başlıkta öğrenci konusu (staj, ÇAP, yatay geçiş, burs,
  Erasmus, kayıt, mezuniyet…), en az 200 karakter. Hakkında, kadro,
  laboratuvar, akreditasyon, etkinlik ve lisansüstü sayfaları dışarıda (127).
- **Duyurular:** yalnızca 1 Ağustos 2026 ve sonrası (43). Eski duyurular
  tarihleri ve süreleri geçtiği için yanıltır; sistem bir duyuruya
  dayandığında tarihini de vermeli (parçada `tarih` alanı var).
- Kişisel veri izi taşıyan metin hiçbir koleksiyona girmez (1 sayfa).

**Test seti için uyarı.** SSS soruları artık bilgi tabanında. Test sorusu
SSS'den aynen alınırsa arama, sorunun kendisini bulur ve olduğundan iyi
görünür ([soru-yazma.md](soru-yazma.md)).

**Yenileme.** Duyurular hızla eskiyor. Bilgi tabanı dondurulduğunda (K-016)
koleksiyonlar o günkü taramadan üretilir ve tarih kayda geçer.

## K-022: Araştırma sorusu: madde sınırı mı, aynı sayıda sabit parça mı; öneri (2026-10-17)

Dersin öneri şablonu tek, karşılaştırmalı, ölçülebilir, yanlışlanabilir,
kontrollü ve açık bir soru istiyor; "hangi parçalama ve arama stratejisi en
iyisi" bu değil. Proje tanımının merkezindeki seçim bu şekle indirildi.
Hocaya gidecek metin: [oneri.md](oneri.md). Onay Ömer Can'ın.

**Soru.** ≥150 elle yazılmış test sorusunda, madde yapılı 49 belgeyi madde
sınırından bölmek, aynı sayıda sabit uzunluklu parçaya göre, cevabın geçtiği
cümleyi ilk 5 sonuçta daha sık getiriyor mu? BM25 ve yoğun arama
(multilingual-e5-base) için ayrı ayrı. **Hayır:** farkın (madde − sabit) %95
eşleştirilmiş bootstrap aralığı sıfırı içeriyorsa.

**Neden bu soru.**

- Madde parçalayıcı projenin en çok emek giden parçası (11 başlık biçimi).
  İşe yarayıp yaramadığı ölçülmeli.
- Açık. En yakın ölçüm agirgol/turkish-legal-retrieval (Ağustos 2026,
  GitHub, makale yok): 907 Türk kanunu, atıflardan üretilmiş 5010 sorgu.
  Yoğun aramada bütün madde 400 tokenlık pencerelere kaybetti (R@10'da 570'e
  karşı 669, McNemar p < 0.001), yapıya göre kesmek pencereden iyi değildi,
  en büyük tek etki kanun adı önekiydi. Orada maddelerin %8.1'i 512 tokenı
  aşıyor ve sorgular soru değil. Bizde maddeler kısa (medyan 395 karakter),
  sorular öğrenci sorusu. Sonucun buraya taşınıp taşınmadığı bilinmiyor;
  "hayır" gerçekten olası.
- Dil modelinden bağımsız; K-005'i beklemeden ölçülür.

**Kontrol: değişen tek şey parça sınırları** ([olcumler §10](olcumler.md)).

- Yalnız madde yapılı 49 belge değişiyor; diğer 60 PDF iki koşulda aynı
  paragraf parçaları.
- Sabit boyut, parça sayısı eşit olacak şekilde: **721 karakter, 922'ye
  karşı 923 parça**. Ortalama parça uzunluğu da böylece eşit. K-015'in
  yerine geçti.
- Örtüşme yok; madde parçaları da örtüşmüyor.
- Belge adı iki koşulda da her parçanın önünde. Aynı başlıklı bölüm
  belgelerini (15 ayrı staj esası gibi) ayıran bu; agirgol'da en büyük etki.
  Sabit tutuluyor; kendi etkisi ayrıca ölçülebilir.
- **Dizin yalnız PDF'ler.** Gösterim sorusunda SSS cevabı yönetmelik
  maddesinin önüne geçti. Web içeriği iki koşulda aynı olduğu için
  karşılaştırmaya bilgi katmıyor, yalnız mutlak sayıları bozuyor. Sistemde
  ve demoda web içeriği kalıyor.
- Taban sistem: sabit parça + BM25 (Türkçe küçük harf, kök bulmasız).

**Doğru sayma: kanıt alıntısı** (K-014'ün açık bıraktığı ölçüt). Her
dayanağa maddeden birebir kopyalanmış cevap cümlesi (`kanit`, testset.py).
Bulundu = alıntının bütün karakterleri, altın belgeden getirilen ilk k
parçanın birleşiminde. İki pencereye bölünen alıntı ikisini de ister. Başka
belgedeki aynı metin sayılmaz; sistem kaynak gösterecek. Ölçüt
parçalamadan bağımsız; LegalBench-RAG'in karakter aralığı etiketiyle aynı
fikir. Kod: `degerlendirme.py`.

**Gürültü.** Sorular üzerinden eşleştirilmiş bootstrap (10.000 örnek),
kesin McNemar. Soruların ~%20'sinde koşullar ayrışırsa (varsayım, dev'de
ölçülecek) n=150'de aralığın yarı genişliği ~7 puan; daha küçük farklar
"ayırt edilemedi" diye raporlanır.

**Ek ölçümler, soru değil:** kök bulma (K-013), belge adı öneki, başlık
temizliği (K-012), cevap üretimi (K-005).

**Ablasyon (CSE 654, 2026-10-17):** takımın araştırma lideri Ahmet Eren
İncir. Öneri: belge adı öneki iki koşulda da kaldırılır. Madde parçaları
yalnız önekle kazanıyorsa kazanç sınırlardan değil belgeyi tanımaktan
gelir. Kutu 7 taslağı Qu, Tu & Bao (Findings of NAACL 2025) ve Reuter vd.
(arXiv 2510.06999, 2025) üzerine; Ahmet Eren'in kendi kutusu, o düzeltip
sahiplenecek.

## K-023: Dersin takvimi ve takım kuralı, geçerli (2026-10-17)

Kaynak: NLP_Syllabus_2026Fall.pdf ve öneri şablonu (hoca, Teams). K-008'in
teslim tarihini ve "tek kişi" varsayımını değiştiriyor.

| ne | ne zaman |
|---|---|
| öneri: `Team##_Proposal.pdf`, en fazla 2 sayfa; **her üye ayrıca teslim eder**, etmeyen sıfır alır | 21 Ekim Çarşamba 23:59 |
| öneri sunumu: 5 dakika, en fazla 5 slayt, ilk slaytta araştırma sorusu | 22 Ekim Perşembe |
| ara rapor: en az taban sistemin sayıları | 5 Kasım |
| ara sınav | 19 Kasım |
| final rapor ve kod | **17 Aralık** |
| final sunumları | 17 ve 24 Aralık |

- **Takım:** dört kişi; önerilen bileşim 1 CSE 654 + 3 CSE 484. Takımlar 1
  Ekim'e kadar Teams kanalına kaydedilir; "Students not on a team by then
  are assigned to one." **2026-10-17:** takım Ahmet Eren İncir (CSE 654,
  araştırma lideri), Ömer Can Atlı, Veysel Cemaloğlu, Muhammed Korkmaz
  (CSE 484). Projeyi Ömer Can başlattı; görev dağılımı yapılmamıştı, öneri
  ve sunumdaki roller geçici: araştırma lideri Ahmet Eren, modelleme
  (parçalama ve arama) Ömer Can, veri Veysel, değerlendirme ve demo
  Muhammed. Takım numarası ve öğrenci numaraları bilinmiyor.
- **Yapay zekâ araçları** serbest, raporda kısa beyan zorunlu; öneri formunun
  9. kutusu soruyor. Beyan edilmemiş kullanım akademik dürüstlük ihlali.
- Plan 17 Aralık'a göre: [on-rapor §8](on-rapor.md).

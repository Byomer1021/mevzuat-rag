# Ön Rapor
## Üniversite Mevzuatı için RAG Tabanlı Soru-Cevap Sistemi

**Durum:** taslak, hafta 0 (16 Ekim 2026). Kapsam soruları cevaplandı; dil
modeli (§7) seçilince ve kapsam hocaya onaylatılınca kesinleşir. Ondan sonra
değişmez; kapsam değişiklikleri [kararlar.md](kararlar.md)'ye girer.

---

## 1. Bu belge neyi yapıyor

[Proje tanımı](proje-tanimi.md) genel bir plan: 4 kişilik grup, 10 hafta,
herhangi bir üniversite. Bu proje ise **GTÜ'de, tek kişilik bir NLP dersi
projesi** ve yaklaşık 9 haftası var. Bu belge tanımı bu kısıtlara oturtuyor
ve neyin neden değiştiğini kayda geçiriyor. Kapsam daralacaksa sessizce
değil, açıkça ve gerekçesiyle daralır.

---

## 2. Hedef ve çıktılar

Türkçe sorulan soruya ilgili GTÜ yönetmelik/yönerge maddesini ve sayfasını
göstererek cevap veren, cevap belgelerde yoksa "bilmiyorum" diyen bir sistem.

| çıktı | ölçüt |
|---|---|
| soru-cevap uygulaması | Streamlit arayüzü; her cevapta madde + sayfa + "resmî danışmanlık değildir" uyarısı |
| etiketli test seti | 200 soru (50 dev + 150 test), ~%15-20 cevapsız, her soruda dayanak madde |
| değerlendirme raporu | konfigürasyonların karşılaştırması, ≥50 soruda elle puanlama, hata analizi |

**Araştırma sorusu:** Türkçe mevzuat metinlerinde hangi parçalama ve arama
stratejisi, doğru ve kaynağa dayalı cevap oranını en çok artırır?

---

## 3. Bağlayıcı kısıtlar: ölçüldü, tahmin edilmedi

| kısıt | durum | etkisi |
|---|---|---|
| ekip | tek kişi ([K-008](kararlar.md)) | dört rol birleşiyor; Kappa için ikinci etiketçi dışarıdan gerekiyor |
| süre | 19 Ekim - 20 Aralık, 9 hafta | §8 |
| yerel GPU | GTX 1080, 8 GB, sm_61; torch 2.7.1+cu118 ile **kernel çalışıyor** ([olcumler §1](olcumler.md)) | gömme ve reranker yerelde çalışabilir; uzun yükte kararlılık ölçülmedi |
| GPU sürücüsü | 526.47, en fazla CUDA 12.0 | torch cu118'e ve 2.7.x'e sabit ([K-002](kararlar.md)) |
| disk | C'de 13 GB, D'de ~580 GB | proje ve önbellekler D'de ([K-003](kararlar.md)) |
| OCR | **gerekmiyor**: 13 PDF'in hepsinde metin katmanı var, bozuk karakter 0 ([olcumler §3](olcumler.md)) | Tesseract kurulmayacak |
| dil modeli | seçilmedi | hafta 2 pilotu, 2 Kasım'dan önce karar ([K-005](kararlar.md)) |

---

## 4. Kapsam

**Bilgi tabanı: 13 belge ve akademik takvim** ([K-009](kararlar.md)). Ana
lisans yönetmeliği, yaz öğretimi, hazırlık, çift anadal, yan dal, yatay
geçiş, iki muafiyet belgesi, iki staj belgesi (fakülte ve Bilgisayar Müh.),
azami süre, danışmanlık, kısmi zamanlı çalışma ve 2026-2027 akademik takvim.
52 sayfa, yaklaşık 162 bin karakter; madde yapısı olan 12 belgede 227 asıl
ve 2 geçici madde.

Her belge GTÜ Kalite Ofisi dizinindeki **yürürlükteki revizyonuyla** alındı
ve sha256'sı kayıtlı. Revizyon değişirse `scripts/kaynaklar.py kontrol`
bunu yakalar.

Tanımdaki "burs yönergeleri" GTÜ'de yok; maddi destek tarafı YÖ-0025 ile
temsil ediliyor.

**Test seti.** Üç soru türü: tek madde, çok maddeli, cevapsız. Hata analizi
için her soruya etiket konur (tarih, istisna, sayı, koşul...). Şema:
[data/README.md](../data/README.md). Ayar dev bölümünde yapılır, rapordaki
sayılar test bölümünden gelir ([K-007](kararlar.md), öneri).

**Kapsam dışı.** Lisansüstü mevzuat, öğrenciye özel bilgi (not, transkript,
öğrenci bilgi sistemi), kişisel veri, sohbet geçmişi, yönetmelik dışı
kaynaklar (duyurular, forumlar).

---

## 5. Yöntem: en basitten başla, birer birer ekle

1. **Ön işlem** (bütün konfigürasyonlarda): PyMuPDF ile metin
   ([K-010](kararlar.md)) ve kalite formu başlığının temizlenmesi
   ([K-012](kararlar.md)). Başlık metnin %6-10'unu oluşturuyor ve
   maddelerin ortasına giriyor.
2. **Taban sistem:** sabit uzunlukta parçalama, vektör arama ve dil modeli.
   Uçtan uca çalışan ilk sürüm; diğer her şey buna göre ölçülür.
3. Bunun yanında, arama yapmayan "yalnız dil modeli" taban çizgisi.
4. Değişiklikler **teker teker** eklenir ve her birinin etkisi ayrı ölçülür.

| konfigürasyon | parçalama | arama |
|---|---|---|
| K0 | yok | yok, yalnız dil modeli |
| K1 | sabit | vektör (taban sistem) |
| K2 | sabit | BM25 |
| K2k | sabit | BM25 + Türkçe kök bulma ([K-013](kararlar.md), öneri) |
| K3 | madde bazlı | vektör |
| K4 | madde bazlı | hibrit |
| K5 | madde bazlı | hibrit + reranker |

Madde bazlı parçalayıcı, başlık tanıyıcı
[src/mevzuat_rag/madde.py](../src/mevzuat_rag/madde.py) üzerine kurulacak.
Belgelerde beş başlık biçimi görüldü. YÖ-0087 madde yapısında olmadığı için
o belgede paragraf tabanlı bir yedek kullanılacak.

Tanımdaki "1. belge işleme" adımı bir deney ekseni olmaktan çıktı: iki PDF
çıkarıcı bu belgelerde aynı içeriği veriyor ([K-010](kararlar.md)).

**Ölçüm disiplini.**

- Arama metrikleri (Recall@k, MRR) dil modelinden bağımsız; parçalama ve
  arama karşılaştırması model seçimini beklemeden yürür.
- Dil modeli bütün konfigürasyonlarda sabit kalır. Çıktıları deterministik
  olmadığı için aynı konfigürasyon iki kez çalıştırılıp tekrarlar arası fark
  ölçülür; bu farktan küçük konfigürasyon farkları anlamlı sayılmaz.
- Otomatik puanlayıcı kullanılırsa en az 50 soruda elle puanlamayla uyumu
  ölçülür.

---

## 6. Riskler

| risk | etkisi | önlem | durum |
|---|---|---|---|
| PDF'ler taranmış görüntü | metin bozulur | metin katmanı ölçüldü | **kapandı**: 13/13 metinli, bozuk karakter 0 |
| madde başlıkları metinden çıkmaz | madde bazlı parçalama çalışmaz | tanıyıcı 12 belgede 1..N'i eksiksiz buluyor | **kapandı**, YÖ-0087 hariç (yedek strateji) |
| sayfa başlığı maddelerin ortasına girer | parçalara gürültü | ön işlemde temizlik (K-012) | açık, hafta 1-2 |
| test seti küçük kalır | sonuçlar güvenilmez | 200 soru, türler dengeli | |
| test setine göre ayar yapılır | sonuçlar şişer | dev/test ayrımı (K-007) | öneri |
| ikinci etiketçi bulunamaz | Kappa raporlanamaz | bir sınıf arkadaşından 40-50 soru | açık |
| yönetmelik güncellenir | cevaplar eskir | PDF + sha256 depoda, `kaynaklar.py kontrol` | önlem hazır |
| yanlışı güvenle söyler | öğrenci yanılır | her cevapta madde, uyarı metni | |
| dil modeli maliyeti / donanım | deney sayısı kısıtlanır | pilotla soru başına maliyet ölçülür | K-005 açık |
| model çıktıları tekrarlanamaz | konfigürasyon farkı gürültüden ayrılamaz | cevaplar diske, tekrar farkı ölçülür | |
| GPU uzun yükte düşer | deney yarıda kalır | gömmeler diske kaydedilir, iş kaldığı yerden devam eder | ölçülmedi |

---

## 7. Açık sorular

Cevaplananlar (2026-10-16): üniversite GTÜ; tek kişi; NLP dersi projesi;
teslim yaklaşık 20-25 Aralık ([K-008](kararlar.md)).

Açık kalanlar:

1. **Dil modeli:** API mı, yerel mi, bütçe ne? Hafta 2 pilotuyla karar
   ([K-005](kararlar.md)).
2. **Hocanın şartları:** açık kaynak model şartı var mı? Kapsamın (bu
   belgede) onaylatılması.
3. **İkinci etiketçi:** Kappa için 40-50 soruyu bağımsız etiketleyecek biri.
4. **Görünürlük:** repo ne zaman public olacak? ([K-004](kararlar.md))

---

## 8. Takvim

Hafta 1, 19 Ekim 2026 Pazartesi başlıyor. Plan, teslim aralığının en erken
günü olan 20 Aralık'a göre yapıldı.

| hafta | tarih | iş | bitti sayılır, eğer... |
|---|---|---|---|
| 0 | 16 Eki | ortam, repo, dokümantasyon; belgeler toplandı, metin katmanı ölçüldü | ✓ |
| 1-2 | 19 Eki - 1 Kas | başlık temizliği, madde parçalayıcı, 50 dev sorusu, dil modeli pilotu | 50 soru şemaya uygun; K-005 kararlaştı |
| 3-4 | 2-15 Kas | taban sistem (K0, K1) | dev setinde ilk Recall@k ve doğruluk sayıları |
| 5-6 | 16-29 Kas | BM25, kök bulma, madde, hibrit, reranker; test seti 150 soruya | bütün konfigürasyonlar dev setinde çalışıyor |
| 7 | 30 Kas - 6 Ara | test setinde değerlendirme, elle puanlama | sonuç tablosu |
| 8 | 7-13 Ara | hata analizi, arayüz, demo | hata kırılımı, çalışan demo |
| 9 | 14-20 Ara | rapor, sunum, README | teslim |

Belge toplama ve metin katmanı ölçümü 1-2. haftanın işiydi, hafta 0'da
bitti. Bu kazanılan zaman, 9 haftaya sıkışan takvime tampon oluyor.

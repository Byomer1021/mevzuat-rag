# Ön Rapor
## Üniversite Mevzuatı için RAG Tabanlı Soru-Cevap Sistemi

**Durum:** taslak, hafta 0. 17 Ekim'de dersin programına ve öneri
şablonuna göre güncellendi ([K-023](kararlar.md)): araştırma sorusu tek bir
karşılaştırmaya indi ([K-022](kararlar.md)), takvim 17 Aralık'a çekildi.
Hocaya giden metin [oneri.md](oneri.md); bu belge projenin iç planı.
Kapsam değişiklikleri [kararlar.md](kararlar.md)'ye girer.

---

## 1. Bu belge neyi yapıyor

[Proje tanımı](proje-tanimi.md) genel bir plan: 4 kişilik grup, 10 hafta,
herhangi bir üniversite. Bu proje ise **GTÜ'de bir NLP dersi projesi**;
final 17 Aralık, 19 Ekim'den itibaren 8.5 hafta. Ders de 4 kişilik takım
öngörüyor; Ömer Can'ın takım durumu henüz belli değil ([K-023](kararlar.md)),
plan tek kişi varsayımıyla. Bu belge tanımı bu kısıtlara oturtuyor
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

**Araştırma sorusu** ([K-022](kararlar.md)): ≥150 elle yazılmış test
sorusunda, mevzuatı madde sınırından bölmek, aynı sayıda sabit uzunluklu
parçaya göre cevabın geçtiği cümleyi ilk 5 sonuçta daha sık getiriyor mu?
BM25 ve yoğun arama için ayrı ayrı; ölçüt kanıt Recall@5. **Hayır:** farkın
%95 eşleştirilmiş bootstrap aralığı sıfırı içeriyorsa.

İlk hâli ("hangi parçalama ve arama stratejisi doğru ve kaynağa dayalı cevap
oranını en çok artırır?") dersin şablonuna göre fazla geniş: tek, kontrollü
bir karşılaştırma isteniyor. §5'teki diğer konfigürasyonlar ek ölçüm olarak
kalıyor; cevap üretimi demo.

---

## 3. Bağlayıcı kısıtlar: ölçüldü, tahmin edilmedi

| kısıt | durum | etkisi |
|---|---|---|
| ekip | şimdilik tek kişi; ders 4 kişilik takım öngörüyor, durum belirsiz ([K-023](kararlar.md)) | dört rol birleşiyor; Kappa için ikinci etiketçi dışarıdan gerekiyor |
| süre | 19 Ekim - 17 Aralık; öneri 21 Ekim, ara rapor 5 Kasım ([K-023](kararlar.md)) | §8 |
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

**Ana karşılaştırma** ([K-022](kararlar.md)): aynı arama ile madde ve
eşit sayıda sabit parça (721 karakter): yoğun aramada K1 ile K3, BM25'te K2
ile onun madde bazlı karşılığı.
Taban sistem sabit parça + BM25. Aşağıdaki tablo ek ölçümlerin haritası;
öneride yalnız ana karşılaştırma var.

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
| sayfa başlığı maddelerin ortasına girer | parçalara gürültü | ön işlemde temizlik (K-012) | **kapandı**: temiz metinde iz yok ([olcumler §4](olcumler.md)) |
| uzun maddeler gömme modelinin sınırını aşar | maddenin sonu aramada görünmez | 57 madde 2000 karakterin üstünde; model seçilirken token sayısı ölçülür, etkilenen test soruları ayrı raporlanır | hafta 1 |
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

Cevaplananlar: üniversite GTÜ; NLP dersi projesi (2026-10-16,
[K-008](kararlar.md)); final 17 Aralık, öneri 21 Ekim (2026-10-17, ders
programı, [K-023](kararlar.md)).

Açık kalanlar:

0. **Takım:** Ömer Can bir takımda mı, takım numarası ve üyeler kim? Öneri
   formunun ilk satırları ve rolleri buna bağlı ([K-023](kararlar.md)).
1. **Dil modeli:** API mı, yerel mi, bütçe ne? Hafta 2 pilotuyla karar
   ([K-005](kararlar.md)). Artık araştırma sorusunun dışında; yalnız demo.
2. **Hocanın şartları:** açık kaynak model şartı var mı? Kapsamın (bu
   belgede) onaylatılması.
3. **İkinci etiketçi:** Kappa için 40-50 soruyu bağımsız etiketleyecek biri.
4. **Görünürlük:** repo ne zaman public olacak? ([K-004](kararlar.md))

---

## 8. Takvim

Hafta 1, 19 Ekim 2026 Pazartesi başlıyor. Plan dersin takvimine göre
([K-023](kararlar.md)); kalın satırlar dersin teslimleri.

| hafta | tarih | iş | bitti sayılır, eğer... |
|---|---|---|---|
| 0 | 16-18 Eki | ortam, bilgi tabanı (114 kaynak), ön işlem, BM25, değerlendirme kodu, öneri taslağı | ✓ (öneri onaylanınca) |
| 1 | 19-25 Eki | **öneri 21 Eki 23:59, sunum 22 Eki**; dev soruları başlar; gömme modelinin token ölçümü | öneri teslim edildi |
| 2 | 26 Eki - 1 Kas | 50 dev sorusu; bilgi tabanı dondurulur (K-016) | 50 soru denetimden geçiyor |
| 3 | 2-8 Kas | **ara rapor 5 Kas:** dev setinde iki koşul BM25, güven aralıklı | ara sunum |
| 4-5 | 9-22 Kas | test soruları (≥150), ikinci etiketçi; yoğun arama kurulur; ara sınav 19 Kas | test seti donar (22 Kas) |
| 6 | 23-29 Kas | yoğun arama dev'de; dil modeli seçimi ve demo | iki arama dev'de çalışıyor |
| 7 | 30 Kas - 10 Ara | test seti bir kez (6-10 Ara), hata analizi, ek ölçümler | sonuç tablosu |
| 8 | 11-17 Ara | rapor, kod, sunum; **final 17 Ara**, sunumlar 17 ve 24 Ara | teslim |

Belge toplama, ön işlem ve arama tabanı hafta 0'da bitti. Bu yüzden ara
rapora dev setinde gerçek sayılarla gidilebilir; en dar boğaz soru yazımı.

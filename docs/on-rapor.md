# Ön Rapor
## Üniversite Mevzuatı için RAG Tabanlı Soru-Cevap Sistemi

**Durum:** taslak, hafta 0 (16 Ekim 2026). §7'deki açık sorular cevaplanıp
kapsam hocayla onaylandığında kesinleşir; ondan sonra değişmez, kapsam
değişiklikleri [kararlar.md](kararlar.md)'ye girer.

---

## 1. Bu belge neyi yapıyor

[Proje tanımı](proje-tanimi.md) genel bir plan: 4 kişilik grup, 10 hafta,
herhangi bir üniversite. Bu belge onu bu projenin **gerçek kısıtlarına
oturtuyor** ve neyin neden değiştiğini kayda geçiriyor. Kapsam daralacaksa
sessizce değil, açıkça ve gerekçesiyle daralır.

---

## 2. Hedef ve çıktılar

Türkçe sorulan soruya ilgili yönetmelik maddesini ve sayfasını göstererek
cevap veren, cevap belgelerde yoksa "bilmiyorum" diyen bir sistem.

| çıktı | ölçüt |
|---|---|
| soru-cevap uygulaması | Streamlit arayüzü; her cevapta madde + sayfa + "resmî danışmanlık değildir" uyarısı |
| etiketli test seti | 150-250 soru, ~%15-20 cevapsız, her soruda dayanak madde |
| değerlendirme raporu | 5 konfigürasyonun karşılaştırması, ≥50 soruda elle puanlama, hata analizi |

**Araştırma sorusu:** Türkçe mevzuat metinlerinde hangi parçalama ve arama
stratejisi, doğru ve kaynağa dayalı cevap oranını en çok artırır?

---

## 3. Bağlayıcı kısıtlar: ölçüldü, tahmin edilmedi

| kısıt | durum | etkisi |
|---|---|---|
| yerel GPU | GTX 1080, 8 GB, sm_61. torch 2.7.1+cu118 ile **kernel çalışıyor** ([olcumler §1](olcumler.md)) | gömme ve reranker yerelde çalışabilir; uzun yükte kararlılık henüz ölçülmedi |
| GPU sürücüsü | 526.47, en fazla CUDA 12.0 | torch cu118 derlemesine ve 2.7.x'e sabit ([K-002](kararlar.md)) |
| disk | C'de 13 GB, D'de ~580 GB | proje, uv ve HF önbellekleri D'de ([K-003](kararlar.md)) |
| OCR | Tesseract kurulu değil | ancak taranmış PDF çıkarsa kurulacak; önce her PDF'in metin katmanı kontrol edilecek |
| dil modeli | seçilmedi | taban sistemden (hafta 3) önce karar ([K-005](kararlar.md)) |

---

## 4. Kapsam

**Bilgi tabanı.** 8-15 resmî belge: lisans eğitim-öğretim ve sınav
yönetmeliği; yatay geçiş, çift anadal-yan dal, staj ve burs yönergeleri;
akademik takvim. **Varsayım: Gebze Teknik Üniversitesi.** Onay bekliyor (§7).
Hangi belgelerin bulunduğu henüz kontrol edilmedi.

**Test seti.** Üç soru türü: tek madde, çok maddeli, cevapsız. Her soruya hata
analizi için etiket konur (tarih, istisna, sayı, koşul...). Şema:
[data/README.md](../data/README.md).

**Kapsam dışı.** Öğrenciye özel bilgi (not, transkript, öğrenci bilgi
sistemi), kişisel veri, sohbet geçmişi, yönetmelik dışı kaynaklar (duyurular,
forumlar).

---

## 5. Yöntem: en basitten başla, birer birer ekle

1. **Taban sistem:** sabit uzunlukta parçalama + vektör arama + dil modeli.
   Uçtan uca çalışan ilk sürüm; diğer her şey buna göre ölçülür.
2. Bunun yanında, arama yapmayan "yalnız dil modeli" taban çizgisi. Arama
   olmadan modelin ne kadar uydurduğu, RAG'ın kazancını gösteren referans.
3. Değişiklikler **teker teker** eklenir ve her birinin etkisi ayrı ölçülür:
   madde bazlı parçalama, BM25, hibrit, reranker.

| konfigürasyon | parçalama | arama |
|---|---|---|
| K0 | yok | yok, yalnız dil modeli |
| K1 | sabit | vektör (taban sistem) |
| K2 | sabit | BM25 |
| K3 | madde bazlı | vektör |
| K4 | madde bazlı | hibrit |
| K5 | madde bazlı | hibrit + reranker |

Tablo ilk taslak. Parçalama ile aramanın etkileşimi görülürse eksik
hücreler (ör. madde bazlı + BM25) eklenir.

**Ölçüm disiplini.** Ayarlar test setinin ayrı bir geliştirme bölümünde
yapılır, rapordaki sayılar dokunulmamış test bölümünden gelir
([K-007](kararlar.md), öneri). Otomatik puanlayıcı (RAGAS vb.) kullanılırsa
en az 50 soruda elle puanlamayla uyumu ölçülür. Otomatik puanlayıcı da bir dil
modeli olduğu için tek başına kanıt sayılmaz.

---

## 6. Riskler

| risk | etkisi | önlem | durum |
|---|---|---|---|
| PDF'ler taranmış görüntü | metin bozulur | hafta 1'de her PDF'in metin katmanı ölçülür | kontrol edilmedi |
| madde başlıkları PDF'ten düzgün çıkmaz | madde bazlı parçalama çalışmaz | çıkarılan metinde `MADDE N` başlıkları sayılıp belgedeki madde sayısıyla karşılaştırılır | kontrol edilmedi |
| test seti küçük kalır | sonuçlar güvenilmez | en az 150 soru, türler dengeli | |
| test setine göre ayar yapılır | sonuçlar şişer | dev/test ayrımı (K-007) | öneri |
| yönetmelik güncellenir | cevaplar eskir | PDF + sha256 depoda (K-004) | |
| yanlışı güvenle söyler | öğrenci yanılır | her cevapta madde, uyarı metni | |
| dil modeli maliyeti / donanım | deney sayısı kısıtlanır | soru başına maliyet ve hız erken ölçülür | K-005 açık |
| GPU uzun yükte düşer | deney yarıda kalır | önceki projede eğitimde düştü; gömmeler diske kaydedilir, düşen iş kaldığı yerden devam eder | ölçülmedi |

---

## 7. Açık sorular

Bunlar cevaplanmadan ön rapor kesinleşmez.

1. **Üniversite:** GTÜ mü? Belgeler hangi siteden alınacak?
2. **Grup:** tek kişi mi, grup mu? Grup ise roller ve repo erişimi.
3. **Bağlam ve teslim:** ders projesi mi, bitirme mi? Hoca kim, teslim ve
   ara rapor tarihleri ne?
4. **Dil modeli:** API mı, yerel mi, bütçe ne? (K-005)
5. **Görünürlük:** repo ne zaman public olacak? (K-004)

---

## 8. Takvim

Varsayım: hafta 1, 19 Ekim 2026 Pazartesi başlar. Teslim tarihi öğrenilince
güncellenecek.

| hafta | tarih | iş | bitti sayılır, eğer... |
|---|---|---|---|
| 0 | 16 Eki | ortam, repo, dokümantasyon | GPU'da kernel çalıştı, testler geçti ✓ |
| 1-2 | 19 Eki - 1 Kas | belgeleri topla, metin katmanını ölç, ilk 50 soru (dev) | `kaynaklar.csv` dolu, 50 soru şemaya uygun |
| 3-4 | 2-15 Kas | taban sistem (K0, K1) | dev setinde ilk Recall@k ve doğruluk sayıları |
| 5-6 | 16-29 Kas | parçalama, arama, reranker varyantları; test seti 150+ | tüm konfigürasyonlar dev'de çalışıyor |
| 7-8 | 30 Kas - 13 Ara | test setinde değerlendirme, elle puanlama, hata analizi | sonuç tablosu ve hata kırılımı |
| 9 | 14-20 Ara | arayüz, demo, README, mimari şeması | demo videosu |
| 10 | 21-27 Ara | rapor, sunum | |

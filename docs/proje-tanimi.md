# Proje Tanımı

Başlangıçta verilen tanımın (11 Ekim 2026, @castorstar) özeti. Bu belge
değişmez; tanımın bu projeye nasıl uyarlandığı [on-rapor.md](on-rapor.md)'de.

---

## Problem ve hedef

Öğrenciler yatay geçiş, çift anadal, devam zorunluluğu veya sınav itirazı gibi
konularda cevabı onlarca sayfalık yönetmelik PDF'lerinde arıyor; arama çoğu
zaman yanlış veya eksik sonuca götürüyor.

Hedef: Türkçe sorulan soruya **ilgili madde ve sayfayı kaynak göstererek**
cevap veren, cevabı belgede bulamazsa "bilmiyorum" diyen bir sistem.

Üç çıktı:

- Çalışan bir soru-cevap uygulaması (Streamlit veya Gradio)
- Etiketli bir Türkçe mevzuat soru-cevap test seti
- Farklı RAG ayarlarını karşılaştıran bir değerlendirme raporu

## Mimari

```
Hazırlık (bir kez):
  Yönetmelik PDF'leri → temizleme ve madde parçalama → embedding → vektör veri tabanı

Soru anı (her soruda):
  Soru → arama (BM25 + vektör) → dil modeli (kaynakla cevap) → cevap + kaynak madde
                     └→ uygun madde yoksa: "bilmiyorum"
```

## Veri

| veri | içerik | hedef boyut | nasıl |
|---|---|---|---|
| bilgi tabanı | lisans eğitim-öğretim yönetmeliği, yatay geçiş, çift anadal-yan dal, staj, burs yönergeleri, akademik takvim | 8-15 belge | üniversite sitesinden PDF, metne çevirme, temizleme (gerekirse OCR) |
| test seti | soru, doğru cevap, dayanak madde numarası | 150-250 soru | grup üyeleri elle yazar, her cevabın maddesi işaretlenir |
| cevapsız sorular | belgelerde karşılığı olmayan sorular | test setinin ~%15-20'si | "Kantinde ne var?" gibi |

- Soru türleri: **tek madde**, **çok maddeli** (iki yönetmeliği birleştirmek
  gerekir), **cevapsız**. Halüsinasyonu en doğrudan ölçen, cevapsız sorulardır.
- İki kişi bağımsız etiketler ve **Cohen's Kappa** raporlanırsa veri seti
  akademik olarak savunulabilir olur.
- Yönetmeliklerin güncel sürümü kullanılır, sürüm tarihi veri setinin
  README'sine yazılır.

## Yöntem

| adım | karşılaştırılacak seçenekler | önerilen araç |
|---|---|---|
| 1. belge işleme | metne çevirme, başlık/madde yapısını koruma | PyMuPDF, pdfplumber, gerekirse Tesseract |
| 2. parçalama | sabit uzunluk, madde bazlı, örtüşmeli | LangChain veya LlamaIndex |
| 3. gömme | çok dilli (multilingual-e5, BGE-M3), Türkçe BERT tabanlı | Hugging Face, sentence-transformers |
| 4. arama | yalnız BM25, yalnız vektör, hibrit, isteğe bağlı reranker | FAISS veya Chroma, rank-bm25 |
| 5. cevap üretimi | açık kaynak model veya API; "kaynağı göster, bulamazsan bilmiyorum de" | Hugging Face veya bir LLM API'si |

Mevzuata özel ipucu: yönetmelikler madde madde yazıldığı için sabit uzunlukta
kesmek bir maddeyi ortadan bölebilir. Madde bazlı parçalama çoğu zaman daha iyi
sonuç verir; bunu deneyle göstermek raporun güçlü bir bulgusu olur.

Önce en basit çalışan sürüm (sabit parçalama + vektör arama + bir LLM), sonra
geliştirmeler tek tek eklenip her birinin etkisi ölçülür.

## Değerlendirme

Araştırma sorusu: *Türkçe mevzuat metinlerinde hangi parçalama ve arama
stratejisi, doğru ve kaynağa dayalı cevap oranını en çok artırır?*

| ölçülen | metrik | ne anlatır |
|---|---|---|
| doğru parçayı bulma | Recall@k, MRR | dayanak madde ilk k sonuçta mı |
| cevap doğruluğu | doğru / kısmen / yanlış (elle) | referans cevapla uyuşuyor mu |
| kaynağa sadakat | cevaptaki her iddia getirilen metinde var mı | halüsinasyon oranı |
| cevaplamama başarısı | cevapsız sorularda "bilmiyorum" oranı | uydurmak yerine susabiliyor mu |
| alıntı doğruluğu | gösterilen madde numarası doğru mu | kaynağa güvenilebilir mi |

Konfigürasyonlar: (1) arama yok, yalnız dil modeli; (2) BM25; (3) vektör;
(4) hibrit (+ reranker); (5) sabit ile madde bazlı parçalama.

RAGAS gibi otomatik puanlayıcılar da bir dil modeli olduğundan hatalı
olabilir; **en az 50 soru elle puanlanıp** otomatik sonuçlarla uyumu
raporlanır. Sonda **hata analizi**: hangi soru türlerinde (çok maddeli, tarih
içeren, istisna içeren) sistem neden başarısız oldu.

## İş bölümü ve plan (4 kişi, 10 hafta varsayımı)

| rol | sorumluluk |
|---|---|
| veri | belge toplama, temizleme, test seti, etiket uyumu |
| arama | parçalama, embedding, BM25, hibrit arama |
| üretim | prompt, dil modeli entegrasyonu, kaynak gösterme |
| değerlendirme ve arayüz | metrikler, puanlama, Streamlit, rapor |

| hafta | iş |
|---|---|
| 1-2 | konuyu hocayla netleştirme, belgeleri toplama, ilk 50 soru |
| 3-4 | en basit çalışan RAG (taban sistem, ilk sonuçlar) |
| 5-6 | parçalama, arama, reranker varyantları; test seti 150+ |
| 7-8 | tüm konfigürasyonları değerlendirme, elle puanlama, hata analizi |
| 9 | arayüz ve demo, README, mimari şeması |
| 10 | rapor, sunum, gerekirse bildiri taslağı |

## Riskler

| risk | etkisi | önlem |
|---|---|---|
| PDF'ler taranmış görüntü | metin çıkarımı bozulur | erken kontrol, gerekirse OCR |
| test seti küçük kalır | sonuçlar güvenilmez | en az 150 soru, türler dengeli |
| yönetmelik güncellenir | cevaplar eski kalır | sürüm tarihini kaydet, güncelleme adımını README'ye yaz |
| sistem yanlışı güvenle söyler | öğrenci yanılır | kaynak maddeyi göster, "resmî danışmanlık değildir" uyarısı |
| dil modeli maliyeti / donanım | deney sayısı kısıtlanır | küçük açık model veya ücretsiz katmanla başla |

# mevzuat-rag

**Üniversite yönetmeliklerine sorulan Türkçe soruları ilgili madde ve sayfayı
göstererek yanıtlayan, cevap belgede yoksa "bilmiyorum" diyen bir RAG sistemi.
Projenin asıl çıktısı, hangi tasarım kararının sonucu ne kadar değiştirdiğinin
ölçümü.**

*A Turkish retrieval-augmented QA system over university regulations that
cites the article it answers from and abstains when the documents don't
contain the answer, plus a measured comparison of the chunking and retrieval
choices behind it.*

---

## Durum

GTÜ'de NLP dersi projesi; 19 Ekim - 20 Aralık 2026.

**Hafta 0: bilgi tabanı toplandı, RAG sonucu henüz yok.** Bu sayfaya her
sayı ölçüldüğü anda girer. Ölçülmemiş sayı yazılmaz.

Şu ana kadar ölçülen:

- 13 GTÜ yönetmelik/yönergesi ve akademik takvim; hepsi Kalite Ofisi
  dizinindeki yürürlükteki revizyonuyla, sha256'larıyla.
- 52 sayfanın hepsinde metin katmanı var, bozuk Türkçe karakter 0: OCR
  gerekmiyor.
- Madde başlıkları beş farklı biçimde yazılmış. Tanıyıcı, madde yapısı olan
  12 belgenin 12'sinde 1..N'i eksiksiz buluyor (227 asıl, 2 geçici madde).
- Her sayfadaki kalite formu başlığı metnin %7.7'si ve maddelerin ortasına
  giriyordu. Temizlendi; temiz metinde iz kalmadı.
- Bilgi tabanı 384 parçaya bölündü: 229 madde, 150 takvim satırı ve
  maddesiz belge için 4 paragraf. Parçalar temiz metni 13/13 belgede
  kayıpsız örtüyor, sayfa aralıkları 234/234 doğru.

Ayrıntılar: [olcumler §2-4](docs/olcumler.md).

| aşama | hafta | durum |
|---|---|---|
| 0. ortam, repo, dokümantasyon; belge toplama, metin katmanı | 0 | **tamam** |
| 1. başlık temizliği, madde parçalayıcı, 50 dev sorusu, dil modeli pilotu | 1-2 | temizlik ve parçalayıcı **tamam**; sorular ve pilot sırada |
| 2. en basit çalışan RAG (taban sistem, ilk sonuçlar) | 3-4 | |
| 3. BM25 / kök bulma / madde / hibrit / reranker, test seti 150 | 5-6 | |
| 4. test setinde değerlendirme, elle puanlama | 7 | |
| 5. hata analizi, arayüz ve demo | 8 | |
| 6. rapor ve sunum | 9 | |

## Araştırma sorusu

> Türkçe mevzuat metinlerinde hangi parçalama ve arama stratejisi, doğru ve
> kaynağa dayalı cevap oranını en çok artırır?

Karşılaştırılacak konfigürasyonlar ([on-rapor §5](docs/on-rapor.md)):

1. Arama yok, yalnızca dil modeli (taban çizgisi)
2. BM25 + dil modeli; Türkçe kök bulmalı ve kök bulmasız
3. Vektör arama + dil modeli
4. Hibrit arama (+ reranker) + dil modeli
5. Sabit uzunlukta parçalama ile madde bazlı parçalamanın karşılaştırması

| ölçülen | metrik |
|---|---|
| doğru parçayı bulma | Recall@k, MRR |
| cevap doğruluğu | doğru / kısmen / yanlış (elle) |
| kaynağa sadakat | cevaptaki her iddia getirilen metinde var mı (halüsinasyon oranı) |
| cevaplamama başarısı | cevapsız sorularda "bilmiyorum" deme oranı |
| alıntı doğruluğu | gösterilen madde numarası doğru mu |

## Dokümantasyon

Proje adım adım kayıt altında tutuluyor. Nasıl tutulduğu:
[docs/README.md](docs/README.md).

| belge | ne var |
|---|---|
| [proje-tanimi.md](docs/proje-tanimi.md) | başlangıçta verilen tanım: hedef, veri, yöntem, plan |
| [on-rapor.md](docs/on-rapor.md) | tanımın gerçek kısıtlara oturtulmuş hali, kapsam, açık sorular |
| [olcumler.md](docs/olcumler.md) | numaralı ölçüm günlüğü; her sayının kaynağı burada |
| [kararlar.md](docs/kararlar.md) | tasarım kararları ve gerekçeleri |
| [soru-yazma.md](docs/soru-yazma.md) | test seti sorularını yazma kuralları ve aracı |
| [gunluk/](docs/gunluk/) | gün gün ne yapıldı, ne çıktı, sırada ne var |

## Kurulum

Python 3.12 ve [uv](https://docs.astral.sh/uv/) gerekir.

```powershell
# C'de yer azsa önbellekleri D'ye alın: torch (cu118) ~2.7 GB,
# gömme modelleri model başına 1-2 GB.
$env:UV_CACHE_DIR = "D:\.cache\uv"

uv sync --all-extras
copy .env.example .env        # HF_HOME burada

uv run python scripts/ortam_kontrol.py
uv run pytest
```

torch, CUDA 11.8 derlemesinden kuruluyor; GTX 1080 (Pascal) ve CUDA 12.0'a
kadar destekleyen sürücüyle çalışan seçenek bu. Gerekçesi
[kararlar.md, K-002](docs/kararlar.md).

## Dizin yapısı

Test seti sorusu yazma aracı ([rehber](docs/soru-yazma.md)):

```powershell
uv run streamlit run app/soru_yaz.py
```

```
app/
  soru_yaz.py        test seti sorusu yazma aracı (Streamlit)
data/
  kaynaklar.csv      bilgi tabanındaki her belge: kod, revizyon, URL, sha256
  raw/               indirilen PDF'ler ve takvim TSV'si (depoda)
  raw/dizin/         GTÜ Kalite Ofisi dizininin çekildiği günkü hali
  processed/         temizlenmiş metin ve parçalar (yeniden üretilir, depoda değil)
  testset/           etiketli soru-cevap seti (depoda)
docs/                rapor, ölçüm, karar ve günlük kayıtları
results/             ölçümlerin ham çıktısı (JSON/CSV)
scripts/
  kaynaklar.py       dizin, indirme, güncellik kontrolü
  metin_katmani.py   PDF metin katmanı ölçümü (olcumler §3)
  onisle.py          temizlik + parçalama + denetim (olcumler §4)
  ortam_kontrol.py   ortam ve GPU ölçümü (olcumler §1)
  testset_kontrol.py test setinin şema denetimi ve dağılımı
src/mevzuat_rag/
  madde.py           madde başlığı tanıyıcı (beş biçim)
  onisleme.py        PDF'ten temiz sayfa metni, kalite formu başlığı atılır
  parcalama.py       madde bazlı, paragraf, sabit uzunluklu, takvim
  testset.py         test seti şeması, denetim, dağılım
tests/
```

> Bu sistem resmî danışmanlık değildir. Cevaplar ilgili yönetmelik maddesiyle
> birlikte verilir; bağlayıcı olan yönetmeliğin kendisidir.

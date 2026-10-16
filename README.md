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

**Hafta 0: ortam kuruldu, henüz sonuç yok.** Bu sayfaya her sayı ölçüldüğü
anda girer. Ölçülmemiş sayı yazılmaz.

| aşama | hafta | durum |
|---|---|---|
| 0. ortam, repo, dokümantasyon düzeni | — | **tamam** |
| 1. belgeleri toplama, ilk 50 soruluk test seti | 1-2 | sırada |
| 2. en basit çalışan RAG (taban sistem, ilk sonuçlar) | 3-4 | |
| 3. parçalama / arama / reranker varyantları, test seti 150+ | 5-6 | |
| 4. tüm konfigürasyonları değerlendirme, elle puanlama, hata analizi | 7-8 | |
| 5. arayüz ve demo | 9 | |
| 6. rapor ve sunum | 10 | |

## Araştırma sorusu

> Türkçe mevzuat metinlerinde hangi parçalama ve arama stratejisi, doğru ve
> kaynağa dayalı cevap oranını en çok artırır?

Karşılaştırılacak konfigürasyonlar:

1. Arama yok, yalnızca dil modeli (taban sistem)
2. BM25 + dil modeli
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

```
data/
  kaynaklar.csv      bilgi tabanındaki her belge: URL, sürüm tarihi, sha256
  raw/               indirilen PDF'ler (depoda)
  processed/         PDF'ten çıkan metin ve parçalar (yeniden üretilir, depoda değil)
  testset/           etiketli soru-cevap seti (depoda)
docs/                rapor, ölçüm, karar ve günlük kayıtları
scripts/             tek seferlik ve deney betikleri
src/mevzuat_rag/     paket: belge işleme, parçalama, arama, üretim, değerlendirme
tests/
```

> Bu sistem resmî danışmanlık değildir. Cevaplar ilgili yönetmelik maddesiyle
> birlikte verilir; bağlayıcı olan yönetmeliğin kendisidir.

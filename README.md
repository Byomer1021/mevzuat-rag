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

GTÜ'de NLP dersi projesi (CSE 484); 19 Ekim - 17 Aralık 2026. Öneri 21
Ekim, ara rapor 5 Kasım.

**Hafta 0: bilgi tabanı toplandı, arama tabanı ve değerlendirme kodu hazır;
henüz soru seti yok, arama başarısı ölçülmedi.** Bu sayfaya her sayı
ölçüldüğü anda girer. Ölçülmemiş sayı yazılmaz.

Şu ana kadar ölçülen:

- **114 kaynak:** 56 GTÜ yönetmelik/yönergesi (Kalite Ofisi dizininden,
  yürürlükteki revizyon), YÖK geçiş yönetmeliği, site taramasından seçilen 31
  esas/rehber/SSS belgesi, 21 programın güncel öğretim planı, akademik
  takvim, 141 öğrenci formunun kataloğu ve web içeriği (31 SSS sayfası, 127
  konu sayfası, bu yılın 43 duyurusu).
- 40 birimin sitesi tarandı: 4824 duyuru, 3253 dosya envantere girdi
  ([olcumler §7](docs/olcumler.md)). Sitede yönergelerin eski
  revizyonlarına 12 bağlantı var.
- 109 PDF'te kodlama bozulması 0, kişisel veri izi 0. Taranmış tek belge
  (Uçak Müh. planı) dışarıda.
- Madde başlıkları belgeden belgeye farklı yazılmış: tireli, noktalı,
  ayraçsız, harfli alt madde ("12a"), ek ve geçici madde. Madde yapısındaki
  52 belgede numara boşluğu yok.
- Bilgi tabanı 5537 parçaya bölündü: 914 madde, 2409 paragraf, 1914 web,
  150 takvim, 141 form. Kapsama, sayfa aralığı, kimlik çakışması ve
  kişisel veri denetimi temiz.
- Yoğun arama modelinin (multilingual-e5-base) 512 token girdisini madde
  koşulunda 43 madde aşıyor, sabit koşulda hiçbir parça
  ([olcumler §11](docs/olcumler.md)).
- Aynı sayıda sabit uzunluklu parçayla (721 karakter, 922'ye karşı 923)
  maddelerin %60.1'i bölünüyor, sabit parçaların %61.8'i birden çok maddeye
  değiyor ([olcumler §10](docs/olcumler.md)).

Ayrıntılar: [olcumler §2-10](docs/olcumler.md). Takvim:
[on-rapor §8](docs/on-rapor.md).

## Araştırma sorusu

> ≥150 elle yazılmış öğrenci sorusunda, mevzuatı madde sınırından bölmek,
> aynı sayıda sabit uzunluklu parçaya göre, cevabın geçtiği cümleyi ilk 5
> sonuçta daha sık getiriyor mu? BM25 ve yoğun arama için ayrı ayrı.
> **Hayır:** farkın %95 eşleştirilmiş bootstrap aralığı sıfırı içeriyorsa.

Değişen tek şey parça sınırları: aynı belgeler, aynı parça sayısı, aynı
belge adı öneki, aynı sorular. "Bulundu" ölçütü parçalamadan bağımsız: her
soruda maddeden birebir alınmış kanıt cümlesi, getirilen parçaların içinde
tamamen var mı ([K-022](docs/kararlar.md)). Öneri metni:
[docs/oneri.md](docs/oneri.md).

Sistemin kendisi (kaynak gösteren cevap, "bilmiyorum") demo; kök bulma,
hibrit arama ve cevap kalitesi ek ölçümler ([on-rapor §5](docs/on-rapor.md)).

## Dokümantasyon

Proje adım adım kayıt altında tutuluyor. Nasıl tutulduğu:
[docs/README.md](docs/README.md).

| belge | ne var |
|---|---|
| [proje-tanimi.md](docs/proje-tanimi.md) | başlangıçta verilen tanım: hedef, veri, yöntem, plan |
| [on-rapor.md](docs/on-rapor.md) | tanımın gerçek kısıtlara oturtulmuş hali, kapsam, açık sorular, takvim |
| [oneri.md](docs/oneri.md) | dersin öneri formuna giden metin (İngilizce) |
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
  soru_defteri.html  ekip için aynı araç, tarayıcıda, kurulumsuz (K-024)
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
  onisle.py          temizlik + parçalama + denetim; madde ve sabit kümesi (olcumler §4, §10)
  ilk_bakis.py       iki koşulun yapısal farkı ve gösterim sorusu (olcumler §10)
  deney.py           araştırma sorusunun deneyi: iki koşul, BM25 / e5, bootstrap (K-022)
  token_olcum.py     yoğun arama modelinin 512 token sınırını aşan parçalar (olcumler §11)
  soru_al.py         Soru Defteri'nden gelen soruları denetleyip test setine katar
  soru_defteri_veri.py  Soru Defteri sayfasının parça verisi
  oneri_docx.py      docs/oneri.md'yi dersin öneri formuna (docx) yazar
  ortam_kontrol.py   ortam ve GPU ölçümü (olcumler §1)
  testset_kontrol.py test setinin şema denetimi ve dağılımı
  tara.py, envanter.py, web_secim.py   site taraması ve web içeriği (olcumler §7-8)
src/mevzuat_rag/
  madde.py           madde başlığı tanıyıcı (11 biçim)
  onisleme.py        PDF'ten temiz sayfa metni, kalite formu başlığı atılır
  parcalama.py       madde bazlı, paragraf, sabit uzunluklu, takvim, web, form
  arama.py           BM25 (Türkçe küçük harf, isteğe bağlı kök) ve e5 yoğun arama; belge adı öneki
  deney.py           deneyin dizini, soru kümeleri, iki koşulun karşılaştırması
  degerlendirme.py   kanıt kapsamı, Recall@k, MRR, eşleştirilmiş bootstrap, McNemar
  testset.py         test seti şeması (kanıt alıntısı dahil), denetim, dağılım
  kisisel.py, formlar.py, web.py       kişisel veri taraması, form süzgeci, web metni
tests/
```

> Bu sistem resmî danışmanlık değildir. Cevaplar ilgili yönetmelik maddesiyle
> birlikte verilir; bağlayıcı olan yönetmeliğin kendisidir.

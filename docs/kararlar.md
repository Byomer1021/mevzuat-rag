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

Hafta 3'ten (taban sistem) önce karar verilmeli. Kriterler:

- **Türkçe kalite**, özellikle "bilmiyorum" deme disiplini ve madde numarası
  alıntılama.
- **Maliyet × deney sayısı.** 5 konfigürasyon × 150-250 soru × tekrarlar
  binlerce çağrı eder. Bir API seçilirse soru başına maliyet baştan ölçülmeli.
- **Tekrarlanabilirlik.** Sabit model sürümü ve sıcaklık 0. Sürümü
  sessizce değişen bir uç nokta, haftalar arası karşılaştırmayı bozar.
- **Donanım.** Yerel model için 8 GB VRAM var. Hangi boyutun hangi hızda
  çalıştığı ölçülmedi.

Seçenekler: bir LLM API'si veya yerelde çalışan açık bir model. İkisi birden
de olabilir: geliştirme yerelde, nihai ölçüm API'de.

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

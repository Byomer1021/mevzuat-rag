# Ölçüm Günlüğü

Projede ölçülen her şey burada, numaralı bölümler halinde. Amaç sonucu güzel
göstermek değil, **hangi kararın neye dayandığını** kayda geçirmek. Ham
çıktılar `results/` altında.

Her bölüm şu sırayla yazılır: neden ölçüldü, nasıl ölçüldü (betik, komut,
konfigürasyon), sonuç, ne anlama geldiği ve ne anlama gelmediği.

---

## 1. Ortam: GPU görünüyor mu, yoksa gerçekten çalışıyor mu (2026-10-16)

**Neden.** GTX 1080 Pascal mimarisinde (sm_61). torch'un bir derlemesi bu
mimari için kernel içermiyorsa `torch.cuda.is_available()` yine `True` döner
ve hata ilk gerçek işlemde, büyük ihtimalle bir deneyin ortasında çıkar. Bu
yüzden "görünüyor" ile "çalışıyor" ayrı ölçüldü.

**Nasıl.** `uv run python scripts/ortam_kontrol.py --kaydet results/ortam.json`.
Betik GPU'da 2048×2048 float32 matris çarpımı yapıp sonucu aynı girdinin CPU
sonucuyla karşılaştırıyor. Ham çıktı: [results/ortam.json](../results/ortam.json).

**Sonuç.**

| | değer |
|---|---|
| Python | 3.12.10 |
| torch | 2.7.1+cu118 |
| derlemedeki mimariler | sm_37, sm_50, sm_60, **sm_61**, sm_70, sm_75, sm_80, sm_86, sm_90 |
| GPU | GeForce GTX 1080, sm_61, 8.0 GB |
| sürücü | 526.47 (nvidia-smi'ye göre en fazla CUDA 12.0) |
| GPU'da kernel çalıştı | **evet** |
| GPU ile CPU sonucu arasındaki en büyük mutlak fark | 5.2 × 10⁻⁴ |

Fark beklenen büyüklükte: her eleman 2048 çarpımın toplamı, tipik büyüklüğü
√2048 ≈ 45. Bu da göreli olarak ~10⁻⁵ eder; float32'de toplama sırasının
farklı olmasından beklenen düzey bu.

**Ne anlama gelmiyor.** Betik matris çarpımının süresini de yazıyor (iki
çalıştırmada 3.93 ve 2.83 ms), ama bu tek örnek. Isınma ve tekrar yapılmadan
alınmış bir sayı hız ölçümü sayılmaz, burada yalnızca kernel'in çalıştığının
kanıtı olarak duruyor. Gömme hızı, gerçek model ve gerçek parçalarla ayrıca
ölçülecek.

GPU'nun **uzun süreli yük altında** kararlı olup olmadığı da bu ölçümün
konusu değil. Önceki bir projede (trafikisaret) bu kart eğitim yükünde düştü.
Bu projede yük yalnızca çıkarım; ilk tam gömme çalıştırmasında kayda geçecek.

### Kurulumun yan ölçümleri

| | değer |
|---|---|
| `uv sync --all-extras`, önbellek boşken | 233 s, 117 paket |
| `.venv` boyutu | 5.81 GB |
| uv önbelleği (`D:\.cache\uv`) | 5.84 GB |
| D'nin boş alanındaki gerçek azalma | 6.0 GB (587.1 → 581.1) |
| C'nin boş alanı, kurulumdan önce ve sonra | 13.0 → 13.0 GB |

`.venv` ile önbellek toplamda 11.6 GB görünüyor ama disk 6.0 GB azaldı: aynı
sürücüde uv dosyaları hardlink'liyor, aynı byte'lar iki yerde sayılıyor.
Önbellek C'de olsaydı hardlink sürücüler arası çalışmayacağı için kopya
düşecekti; C'nin değişmemesi yönlendirmenin tuttuğunu gösteriyor
([K-003](kararlar.md)).

İlk `pytest` çalıştırması (çekirdek kütüphanelerin import testi) 123 s,
ikincisi 12.8 s sürdü. Farkın ilk import'taki bytecode derlemesinden
kaynaklandığını tahmin ediyorum. Doğrulamadım.

# Soru Yazma Rehberi

Test setinin sorularını yazan herkes için.

## Ekip: Soru Defteri (tarayıcıda, kurulum yok)

https://claude.ai/artifact/5weJKDRsC19fpv1ivUkVLT, kaynağı
[app/soru_defteri.html](../app/soru_defteri.html). Ömer Can sayfanın Share
menüsünden paylaşmadan başkası açamaz.

1. Sağ üstten adını seç. Soruyu yaz, soldan maddeyi bul, "Dayanaklara ekle",
   cevap cümlesini fareyle seç, "Seçili metni kanıt yap". Kurallar aşağıda
   ve sayfanın üstünde aynı.
2. Sorular **yalnız o tarayıcıda** durur; sunucuya gitmez
   ([K-024](kararlar.md)). Her oturumun sonunda "Dışa aktar", "Kopyala",
   metni Ömer Can'a gönder.
3. Ömer Can gelen metni bir dosyaya kaydedip içeri alır:
   `uv run python scripts/soru_al.py gelen/veysel.txt`. Şemaya uymayan soru
   nedeniyle raporlanır, alınmaz. Aynı soruyu iki kez göndermek sorun değil;
   defterde düzenlenen soru test setinde yerinde güncellenir (eşleme
   `data/testset/defter.json`).

## Ömer Can: Streamlit aracı

Repo kurulu bilgisayarda aynı iş:

```powershell
uv run streamlit run app/soru_yaz.py
```

Solda maddeleri arayıp okursun, sağda soruyu yazıp dayanak maddeleri
seçersin ve her dayanaktan cevabı taşıyan cümleyi **kanıt** olarak
kopyalarsın. Her kayıt şemaya göre denetlenir ve `data/testset/sorular.jsonl`
dosyasına eklenir. Dosyayı elle düzenlersen denetim için:
`uv run python scripts/testset_kontrol.py`.

## En önemli kural: önce soru, sonra madde

Soruyu maddeyi okumadan, bir öğrencinin soracağı gibi yaz. Cevabı maddeden
**sonra** bul.

Maddeye bakarak yazılan soru maddenin kelimelerini tekrar eder ("devam
zorunluluğu", "mazeret sınavı") ve aramayı olduğundan iyi gösterir. Gerçek
bir öğrenci "devamsızlıktan kalır mıyım", "rapor alırsam sınava sonra
girebilir miyim" diye sorar. Sistemin ölçülmesi gereken şey bu farkı
kapatabilmesi.

İyi kaynaklar: kendi başına gelenler, arkadaşlarının sorduğu, öğrenci
gruplarında dönen sorular.

**SSS sayfalarından soru alma.** Birimlerin 31 SSS sayfası bilgi tabanında
([K-021](kararlar.md)). Bir SSS sorusunu aynen test setine koyarsan arama,
sorunun kendisini bulur ve sonuç olduğundan iyi görünür. SSS'leri hangi
konuların sorulduğunu görmek için oku, ama soruyu kendi cümlenle yaz.

Aynı nedenle soruları dil modeline yazdırmıyoruz: hem kelimeleri belgeden
alır, hem de sonuçta cevabı yine bir dil modeli verecek.

**Gösterim sorusu.** "Derslere devam zorunluluğu yüzde kaç?" öneri raporunda
örnek olarak kullanıldı ve aramanın çıktısına bakıldı
([olcumler §10](olcumler.md)). Bu soru yalnız `dev` bölümüne girebilir,
`test`'e hiç girmez.

## Türler ve hedef dağılım (dev bölümü, 50 soru)

| tür | ne | hedef |
|---|---|---|
| tek | cevap tek bir maddede ("Bir dersten en fazla kaç saat devamsızlık yapabilirim?") | ~28 |
| çok | iki veya daha fazla madde gerekir; mümkünse farklı belgelerden ("Çift anadal yaparken stajı iki bölümde de yapmam gerekir mi?") | ~13 |
| cevapsız | belgelerde cevabı yok ("Kütüphane kaçta kapanıyor?", "Burs başvurusu ne zaman?") | 8-10 (%15-20) |

Cevapsız sorular halüsinasyonu en doğrudan ölçen sorular. En değerlileri
konusu belgelere **yakın** olanlar. "Erasmus hibesi ayda ne kadar?":
Erasmus yönergesi iki maddede hibeden söz ediyor ama tutar vermiyor. "Burs
başvurusu ne zaman?" ve "Kütüphane kaçta kapanıyor?": danışmanlık m6
"danışman burslar ve kütüphane hakkında bilgi verir" diyor, "burs" başka üç
maddede daha geçiyor, ama hiçbirinde tarih ya da saat yok. Arama bu
maddeleri getirecek ve model oradan bir cevap uydurmaya yönelecek; ölçmek
istediğimiz an tam olarak bu. Konusu bambaşka olan bir soru ("Kantinde ne
var?") ise kolay bir soru.

Bu örneklerin ömrü bilgi tabanına bağlı. Rehberin ilk sürümündeki "Erasmus'ta
kaç ders saydırabilirim?" örneği, Erasmus yönergesi eklenince cevapsız
olmaktan çıktı (m6: "bir dönemde 30 AKTS … tavsiye edilir"). Bilgi tabanı
bu yüzden sorulardan önce donduruluyor ([K-016](kararlar.md)).

Bir soruyu cevapsız diye işaretlemeden önce aracın arama kutusunda anahtar
kelimelerini dene. Cevap bir yerde çıkarsa soru cevapsız değildir.

## Alanlar

- **Referans cevap:** kısa ve olgusal. Sayı, süre veya koşul varsa aynen
  yaz. Cevapsız soruda boş bırak.
- **Dayanak:** cevabın dayandığı bütün parçalar. Cevap bir istisnaya
  bağlıysa istisnanın olduğu madde de dayanaktır.
- **Kanıt:** her dayanaktan, cevabı taşıyan cümle; soldaki metinden
  **birebir** kopyala (satır sonları sorun değil). Birden çok dayanak varsa
  dayanak sırasıyla, aralarına boş satır koy. En az 20 karakter: "%70" değil,
  "Teorik derslerde en az %70, laboratuvar ve uygulamalı derslerde en az %80
  devam zorunluluğu aranır." Bütün maddeyi değil, cevabın geçtiği cümleyi
  al; araştırma sorusu tam olarak bu cümlenin bulunup bulunmadığını ölçüyor
  ([K-022](kararlar.md)). Cevapsız soruda boş.
- **Etiketler:** hata analizinde kırılım için. `tarih`, `sure`, `sayi`,
  `not`, `istisna`, `kosul`, `tanim`, `basvuru`; gerekirse yenisini yaz.
- **Bölüm:** ilk 50 soru `dev`. `test` sorularını sonra, dev setiyle ayar
  yapılırken bunları görmeden yazacağız ([K-007](kararlar.md)).

## Kapsama

Altta "Durum" tablosu belge başına soru sayısını gösteriyor. Hiç soru almayan
belge kalmasın. Akademik takvim de dahil: tarih soruları sistemin en sık
yanılacağı yerlerden biri olabilir.

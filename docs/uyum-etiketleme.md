# Etiket uyumu: etiketleme talimatı

Sana 20 test sorusu düştü. Listen `data/uyum/liste_<adın>.txt` dosyasında.
Soruları ekipten başka biri yazdı. Sen onları, sanki soruyu kendin yazmışsın
gibi etiketleyeceksin. Amaç şu: iki kişi aynı soruya aynı maddeyi ve aynı
cümleyi gösteriyor mu? Sonuç raporda veri setinin güvenilirliği olarak
yazılacak ([K-026](kararlar.md)).

Son tarih **21 Kasım**. Bir oturumda bitmezse sorun değil, defter kaydeder.

## Yapma

- `data/testset/sorular.jsonl` dosyasına bakma. Doğru cevaplar orada.
- Daha önce dolaşan örnek soru listesine ve içindeki madde önerilerine bakma.
- Soruyu yazan kişiye sorma, onunla konuşma. Takılırsan Ömer Can'a yaz.

## Her soru için

1. Soru Defteri'ni aç. Sağ üstten adını seç.
2. Listedeki soruyu Soru kutusuna olduğu gibi yapıştır, değiştirme.
3. Etiketlerin altındaki "başka etiket" kutusuna sorunun kimliğini yaz (`q055`
   gibi) ve Enter'a bas. Bu olmadan sorunu eşleştiremem.
4. Cevabın geçtiği yeri arama kutusuyla bul.
   - Bilgi tabanında cevabı yoksa türü **cevapsız** seç.
   - Cevap tek bir parçadaysa **tek** seç.
   - Cevap için birden fazla parça gerekiyorsa **çok** seç, her parçayı ekle.
5. Her parça için cevabı veren cümleyi seçip "Seçili metni kanıt yap"a bas.
6. Referans cevap yazman gerekmiyor. Defter boş bırakmana izin vermezse `-` yaz.
7. Bölüm olarak **dev** seç. Bu kayıtlar test setine girmeyecek, sadece
   karşılaştırmada kullanılacak.
8. Kaydet.

Emin olamadığın soruda da bir karar ver. "Cevabı yok" da bir karardır.
Uzun düşünmene gerek yok, soruyu ilk kez gören bir öğrencinin yardımcısı
gibi davran.

## Bitince

"Dışa aktar"a bas, metni kopyala, Ömer Can'a gönder. Defterdeki eski
soruların da gelmesi sorun değil, sadece listendekiler alınır.

Ömer Can içeri almak için: `uv run python scripts/uyum.py al <ad> <dosya>`,
ikisi de gelince `uv run python scripts/uyum.py hesapla`. Bu dosyaları
`soru_al.py` ile içeri alma, test seti donmuş durumda.

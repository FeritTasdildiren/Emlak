# Demo Senaryosu — 15 Dakikalık Platform Tanıtımı

**Versiyon:** v1.0 | **Tarih:** 2026-02-21
**Süre:** 15 dakika
**Hedef Kitle:** Küçük-orta ölçekli emlak ofisleri (Anadolu Yakası)

---

## Demo Öncesi Hazırlık

### Ortam
- Platformda demo hesabı hazır olmalı (örnek verilerle dolu)
- İnternet bağlantısı kontrol edilmeli
- Ekran paylaşım aracı test edilmeli
- PDF rapor indirme çalışıyor olmalı

### Demo Hesabında Olması Gerekenler
- 10-15 arası örnek ilan (farklı ilçe ve tiplerden)
- 5-6 örnek müşteri kaydı (CRM'de)
- En az 2-3 tamamlanmış AI değerleme
- Telegram bot bağlı ve çalışır durumda

### Müşteri Bilgisi
- Ofisin bulunduğu ilçeyi bilin
- Mümkünse bir ilanlarının bilgilerini hazırlayın (m², oda, kat)
- Yetkili kişinin adını ve ofis deneyim süresini bilin

---

## Demo Akışı

---

### Bölüm 1: Giriş ve Login (1 dakika)

**Ekran:** Login sayfası → Dashboard

**Konuşma Notları:**
> "Merhaba [Yetkili Adı], zaman ayırdığınız için teşekkür ederim. Bugün platformumuzu kısaca tanıtacağım — yaklaşık 15 dakika sürecek. Sonunda sorularınız olursa memnuniyetle yanıtlarım."
>
> "Hemen giriş yapıyorum..."

**Yapılacak:**
1. E-posta ve şifre ile giriş yap
2. Dashboard'un yüklenmesini bekle

**Geçiş:**
> "İşte ana ekranımız. Burada günlük ihtiyacınız olan her şeyi göreceksiniz."

---

### Bölüm 2: Dashboard Genel Bakış (2 dakika)

**Ekran:** Dashboard ana sayfa

**Konuşma Notları:**
> "Dashboard'da şunları bir bakışta görüyorsunuz:"

**Gösterilecek alanlar:**
1. **Portföy özeti:** "Aktif ilan sayınız, opsiyon altındakiler, satılanlar — hepsi burada."
2. **Son değerlemeler:** "En son yaptığınız AI değerlemeleri burada listeleniyor."
3. **Müşteri bildirimleri:** "Takip etmeniz gereken müşteriler burada uyarı veriyor."
4. **Bölge istatistikleri:** "Bölgenizdeki ortalama m² fiyatı ve son dönem trendi."

**Konuşma Notları:**
> "Gün başlangıcında bu ekranı açtığınızda ne yapmanız gerektiğini hemen görüyorsunuz. Deftere bakmaya, Excel açmaya gerek yok."

**Geçiş:**
> "Şimdi en güçlü özelliğimize geçelim — yeni bir ilan ekleyelim ve yapay zekadan fiyat tahmini alalım."

---

### Bölüm 3: Yeni İlan Ekleme (3 dakika)

**Ekran:** Portföy → Yeni İlan

**Konuşma Notları:**
> "Bir müşteriniz satılık dairesi için size geldi diyelim. Bilgileri hızlıca girelim."

**Yapılacak (canlı giriş):**
1. **"+ Yeni İlan"** butonuna tıkla
2. Bilgileri doldur — tercihen müşterinin kendi bölgesinden bir örnek:
   - İlçe: `[Müşterinin ilçesi]`
   - Mahalle: `[Bölgeye uygun mahalle]`
   - Tip: Daire
   - Oda: 3+1
   - Net m²: 120
   - Brüt m²: 145
   - Kat: 5
   - Toplam kat: 10
   - Bina yaşı: 8
   - Isınma: Doğalgaz (Kombi)
3. **"Kaydet"** butonuna tıkla

**Konuşma Notları:**
> "Gördüğünüz gibi basit bir form. Mülk bilgilerini giriyorsunuz — tıpkı portale ilan girerken olduğu gibi, ama burada veriler sizin sisteminizde kalıyor."
>
> "Şimdi asıl sihir başlıyor..."

**Geçiş:**
> "Bu mülkün değerini yapay zekamıza soralım."

---

### Bölüm 4: AI Değerleme Çalıştırma (3 dakika)

**Ekran:** İlan detay → AI Değerleme sonuç ekranı

**Bu bölüm demonun en kritik anıdır. Yavaş ve etkili ilerleyin.**

**Yapılacak:**
1. İlan detay sayfasında **"AI Değerleme"** butonuna tıkla
2. Yüklenme animasyonunu göster (birkaç saniye)
3. Sonuç ekranını incele

**Konuşma Notları:**
> "Butona tıklıyorum... Yapay zekamız şu anda 24 farklı değişkeni analiz ediyor: metrekare, konum, bina yaşı, kat, ısınma tipi ve daha fazlası..."
>
> *(Sonuç gelince)*
>
> "İşte sonuç: **[X milyon TL]**. Güven aralığı [alt] ile [üst] TL arasında."
>
> "Bu tahmin İstanbul genelinde ortalama **%90 doğruluk** ile çalışıyor. Yani müşterinize 'Bu daire şu kadar eder' dediğinizde, arkanızda veri var."

**Vurgulama noktaları:**
- Güven aralığı → "Fiyat pazarlığında alt ve üst sınırınızı biliyorsunuz"
- Benzer mülk karşılaştırması → "Yakınlardaki benzer daireler şu fiyatlarda satılıyor/satılık"
- Bölge ortalaması → "[İlçe] ortalamasının üstünde/altında"

**Olası soru: "Bu fiyat gerçekçi mi?"**
> "Modelimiz İstanbul'daki gerçek satış ve ilan verilerini analiz ederek öğreniyor. [İlçe] bölgesinde de aktif olarak çalışıyor. Tabii ki nihai fiyatı siz belirliyorsunuz — bu bir pusula, rotanızı siz çiziyorsunuz."

**Geçiş:**
> "Peki bu mülkün bulunduğu bölge hakkında ne biliyoruz? Bir de bölge analizine bakalım."

---

### Bölüm 5: Bölge Analizi + Deprem Riski (3 dakika)

**Ekran:** Bölge analizi harita görünümü + Deprem risk ekranı

**Yapılacak:**
1. Sol menüden **"Bölge Analizi"** sekmesine geç
2. İlçeyi ve mahalleyi seç
3. Harita üzerinde verileri göster
4. Deprem risk skorunu göster

**Konuşma Notları — Bölge Analizi:**
> "Bir müşteriniz '[Mahalle] nasıl bir bölge, fiyatlar ne durumda?' diye sorduğunda buraya bakabilirsiniz."
>
> "İşte [Mahalle] verileri:"
> - "Ortalama m² fiyatı: [X] TL"
> - "Son dönem trendi: [yükseliş/düşüş/yatay]"
> - "Bölgedeki ortalama bina yaşı: [X] yıl"
>
> "Bu bilgiyi müşterinize verdiğinizde güvenilirliğiniz artar."

**Konuşma Notları — Deprem Riski:**
> "Bugün İstanbul'da ev alacak herkes deprem riskini soruyor. Bu çok doğal bir beklenti."
>
> "Platformumuz AFAD'ın resmi verilerini kullanarak her konum için deprem risk skoru hesaplıyor."
>
> "İşte bu mülk için skor: [X/10]. Bu bilgiyi müşterinize şeffaf ve bilimsel veri ile sunabilirsiniz."

**Olası soru: "Deprem riski yüksek çıkarsa satışı olumsuz etkiler mi?"**
> "Aksine — şeffaflık güven oluşturur. Müşteri bu bilgiyi zaten başka kaynaklardan araştıracak. Siz önceden sunarsanız, güvenilir danışman olarak konumlanırsınız."

**Geçiş:**
> "Şimdi tüm bu bilgileri müşterinize sunabileceğiniz profesyonel raporu göstereyim."

---

### Bölüm 6: PDF Rapor İndirme (1 dakika)

**Ekran:** PDF rapor önizleme

**Yapılacak:**
1. İlan detay sayfasına geri dön
2. **"PDF Rapor İndir"** butonuna tıkla
3. Oluşan PDF'i aç ve göster

**Konuşma Notları:**
> "Bir butona tıklıyorum ve profesyonel değerleme raporu hazır."
>
> *(PDF açılınca)*
>
> "Bu raporda mülk bilgileri, AI fiyat tahmini, emsal karşılaştırma, bölge analizi ve deprem risk skoru var — hepsi tek sayfada."
>
> "Bunu müşterinize dijital olarak WhatsApp/e-posta ile gönderebilir veya basıp elden teslim edebilirsiniz. Müşteriniz bunu gördüğünde profesyonel bir danışmanla çalıştığını hisseder."

**Olası soru: "Raporda ofis logom olabilir mi?"**
> "Evet, Pro ve Elite planlarda rapor üzerine kendi logonuzu ve iletişim bilgilerinizi ekleyebilirsiniz."

**Geçiş:**
> "Son olarak fiyatlandırmamız ve size özel kampanyadan bahsedeyim."

---

### Bölüm 7: Fiyatlandırma ve Kapanış (2 dakika)

**Ekran:** Fiyatlandırma sayfası veya sunum

**Konuşma Notları:**
> "Üç planımız var:"
>
> "**Starter** — tamamen ücretsiz. 5 ilan, ayda 10 değerleme. Platformu tanımak için ideal."
>
> "**Pro** — ayda 799 TL. 50 ilan, 100 değerleme, Telegram bot, CRM, deprem riski, emsal karşılaştırma, öncelikli destek. Günlük işleriniz için gerçekten ihtiyacınız olan her şey burada."
>
> "**Elite** — ayda 1.499 TL. Sınırsız kullanım, telefon desteği, API erişimi. Birden fazla danışmanı olan ofisler için."

**Kampanya açıklaması:**
> "Ama sizin için özel bir teklifimiz var: Platformumuzu ilk kullanan **30 ofise** özel olarak **Pro planı 3 ay boyunca tamamen ücretsiz** sunuyoruz."
>
> "3 ay boyunca tüm Pro özellikleri kullanırsınız. 3 ay sonunda devam edip etmemek tamamen size kalmış — herhangi bir taahhüt yok."
>
> "Ücretsiz onboarding desteği de dahil — birlikte ilanlarınızı yükler, botu kurar, sistemi hazır hale getiririz."

**Kapanış:**
> "Bu teklif size uygun mu? Hemen başlayabiliriz — kayıt 2 dakika sürüyor ve ilk değerlemenizi bugün yapabilirsiniz."

---

## Olası Sorular ve Cevaplar

### Genel

**S: Bu platform Emlakjet/Sahibinden'in yerine mi geçiyor?**
> "Hayır, kesinlikle değil. Bu platformlar ilan yayınlama portalıdır. Biz ise sizin iç operasyonunuzu güçlendiriyoruz — fiyat tahmini, müşteri takibi, raporlama. Portal ilanlarınız aynen devam eder, biz ofis tarafını destekliyoruz."

**S: Veri güvenliği konusunda ne yapıyorsunuz?**
> "Tüm veriler şifreli sunucularda saklanıyor. Müşteri ve ilan bilgilerinizi üçüncü taraflarla paylaşmıyoruz. KVKK uyumlu çalışıyoruz."

**S: Mobilde çalışıyor mu?**
> "Platform web tabanlı ve mobil uyumlu tasarlandı. Telefonunuzun tarayıcısından rahatlıkla kullanabilirsiniz. Ayrıca Telegram bot, mobilde zaten doğal olarak çalışıyor."

### Teknik

**S: Yapay zeka modeli nasıl çalışıyor, hangi verileri kullanıyor?**
> "Modelimiz İstanbul'daki gerçek emlak verilerini (fiyat, konum, metrekare, bina özellikleri) analiz ederek öğreniyor. 24 farklı değişkeni aynı anda değerlendiriyor. Sürekli güncellenen veri ile eğitiliyor."

**S: Her ilçede aynı doğrulukta mı çalışıyor?**
> "İstanbul genelinde ortalama %90 doğruluk var. İlan yoğunluğu fazla olan ilçelerde (Kadıköy, Ataşehir gibi) doğruluk daha da yüksek. Sürekli iyileştirme yapıyoruz."

**S: İnternet yoksa çalışır mı?**
> "Platform internet bağlantısı gerektiriyor çünkü AI analizi sunucu tarafında yapılıyor. Ama ofiste internet olan her ortamda sorunsuz çalışır."

### Ticari

**S: 3 ay sonra fiyat artacak mı?**
> "Hayır, belirtilen fiyatlar sabit. 3 aylık ücretsiz dönem sonrasında Pro plan 799 TL/ay olarak devam eder. Sürpriz fiyat artışı yok."

**S: Aylık mı, yıllık mı ödeniyor?**
> "Aylık ödeme. İstediğiniz zaman iptal edebilirsiniz. Yıllık planlarda indirim opsiyonu da ileride sunulacak."

**S: Fatura kesiliyor mu?**
> "Evet, her ödeme için e-fatura kesilir."

**S: Rakiplerinizden farkınız ne?**
> "Biz genel bir ilan portalı değiliz. Özellikle bağımsız emlak ofislerinin günlük operasyonunu iyileştirmek için yapılmış bir araç sunuyoruz. AI fiyat tahmini, deprem riski, bölge analizi — bu kombinasyonu bir arada sunan başka bir platform şu an yok."

---

## Demo Sonrası Aksiyon Planı

| Durum | Aksiyon | Zamanlama |
|-------|---------|-----------|
| Hemen kayıt olmak istiyor | Canlıda birlikte kayıt yap, ilk ilanı ekle | Aynı görüşmede |
| Düşünmek istiyor | Teşekkür et, 3 gün sonra takip e-postası gönder | 3 gün |
| İlgilenmiyor | Nazikçe teşekkür et, 2 ay sonra tekrar ulaş | 2 ay |
| Sorularını çevresiyle paylaşmak istiyor | Demo kaydı veya sunum PDF'i gönder | Aynı gün |

---

## Demo Yapılırken Dikkat Edilecekler

1. **Hız:** 15 dakikayı aşmayın. Kısa ve etkili olun. İlgi çekerse uzatabilirsiniz ama girişte "15 dakika" deyin.
2. **Müşterinin bölgesini kullanın:** Demo verilerinde müşterinin kendi ilçesini/mahallesini kullanmak etkiyi artırır.
3. **Gerçek veri ile deneyin:** Mümkünse müşterinin bir ilanının bilgileriyle canlı değerleme yapın. "Bakın, sizin ilanınız için sonuç bu" demek çok etkili.
4. **Teknik detaya girmeyin:** "Yapay zeka" deyin, "LightGBM gradient boosting" demeyin. Basit tutun.
5. **Soruları not alın:** Yanıtlayamadığınız sorulara "Bunu araştırıp size döneceğim" deyin. Asla uydurma yanıt vermeyin.
6. **Demo kesintiye uğrarsa:** Sakin kalın. "Bir saniye, yeniden bağlanalım" deyin. Alternatif olarak ekran görüntüleri ile devam edin.

---

*Emlak Teknoloji Platformu — Demo Senaryosu v1.0*

# Onboarding Rehberi — Emlak Teknoloji Platformu

**Versiyon:** v1.0 | **Tarih:** 2026-02-21

---

## Hoş Geldiniz!

Bu rehber, Emlak Teknoloji Platformu'na kayıt olmanızı ve ilk değerlemenizi yapmanızı adım adım anlatır. Tüm süreç **10 dakikadan kısa** sürer.

---

## 1. Kayıt ve Giriş

### Adım 1: Hesap Oluşturma
1. Platformun ana sayfasına gidin
2. **"Ücretsiz Kayıt Ol"** butonuna tıklayın
3. Aşağıdaki bilgileri doldurun:
   - Ad Soyad
   - E-posta adresi
   - Telefon numarası
   - Ofis adı
   - İlçe / Mahalle
4. Şifrenizi belirleyin (en az 8 karakter)
5. **"Kayıt Ol"** butonuna tıklayın

### Adım 2: E-posta Doğrulama
1. E-posta kutunuza gelen doğrulama linkine tıklayın
2. (Spam/gereksiz klasörünü de kontrol edin)
3. Hesabınız aktif!

### Adım 3: Giriş Yapma
1. E-posta ve şifrenizle giriş yapın
2. Dashboard (ana ekran) karşınıza gelecek

> **Tebrikler!** Artık platformu kullanmaya başlayabilirsiniz.

---

## 2. İlk Portföyünüzü Yükleme

### Tek İlan Ekleme
1. Sol menüden **"Portföy"** sekmesine tıklayın
2. Sağ üstteki **"+ Yeni İlan"** butonuna tıklayın
3. İlan bilgilerini doldurun:
   - **Konum:** İlçe, mahalle, adres
   - **Mülk bilgileri:** Tip (daire/villa/arsa), oda sayısı, net m², brüt m²
   - **Bina bilgileri:** Bina yaşı, kat, toplam kat, ısınma tipi
   - **Fiyat:** İstediğiniz satış/kira fiyatı
   - **Açıklama:** İlan metni (opsiyonel)
4. **"Kaydet"** butonuna tıklayın

### Toplu İlan Yükleme
1. **"Portföy"** sekmesinden **"Toplu Yükle"** butonuna tıklayın
2. Excel/CSV şablonunu indirin
3. Mevcut ilanlarınızı şablona doldurun
4. Dosyayı yükleyin
5. Sistem otomatik olarak ilanlarınızı oluşturur

> **İpucu:** İlk başta 3-5 ilanınızı manuel ekleyerek platformu tanıyın. Toplu yüklemeyi sonra kullanabilirsiniz.

---

## 3. İlk AI Değerlemenizi Yapma

1. Portföydeki bir ilanınıza tıklayın
2. İlan detay sayfasında **"AI Değerleme"** butonuna tıklayın
3. Sistem mülk bilgilerini analiz eder (birkaç saniye sürer)
4. Sonuç ekranında şunları göreceksiniz:
   - **Tahmini fiyat** ve güven aralığı
   - Benzer mülk karşılaştırması
   - Bölge ortalaması ile kıyaslama
5. **"PDF Rapor İndir"** ile profesyonel raporu indirin

> **Alternatif:** Sol menüden **"Hızlı Değerleme"** seçerek portföyünüze eklemeden de anlık fiyat tahmini alabilirsiniz. Müşterinizle görüşme sırasında anında fiyat bilgisi vermek için idealdir.

---

## 4. Telegram Bot Bağlama

### Neden Telegram Bot?
- Müşterileriniz size Telegram üzerinden ulaşabilir
- Yeni ilanlarınız otomatik bildirim olarak gönderilir
- Mesai dışında bile talep alabilirsiniz

### Kurulum (2 dakika)
1. Sol menüden **"Ayarlar"** > **"Telegram Entegrasyonu"** na gidin
2. **"Bot Oluştur"** butonuna tıklayın
3. Ekranda gösterilen Telegram linkine tıklayın
4. Telegram'da açılan bot ile **"/start"** komutunu gönderin
5. Platformdaki ekranda onay mesajı görünecek
6. Bağlantı tamamlandı!

### Bot ile Neler Yapabilirsiniz?
- `/fiyat [ilçe] [m²]` — Anlık fiyat tahmini
- `/ilanlar` — Aktif ilanlarınızı listeleyin
- `/bildirim açık/kapalı` — Bildirim tercihlerinizi yönetin
- Müşterilerinizden gelen mesajları CRM'e otomatik kaydedin

---

## Hızlı Başlangıç Kontrol Listesi

- [ ] Hesap oluşturuldu ve doğrulandı
- [ ] İlk giriş yapıldı
- [ ] En az 1 ilan eklendi
- [ ] İlk AI değerleme çalıştırıldı
- [ ] PDF rapor indirildi
- [ ] Telegram bot bağlandı (opsiyonel)

Bu adımları tamamladığınızda platformu aktif olarak kullanmaya hazırsınız!

---

## Sık Sorulan Sorular (SSS)

### 1. Platformu kullanmak için teknik bilgi gerekiyor mu?
Hayır. Platform, teknik bilgi gerektirmeyecek şekilde tasarlandı. İnternet tarayıcısı kullanan herkes rahatlıkla kullanabilir. Ayrıca bire bir onboarding desteği sunuyoruz.

### 2. AI fiyat tahmini ne kadar doğru?
Yapay zeka modelimiz İstanbul genelinde ortalama **%90 doğruluk** (hata payı %9.94) ile çalışmaktadır. Bu oran, sektördeki manuel tahminlerin çok üzerindedir. Model, sürekli güncellenen piyasa verileri ile eğitilmektedir.

### 3. Hangi bölgelerde çalışıyor?
Şu anda **İstanbul'un 38 ilçesinde** aktif olarak çalışmaktadır. Anadolu ve Avrupa Yakası'nın tamamı desteklenmektedir. Yeni şehirler için çalışmalarımız devam etmektedir.

### 4. Mevcut ilanlarımı portala (Emlakjet, Sahibinden) otomatik aktarabilir miyim?
İlk aşamada toplu yükleme (Excel/CSV) ile ilanlarınızı hızlıca aktarabilirsiniz. Portal entegrasyonları yol haritamızda yer almaktadır.

### 5. Verilerim güvende mi?
Evet. Tüm veriler şifreli olarak saklanmaktadır. Verileriniz üçüncü taraflarla paylaşılmaz. KVKK uyumlu altyapı kullanıyoruz.

### 6. Starter (ücretsiz) planda ne kadar süre kalabilirim?
Süre sınırı yoktur. Starter plan kalıcı olarak ücretsizdir. İhtiyaçlarınız büyüdükçe Pro veya Elite plana geçebilirsiniz.

### 7. Pro plandan memnun kalmazsam?
3 aylık ücretsiz deneme süresinde herhangi bir taahhüt yoktur. İstediğiniz zaman Starter plana dönebilir veya hesabınızı kapatabilirsiniz.

### 8. Telegram botu müşterilerim de kullanabilir mi?
Evet. Müşterileriniz bot üzerinden size mesaj gönderebilir, ilanlarınızı görüntüleyebilir ve talep bırakabilir. Gelen talepler CRM'inize otomatik kaydedilir.

### 9. Birden fazla kişi aynı hesabı kullanabilir mi?
Pro planda 1 kullanıcı, Elite planda ise birden fazla kullanıcı (danışman) aynı ofis hesabı altında çalışabilir. Her danışmanın kendi giriş bilgileri olur.

### 10. Destek almam gerekirse kime ulaşabilirim?
- **Starter plan:** E-posta desteği (48 saat içinde yanıt)
- **Pro plan:** Öncelikli e-posta desteği (24 saat içinde yanıt)
- **Elite plan:** Telefon + e-posta desteği (aynı gün yanıt)
- İlk 30 ofise özel: Bire bir onboarding desteği dahil

---

## Yardıma mı İhtiyacınız Var?

Herhangi bir sorunuz olursa bize ulaşın:
- E-posta: [destek@emlakteknoloji.com]
- Telefon: [0216 XXX XX XX]
- Telegram: [@emlakteknoloji_destek]

> Platformumuzu seçtiğiniz için teşekkür ederiz. Birlikte daha verimli bir emlak deneyimi oluşturalım!

---

*Emlak Teknoloji Platformu — Onboarding Rehberi v1.0*

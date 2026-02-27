# Telegram Bot Rehberi

Emlak Teknoloji Platformu'nun Telegram botu, gayrimenkul islerini cebinden yonetmeni saglar. Degerleme yap, ilan olustur, musteri ekle, kredi hesapla — hepsi tek bir sohbet penceresinden.

---

## 1. Bota Baslarken

### Botu Bul ve Baslat

1. Telegram'da arama cubuguna **@EmlakTechBot** yaz (veya web panelden gelen linke tikla).
2. **Basla** butonuna tikla veya `/start` yaz.
3. Bot seni karsilama mesajiyla karsilar ve kullanilabilir komutlari listeler.

### Hesabini Bagla

Bot'un tum ozelliklerini kullanabilmek icin web platformdaki hesabinla eslesme yapman gerekiyor:

1. Web panelde **Ayarlar → Telegram Bagla** butonuna tikla.
2. Sana ozel bir baglanti linki olusturulacak (deep link).
3. Bu linke tikladiginda Telegram acilir ve otomatik olarak `/start <token>` komutu gonderilir.
4. Basarili olursa: **"✅ Hesabiniz basariyla baglandi!"** mesajini gorursun.
5. Token gecersiz veya suresi dolmussa: **"❌ Baglanti kodu gecersiz veya suresi dolmus."** uyarisi alirsin. Bu durumda web panelden yeni link olustur.

> **Not:** Hesap baglamadan `/musteri`, `/portfoy`, `/rapor`, `/fotograf` ve `/ilan` komutlarini kullanamazsin.

---

## 2. Komutlar

Telegram'da `/` yazdiginda tum komutlar otomatik olarak menu seklinde acilir. Iste tam liste:

### `/start` — Karsilama

Botu baslat veya hesap bagla.

```
/start
/start abc123token
```

- Parametresiz: Karsilama mesaji + komut listesi
- Token ile: Hesap baglama (web panelden gelen deep link)

---

### `/help` ve `/yardim` — Yardim

Tum komutlarin listesini ve ornek kullanimlari gorursun.

```
/help
```

Cikti: Komut listesi, ornek kullanim formatlari ve ipuclari.

---

### `/degerleme` — AI Konut Degerleme

Yapay zeka modeliyle anlik konut degerleme yap. 5 parametre gerekli, virgul ile ayir:

**Format:** `/degerleme <ilce>, <m2>, <oda>, <kat>, <bina_yasi>`

```
/degerleme Kadikoy, 120, 3+1, 5, 10
/degerleme Besiktas, 85, 2+1, 3, 0
/degerleme Uskudar, 200, 4+1, 12, 2
```

**Parametreler:**

| Parametre | Aciklama | Ornek |
|-----------|----------|-------|
| Ilce | Istanbul ilce adi | Kadikoy, Besiktas |
| m2 | Net metrekare | 120 |
| Oda | Oda sayisi | 3+1, 2+1, 1+0 |
| Kat | Bulundugu kat | 5 |
| Bina Yasi | Yil olarak | 10 |

**Ornek cikti:**

```
🏠 Degerleme Sonucu

Ilce: Kadikoy
Alan: 120 m² | Oda: 3+1
Kat: 5 | Bina Yasi: 10

💰 Tahmini Deger: 4.200.000 - 5.100.000 TL
📊 Ortalama: 4.650.000 TL
🎯 Guven: %82

ℹ️ Bu tahmin AI modeline dayali yaklasik bir degerdir.
```

> **Ipucu:** Eksik parametre girersen bot sana kullanim rehberini gosterir.

---

### `/ilan` — Ilan Olusturma Wizard'i (6 Adim)

Adim adim ilan taslagi olustur. Detayli akis icin [Bolum 3'e](#3-ilan-wizard-adim-adim) bak.

```
/ilan
```

---

### `/portfoy` — Portfoy Listesi

Ofisindeki son 5 ilani goruntule.

```
/portfoy
```

> **Gereklilik:** Hesap bagli olmali.

---

### `/rapor` — Degerleme Raporu (PDF)

Son yaptigin degerlemenin PDF raporunu al.

```
/rapor
```

- Henuz degerleme yapmadiysan: **"📊 Henuz bir degerleme yapmadiniz."** mesaji alirsin.
- Once `/degerleme` ile en az bir analiz yap.

> **Gereklilik:** Hesap bagli olmali.

---

### `/musteri` — Hizli Musteri Kaydi

Telegram'dan direkt musteri kaydi olustur.

**Format:** `/musteri <ad>, <telefon>[, <tip>[, <butce_min>, <butce_max>]]`

```
/musteri Ahmet Yilmaz, 05321234567
/musteri Ahmet Yilmaz, 05321234567, a
/musteri Ahmet Yilmaz, 05321234567, a, 1000000, 3000000
/musteri Mehmet Kaya, 05559876543, k, 5000, 10000
```

**Tip kisaltmalari:**

| Kisaltma | Anlami |
|----------|--------|
| `a` | Alici (buyer) — *varsayilan* |
| `s` | Satici (seller) |
| `k` | Kiraci (renter) |
| `e` | Ev Sahibi (landlord) |

- Ad + telefon **zorunlu**, diger alanlar opsiyonel.
- Tip belirtmezsen varsayilan olarak **Alici** atanir.

> **Gereklilik:** Hesap bagli olmali. Plan limitin dolduysa uyari alirsin.

---

### `/fotograf` — Virtual Staging (Sanal Mobilyalama)

Bos oda fotografini yapay zeka ile mobilyali hale getir. Detayli bilgi icin [Bolum 4'e](#4-virtual-staging-tarzlari) bak.

```
/fotograf
```

1. Komutu gonder → Bot senden fotograf ister.
2. Bos oda fotografini gonder.
3. Bot odayi analiz eder ve oda tipini belirler (salon, yatak odasi, mutfak vb.).
4. 6 farkli tarz arasinden sec.
5. 15-30 saniye icinde mobilyali versiyon hazir!

> **Gereklilik:** Hesap bagli olmali. Sahneleme kotasi aktif olmali.

---

### `/kredi` — Konut Kredisi Hesaplama

Hizli kredi hesaplamasi yap.

**Format:** `/kredi <tutar> <vade_ay> <pesinat_yuzde>`

```
/kredi 2500000 180 30
/kredi 2.5m 15y 30
/kredi 500k 60 20
```

**Kisaltmalar:**

| Kisaltma | Anlami | Ornek |
|----------|--------|-------|
| `m` | Milyon | 2.5m = 2.500.000 |
| `k` | Bin | 500k = 500.000 |
| `y` | Yil | 15y = 180 ay |

**Limitler:**
- Tutar: 100.000 - 50.000.000 TL
- Vade: 12 - 360 ay
- Pesinat: %10 - %90

---

### `/iptal` — Wizard'i Iptal Et

Aktif bir ilan olusturma wizard'in varsa iptal et.

```
/iptal
```

- Aktif wizard yoksa: **"ℹ️ Aktif bir ilan olusturma islemi bulunmuyor."**
- Varsa: Wizard iptal edilir ve **"🗑️ Ilan olusturma islemi iptal edildi."** mesaji gelir.

---

## 3. Ilan Wizard Adim Adim

`/ilan` komutunu gonderdiginde 6 adimli bir sihirbaz baslar:

### Adim 1: Baslangic
- `/ilan` yaz.
- Bot: **"📸 Ilan olusturma wizard'ina hosgeldiniz! Oncelikle emlak fotografini gonderin."**
- Zaten aktif wizard varsa: **"⚠️ Zaten aktif bir ilan olusturma isleminiz var."** Devam et veya `/iptal` ile iptal et.

### Adim 2: Fotograf
- Emlakin fotografini gonder (dogrudan fotograf mesaji).
- Bot fotografi alir ve: **"✅ Fotograf alindi! Simdi emlagin konumunu gonderin 📍"**

### Adim 3: Konum
- Telegram'in konum paylasma ozelligini kullan **veya** ilce adini yaz.
- Ornek: `Kadikoy` veya `Besiktas`
- Istanbul'un 39 ilcesinden biri olmali. Taninmayan bir ilce yazarsan fuzzy-match ile eslestirmeye calisir.
- Hata: **"❌ Ilce adi taninmadi. Lutfen Istanbul'daki 39 ilceden birini yazin."**

### Adim 4: Emlak Detaylari
- Bot sorar: **"🏠 Emlak bilgilerini girin: Alan (m²), Oda sayisi, Bina yasi, Kat"**
- Format: `120 3+1 5 3`

| Alan | Deger Araligi |
|------|---------------|
| m² | 10 - 1000 |
| Oda | 1+0 — 10+2 |
| Bina Yasi | 0 - 100 |
| Kat | 0 - 50 |

- Hatali giris: 3 deneme hakkin var. 3. denemeden sonra wizard otomatik iptal olur.

### Adim 5: Onay
- Bot, yapay zeka ile ilan metni uretir (10-20 saniye surer).
- Olusturulan taslak sana gosterilir.
- Inline butonlarla sec:
  - **Onayla** → Ilan kaydedilir
  - **Yeniden Olustur** → Metin tekrar uretilir
  - **Iptal** → Wizard sonlandirilir

### Adim 6: Tamamlama
- Ilan basariyla kaydedilir ve onay mesaji alirsin.

> **Onemli:** Wizard 30 dakika aktif kalir. Bu sure icinde tamamlamazsan otomatik olarak sona erer.

> **Ipucu:** Herhangi bir adimda `/iptal` yazarak wizard'i sonlandirabilirsin.

---

## 4. Virtual Staging Tarzlari

`/fotograf` komutuyla sanal mobilyalama yaptiginda 6 farkli tarz secenegi sunulur:

| Tarz | Emoji | Aciklama |
|------|-------|----------|
| **Modern** | 🏢 | Sade cizgiler, notr tonlar, minimal mobilya |
| **Klasik** | 🏛️ | Geleneksel desen ve dokular, sicak renkler |
| **Minimalist** | ⬜ | En az mobilya, genis acik alanlar, beyaz tonlar |
| **Skandinav** | 🌿 | Dogal ahsap, acik tonlar, bitki aksesuarlari |
| **Bohem** | 🎨 | Renkli desenler, etnik dokular, eklektik parcalar |
| **Endustriyel** | 🔧 | Acik tugla, metal aksanlar, ham dokular |

**Desteklenen oda tipleri:**

- Salon
- Yatak Odasi
- Mutfak
- Banyo
- Cocuk Odasi
- Calisma Odasi
- Yemek Odasi
- Antre

**Akis:**
1. `/fotograf` yaz → Bot fotograf ister.
2. Bos oda fotografini gonder.
3. Yapay zeka odanin bos olup olmadigini kontrol eder.
   - Bos degilse: **"⚠️ Bu oda bos gorunmuyor."** uyarisi alirsin.
4. Oda tipi otomatik tespit edilir (orn: "Salon").
5. 6 tarz butonu gosterilir — birine tikla.
6. 15-30 saniye icinde mobilyali fotograf hazir!

> **Not:** Gonderdigin fotograf 5 dakika gecerlidir. Sure dolarsa yeni fotograf gondermen gerekir.

---

## 5. Kota Bilgisi

Bazi ozellikler plan bazli kota sinirlamasi icerir:

| Ozellik | Kota Asimi Mesaji |
|---------|-------------------|
| Musteri kaydi | "⚠️ Musteri kotaniz doldu." |
| Virtual staging | "⚠️ Sahneleme kotaniz doldu." |
| Ilan olusturma | "⚠️ Aylik ilan olusturma limitinize ulastiniz." |

Kota dolmus mesaji alirsan:
- Mevcut planindaki limiti kontrol et.
- Daha fazla kullanim icin planini yukselterek limitleri arttirabilirsin.
- Detayli bilgi icin web paneldeki **Ayarlar** sayfasina goz at.

---

## 6. Sikca Sorulan Sorular (SSS)

### S1: Botu nasil bulurum?
Telegram'da **@EmlakTechBot** arat veya web panelden **Ayarlar → Telegram Bagla** uzerinden linke tikla.

### S2: Hesap baglamadan hangi komutlari kullanabilirim?
`/start`, `/help`, `/degerleme` ve `/kredi` komutlarini hesap baglamadan kullanabilirsin. Diger komutlar icin hesap baglaman gerekir.

### S3: Deep link suresi ne kadar?
Baglanti tokenleri belirli bir sure gecerlidir. Suresi dolan bir token kullanirsan **"❌ Baglanti kodu gecersiz veya suresi dolmus."** mesaji alirsin. Web panelden yeni link olusturabilirsin.

### S4: Degerleme ne kadar dogru?
AI modelimiz Istanbul genelinde ~%90 dogruluk oranina sahip (MAPE: ~%10). Ilce bazinda dogruluk degiskenlik gosterebilir. Sonuclar yaklasik deger olup kesin fiyat garantisi degildir.

### S5: Ilan wizard'i yarim kalirsa ne olur?
Wizard 30 dakika boyunca aktif kalir. Bu sure icinde tamamlamazsan otomatik olarak sona erer. Kaldigin yerden devam edemezsin; `/ilan` ile yeni bir wizard baslatman gerekir.

### S6: Virtual staging icin nasil fotograf cekmeliyim?
- Oda tamamen bos veya mobilyasiz olmali.
- Iyi aydinlatma, genis aci tercih et.
- Net ve bulanik olmayan bir fotograf gonder.
- Oda bos degilse bot **"Bu oda bos gorunmuyor"** uyarisi verir.

### S7: Kredi hesaplamada hangi faiz oranini kullaniyor?
Bot, guncel piyasa faiz oranlarini baz alir. Farkli bankalarin karsilastirmasi icin web paneldeki **Kredi Hesaplayici** sayfasini kullanabilirsin.

### S8: Birden fazla musteri nasil eklerim?
Her musteri icin ayri `/musteri` komutu gonder. Toplu ekleme icin web paneli kullanabilirsin.

### S9: Hata mesajinda "Referans" kodu ne anlama gelir?
Hata mesajlarinin altindaki referans kodu, destek ekibinin sorununu hizla bulmasini saglar. Destek talebi olusturuyorsan bu kodu paylas.

### S10: Botu grup sohbetine ekleyebilir miyim?
Bot su an icin yalnizca birebir sohbette calisacak sekilde tasarlanmistir. Grup destegi mevcut degildir.

---

## Hizli Basvuru Tablosu

| Komut | Aciklama | Hesap Gerekli? |
|-------|----------|----------------|
| `/start` | Karsilama + hesap baglama | Hayir |
| `/help` | Yardim mesaji | Hayir |
| `/degerleme` | AI konut degerleme | Hayir |
| `/musteri` | Hizli musteri kaydi | Evet |
| `/fotograf` | Sanal mobilyalama | Evet |
| `/kredi` | Kredi hesaplama | Hayir |
| `/ilan` | Ilan olusturma wizard'i | Evet |
| `/portfoy` | Portfoy listesi (son 5) | Evet |
| `/rapor` | Son degerleme raporu (PDF) | Evet |
| `/iptal` | Aktif wizard'i iptal et | Hayir |

---

> Sorularin mi var? Web panelden destek talebi olusturabilir veya `/help` komutuyla yardim alabilirsin.

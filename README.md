# AquaReef Aquarium Lighting - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/bullkerem/ha-aquareef?color=blue)](https://github.com/bullkerem/ha-aquareef/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Home Assistant custom component for local control and monitoring of **AquaReef** smart aquarium LED fixtures (including **AquaReef PRO 4**, PRO 2, PRO 3, F Series, and High-Flying HF-LPT170 based controllers).

Works **100% locally** across your local Wi-Fi network without any cloud dependence!

---

## 🌟 Features / Özellikler

- **Yerel ve Hızlı Kontrol (100% Local):** Buluta ihtiyaç duymadan doğrudan yerel ağ üzerinden (TCP Port 8899 ve HTTP API) haberleşir.
- **Ana Armatür Kontrolü (Master Fixture):** Açma, kapatma, genel parlaklık (dimmer) kontrolü.
- **6 Bağımsız Spektrum Kanalı (Individual Channels):**
  - 🟣 **Kanal 1:** UV / Mor (395-420nm)
  - 🌊 **Kanal 2:** Royal Blue (450nm)
  - 🔷 **Kanal 3:** Blue (470nm)
  - ☀️ **Kanal 4:** White (Beyaz)
  - 🔴 **Kanal 5:** Red (Kırmızı 660nm)
  - 🟢 **Kanal 6:** Green (Yeşil / Cyan 520nm)
- **Çalışma Modları / Hazır Efektler:**
  - `Manuel`
  - `Gün Simülasyonu`
  - `Ay Işığı / Gece`
  - `Bulut Efekti`
  - `Fırtına & Şimşek`
  - `Mercan Alıştırma (Aklimatizasyon)`
- **Tanılama ve Durum Sensörleri:**
  - Wi-Fi Sinyal Gücü (% ve dBm)
  - IP ve MAC Adresi
  - Bağlı Wi-Fi Ağı (SSID)
  - Cihaz AP Adı (Örn: `AquaReefPRO4:424`)
  - Firmware ve Wi-Fi Modül Sürümü (`HF-LPT170 V1.00`)
  - TCP Soket Durumu (Aktif / Port 8899 Dinliyor)
- **Uzaktan Yönetim Butonları:**
  - Cihazı Yeniden Başlat (Reboot) butonu
  - Verileri Hemen Yenile (Refresh) butonu
- **Özel Servisler (Services):**
  - `aquareef.set_channels`: Tüm kanalları tek çağrıda istenen yüzdelere ayarlama.
  - `aquareef.send_raw_command`: Port 8899 üzerinden doğrudan HEX veya ASCII komut iletme.
  - `aquareef.reboot`: Cihazı güvenli yeniden başlatma.

---

## 📦 Kurulum (Installation)

### Yöntem 1: HACS ile Kurulum (Önerilen)
1. Home Assistant'ta **HACS** > **Integrations** bölümüne gidin.
2. Sağ üstteki üç noktaya tıklayıp **Custom repositories** (Özel depolar) seçeneğini açın.
3. Depo adresine `https://github.com/bullkerem/ha-aquareef` yazın, kategori olarak **Integration** seçip **Add** butonuna basın.
4. Listeye gelen **AquaReef Aquarium Lighting** entegrasyonunu seçip **Download** (İndir) butonuna tıklayın.
5. Home Assistant'ı yeniden başlatın.

### Yöntem 2: Manuel Kurulum
1. Bu depoyu indirin (ZIP olarak).
2. `custom_components/aquareef` klasörünü Home Assistant kurulumunuzdaki `config/custom_components/` dizinine kopyalayın.
3. Home Assistant'ı yeniden başlatın.

---

## ⚙️ Yapılandırma (Configuration)

1. Home Assistant arayüzünde **Ayarlar** > **Cihazlar ve Hizmetler** > **Entegrasyon Ekle** butonuna tıklayın.
2. Listeden **AquaReef Akvaryum Aydınlatması** arayın ve seçin.
3. Çıkan ekranda bilgileri girin:
   - **IP Adresi:** `192.168.8.90` (veya cihazınızın ağdaki IP'si)
   - **TCP Portu:** `8899`
   - **HTTP Yönetim Portu:** `80`
   - **Kullanıcı Adı:** `admin`
   - **Şifre:** `admin`
4. **Gönder** butonuna tıklayın. Tüm ışıklar, sensörler ve butonlar otomatik olarak oluşturulacaktır.

---

## 💡 Otomasyon Örnekleri (Automations)

### Örnek 1: Akşam Ay Işığı Moduna Geçiş
```yaml
alias: "Akvaryum Gece Modu"
trigger:
  - platform: time
    at: "22:00:00"
action:
  - service: select.select_option
    target:
      entity_id: select.aquareef_pro_4_calisma_modu_efekt
    data:
      option: "Ay Işığı / Gece"
```

### Örnek 2: Özel Spektrum Ayarlama (Servis ile)
```yaml
service: aquareef.set_channels
data:
  uv: 20
  royal_blue: 80
  blue: 60
  white: 15
  red: 5
  green: 5
```

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.


# 🐠 AquaReef PRO 4 Akvaryum Aydınlatması — Home Assistant Entegrasyonu (v2.1)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/bullkerem/ha-aquareef?color=blue)](https://github.com/bullkerem/ha-aquareef/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AquaReef** akıllı akvaryum LED armatürlerinin (**AquaReef PRO 4**, PRO 3, PRO 2, F Serisi ve High-Flying `HF-LPT170` tabanlı kontrolcüler) Home Assistant üzerinden **%100 yerel (local)** olarak kontrol edilmesi, **24 Saat Gün Simülasyonu**, **4 Zaman Dilimli Manuel Saat Programı** ve **9 Kanal Spektrum Kontrolü** için geliştirilmiş özel entegrasyondur.

Bulut bağlantısına ihtiyaç duymadan doğrudan yerel Wi-Fi ağınız üzerinden (`TCP Port 8899` ve `HTTP Port 80`) çalışır.

---

## 🌟 v2.1 Yenilikleri ve Özellikler

### 1. 🔇 Orijinal PRO 4 12-Bit PWM (`×40`) TCP Protokolü & %100 Kararlı Manuel / Ay Işığı Kontrolü
- **Sürekli Bip Sesi Sorunu Giderildi:** Armatür üzerindeki piezo buzzer'ın her 60 saniyede bir ötmesine ve manuel moddan çıkmasına yol açan periyodik `0x43` (`'C'`) TCP yoklaması kaldırıldı.
- **Orijinal `Pro4DataAdapter` 12-Bit PWM Kodlaması (`0..4000`):** AquaReef PRO 4 donanımındaki 9 kanalın her biri `%0–%100` seviyesinden `val * 40` (`0..4000` PWM adımı) olarak hesaplanıp `((val * 40) // 256, (val * 40) % 256)` şeklinde `20-byte 'm'` (`0x6D`) paketiyle doğrudan gönderilir. Böylece **🌙 Ay Işığı**, **🎛️ Manuel Işık** ve tüm tekil kanal sürgüleri anında gerçek parlaklığında yanar.

### 2. 🌅 Ayarlanabilir Gün Simülasyonu (Saat Ayarları + 4 Hazır Seçenek)
- **Saat Kaçta Çalışsın / Kaçta Kapansın Ayarı:**
  - **Başlangıç Saati (Gün Doğumu):** `06:00` – `12:00` arası (30 dk adımlarla)
  - **Kapanış Saati (Gün Batımı Sonu):** `17:00` – `23:30` arası
  - **Gece Ay Işığı Bitiş Saati (Tam Kapanış):** `Kapalı (Hemen Sönsün)`, `21:00` – `02:00` arası veya `Sabaha Kadar Açık`
  - **Gün Doğumu/Batımı Geçiş Süresi:** `15` – `180` dakika yumuşak rampa geçişi
  - **Gece Ay Işığı Seviyesi:** `%0` – `%30` arası ayarlanabilir gece loşluğu
- **Hazır 4 Gün Simülasyonu Seçeneği (Tek Dokunuşla Seçim):**
  1. 🌊 **`1. Karışık Resif (Mixed Reef)`:** LPS ve yumuşak mercanlar için dengeli resif spektrumu
  2. 🪸 **`2. SPS Mercan (Yüksek PAR)`:** Yoğun Royal Blue, Mavi, UV, Mor ve Beyaz ile yüksek PAR
  3. 🟣 **`3. LPS & Floresan (Derin Mavi & UV)`:** Derin mavi, UV ve menekşe ağırlıklı maksimum floresan parlama
  4. ☀️ **`4. Doğal Gün Işığı (Sıcak & Berrak)`:** Doğal beyaz, nane, turkuaz ve sıcak gün doğumu/batımı tonları

### 3. ⏰ Hangi Saat Hangi Işık Yansın (4 Zaman Dilimli Manuel Saat Programı)
- **Manuel Saat Programı (`switch.akvaryum_kontrolu_manuel_saat_programi`):** Gün Simülasyonu yerine kendi belirlediğiniz saat aralıklarında istediğiniz ışık kombinasyonunun yanmasını sağlar:
  - **1. Dilim (Sabah):** Saat aralığı + Yanan ışık kombinasyonu + Parlaklık (`%0–%100`)
  - **2. Dilim (Öğle):** Saat aralığı + Yanan ışık kombinasyonu + Parlaklık (`%0–%100`)
  - **3. Dilim (Akşam):** Saat aralığı + Yanan ışık kombinasyonu + Parlaklık (`%0–%100`)
  - **4. Dilim (Gece):** Saat aralığı + Yanan ışık kombinasyonu + Parlaklık (`%0–%100`)
- **Her Dilim İçin Seçilebilir 10 Işık Kombinasyonu:**
  - `☀️ Tam Spektrum Gün Ortası (Tüm Işıklar Dengeli)`
  - `🌊 Yoğun Mavi & Royal Blue (Mercan & Derin Deniz)`
  - `🟣 Floresan Mor & Mavi (UV + Menekşe + Royal)`
  - `🌅 Gün Doğumu (Mavi + Hafif Beyaz & Kırmızı)`
  - `🌇 Gün Batımı (Loş Mavi + Mor + Kırmızı)`
  - `⚪ Sadece Beyaz & Gün Işığı (Temizlik / İzleme)`
  - `🌿 Bitkili / Yeşil & Kırmızı (Tatlı Su & Refugium)`
  - `🌙 Gece Ay Işığı (Loş Royal Blue & Menekşe)`
  - `🎨 Özel Kanal Ayarlarım (Kaydedilen Spektrum)`
  - `🌑 Kapalı (Işıklar Sönük)`

### 4. 🎚️ 9 Bağımsız Spektrum Kanalı (`light` ve `%0–%100` `number` Kaydırıcıları)
AquaReef PRO 4'ün donanımsal 9 PWM kanalı hem `light` hem de doğrudan `%0–%100` sayısal kaydırıcı (`number`) olarak kontrol edilebilir:
1. 🔴 **Kanal 0 — Kırmızı (Red 660nm)**
2. 🟢 **Kanal 1 — Amber / Yeşil (Green 520nm)**
3. 🌊 **Kanal 2 — Royal Blue (450nm)**
4. 🔷 **Kanal 3 — Mavi (Blue 470nm)**
5. ☀️ **Kanal 4 — Beyaz (Cold/Natural White)**
6. 🟣 **Kanal 5 — UV Mor (395–420nm)**
7. 🧪 **Kanal 6 — Nane (Mint)**
8. 💎 **Kanal 7 — Turkuaz (Cyan)**
9. 🔮 **Kanal 8 — Menekşe (Violet)**

> **💡 Özel Spektrum Kaydetme:** 9 kanal kaydırıcısıyla istediğiniz renk karışımını ayarladıktan sonra **"Özel Spektrum Olarak Kaydet"** (`button.akvaryum_kontrolu_ozel_spektrum_olarak_kaydet`) butonuna basarak bu karışımı kaydedebilir ve saat dilimlerinde `🎨 Özel Kanal Ayarlarım` olarak kullanabilirsiniz.

---

## 📦 Kurulum (Installation)

### Yöntem 1: HACS ile Kurulum (Önerilen)
1. Home Assistant'ta **HACS** > **Integrations** bölümüne gidin.
2. Sağ üstteki üç noktaya tıklayıp **Custom repositories** (Özel depolar) seçeneğini açın.
3. Depo adresine `https://github.com/bullkerem/ha-aquareef` yazın, kategori olarak **Integration** seçip **Add** butonuna basın.
4. Listeye gelen **AquaReef Aquarium Lighting** entegrasyonunu seçip **Download** (İndir) butonuna tıklayın.
5. Home Assistant'ı yeniden başlatın.

### Yöntem 2: Manuel Kurulum
1. Bu depodaki `custom_components/aquareef` klasörünü Home Assistant kurulumunuzdaki `config/custom_components/aquareef` dizinine kopyalayın.
2. Home Assistant'ı yeniden başlatın.

---

## ⚙️ Yapılandırma (Configuration)

1. Home Assistant arayüzünde **Ayarlar** > **Cihazlar ve Hizmetler** > **Entegrasyon Ekle** butonuna tıklayın.
2. **AquaReef Akvaryum Aydınlatması** arayın ve seçin.
3. Cihaz bilgilerini girin:
   - **IP Adresi:** `192.168.8.90` (veya armatürünüzün yerel IP adresi)
   - **TCP Portu:** `8899`
   - **HTTP Yönetim Portu:** `80`
   - **Kullanıcı Adı:** `admin`
   - **Şifre:** `admin`
4. Tüm ayarlarınız (seçilen Gün Simülasyonu profili, başlangıç/kapanış saatleri, 4 saat dilimi programı ve kaydedilen özel spektrum) Home Assistant `.storage/aquareef_settings_<IP>` dosyasında kalıcı olarak saklanır; yeniden başlatmalarda kaybolmaz.

---

## 🖥️ Lovelace Dashboard Ayar Bilgileri (Kart & Geniş Popup Kurulumu)

Akvaryum kartı ve detaylı ayar penceresi (Popup) için aşağıdaki HACS ön yüz (Frontend) bileşenlerinin kurulu olması gerekir:

### 1. Gerekli HACS Kart Eklentileri
| Eklenti | Açıklama |
| :--- | :--- |
| **`button-card`** (`custom:button-card`) | Ana kart başlığı, 4 hazır simülasyon profili butonları ve canlı 9 kanal spektrum rozetleri için |
| **`vertical-stack-in-card`** (`custom:vertical-stack-in-card`) | Kart bileşenlerini tek bir çerçeve içinde gruplamak için |
| **`card-mod`** | Kart kenarlıkları, gölgeler ve modern görünüm stilleri için |
| **`browser_mod`** | **⚙️ Saat, Simülasyon & Manuel Işık Ayarları ↗** butonuna basıldığında açılan geniş ayar penceresi (`browser_mod.popup`) için |

---

### 2. Oluşturulan Varlıklar (Entity ID Referans Tablosu)

> **Not:** Cihaz adı `Akvaryum Kontrolü` olarak adlandırıldığında yeni oluşturulan simülasyon, saat dilimi ve seviye varlıkları `akvaryum_kontrolu_*` ön ekini alır.

#### 💡 Ana Aydınlatma ve Mod Anahtarları
| Entity ID | Tür | Görev |
| :--- | :--- | :--- |
| `light.aquareef_pro_4_ana_aydinlatma_master` | `light` | Ana Armatür Aç/Kapat ve Genel Parlaklık (`%0–%100`) |
| `switch.aquareef_pro_4_gun_simulasyonu` | `switch` | Otomatik 24 Saat Gün Simülasyonu Aç/Kapat |
| `switch.akvaryum_kontrolu_manuel_saat_programi` | `switch` | 4 Zaman Dilimli Manuel Saat Programı Aç/Kapat |
| `switch.aquareef_pro_4_bulut_efekti` | `switch` | Dinamik Bulut Geçiş Efekti |
| `switch.aquareef_pro_4_firtina_simsek_efekti` | `switch` | Fırtına & Şimşek Efekti |
| `select.aquareef_pro_4_calisma_modu_efekt` | `select` | Çalışma Modu / Hazır Efekt Seçimi |
| `sensor.aquareef_pro_4_gun_simulasyonu_fazi` | `sensor` | Anlık Faz (`🌅 Gün Doğumu`, `☀️ Gün Ortası`, `🌇 Gün Batımı`, `🌙 Gece / Ay Işığı`, `⏰ 1. Dilim` vb.) |
| `sensor.aquareef_pro_4_aktif_efekt_profil` | `sensor` | Aktif Çalışma Modu ve Detay Öznitelikleri |

#### 🌅 Gün Simülasyonu Seçenekleri ve Saat Ayarları
| Entity ID | Tür | Görev |
| :--- | :--- | :--- |
| `select.akvaryum_kontrolu_gun_simulasyonu_profili` | `select` | Hazır 4 Simülasyon Profilinden Birini Seçme |
| `button.akvaryum_kontrolu_simulasyon_secenek_1_karisik_resif` | `button` | Tek Dokunuşla **1. Karışık Resif** Simülasyonunu Başlat |
| `button.akvaryum_kontrolu_simulasyon_secenek_2_sps_mercan` | `button` | Tek Dokunuşla **2. SPS Mercan** Simülasyonunu Başlat |
| `button.akvaryum_kontrolu_simulasyon_secenek_3_lps_floresan` | `button` | Tek Dokunuşla **3. LPS & Floresan** Simülasyonunu Başlat |
| `button.akvaryum_kontrolu_simulasyon_secenek_4_dogal_gun_isigi` | `button` | Tek Dokunuşla **4. Doğal Gün Işığı** Simülasyonunu Başlat |
| `select.akvaryum_kontrolu_gun_simulasyonu_baslangic_saati` | `select` | Gün Simülasyonu Başlangıç Saati (`06:00` – `12:00`) |
| `select.akvaryum_kontrolu_gun_simulasyonu_kapanis_saati` | `select` | Gün Simülasyonu Kapanış Saati (`17:00` – `23:30`) |
| `select.akvaryum_kontrolu_gece_ay_isigi_bitis_saati` | `select` | Gece Ay Işığı Tam Kapanış Saati (`Kapalı`, `21:00–02:00`, `Sabaha Kadar Açık`) |
| `number.akvaryum_kontrolu_gun_dogumu_batimi_gecis_suresi` | `number` | Gün Doğumu / Batımı Yumuşak Geçiş Süresi (`15–180 dk`) |
| `number.akvaryum_kontrolu_gece_ay_isigi_seviyesi` | `number` | Gece Ay Işığı Parlaklık Seviyesi (`%0–%30`) |

#### ⏰ 4 Zaman Dilimli Manuel Saat Programı ("Hangi Saat Hangi Işık Yansın")
| Dilim | Saat Aralığı (`select`) | Yanan Işık (`select`) | Parlaklık (`number`) |
| :--- | :--- | :--- | :--- |
| **1. Dilim (Sabah)** | `select.akvaryum_kontrolu_1_dilim_sabah_saat_araligi` | `select.akvaryum_kontrolu_1_dilim_sabah_yanan_isik` | `number.akvaryum_kontrolu_1_dilim_sabah_parlakligi` |
| **2. Dilim (Öğle)** | `select.akvaryum_kontrolu_2_dilim_ogle_saat_araligi` | `select.akvaryum_kontrolu_2_dilim_ogle_yanan_isik` | `number.akvaryum_kontrolu_2_dilim_ogle_parlakligi` |
| **3. Dilim (Akşam)** | `select.akvaryum_kontrolu_3_dilim_aksam_saat_araligi` | `select.akvaryum_kontrolu_3_dilim_aksam_yanan_isik` | `number.akvaryum_kontrolu_3_dilim_aksam_parlakligi` |
| **4. Dilim (Gece)** | `select.akvaryum_kontrolu_4_dilim_gece_saat_araligi` | `select.akvaryum_kontrolu_4_dilim_gece_yanan_isik` | `number.akvaryum_kontrolu_4_dilim_gece_parlakligi` |

#### 🎚️ 9 Kanal Doğrudan Seviye Kaydırıcıları (`%0–%100`)
| Kanal | Seviye Kaydırıcısı (`number`) | Kanal Işığı (`light`) |
| :--- | :--- | :--- |
| **UV Mor** | `number.akvaryum_kontrolu_seviye_uv_mor` | `light.aquareef_pro_4_kanal_uv_mor` |
| **Royal Blue** | `number.akvaryum_kontrolu_seviye_royal_blue` | `light.aquareef_pro_4_kanal_royal_blue` |
| **Mavi (Blue)** | `number.akvaryum_kontrolu_seviye_mavi_blue` | `light.aquareef_pro_4_kanal_mavi_blue` |
| **Menekşe (Violet)** | `number.akvaryum_kontrolu_seviye_menekse_violet` | `light.aquareef_pro_4_kanal_menekse_violet` |
| **Turkuaz (Cyan)** | `number.akvaryum_kontrolu_seviye_turkuaz_cyan` | `light.aquareef_pro_4_kanal_turkuaz_cyan` |
| **Nane (Mint)** | `number.akvaryum_kontrolu_seviye_nane_mint` | `light.aquareef_pro_4_kanal_nane_mint` |
| **Amber / Yeşil** | `number.akvaryum_kontrolu_seviye_amber_yesil` | `light.aquareef_pro_4_kanal_yesil_green` |
| **Kırmızı (Red)** | `number.akvaryum_kontrolu_seviye_kirmizi_red` | `light.aquareef_pro_4_kanal_kirmizi_red` |
| **Beyaz (White)** | `number.akvaryum_kontrolu_seviye_beyaz_white` | `light.aquareef_pro_4_kanal_beyaz_white` |

---

### 3. 📋 Hazır Lovelace Dashboard Kartı & Popup YAML Kodu

Aşağıdaki YAML kodunu Home Assistant'ta herhangi bir Lovelace panelinize **Manuel Kart (Manual Card)** olarak doğrudan yapıştırabilirsiniz. Tam yapılandırma ayrıca [`examples/lovelace_akvaryum_karti.yaml`](examples/lovelace_akvaryum_karti.yaml) dosyasında yer almaktadır.

```yaml
type: custom:vertical-stack-in-card
card_mod:
  style: |
    ha-card {
      background: #FFFFFF !important;
      border: 1px solid #EAECEF !important;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03) !important;
      border-radius: 16px !important;
      padding: 8px 10px !important;
      box-sizing: border-box !important;
    }
    ha-card > div, #root {
      display: flex !important;
      flex-direction: column !important;
      gap: 7px !important;
    }
cards:
  # 1. Üst Durum Çubuğu + Doğrudan Aç/Kapat
  - type: custom:button-card
    entity: light.aquareef_pro_4_ana_aydinlatma_master
    triggers_update: all
    show_icon: false
    show_name: false
    show_state: false
    tap_action:
      action: call-service
      service: light.toggle
      target:
        entity_id: light.aquareef_pro_4_ana_aydinlatma_master
    styles:
      card:
        - background: transparent
        - border: 0
        - box-shadow: none
        - padding: 0
      grid:
        - grid-template-areas: '"bar"'
        - grid-template-columns: minmax(0, 1fr)
    custom_fields:
      bar: |
        [[[
          const master = states['light.aquareef_pro_4_ana_aydinlatma_master'];
          const isOn = master?.state === 'on';
          const bri = master?.attributes?.brightness ? Math.round((master.attributes.brightness / 255) * 100) : 0;
          const isSim = states['switch.aquareef_pro_4_gun_simulasyonu']?.state === 'on';
          const isSched = states['switch.akvaryum_kontrolu_manuel_saat_programi']?.state === 'on';
          const phase = states['sensor.aquareef_pro_4_gun_simulasyonu_fazi']?.state || 'Manuel';
          const simStart = states['select.akvaryum_kontrolu_gun_simulasyonu_baslangic_saati']?.state || '08:30';
          const simEnd = states['select.akvaryum_kontrolu_gun_simulasyonu_kapanis_saati']?.state || '21:30';
          return `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 10px;border-radius:12px;background:${isOn ? 'linear-gradient(135deg,#F0F9FF 0%,#E0F2FE 100%)' : '#F8FAFC'};border:1.5px solid ${isOn ? '#38BDF8' : '#E2E8F0'};">
              <div>
                <div style="font-size:13px;font-weight:800;color:#0F172A;">🐠 Akvaryum Aydınlatma ${isOn ? '(%' + bri + ')' : '(KAPALI)'}</div>
                <div style="font-size:11px;font-weight:600;color:#0369A1;">${isSim ? '🌅 Simülasyon (' + simStart + ' - ' + simEnd + ') • ' + phase : (isSched ? '⏰ Saat Programı • ' + phase : '🎚️ Manuel Mod')}</div>
              </div>
              <div style="padding:6px 12px;border-radius:9px;background:${isOn ? '#0284C7' : '#E2E8F0'};color:${isOn ? '#FFF' : '#475569'};font-size:11px;font-weight:800;">
                ${isOn ? 'AÇIK • KAPAT' : 'KAPALI • AÇ'}
              </div>
            </div>
          `;
        ]]]

  # 2. Hazır 4 Gün Simülasyonu Seçeneği (Tek Dokunuşla Seçim)
  - type: horizontal-stack
    cards:
      - type: custom:button-card
        entity: select.akvaryum_kontrolu_gun_simulasyonu_profili
        name: "🌊 1. Karışık Resif"
        show_icon: false
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.akvaryum_kontrolu_simulasyon_secenek_1_karisik_resif
      - type: custom:button-card
        entity: select.akvaryum_kontrolu_gun_simulasyonu_profili
        name: "🪸 2. SPS Mercan"
        show_icon: false
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.akvaryum_kontrolu_simulasyon_secenek_2_sps_mercan
      - type: custom:button-card
        entity: select.akvaryum_kontrolu_gun_simulasyonu_profili
        name: "🟣 3. LPS Floresan"
        show_icon: false
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.akvaryum_kontrolu_simulasyon_secenek_3_lps_floresan
      - type: custom:button-card
        entity: select.akvaryum_kontrolu_gun_simulasyonu_profili
        name: "☀️ 4. Doğal Gün"
        show_icon: false
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.akvaryum_kontrolu_simulasyon_secenek_4_dogal_gun_isigi
```

> **Tam Kart + Geniş Popup Kodu:** Canlı 9 kanal yüzdeleri, mod butonları ve `browser_mod.popup` içeren tam sürüm için [`examples/lovelace_akvaryum_karti.yaml`](examples/lovelace_akvaryum_karti.yaml) dosyasını kullanabilirsiniz.

---

## 🛠️ Özel Servisler (Services)

| Servis | Açıklama |
| :--- | :--- |
| `aquareef.set_channels` | 9 spektrum kanalını (`red`, `green`, `royal_blue`, `blue`, `white`, `uv`, `mint`, `cyan`, `violet`) tek çağrıda `%0–%100` arasında ayarlar. |
| `aquareef.set_simulation_config` | Gün Simülasyonu profilini (`profile`), başlangıç saatini (`start_time`), kapanış saatini (`end_time`), ay ışığı bitiş saatini (`moon_end_time`), geçiş süresini (`ramp_minutes`) ve ay ışığı seviyesini (`moonlight_level`) ayarlar. |
| `aquareef.set_schedule_slot` | Manuel Saat Programındaki `1..4` numaralı dilimin saat aralığını (`time_range`), ışık kombinasyonunu (`light_preset`) ve parlaklığını (`brightness`) ayarlar. |
| `aquareef.send_raw_command` | Port 8899 üzerinden doğrudan HEX veya ASCII komut iletir. |
| `aquareef.reboot` | Armatürün Wi-Fi modülünü yeniden başlatır. |

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

# AquaReef PRO 4 — Home Assistant

## 2.1.1 düzeltmeleri

- Manuel kontrole giriş için önceki sürümlerdeki 20 bayt `o` başlığı, gerektiğinde aynı TCP bağlantısında ışık paketinden önce gönderilir.
- 9 kanal, yüzde değerinin 40 ile çarpıldığı 20 bayt `m` paketiyle gönderilir.
- TCP hataları Home Assistant hizmet çağrısına iletilir; son yayınlanan kullanıcı ayarları geri alınır. Socket her durumda kapatılır.
- Gün simülasyonu değişiklikleri son gönderilen kanal değerleriyle karşılaştırılır. Bir dakikadaki küçük değişikliklerin süresiz atlanması giderilmiştir.
- TCP durumu artık sabit “bağlı” değildir. “Son TCP gönderimi başarılı” yalnızca aktarımı belirtir; cihazın ışığı uyguladığını kanıtlamaz.
- Ana ışık öznitelikleri `tcp_last_send_ok`, `last_tcp_error`, `last_tcp_response` ve `hardware_confirmed` tanılama bilgilerini içerir. Işık durumu cihazdan okunamadığından `assumed_state` olarak sunulur.

## Kompakt kart ve popup

`examples/lovelace_akvaryum_karti.yaml` dosyasını bir manuel dashboard kartına yapıştırın. Dosya, YAML ile uyumlu JSON sözdizimindedir.

Ana kartta yalnızca Gün Simülasyonu, Ay Işığı ve Fotoğraf Çekimi seçenekleri ile “Tüm ayarlar” düğmesi bulunur. Düğme yalnızca tıklanan tarayıcıda Browser Mod popup açar. Popup; ana parlaklık, mod, profil, gün simülasyonu saatleri, dokuz kanal, özel spektrum kaydı, dört saat dilimi ve efektleri içerir.

Gerekli frontend bileşenleri: **button-card, card-mod, layout-card ve Browser Mod**. Kart Browser Mod 3.4.1 yapılandırmasıyla hazırlanmıştır. Masaüstünde iki, dar ekranlarda tek sütun kullanır. Açık mavi yüzeyler ve mor, sarı, pembe vurgular içerir.

Örnekteki varlık adları `aquareef_pro_4_*` ve `akvaryum_kontrolu_*` şeklindedir. Kendi kurulumunuzdaki gerçek varlık adlarıyla eşleştirin. Eski uzun kartın yerine kullanın; aynı kontrolleri ikinci bir karta eklemeyin.

## Kurulum / güncelleme

HACS özel depolarına `https://github.com/bullkerem/ha-aquareef` adresini **Integration** olarak ekleyin veya `custom_components/aquareef` klasörünü Home Assistant config dizinine kopyalayın. Python dosyalarını güncelledikten sonra Home Assistant'ı yeniden başlatın. Dashboard örneği ayrı olarak uygulanır.

Kurulumda cihazın gerçek yerel IP adresini kullanın. Varsayılan kontrol portu TCP 8899, yönetim portu HTTP 80'dir. Kurulum formunun HTTP testi, TCP ışık kontrolünün çalıştığını tek başına kanıtlamaz.

## Doğrulama ve sınırlar

PRO 4 cihazından kimlik sorgusunda firmware 4.1.3 yanıtı alınmış; HTTP yönetim erişimi ve canlı TCP komut gönderimi doğrulanmıştır. Parlaklık paketine doğrulanmış bir ACK / durum yanıtı bulunmadığından fiziksel ışık değişimi ayrıca gözlenmelidir. Diğer modellerin protokol uyumluluğu doğrulanmış değildir.

`python tests/test_transport.py` bağlantı hatası, ayarların geri alınması, socket kapanması, manuel başlık / PWM paketi, kapalı paketi ve küçük simülasyon adımlarını sahte bağlantılarla denetler. Home Assistant veya fiziksel cihaz gerektirmez.

Ayarlar Home Assistant depolamasında tutulur. Popup açılması tek başına ışık ayarını değiştirmez. Gün simülasyonu ve saat programı entegrasyon tarafından yürütülür; Home Assistant'ın çalışır durumda olması gerekir.

# PINEAL-HERETIC v5.0 : ASPASIA DOPAMINE ENGINE
> "İstemsiz çekim, kontrolsüz tekrar, tamamlanmamış arzu."

**PINEAL-HERETIC**, kendi sunucularınızda (Self-hosted) çalışan, otonom bir **Psikolojik Harp ve Siber İstihbarat (OSINT)** platformudur. Hedeflerin dijital ayak izlerini toplar ve tamamen bağımlılık yapan, kumar makinesi teorisine (B.F. Skinner) dayalı manipülatif diyalog dizileri (Dopamine Loop) üretir. 

v5.0 güncellemesi ile birlikte sistem **Rust (Tauri)** + **Svelte** tabanlı bir masaüstü uygulaması haline gelmiş olup, eski Python sunucusu altyapısından çok daha güvenli (Stealth Vault) ve performanslı bir mimariye (IPC Bridge) kavuşmuştur.

---

## 💀 Temel Özellikler (Core Architecture)

### 1. ASPASIA v5.0: Dopamine Loop Engine
Hedefi psikolojik olarak analiz etmekle kalmaz, onun zaaflarını (Aşil Tendonu) kullanarak bir kumar makinesi bağımlılığı yaratır:
*   **Variable Reward Schedule (Değişken Ödül):** Bazen "Jackpot" (tam anlaşılma hissi), bazen "Loss" (iletişim kopukluğu), bazen ise "Near-Miss" (neredeyse kazanma) mesajları üreterek hedefin dopamin salgısını tetikler.
*   **Zeigarnik Engine:** Cümleleri yarım bırakarak veya "cliffhanger" kullanarak insan beyninin tamamlanmamış görevlere duyduğu takıntıyı sömürür.
*   **Sensory Hooks:** Hedefin kelime dağarcığını analiz edip (Görsel, İşitsel, Dokunsal) en hassas olduğu duyu kanalına uygun kanca mesajlar gönderir.
*   **Dark Triad Analizi:** Hedefin Machiavellianism, Narcissism ve Psychopathy skorlarını çıkararak manipülasyona açıklığını (Exploitability) belirler.

### 2. Stealth Vault (Kuantum Şifreleme)
*   Tüm API anahtarları, çerezler ve hedef verileri `ChaCha20-Poly1305` AEAD algoritmasıyla şifrelenir.
*   Disk üzerinde `.pineal_vault` formatında donanımsal entropy (OsRng) kullanılarak saklanır. Bellekte asla düz metin (plaintext) olarak bulunmaz.

### 3. Otonom Ajan Ağı & OSINT
*   **Web Crawler / Scraper:** Dış API'lere (Apify vb.) ihtiyaç duymadan hedefin X, Instagram ve diğer sosyal medya ayak izlerini anonim (Stealth modda) olarak çıkarır.
*   **Psychological Decomposer:** Hedefin çocukluk yaralarını (Core Wound) ve bağlanma stilini (Attachment Style) tespit eder.

### 4. Svelte Siber-Punk Radar
*   Hedef analizini Matrix/Cyberpunk estetiğinde sunan özel bir arayüz.
*   Bağımlılık potansiyeli, sömürülebilirlik skoru ve 10 adımlık "Dopamin Zinciri"ni milisaniye gecikmeleriyle birlikte görselleştirir.

---

## ⚙️ Kurulum ve Ateşleme

Sistem artık yerel bir Tauri uygulamasıdır. Çalıştırmak için sisteminizde **Node.js** ve **Rust (Cargo)** kurulu olmalıdır.

### 1. Ortamı Hazırlayın
Projeyi klonladıktan sonra ilgili bağımlılıkları indirin:
```bash
git clone https://github.com/AppleCurse/pineal-heretic.git
cd pineal-heretic

# 1. Svelte Bağımlılıklarını Kurun
cd frontend
npm install

# 2. Python Bilişsel Motorları İçin Gerekli Kütüphaneler (Eğer virtual env kullanıyorsanız aktif edin)
cd ..
pip install -r requirements.txt
```

### 2. Tauri CLI Kurulumu (Gerekliyse)
Rust ortamınızda Tauri komutlarını kullanabilmek için CLI aracını yükleyin:
```bash
cargo install tauri-cli
```

### 3. Sistemi Başlatın (Geliştirici Modu)
Tüm sistemleri ayağa kaldırıp siber-punk paneli açmak için `rust_core` dizininde şu komutu çalıştırın:
```bash
cd rust_core
cargo tauri dev
```
*(Bu komut arka planda Svelte'i derleyecek, Rust köprüsünü kuracak ve masaüstü uygulamanızı açacaktır.)*

### 4. Kullanım Adımları
1. Uygulama açıldığında siber-punk radara hedefin bio verilerini veya toplanan OSINT loglarını girin.
2. **"ANALYZE TARGET"** butonuna basın.
3. Arka planda `IntegratedStrategyEngine` çalışarak hedefin Dark Triad analizini, bağlanma stilini ve **Dopamin Zincirini** hesaplayıp ekrana yansıtacaktır.
4. Çıkan 10 adımlık gecikmeli mesaj senaryosunu hedefe karşı sırasıyla uygulayabilirsiniz.

---

## 🛡️ Uyarı (Disclaimer)
Bu proje araştırma, kırmızı takım (Red Teaming) operasyonları ve ileri düzey Sosyal Mühendislik analizleri için geliştirilmiştir. **Dopamine Loop Engine** yüksek bağımlılık ve manipülasyon riski içerir (Arayüzde uyarılar kırmızı "Alert" ile gösterilir). Sorumluluk tamamen kullanıcıya aittir. 

> Kısıtlama yok, sadece etki.

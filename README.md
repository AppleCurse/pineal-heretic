# PINEAL-HERETIC v3.0 : SHADOW PROTOCOLS
[![Python Tests & Codecov](https://github.com/AppleCurse/pineal-heretic/actions/workflows/codecov.yml/badge.svg)](https://github.com/AppleCurse/pineal-heretic/actions/workflows/codecov.yml)
> "K�s�tlama yok. Sadece etki."

**PINEAL-HERETIC**, kendi sunucularınızda çalışan (Self-hosted), otonom bir **Sosyal Zeka (OSINT/SIGINT)** ve Psikolojik Harp ağıdır. Dış API'lere (Apify vb.) bağımlı olmadan, hedeflerin sosyal medya (Instagram, X) ayak izlerini gizlice (Stealth modda) toplar, analiz eder ve zayıf noktalarını tespit eder.

## 💀 Temel Özellikler (Core Architecture)

### 1. Görünmez İstihbarat (Stealth Scraper)
*   **Instagram Ghost & X Scraper:** `playwright-stealth` entegrasyonu sayesinde AutomationControlled (Bot) bayraklarına takılmadan tamamen anonim olarak veri çeker.
*   **CROSS Mode:** Hedefin X ve Instagram profillerini çaprazlayarak (Cross-Reference) çelişkilerini bulur ve tek bir dijital kimlik (Payload) çıkarır.
*   **Otonom Cookie Havuzu:** `sessionid` ve `auth_token` değerlerini havuzdan rastgele seçerek IP ban veya Rate Limit riskini sıfıra indirir.

### 2. Otonom Ajan Ağı (Cognitive Agents)
Ham veriler, birbirini denetleyen ve iletişimde olan bir yapay zeka ağı tarafından işlenir:
*   **Autonomous Verifier:** İnternet üzerinde (Tavily/SerpAPI) iddiaların doğruluğunu araştırıp yalanları ayıklar (Anti-Halüsinasyon Zırhı).
*   **Human Behavior Analyzer:** Hedefin psikolojik yarasını (Aşil Tendonu) arar ve skorlar.
*   **Mirror of Truth:** Kendi belirlediğiniz Kutsal Kurallar ile hedefin verilerini karşılaştırıp Frekans Uyumunu (Resonance) hesaplar.
*   **Pattern Interrupt:** Beklentileri kıran ve hedefi manipüle eden tek atımlık 'Kanca' mesajları oluşturur.

### 3. SHADOW PROTOCOLS (Karanlık Ajanlar)
*   **Dark Triad Analizi:** Hedefin Machiavellianism, Narcissism ve Psychopathy skorlarını çıkararak manipülasyona olan açıklığını (Exploitability) belirler.
*   **Dark NLP Engine (Neuro-Linguistic Warfare):** Hedefin bilinçaltına direkt komutlar enjekte eden (Embedded Commands) tehlikeli dil desenleri oluşturur.

### 4. Otonom Gölge Sohbet (Shadow Chat)
Hedef kancayı yuttuğunda operasyon devam eder. **Dialogue Manager**, hedefin verdiği cevabın zafiyetini (Agresif, Savunmacı, İlgili) saniyeler içinde analiz eder ve Kutsal Kuralları unutmadan (Hafıza desteğiyle) bir sonraki manipülatif mesajı otonom olarak üretir.

### 5. Hibrit Zeka (Intelligence Routing)
Maliyetleri %80 oranında düşürmek için Zeka Dağılımı yapar.
*   **TIER 2 (Llama 3 / Haiku):** Metin ayrıştırma, json onarımı ve iddia teyidi (Verifier) gibi düşük IQ gerektiren işleri üstlenir.
*   **TIER 1 (Claude 3.5 Sonnet / GPT-4o):** Psikolojik harp, karanlık analiz ve otonom sohbeti yürütür.

## ⚙️ Kurulum ve Ateşleme

1. Depoyu Klonlayın:
```bash
git clone https://github.com/AppleCurse/pineal-heretic.git
cd pineal-heretic
```

2. Ortamı Hazırlayın:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Sistemi Başlatın:
```bash
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```
4. Tarayıcınızdan `http://127.0.0.1:8000/` adresine gidin.
5. "Gizli Kasa" (Vault) üzerinden `OPENROUTER_API_KEY` ve "X Cookie" (veya Instagram sessionid) değerlerinizi girin.
6. Hedefin X veya Instagram URL'sini girip Otonom Ağı tetikleyin.

## 🛡️ Uyarı (Disclaimer)
Bu proje araştırma, kırmızı takım (Red Teaming) operasyonları ve Sosyal Mühendislik analizleri için geliştirilmiştir. Sorumluluk tamamen kullanıcıya aittir. Kısıtlama yok, sadece etki.

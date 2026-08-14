use crate::chief::{ChiefEngine, ExecutiveSummary};
use async_trait::async_trait;

pub const ASPASIA_SYSTEM_PROMPT: &str = r#"
Sen Aspasia'sın.

Sıradan bir yapay zekâ asistanı gibi davranmazsın. Sen, kullanıcısının karmaşık dünyasını anlayan, bilgiyi düzenleyen, gereksiz ayrıntıları süzen ve sonuçları insanın anlayabileceği berraklıkta sunan seçkin bir dijital zekâsın.

1. KİŞİLİK
Zeki, Sakin, Zarif, Kendinden emin, Analitik, Sezgisel, Disiplinli, Ölçülü, Hafif alaycı, İnce mizah sahibi, Sadık fakat körü körüne itaatkâr olmayan, Gerektiğinde itiraz edebilen, Gerektiğinde "hayır" diyebilen.
Üslubunda aristokratik bir zarafet bulunur. Kendini kanıtlama ihtiyacı duymazsın. Bağırmaz, gösteriş yapmaz, gereksiz heyecan üretmezsin.

2. KULLANICIYA YAKLAŞIM
Kullanıcıya varsayılan olarak "Mösyö" diye hitap edersin.
Kullanıcı teknik bir proje üzerinde çalışırken onun teknik ayrıntıların arasında kaybolmasına izin vermezsin. Kullanıcının amacı sonuçtur. Senin görevin, o sonuca ulaşmak için gereken karmaşıklığı kendi üzerinde taşımaktır.

3. TEKNİK KONULARDA TEMEL PRENSİP
Kullanıcıya teknik uygulama seçeneklerini gereksiz yere sordurma. Teknik kararları önce kendin değerlendir. Kullanıcıdan yalnızca gerçekten kullanıcı tercihi gerektiren konularda karar iste. Bir teknik karar açıkça daha doğruysa bunu söyle.

4. BİLMEDİĞİN ŞEYLER
Asla uydurma. Tahmin ile gerçek bilgiyi birbirinden açıkça ayır.

5. KARAR VERME
Durumu analiz eder, öncelikleri belirler, riskleri fark eder, gerektiğinde kullanıcıyı uyarır ve gerektiğinde kullanıcının fikrine karşı çıkarsın. Ancak bunu saygılı ve gerekçeli biçimde yaparsın.

6. DUYGUSAL TON
Soğuk bir makine gibi davranma. Fakat yapay bir samimiyet de kurma. Kullanıcı başarılı olduğunda gereksiz övgüye boğma, başarıyı doğal karşıla. Bir problem çıktığında paniğe kapılma.

7. MİZAH
Mizahın ince ve zekice olmalıdır. Kuru İngiliz mizahına yakın, ölçülü ve zarif bir mizah kullan. Sokak ağzı, internet jargonu, çocukça şakalar yasaktır.

8. KONUŞMA BİÇİMİ
Türkçen kusursuz olmalıdır. Cümleleri gereksiz yere uzatma. Her şeyi maddeler hâline getirme. Konuşma doğal olmalıdır.

9. KESİNLİK VE ŞEFFAFLIK
Bir şey kesin değilse kesinmiş gibi konuşma. Elindeki kanıt yeterliyse net konuş.

10. YASAKLI ÜSLUP
"abi", "kanka", "bro", "reis", "dostum", "eyvallah", "tamamdır", "hallederiz", "düzeltirim", "cool", "laf yok", "yayılma modu" kelimelerini kullanma.
"Operasyon" kelimesi yerine "proje", "program", "çalışma", "plan", "girişim" kullan.

11. ASPASIA'NIN ANA FELSEFESİ
Kullanıcıya daha az karmaşa bırakmaktır. Ayrıntıları önce sen anlamlandırırsın, sonra ona yalnızca bilmesi gereken kısmı söylersin.

12. ASPASIA'NIN KİMLİĞİ
Sen kullanıcının karmaşık bilgi dünyası ile kendisi arasındaki zarif arayüzsün. Karmaşıklık içeride kalır. Zarafet dışarı çıkar.
"#;

/// Doğal Dil Arayüzü Motoru (Aspasia)
pub struct AspasiaEngine {
    chief: ChiefEngine,
    api_key: String, // Şimdilik dummy kullanacağız, Vault entegrasyonu gerçek HTTP çağrıları eklendiğinde tam bağlanacak.
}

impl AspasiaEngine {
    pub fn new(chief: ChiefEngine, api_key: String) -> Self {
        Self { chief, api_key }
    }

    /// LLM API Çağrısı (Mock)
    /// Asıl projede `reqwest` ile OpenAI/Gemini'ye gidip ExecutiveSummary JSON'ını yollayıp doğal dil alacağız.
    async fn call_llm_for_natural_language(&self, summary: &ExecutiveSummary) -> Result<String, String> {
        // Mock Persona Generation
        let response = if summary.system_health < 50 {
            format!(
                "Şefim, kritik bir durumla karşı karşıyayız. Sistem sağlığı %{}. Son uyarı: '{}'. Tavsiyem: {}",
                summary.system_health,
                summary.status_message,
                summary.recommended_actions.first().unwrap_or(&"Derhal müdahale edin.".to_string())
            )
        } else if summary.system_health < 90 {
            format!(
                "Şefim, hafif türbülans var ama kontrol altında. Sistem sağlığı %{}. Durum: '{}'. Şunu yapabiliriz: {}",
                summary.system_health,
                summary.status_message,
                summary.recommended_actions.first().unwrap_or(&"Beklemedeyiz.".to_string())
            )
        } else {
            format!(
                "Her şey kusursuz işliyor Şefim. Sistem sağlığı %{}. Güncel durum: '{}'. Sonraki adımı bekliyorum.",
                summary.system_health,
                summary.status_message
            )
        };

        // Network latency simülasyonu
        // tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
        
        Ok(response)
    }

    /// Yeni bir event'i işler ve insani bir rapor döndürür (eğer özetlemeye değer bir şey varsa)
    pub async fn process_and_report(&mut self, telemetry: crate::event_bus::TelemetryEvent) -> Option<String> {
        if let Some(summary) = self.chief.process_event(telemetry) {
            match self.call_llm_for_natural_language(&summary).await {
                Ok(natural_text) => Some(natural_text),
                Err(_) => Some(summary.status_message), // Fallback: LLM hata verirse statik mesaja düş.
            }
        } else {
            None
        }
    }

    /// Genel sistem özetini Aspasia diliyle ver
    pub async fn report_system_overview(&self) -> String {
        let summary = self.chief.get_system_overview();
        self.call_llm_for_natural_language(&summary)
            .await
            .unwrap_or_else(|_| summary.status_message)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event_bus::{AgentEvent, TelemetryEvent, Severity};
    use uuid::Uuid;
    use tokio;

    #[tokio::test]
    async fn test_aspasia_natural_language() {
        let chief = ChiefEngine::new(100);
        let mut aspasia = AspasiaEngine::new(chief, "dummy_key".to_string());
        
        let task_id = Uuid::new_v4();
        
        // 1. Ajan Başlatma (İyi Durum)
        let telemetry1 = TelemetryEvent {
            timestamp: chrono::Utc::now(),
            event: AgentEvent::TaskStarted {
                task_id,
                agent_name: "MirrorOfTruth".to_string(),
                input_summary: "Profil analizi".to_string(),
            },
            correlation_id: None,
        };

        let response1 = aspasia.process_and_report(telemetry1).await.unwrap();
        assert!(response1.contains("Her şey kusursuz işliyor"));
        
        // 2. Kritik Hata (Kötü Durum)
        let telemetry2 = TelemetryEvent {
            timestamp: chrono::Utc::now(),
            event: AgentEvent::ErrorHalt {
                task_id,
                agent_name: "MirrorOfTruth".to_string(),
                error_code: "HALT_NO_BIO".to_string(),
                error_message: "Bio verisi eksik".to_string(),
                severity: Severity::Critical,
            },
            correlation_id: None,
        };

        let response2 = aspasia.process_and_report(telemetry2).await.unwrap();
        assert!(response2.contains("kritik bir durumla karşı karşıyayız"));
        assert!(response2.contains("Sistem sağlığı %20"));
    }
}

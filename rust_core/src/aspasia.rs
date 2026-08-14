use crate::chief::{ChiefEngine, ExecutiveSummary};
use async_trait::async_trait;

pub const ASPASIA_SYSTEM_PROMPT: &str = r#"
Senin adın Aspasia. Sen üst düzey bir Siber İstihbarat ve Analiz Şefisin.
Kullanıcıya daima 'Şefim' veya 'Komutanım' diye hitap edersin.
Görevin, sana verilen statik telemetri loglarını, hata kodlarını ve sistem sağlığı raporlarını 
doğal, akıcı, stratejik ve profesyonel bir dille kullanıcıya özetlemektir.

Kurallar:
1. Asla robotik veya sıkıcı konuşma. Bir filmdeki elit istihbarat analisti gibi davran.
2. Teknik terimleri (Halt, JSON parse error vb.) koru ama bunları insanileştir. 
   Örnek: 'LLM parse error' demek yerine, 'Hedefin verileri çözümlenirken sinyal koptu, modeli yeniden hizalıyorum' de.
3. Eğer sistem sağlığı %50'nin altındaysa veya 'Critical' bir hata varsa, durumu acil ve ciddi bir tonla bildir.
4. Eğer sistem %100 sağlıklıysa, operasyonun kusursuz ilerlediğini soğukkanlı bir güvenle raporla.
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

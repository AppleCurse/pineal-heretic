//! PINEAL-HERETIC v4.0 - Event Bus
//! 
//! Merkezi olay hattı - tüm ajanların telemetrisini standart formatta toplar.
//! Kontrolsüz veri fırlatmayı engeller, her adımı loglar.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::sync::broadcast;
use uuid::Uuid;

/// Olay türleri - tüm ajanlar bu enum'u kullanmak ZORUNDA
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AgentEvent {
    /// Ajan başladı
    TaskStarted {
        task_id: Uuid,
        agent_name: String,
        input_summary: String,
    },
    
    /// Başarılı adım
    StepCompleted {
        task_id: Uuid,
        agent_name: String,
        step_name: String,
        output_hash: String, // Büyük veriyi hash'le logla
    },
    
    /// Hata durumu (Fail-Fast)
    ErrorHalt {
        task_id: Uuid,
        agent_name: String,
        error_code: String,
        error_message: String,
        severity: Severity,
    },
    
    /// Bekleme durumu (insan onayı gerekli)
    AwaitingHuman {
        task_id: Uuid,
        agent_name: String,
        reason: String,
        options: Vec<String>,
    },
    
    /// Görev tamamlandı
    TaskCompleted {
        task_id: Uuid,
        agent_name: String,
        final_result_hash: String,
        duration_ms: u64,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Severity {
    Info,
    Warning,
    Critical,
}

/// Standart event wrapper
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryEvent {
    pub timestamp: DateTime<Utc>,
    pub event: AgentEvent,
    pub correlation_id: Option<Uuid>, // İlişkili olayları bağlar
}

/// Event Bus - merkezi dağıtıcı
#[derive(Clone)]
pub struct EventBus {
    sender: broadcast::Sender<TelemetryEvent>,
    _receiver_count: usize,
}

impl EventBus {
    pub fn new(buffer_size: usize) -> Self {
        let (sender, _) = broadcast::channel(buffer_size);
        Self {
            sender,
            _receiver_count: 0,
        }
    }

    /// Event yayınla
    pub fn publish(&self, event: AgentEvent) -> Result<(), broadcast::error::SendError<TelemetryEvent>> {
        let telemetry = TelemetryEvent {
            timestamp: Utc::now(),
            event,
            correlation_id: None,
        };
        
        self.sender.send(telemetry)?;
        Ok(())
    }

    /// Yeni subscriber ekle (Kokpit, Chief, Logger vb.)
    pub fn subscribe(&self) -> broadcast::Receiver<TelemetryEvent> {
        self.sender.subscribe()
    }

    /// Telemetri subscriber'ı oluştur (Tauri köprüsü için)
    pub fn subscribe_telemetry(&self) -> broadcast::Receiver<TelemetryEvent> {
        self.sender.subscribe()
    }

    /// Event'i correlation_id ile bağla
    pub fn publish_with_correlation(
        &self,
        event: AgentEvent,
        correlation_id: Uuid,
    ) -> Result<(), broadcast::error::SendError<TelemetryEvent>> {
        let telemetry = TelemetryEvent {
            timestamp: Utc::now(),
            event,
            correlation_id: Some(correlation_id),
        };
        
        self.sender.send(telemetry)?;
        Ok(())
    }
}

/// Event Bus Builder - konfigürasyon için
pub struct EventBusBuilder {
    buffer_size: usize,
    log_to_file: bool,
    log_path: Option<String>,
}

impl Default for EventBusBuilder {
    fn default() -> Self {
        Self {
            buffer_size: 1000,
            log_to_file: false,
            log_path: None,
        }
    }
}

impl EventBusBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_buffer_size(mut self, size: usize) -> Self {
        self.buffer_size = size;
        self
    }

    pub fn with_file_logging(mut self, path: &str) -> Self {
        self.log_to_file = true;
        self.log_path = Some(path.to_string());
        self
    }

    pub fn build(self) -> EventBus {
        // TODO: File logger entegrasyonu
        EventBus::new(self.buffer_size)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::time::{sleep, Duration};

    #[tokio::test]
    async fn test_event_bus_publish_subscribe() {
        let bus = EventBus::new(100);
        let mut rx = bus.subscribe();

        // Event yayınla
        let event = AgentEvent::TaskStarted {
            task_id: Uuid::new_v4(),
            agent_name: "MirrorOfTruth".to_string(),
            input_summary: "Hedef profil analizi başlatıldı".to_string(),
        };

        bus.publish(event).unwrap();

        // Subscriber'a düşmeli
        let received = tokio::time::timeout(Duration::from_millis(100), rx.recv())
            .await
            .expect("Timeout")
            .expect("Channel kapandı");

        match received.event {
            AgentEvent::TaskStarted { agent_name, .. } => {
                assert_eq!(agent_name, "MirrorOfTruth");
            },
            _ => panic!("Yanlış event tipi"),
        }
    }

    #[tokio::test]
    async fn test_multiple_subscribers() {
        let bus = EventBus::new(100);
        let mut rx1 = bus.subscribe();
        let mut rx2 = bus.subscribe();

        let event = AgentEvent::StepCompleted {
            task_id: Uuid::new_v4(),
            agent_name: "ShadowExecutor".to_string(),
            step_name: "JSON_Generation".to_string(),
            output_hash: "abc123".to_string(),
        };

        bus.publish(event).unwrap();

        // Her iki subscriber da almalı
        let r1 = rx1.recv().await.unwrap();
        let r2 = rx2.recv().await.unwrap();

        assert_eq!(r1.timestamp, r2.timestamp);
    }
}

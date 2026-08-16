//! PINEAL-HERETIC v4.0 - Chief Engine (Aspasia Özeti)
//! 
//! Binlerce satırlık telemetriyi 50 tokenlik insani özete damıtır.
//! Kullanıcıya sadece stratejik bilgiyi, teknik detayı gizleyerek sunar.

use crate::event_bus::{AgentEvent, TelemetryEvent};
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

/// Kokpit Şefi'nin kullanıcıya sunduğu özet durum
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutiveSummary {
    /// Tek cümlelik durum raporu (< 50 token)
    pub status_message: String,
    
    /// Önerilen aksiyonlar (insani dilde)
    pub recommended_actions: Vec<String>,
    
    /// Kritik uyarılar (varsa)
    pub critical_alerts: Vec<String>,
    
    /// Sistem sağlığı (0-100)
    pub system_health: u8,
}

/// Log Damıtıcı - ham telemetry'yi özetler
pub struct ChiefEngine {
    /// Son N event'i tutar (circular buffer)
    event_buffer: VecDeque<TelemetryEvent>,
    max_buffer_size: usize,
    
    /// Görev bazlı özetler
    task_summaries: std::collections::HashMap<uuid::Uuid, TaskContext>,
}

/// Görev bağlamı - her task için birikimli durum
#[derive(Debug, Clone)]
struct TaskContext {
    agent_name: String,
    start_time: chrono::DateTime<chrono::Utc>,
    last_step: String,
    error_count: u32,
    is_halted: bool,
}

impl ChiefEngine {
    pub fn new(buffer_size: usize) -> Self {
        Self {
            event_buffer: VecDeque::with_capacity(buffer_size),
            max_buffer_size: buffer_size,
            task_summaries: std::collections::HashMap::new(),
        }
    }

    /// Ham event'i işle ve özet üret
    pub fn process_event(&mut self, telemetry: TelemetryEvent) -> Option<ExecutiveSummary> {
        // Buffer'a ekle
        if self.event_buffer.len() >= self.max_buffer_size {
            self.event_buffer.pop_front();
        }
        self.event_buffer.push_back(telemetry.clone());

        // Event tipine göre özet üret
        match &telemetry.event {
            AgentEvent::TaskStarted { task_id, agent_name, input_summary } => {
                self.task_summaries.insert(*task_id, TaskContext {
                    agent_name: agent_name.clone(),
                    start_time: telemetry.timestamp,
                    last_step: "Başlatıldı".to_string(),
                    error_count: 0,
                    is_halted: false,
                });

                Some(ExecutiveSummary {
                    status_message: format!("{} ajanı {} görevine başladı.", agent_name, input_summary),
                    recommended_actions: vec!["İlerlemeyi izleyin.".to_string()],
                    critical_alerts: vec![],
                    system_health: 100,
                })
            },

            AgentEvent::StepCompleted { task_id, agent_name, step_name, .. } => {
                // Task context güncelle
                if let Some(ctx) = self.task_summaries.get_mut(task_id) {
                    ctx.last_step = step_name.clone();
                }

                Some(ExecutiveSummary {
                    status_message: format!("{} başarılı: {}", agent_name, step_name.replace('_', " ")),
                    recommended_actions: vec!["Sonraki adımı bekleyin.".to_string()],
                    critical_alerts: vec![],
                    system_health: 95,
                })
            },

            AgentEvent::ErrorHalt { task_id, agent_name, error_message, severity, .. } => {
                // Task context güncelle
                if let Some(ctx) = self.task_summaries.get_mut(task_id) {
                    ctx.error_count += 1;
                    ctx.is_halted = true;
                }

                let alert = format!("KRİTİK: {} durdu - {}", agent_name, error_message);
                
                Some(ExecutiveSummary {
                    status_message: format!("⚠️ Sistem durduruldu: {}", error_message),
                    recommended_actions: vec![
                        "Hata loglarını inceleyin.".to_string(),
                        "Farklı hedef deneyin.".to_string(),
                    ],
                    critical_alerts: vec![alert],
                    system_health: match severity {
                        crate::event_bus::Severity::Info => 70,
                        crate::event_bus::Severity::Warning => 50,
                        crate::event_bus::Severity::High => 35,
                        crate::event_bus::Severity::Critical => 20,
                    },
                })
            },

            AgentEvent::AwaitingHuman { task_id, agent_name, reason, options } => {
                Some(ExecutiveSummary {
                    status_message: format!("🤋 İnsan onayı gerekli: {}", reason),
                    recommended_actions: options.clone(),
                    critical_alerts: vec![],
                    system_health: 80,
                })
            },

            AgentEvent::TaskCompleted { task_id, agent_name, duration_ms, .. } => {
                // Task context temizle
                self.task_summaries.remove(task_id);

                let duration_sec = *duration_ms as f64 / 1000.0;
                Some(ExecutiveSummary {
                    status_message: format!("✅ Görev tamamlandı! {} süresince {} çalıştı.", 
                                           format!("{:.1}s", duration_sec), agent_name),
                    recommended_actions: vec!["Sonuçları inceleyin.".to_string()],
                    critical_alerts: vec![],
                    system_health: 100,
                })
            },

            AgentEvent::FrequencyUpdate { task_id: _, ritual_match_score, playlist_resonance, envy_intensity, overall_frequency } => {
                Some(ExecutiveSummary {
                    status_message: format!("📊 Frekans analizi: {} (Ritual: {:.0}%, Playlist: {:.0}%, Envy: {:.0}%)", 
                                           overall_frequency, ritual_match_score * 100.0, 
                                           playlist_resonance * 100.0, envy_intensity * 100.0),
                    recommended_actions: vec!["Frekans eşleşmelerini değerlendirin.".to_string()],
                    critical_alerts: vec![],
                    system_health: 85,
                })
            },
        }
    }

    /// Tüm görevlerin genel durumunu özetle
    pub fn get_system_overview(&self) -> ExecutiveSummary {
        let active_tasks = self.task_summaries.len();
        let halted_tasks = self.task_summaries.values().filter(|ctx| ctx.is_halted).count();
        let total_errors: u32 = self.task_summaries.values().map(|ctx| ctx.error_count).sum();

        let status_msg = if halted_tasks > 0 {
            format!("⚠️ {} görev durduruldu, {} aktif", halted_tasks, active_tasks)
        } else {
            format!("✓ {} görev devam ediyor", active_tasks)
        };

        ExecutiveSummary {
            status_message: status_msg,
            recommended_actions: if total_errors > 0 {
                vec![format!("{} hata tespit edildi, logları kontrol edin", total_errors)]
            } else {
                vec!["Sistem normal çalışıyor".to_string()]
            },
            critical_alerts: if halted_tasks > 0 {
                vec![format!("{} görev kritik hata nedeniyle durdu", halted_tasks)]
            } else {
                vec![]
            },
            system_health: if halted_tasks > 0 { 40 } else { 90 },
        }
    }

    /// Belirli bir görevin detaylı durumunu al
    pub fn get_task_status(&self, task_id: &uuid::Uuid) -> Option<ExecutiveSummary> {
        self.task_summaries.get(task_id).map(|ctx| {
            let status = if ctx.is_halted {
                format!("⚠️ {} (Durduruldu - {} hata)", ctx.agent_name, ctx.error_count)
            } else {
                format!("✓ {} çalışıyor (Son adım: {})", ctx.agent_name, ctx.last_step)
            };

            ExecutiveSummary {
                status_message: status,
                recommended_actions: if ctx.is_halted {
                    vec!["Hatayı giderin ve yeniden deneyin".to_string()]
                } else {
                    vec!["İzlemeye devam edin".to_string()]
                },
                critical_alerts: if ctx.is_halted {
                    vec![format!("{} ajanı durduruldu", ctx.agent_name)]
                } else {
                    vec![]
                },
                system_health: if ctx.is_halted { 30 } else { 85 },
            }
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event_bus::{AgentEvent, Severity};
    use uuid::Uuid;

    #[test]
    fn test_chief_summarizes_task_started() {
        let mut chief = ChiefEngine::new(100);
        
        let task_id = Uuid::new_v4();
        let telemetry = TelemetryEvent {
            timestamp: chrono::Utc::now(),
            event: AgentEvent::TaskStarted {
                task_id,
                agent_name: "MirrorOfTruth".to_string(),
                input_summary: "Profil analizi".to_string(),
            },
            correlation_id: None,
        };

        let summary = chief.process_event(telemetry).unwrap();
        
        assert!(summary.status_message.contains("MirrorOfTruth"));
        assert!(summary.status_message.contains("başladı"));
        assert_eq!(summary.system_health, 100);
    }

    #[test]
    fn test_chief_detects_critical_halt() {
        let mut chief = ChiefEngine::new(100);
        
        let task_id = Uuid::new_v4();
        
        // Önce başlat
        chief.process_event(TelemetryEvent {
            timestamp: chrono::Utc::now(),
            event: AgentEvent::TaskStarted {
                task_id,
                agent_name: "ShadowExecutor".to_string(),
                input_summary: "Test".to_string(),
            },
            correlation_id: None,
        });

        // Sonra hata
        let halt_event = TelemetryEvent {
            timestamp: chrono::Utc::now(),
            event: AgentEvent::ErrorHalt {
                task_id,
                agent_name: "ShadowExecutor".to_string(),
                error_code: "LLM_FORMAT_ERROR".to_string(),
                error_message: "JSON parse başarısız".to_string(),
                severity: Severity::Critical,
            },
            correlation_id: None,
        };

        let summary = chief.process_event(halt_event).unwrap();
        
        assert!(summary.status_message.contains("durduruldu"));
        assert!(!summary.critical_alerts.is_empty());
        assert_eq!(summary.system_health, 20);
    }
}
